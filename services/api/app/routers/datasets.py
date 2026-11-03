"""POST /api/datasets (อัปโหลด) · GET /api/datasets (เฉพาะของตัวเอง)

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md หัวข้อ 4
"""

from pathlib import PurePath

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from .. import db
from ..ingest import MAX_BYTES, IngestError, read_upload
from ..security import current_user

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("", status_code=status.HTTP_201_CREATED)
def upload(file: UploadFile = File(...), username: str = Depends(current_user)) -> dict:
    # อ่านเกินขีดจำกัด 1 byte เพื่อรู้ว่าไฟล์ใหญ่เกิน โดยไม่ต้องอ่านทั้งไฟล์เข้าหน่วยความจำ
    content = file.file.read(MAX_BYTES + 1)
    try:
        tables = read_upload(file.filename or "", content)
    except IngestError as exc:
        code = status.HTTP_413_CONTENT_TOO_LARGE if len(content) > MAX_BYTES else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc)) from exc

    name = PurePath(file.filename or "data").name[:128]
    created = db.create_dataset(username, name, tables)
    return {"dataset_id": created["dataset_id"], "tables": created["tables"]}


@router.get("")
def list_mine(username: str = Depends(current_user)) -> list[dict]:
    return db.list_datasets(username)
