"""GET /api/model

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md หัวข้อ 1, 4
"""

from fastapi import APIRouter, Depends

from ..agent.model import model_info
from ..security import current_user

router = APIRouter(prefix="/api", tags=["model"])


@router.get("/model")
def get_model(_username: str = Depends(current_user)) -> dict:
    return model_info()
