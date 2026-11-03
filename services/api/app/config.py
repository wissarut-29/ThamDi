"""อ่านค่าตั้งจาก .env (MODEL_PATH, MODEL_BACKEND, JWT_SECRET, ...)

เจ้าของ: Suphakorn · งาน: S1 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md หัวข้อ 8
"""

import logging
import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
_PLACEHOLDER_SECRETS = {"", "change-me"}
# ใช้แทน JWT_SECRET ที่ยังเป็นค่าตัวอย่าง: สุ่มครั้งเดียวต่อ process ใครรู้ค่าใน .env.example ก็ปลอม token ไม่ได้
# (token เก่าใช้ไม่ได้หลังรีสตาร์ต ต้อง login ใหม่)
_RUNTIME_JWT_SECRET = secrets.token_urlsafe(32)

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    # อ่าน .env ที่ root ของ repo เสมอ ไม่ว่าจะรัน uvicorn จากโฟลเดอร์ไหน
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    MODEL_BACKEND: Literal["fake", "local"] = "fake"
    MODEL_PATH: Path = Path("models/thamdi")
    DEMO_MODE: bool = False
    JWT_SECRET: str = "change-me"
    DEMO_PASSWORD: str = "change-me"
    CORS_ORIGINS: str = ""
    DATA_DIR: Path = Path("data")

    @field_validator("MODEL_BACKEND", mode="before")
    @classmethod
    def _lower(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("MODEL_PATH", "DATA_DIR")
    @classmethod
    def _from_repo_root(cls, value: Path) -> Path:
        return value if value.is_absolute() else REPO_ROOT / value

    @property
    def jwt_secret(self) -> str:
        """secret ที่ใช้เซ็น/ตรวจ JWT จริง · ห้ามใช้ JWT_SECRET ตรง ๆ"""
        if self.JWT_SECRET.strip() in _PLACEHOLDER_SECRETS:
            return _RUNTIME_JWT_SECRET
        return self.JWT_SECRET

    @property
    def demo_password_usable(self) -> bool:
        """เครื่องเดโม (local) ห้ามสร้างผู้ใช้ demo ด้วยรหัสตัวอย่าง · fake (เครื่องพัฒนา) ยอมให้ใช้ได้"""
        password = self.DEMO_PASSWORD.strip()
        if not password:
            return False
        return not (self.MODEL_BACKEND == "local" and password in _PLACEHOLDER_SECRETS)

    @property
    def cors_origins(self) -> list[str]:
        # ว่างต้องได้ [] ห้ามกลายเป็น "*"
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip() and o.strip() != "*"]

    def warn_insecure(self) -> list[str]:
        """คืนชื่อค่าที่ยังเป็นค่าตัวอย่าง และ log คำเตือนเมื่อรันโมเดลจริง (เครื่องเดโม)"""
        weak = [
            name
            for name in ("JWT_SECRET", "DEMO_PASSWORD")
            if getattr(self, name).strip() in _PLACEHOLDER_SECRETS
        ]
        if weak and self.MODEL_BACKEND == "local":
            log.warning("ยังไม่ได้ตั้งค่า %s ใน .env (ยังเป็น change-me หรือว่าง)", ", ".join(weak))
        return weak


def get_settings() -> Settings:
    """ค่าตั้งปัจจุบัน · cache ไว้ อ่าน .env ใหม่เฉพาะเมื่อไฟล์หรือ env ที่เกี่ยวข้องเปลี่ยน
    (เทสต์ยังเปลี่ยนค่าด้วย monkeypatch.setenv ได้ทันทีโดยไม่ต้อง clear cache)"""
    env_file = Settings.model_config.get("env_file")
    try:
        mtime = Path(env_file).stat().st_mtime_ns if env_file else None
    except OSError:
        mtime = None
    env = tuple(os.environ.get(name) for name in Settings.model_fields)
    return _load_settings((str(env_file) if env_file else None, mtime, env))


@lru_cache(maxsize=16)
def _load_settings(_key: tuple) -> Settings:
    return Settings()
