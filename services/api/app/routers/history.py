"""GET /api/history (ประวัติคำถามของตัวเอง ใหม่สุดก่อน)

เจ้าของ: Suphakorn · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md หัวข้อ 4
"""

from fastapi import APIRouter, Depends, Query

from .. import db
from ..security import current_user

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def list_mine(
    dataset_id: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=50, ge=1, le=200),
    username: str = Depends(current_user),
) -> list[dict]:
    # กรองด้วย username เสมอ · dataset ของคนอื่นจึงได้รายการว่าง ไม่รั่วว่ามีอยู่จริง
    return db.list_history(username, dataset_id=dataset_id, limit=limit)
