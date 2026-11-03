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
from .agent import pipeline
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
    if settings.DEMO_PASSWORD.strip():
        db.upsert_user(DEMO_USERNAME, hash_password(settings.DEMO_PASSWORD))
    else:
        log.warning("DEMO_PASSWORD ว่าง จะ login ผู้ใช้เดโมไม่ได้")

    # โหลดโมเดลใน thread แยก API ตอบได้ทันที (ระหว่างนั้น /api/model บอก loaded=false)
    threading.Thread(target=model_backend.preload, name="model-preload", daemon=True).start()

    # ชั่วคราว: pipeline.get_dataset() ยังเป็น stub (docs/ISSUES.md ข้อ 5) จึงเสียบ db.open_dataset
    # ตอนแอปเริ่ม และคืนของเดิมตอนปิด · ลบเมื่อ Chalakorn ให้ get_dataset เรียก db.open_dataset แล้ว
    original_get_dataset = pipeline.get_dataset
    pipeline.get_dataset = db.open_dataset
    try:
        yield
    finally:
        pipeline.get_dataset = original_get_dataset


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
