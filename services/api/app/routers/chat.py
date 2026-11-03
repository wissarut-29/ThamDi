"""POST /api/chat

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md หัวข้อ 4

ลำดับ: ตรวจ token → ตรวจเจ้าของ dataset → (DEMO_MODE/โมเดลไม่พร้อม: คำตอบเดโม)
→ pipeline.run() → answer.render() → บันทึกประวัติ
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from .. import db
from ..agent import answer, demo, pipeline
from ..agent.model import model_info
from ..config import get_settings
from ..security import current_user, require_dataset_owner

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])

NOT_READY_TEXT = "ตอนนี้โมเดลยังไม่พร้อม และคำถามนี้ไม่อยู่ในคำถามเดโม ลองใหม่อีกครั้งภายหลัง"


class ChatIn(BaseModel):
    dataset_id: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=500)


def _demo_answer(question: str) -> dict | None:
    # demo.lookup(question) -> dict | None เป็นของ Chalakorn (C5) ถ้ายังไม่มีให้ถือว่าไม่มีคำตอบเดโม
    lookup = getattr(demo, "lookup", None)
    return lookup(question) if lookup else None


@router.post("/chat")
def chat(body: ChatIn, username: str = Depends(current_user)) -> dict:
    require_dataset_owner(body.dataset_id, username)
    question = body.question.strip()

    if get_settings().DEMO_MODE or not model_info()["loaded"]:
        canned = _demo_answer(question)
        if canned is not None:
            reply = {k: canned.get(k) for k in ("answer", "status", "sql", "columns", "rows")}
        else:
            reply = {"answer": NOT_READY_TEXT, "status": "error", "sql": None, "columns": [], "rows": []}
    else:
        try:
            result = pipeline.run(question, body.dataset_id, "M3")
        except Exception:  # โมเดล/ฐานข้อมูลพัง ต้องไม่ทำให้ทั้ง request ล่ม
            log.exception("pipeline.run ล้มเหลว")
            result = pipeline.PipelineResult(status="error", error="internal")
        reply = {
            "answer": answer.render(question, result),
            "status": result.status,
            "sql": result.sql,
            "columns": result.columns,
            "rows": result.rows,
        }

    reply = jsonable_encoder(reply)  # date/Decimal → JSON
    db.add_history(username, body.dataset_id, question, reply["status"], reply["sql"], reply["answer"])
    return reply
