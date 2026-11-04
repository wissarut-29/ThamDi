"""สร้างแอป API และผูก routers ทั้งหมด

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

รัน: cd services/api && uvicorn app.main:app --port 8000
"""

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .agent import model as model_backend
from .config import get_settings
from .routers import auth, chat, datasets, model
from .routers import eval as eval_router
from .security import current_user, hash_password, reset_rate_limits

DEMO_USERNAME = "demo"
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.warn_insecure()
    reset_rate_limits()
    db.init_db()
    # ผู้ใช้เดโมใช้รหัสจาก DEMO_PASSWORD ใน .env (ไม่ฮาร์ดโค้ด)
    if settings.demo_password_usable:
        db.upsert_user(DEMO_USERNAME, hash_password(settings.DEMO_PASSWORD))
    else:
        # ลบผู้ใช้ demo ที่อาจค้างจากรอบก่อน ไม่ให้ login ด้วยรหัสเดิมได้
        db.delete_user(DEMO_USERNAME)
        log.warning("ไม่สร้างผู้ใช้ demo: ตั้ง DEMO_PASSWORD ใน .env ก่อน (ห้ามว่าง/change-me บนเครื่องเดโม)")

    # โหลดโมเดลใน thread แยก API ตอบได้ทันที (ระหว่างนั้น /api/model บอก loaded=false)
    threading.Thread(target=model_backend.preload, name="model-preload", daemon=True).start()

    yield


def create_app() -> FastAPI:
    app = FastAPI(title="ThamDi API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(auth.router)
    app.include_router(datasets.router)
    app.include_router(chat.router)
    app.include_router(model.router)
    # routers/eval.py ของ Wissarut ไม่มีการตรวจ token เอง จึงครอบ token ไว้ตรงนี้ (CONTRACT หัวข้อ 4)
    app.include_router(eval_router.router, dependencies=[Depends(current_user)])
    return app


app = create_app()
