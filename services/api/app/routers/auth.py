"""POST /api/auth/login · POST /api/auth/register · GET /api/auth/config

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md หัวข้อ 4
"""

import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .. import db
from ..config import get_settings
from ..security import create_token, hash_password, limit_by_ip, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ต่อ IP ต่อนาที · ทั้งห้องที่ใช้ WiFi เดียวกันออกเน็ตด้วย IP เดียว (NAT) จึงตั้งให้พอสำหรับราว 50 คน
# ยังกันการเดารหัสได้: ลองได้ไม่เกิน 50 ครั้ง/นาที และ bcrypt ทำให้แต่ละครั้งช้าอยู่แล้ว
LOGIN_PER_IP = 50
REGISTER_PER_IP = 50


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


@router.post("/login", dependencies=[Depends(limit_by_ip("login", limit=LOGIN_PER_IP))])
def login(body: LoginIn) -> dict:
    # register เก็บชื่อเป็นตัวเล็กเสมอ · login ต้องแปลงแบบเดียวกัน (สมัคร Bob แล้ว login ด้วย Bob ได้)
    username = body.username.strip().lower()
    password_hash = db.get_password_hash(username)
    # ตอบแบบเดียวกันทั้งไม่มีผู้ใช้และรหัสผิด ไม่บอกว่ามีชื่อนี้หรือไม่
    if password_hash is None or not verify_password(body.password, password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    return {"token": create_token(username)}


USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,32}$")
RESERVED = {"demo", "admin", "root", "system", "thamdi"}


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)


@router.get("/config")
def auth_config() -> dict:
    """หน้าเว็บใช้ซ่อน/แสดงแท็บสมัครบัญชี (ไม่ต้องมี token)"""
    return {"allow_register": get_settings().ALLOW_REGISTER}


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_by_ip("register", limit=REGISTER_PER_IP))],
)
def register(body: RegisterIn) -> dict:
    settings = get_settings()
    if not settings.ALLOW_REGISTER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ปิดรับสมัครบัญชีใหม่อยู่")
    username = body.username.strip().lower()
    if not USERNAME_RE.fullmatch(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ชื่อผู้ใช้ใช้ได้เฉพาะ a-z 0-9 _ . - ยาว 3–32 ตัว",
        )
    if username in RESERVED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ชื่อผู้ใช้นี้ถูกใช้แล้ว")
    if db.count_users() >= settings.MAX_USERS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="จำนวนบัญชีเต็มแล้ว")
    if not db.create_user(username, hash_password(body.password)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ชื่อผู้ใช้นี้ถูกใช้แล้ว")
    # สมัครแล้วเข้าสู่ระบบทันที
    return {"token": create_token(username), "username": username}
