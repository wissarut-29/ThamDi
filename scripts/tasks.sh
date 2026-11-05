#!/bin/sh
# คำสั่งประจำของโปรเจกต์ · ใช้ได้ทั้ง Git Bash บน Windows (ไม่มี make) และ macOS/Linux
#   sh scripts/tasks.sh setup|data|test|model|dev|funnel
# Makefile เรียกไฟล์นี้อีกที จะได้มีคำสั่งชุดเดียว
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
PYTHON=${PYTHON:-python}
PORT=${PORT:-8000}

case "${1:-}" in
setup)
    # ติดตั้งไลบรารีของ API + eval (ไม่รวม torch: ใช้ requirements-model.txt เมื่อจะรันโมเดลจริง)
    "$PYTHON" -m pip install -r services/api/requirements.txt -r eval/requirements.txt
    [ -f .env ] || { cp .env.example .env; echo "สร้าง .env จาก .env.example แล้ว — แก้ JWT_SECRET/DEMO_PASSWORD ก่อนใช้จริง"; }
    ;;
data)
    "$PYTHON" scripts/gen_sales_db.py
    ;;
test)
    (cd services/api && ruff check . && MODEL_BACKEND=fake "$PYTHON" -m pytest -q)
    PYTHONUTF8=1 "$PYTHON" eval/run.py --check-gold
    ;;
model)
    # ลิงก์โมเดลอยู่ใน docs/MODEL_CARD.md (Chalakorn) · ใส่เป็น MODEL_URL ไฟล์ .zip ที่ข้างในเป็นโฟลเดอร์ HF
    : "${MODEL_URL:?ตั้ง MODEL_URL ก่อน เช่น MODEL_URL=https://... sh scripts/tasks.sh model}"
    dest=${MODEL_PATH:-models/thamdi}
    mkdir -p "$dest"
    tmp="$dest.download.zip"
    # MODEL_CURL_OPTS=--ssl-no-revoke ใช้บน Windows ที่ curl ขึ้น CRYPT_E_REVOCATION_OFFLINE
    # shellcheck disable=SC2086
    curl -fL --retry 3 ${MODEL_CURL_OPTS:-} -o "$tmp" "$MODEL_URL"
    # zip จาก Drive มักมีโฟลเดอร์ชั้นบนครอบ (เช่น model/config.json) → ย้ายของข้างในขึ้นมาไว้ที่ $dest ตรง ๆ
    "$PYTHON" - "$tmp" "$dest" <<'PY'
import shutil, sys, tempfile, zipfile
from pathlib import Path

zip_path, dest = sys.argv[1], Path(sys.argv[2])
with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
    zipfile.ZipFile(zip_path).extractall(tmp)
    root = Path(tmp)
    entries = [p for p in root.iterdir() if p.name != "__MACOSX"]
    if len(entries) == 1 and entries[0].is_dir():
        root = entries[0]
    for item in root.iterdir():
        target = dest / item.name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
        shutil.move(str(item), str(target))
PY
    rm -f "$tmp"
    [ -f "$dest/config.json" ] || { echo "ไม่พบ $dest/config.json หลังแตกไฟล์ — zip ไม่ใช่โฟลเดอร์โมเดล HF" >&2; exit 1; }
    # หน้า "เกี่ยวกับโมเดล" อ่านเวอร์ชันจากไฟล์นี้ · zip จาก Drive ไม่มีไฟล์นี้มาให้
    [ -f "$dest/VERSION" ] || echo "${MODEL_VERSION:-v2}" > "$dest/VERSION"
    echo "โมเดล $(cat "$dest/VERSION") อยู่ที่ $dest แล้ว · ตั้ง MODEL_BACKEND=local ใน .env เพื่อใช้"
    ;;
dev)
    # API อย่างเดียว · เว็บรันแยก: cd apps/web && npm run dev
    cd services/api && exec "$PYTHON" -m uvicorn app.main:app --reload --port "$PORT"
    ;;
funnel)
    # ลิงก์สาธารณะผ่าน Tailscale Funnel · funnel off = ปิด · รายละเอียดใน docs/FUNNEL.md
    shift; exec sh scripts/funnel.sh "$@"
    ;;
*)
    echo "ใช้: sh scripts/tasks.sh {setup|data|test|model|dev|funnel}" >&2
    exit 2
    ;;
esac
