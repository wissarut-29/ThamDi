"""สร้าง/ตรวจ JWT และตรวจว่าผู้ใช้เป็นเจ้าของ dataset

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md
"""

import ipaddress
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


def _is_trusted(value: str, trusted) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(ip in net for net in trusted)


def client_ip(request: Request, trusted=None) -> str:
    """IP ของผู้ใช้ · ถ้ามาจาก proxy ที่เชื่อได้ (TRUSTED_PROXIES เช่น Cloudflare tunnel → เว็บ Next.js → API
    ในเครื่องเดียวกัน หรือ container เว็บใน Docker) ใช้ X-Forwarded-For ไม่งั้นทุกคนที่เข้าผ่านลิงก์จะนับเป็น IP
    ของ proxy เดียวกัน แล้วโดน rate limit รวมกันทั้งห้อง
    เอาค่าขวาสุดที่ไม่ใช่ proxy ที่เชื่อได้ (proxy ต่อค่าทางขวา ผู้ใช้ปลอมได้แค่ค่าทางซ้าย จึงใช้ค่าแรกไม่ได้)"""
    if trusted is None:
        trusted = get_settings().trusted_proxies
    host = request.client.host if request.client else "-"
    if not _is_trusted(host, trusted):
        return host
    hops = [h.strip() for h in request.headers.get("x-forwarded-for", "").split(",") if h.strip()]
    for hop in reversed(hops):
        if not _is_trusted(hop, trusted):
            return hop
    return host


def limit_by_ip(bucket: str, limit: int, window_s: float = 60):
    """dependency: จำกัดตาม IP (ใช้กับ login กันเดารหัส)"""

    def dependency(request: Request) -> None:
        _check_rate(bucket, client_ip(request), limit, window_s)

    return dependency


# บัญชี demo ใช้ร่วมกันทั้งห้องตอนเดโม จึงได้ limit ต่อผู้ใช้มากกว่าบัญชีทั่วไป
SHARED_USERS = frozenset({"demo"})
SHARED_MULTIPLIER = 6


def limit_by_user(bucket: str, limit: int, window_s: float = 60):
    """dependency: จำกัดตามผู้ใช้ (ใช้กับ chat/upload กันถามรัวจนโมเดลค้าง) · คืนชื่อผู้ใช้
    บัญชีที่ใช้ร่วมกัน (SHARED_USERS) ได้ limit x SHARED_MULTIPLIER เช่น chat 20 → 120 ครั้ง/นาที"""

    def dependency(username: str = Depends(current_user)) -> str:
        allowed = limit * SHARED_MULTIPLIER if username in SHARED_USERS else limit
        _check_rate(bucket, username, allowed, window_s)
        return username

    return dependency
