"""สร้าง/ตรวจ JWT และตรวจว่าผู้ใช้เป็นเจ้าของ dataset

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md
"""

import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import db
from .config import get_settings

TOKEN_TTL = timedelta(hours=8)  # พอสำหรับวันสอบทั้งวัน
_ALGORITHM = "HS256"
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        return False


def create_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": username, "iat": now, "exp": now + TOKEN_TTL}
    return jwt.encode(payload, get_settings().jwt_secret, algorithm=_ALGORITHM)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="กรุณาเข้าสู่ระบบใหม่",
        headers={"WWW-Authenticate": "Bearer"},
    )


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """dependency: คืนชื่อผู้ใช้จาก token · ไม่มี/หมดอายุ/ปลอม → 401"""
    if credentials is None:
        raise _unauthorized()
    try:
        payload = jwt.decode(
            credentials.credentials, get_settings().jwt_secret, algorithms=[_ALGORITHM]
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc
    username = payload.get("sub")
    if not username or not db.user_exists(username):
        raise _unauthorized()
    return username


def require_dataset_owner(dataset_id: str, username: str) -> dict:
    """คืนข้อมูล dataset ถ้าเป็นของผู้ใช้ · ของคนอื่นหรือไม่มี → 404 (ไม่บอกว่ามีอยู่จริง)"""
    dataset = db.get_dataset_meta(dataset_id)
    if dataset is None or dataset["owner"] != username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบ dataset")
    return dataset


# ---------- rate limit (S-09) · เก็บในหน่วยความจำ พอสำหรับเครื่องเดโมเครื่องเดียว ----------

_hits: dict[tuple[str, str], deque] = defaultdict(deque)
_hits_lock = threading.Lock()


def reset_rate_limits() -> None:
    with _hits_lock:
        _hits.clear()


def _check_rate(bucket: str, key: str, limit: int, window_s: float) -> None:
    now = time.monotonic()
    with _hits_lock:
        hits = _hits[(bucket, key)]
        while hits and now - hits[0] > window_s:
            hits.popleft()
        if len(hits) >= limit:
            retry = max(1, int(window_s - (now - hits[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"ส่งคำขอถี่เกินไป รออีก {retry} วินาทีแล้วลองใหม่",
                headers={"Retry-After": str(retry)},
            )
        hits.append(now)


def limit_by_ip(bucket: str, limit: int, window_s: float = 60):
    """dependency: จำกัดตาม IP (ใช้กับ login กันเดารหัส)"""

    def dependency(request: Request) -> None:
        _check_rate(bucket, request.client.host if request.client else "-", limit, window_s)

    return dependency


def limit_by_user(bucket: str, limit: int, window_s: float = 60):
    """dependency: จำกัดตามผู้ใช้ (ใช้กับ chat/upload กันถามรัวจนโมเดลค้าง) · คืนชื่อผู้ใช้"""

    def dependency(username: str = Depends(current_user)) -> str:
        _check_rate(bucket, username, limit, window_s)
        return username

    return dependency
