"""อ่านค่าตั้งจาก .env (MODEL_PATH, MODEL_BACKEND, JWT_SECRET, ...)

เจ้าของ: Suphakorn · งาน: S1 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md หัวข้อ 8
"""

import logging
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
_PLACEHOLDER_SECRETS = {"", "change-me"}

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    # อ่าน .env ที่ root ของ repo เสมอ ไม่ว่าจะรัน uvicorn จากโฟลเดอร์ไหน
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    MODEL_BACKEND: Literal["fake", "local"] = "fake"
    MODEL_PATH: Path = Path("models/thamdi")
    DEMO_MODE: bool = False
    JWT_SECRET: str = "change-me"
    DEMO_PASSWORD: str = "change-me"
    CORS_ORIGINS: str = ""
    DATA_DIR: Path = Path("data")

    @field_validator("MODEL_BACKEND", mode="before")
    @classmethod
    def _lower(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("MODEL_PATH", "DATA_DIR")
    @classmethod
    def _from_repo_root(cls, value: Path) -> Path:
        return value if value.is_absolute() else REPO_ROOT / value

    @property
    def cors_origins(self) -> list[str]:
        # ว่างต้องได้ [] ห้ามกลายเป็น "*"
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip() and o.strip() != "*"]

    def warn_insecure(self) -> list[str]:
        """คืนชื่อค่าที่ยังเป็นค่าตัวอย่าง และ log คำเตือนเมื่อรันโมเดลจริง (เครื่องเดโม)"""
        weak = [
            name
            for name in ("JWT_SECRET", "DEMO_PASSWORD")
            if getattr(self, name).strip() in _PLACEHOLDER_SECRETS
        ]
        if weak and self.MODEL_BACKEND == "local":
            log.warning("ยังไม่ได้ตั้งค่า %s ใน .env (ยังเป็น change-me หรือว่าง)", ", ".join(weak))
        return weak


def get_settings() -> Settings:
    # สร้างใหม่ทุกครั้ง (ถูกมาก) เทสต์จะได้เปลี่ยนค่าด้วย monkeypatch.setenv ได้ทันที
    return Settings()
