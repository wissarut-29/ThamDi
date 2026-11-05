"""โหลดโมเดลครั้งเดียว และให้ generate_sql() / model_info()

เจ้าของ: Suphakorn · งาน: S2 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md หัวข้อ 1

MODEL_BACKEND=fake  คืน SQL ตายตัวไว้เทสต์ (ไม่ import torch)
MODEL_BACKEND=local โหลดโมเดลที่ทีมเทรนเอง (HF format, merge LoRA แล้ว, fp16) จาก MODEL_PATH
                    ให้ตรงกับ ml/train.ipynb: prompt จาก ml/format.py ตรง ๆ ไม่ใส่ chat template,
                    tokenize ด้วย add_special_tokens=False, beam search ไม่ sample
"""

import json
import logging
import re
import threading
import time

from ..config import get_settings

log = logging.getLogger(__name__)

_REFUSE_WORDS = ("ลบ", "drop", "delete", "truncate")
_FIRST_TABLE = re.compile(r"CREATE\s+TABLE\s+(\w+)", re.IGNORECASE)
_QUESTION = re.compile(r"### คำถาม\n(.*?)\n\n### SQL", re.DOTALL)

MAX_NEW_TOKENS = 160
MAX_CONCURRENT = 1  # รันพร้อมกันได้ 1 งาน งานที่เกินรอคิว (CPU/RAM เครื่องเดโมมีจำกัด)
# รอคิวไม่นาน: request ที่รอยึด thread ของ FastAPI ไว้ ถ้ารอนาน endpoint อื่น (login, /api/model) จะค้างตาม
QUEUE_TIMEOUT_S = 10


class ModelNotReady(RuntimeError):
    """โมเดลยังโหลดไม่เสร็จ / โหลดไม่ขึ้น · router แปลงเป็น status error"""


class ModelBusy(ModelNotReady):
    """คิวโมเดลเต็มเกิน QUEUE_TIMEOUT_S · router ตอบ 503 ให้ผู้ใช้ลองใหม่"""


def _backend() -> str:
    # อ่านทุกครั้งที่เรียก เทสต์จะได้สลับ backend ด้วย monkeypatch.setenv ได้
    # ค่าที่ไม่ใช่ fake/local -> pydantic ValidationError (เป็น ValueError)
    return get_settings().MODEL_BACKEND


# ---------------------------------- fake ----------------------------------


def _fake_generate(prompt: str, n: int) -> list[str]:
    # ดูแค่ส่วนคำถาม ไม่ให้ชื่อคอลัมน์ใน schema ทำให้ปฏิเสธผิด
    match = _QUESTION.search(prompt)
    question = (match.group(1) if match else prompt).lower()
    if any(word in question for word in _REFUSE_WORDS):
        return ["<REFUSE>"] * n

    table = _FIRST_TABLE.search(prompt)
    sql = f"SELECT COUNT(*) AS n FROM {table.group(1)}" if table else "SELECT 1"
    return [sql] * n


# ---------------------------------- local ---------------------------------


class _LocalModel:
    """เก็บโมเดลที่โหลดแล้วไว้ทั้ง process · โหลดครั้งเดียว ถ้าโหลดไม่ขึ้นจำ error ไว้ไม่ลองซ้ำ"""

    def __init__(self):
        self._load_lock = threading.Lock()
        self._slots = threading.BoundedSemaphore(MAX_CONCURRENT)
        self.model = None
        self.tokenizer = None
        self.device = None
        self.error: str | None = None
        self.load_seconds: float | None = None

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        with self._load_lock:
            if self.loaded or self.error:
                return
            path = get_settings().MODEL_PATH
            if not (path / "config.json").is_file():
                self.error = f"ไม่พบไฟล์โมเดลที่ {path} (รัน make model ก่อน)"
                log.warning(self.error)
                return
            started = time.perf_counter()
            try:
                # import ตรงนี้ เพื่อให้ backend fake และ CI ไม่ต้องมี torch
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer

                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                # fp16 บน CPU ช้าและบาง op ไม่รองรับ จึงใช้ float32 บน CPU
                dtype = torch.float16 if self.device == "cuda" else torch.float32
                tokenizer = AutoTokenizer.from_pretrained(path)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                model = AutoModelForCausalLM.from_pretrained(path, dtype=dtype)
                model.to(self.device).eval()
            except Exception as exc:  # RAM ไม่พอ / ไฟล์เสีย ต้องไม่ทำให้ API ล่ม
                self.error = f"โหลดโมเดลไม่ขึ้น: {type(exc).__name__}: {exc}"
                log.exception("โหลดโมเดลไม่ขึ้น")
                return
            self.tokenizer, self.model = tokenizer, model
            self.load_seconds = round(time.perf_counter() - started, 1)
            log.info("โหลดโมเดลเสร็จใน %.1f วินาที บน %s", self.load_seconds, self.device)

    def generate(self, prompt: str, n: int) -> list[str]:
        self.load()
        if not self.loaded:
            raise ModelNotReady(self.error or "โมเดลยังไม่พร้อม")
        if not self._slots.acquire(timeout=QUEUE_TIMEOUT_S):
            raise ModelBusy("คิวโมเดลเต็ม")
        try:
            import torch

            inputs = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=MAX_NEW_TOKENS,
                    num_beams=max(n, 1),
                    num_return_sequences=n,
                    do_sample=False,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
        finally:
            self._slots.release()
        # decode เฉพาะส่วนหลัง prompt · โมเดลเรียนให้จบด้วย eos
        start = inputs["input_ids"].shape[1]
        return [self.tokenizer.decode(out[start:], skip_special_tokens=True).strip() for out in outputs]


_local = _LocalModel()


def preload() -> None:
    """เรียกตอนแอปเริ่ม (ใน thread แยก) API จะได้ตอบได้ระหว่างที่โมเดลกำลังโหลด"""
    if _backend() == "local":
        _local.load()


# โมเดลตั้งต้นตาม docs/MODEL_CARD.md · ใช้เมื่อ config.json ไม่มี _name_or_path
# (transformers 5 ไม่เขียนคีย์นี้ตอน export)
DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"


def _local_info() -> dict:
    path = get_settings().MODEL_PATH
    base_model, version = "", ""
    try:
        config = json.loads((path / "config.json").read_text(encoding="utf-8"))
        base_model = config.get("_name_or_path") or DEFAULT_BASE_MODEL
    except (OSError, ValueError):
        pass
    try:
        # ไฟล์ VERSION (ถ้ามี) ใส่มากับโมเดลตอน export เช่น v1, v2
        version = (path / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        pass
    return {
        "name": path.name,
        "base_model": base_model,
        "version": version,
        "backend": "local",
        "loaded": _local.loaded,
    }


# ---------------------------------- API -----------------------------------


def generate_sql(prompt: str, n: int = 1) -> list[str]:
    """คืนผลลัพธ์จากโมเดล n แบบ (beam) เรียงจากดีที่สุด แต่ละตัวเป็น SQL หรือ <REFUSE> / <CLARIFY>"""
    n = max(int(n), 1)
    if _backend() == "fake":
        return _fake_generate(prompt, n)
    return _local.generate(prompt, n)


def model_info() -> dict:
    """คืน {"name", "base_model", "version", "backend", "loaded"} ให้ GET /api/model"""
    if _backend() == "fake":
        return {
            "name": "thamdi-fake",
            "base_model": "-",
            "version": "fake",
            "backend": "fake",
            "loaded": True,
        }
    return _local_info()
