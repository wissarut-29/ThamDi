"""POST /api/auth/login

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md หัวข้อ 4
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from .. import db
from ..security import create_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


@router.post("/login")
def login(body: LoginIn) -> dict:
    password_hash = db.get_password_hash(body.username)
    # ตอบแบบเดียวกันทั้งไม่มีผู้ใช้และรหัสผิด ไม่บอกว่ามีชื่อนี้หรือไม่
    if password_hash is None or not verify_password(body.password, password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    return {"token": create_token(body.username)}
