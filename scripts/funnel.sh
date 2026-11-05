#!/bin/sh
# เปิดเว็บให้คนนอกเข้าผ่านลิงก์ด้วย Tailscale Funnel (ลิงก์เดิมทุกครั้ง: https://<ชื่อเครื่อง>.<tailnet>.ts.net)
#   sh scripts/funnel.sh            # เว็บที่ http://localhost:3000 (docker compose)
#   PORT=3001 sh scripts/funnel.sh  # เว็บรันเองที่พอร์ตอื่น
#   sh scripts/funnel.sh off        # ปิดลิงก์
# ต้องติดตั้ง Tailscale + login แล้ว และเปิด Funnel ให้ tailnet ครั้งแรก (ดู docs/FUNNEL.md)
# Funnel ทำงานเบื้องหลัง (--bg) ปิดหน้าต่างนี้ได้ ลิงก์ยังเปิดอยู่จนกว่าจะสั่ง off
# เว็บส่งต่อ /api ไปที่ API เอง (apps/web/next.config.mjs) จึงเปิดแค่พอร์ตเว็บพอร์ตเดียว
set -eu

PORT=${PORT:-3000}
TS=${TAILSCALE:-tailscale}
if ! command -v "$TS" >/dev/null 2>&1; then
    TS="/c/Program Files/Tailscale/tailscale.exe" # Git Bash บน Windows มักไม่มี tailscale ใน PATH
    [ -x "$TS" ] || { echo "ไม่พบ tailscale · ติดตั้งจาก https://tailscale.com/download แล้ว login" >&2; exit 1; }
fi

if [ "${1:-}" = "off" ]; then
    "$TS" funnel reset
    echo "ปิดลิงก์ Funnel แล้ว"
    exit 0
fi

curl -fs -o /dev/null --max-time 5 "http://127.0.0.1:$PORT" || {
    echo "เปิด http://127.0.0.1:$PORT ไม่ได้ · เริ่มเว็บก่อน (docker compose up หรือ next start -p $PORT)" >&2
    exit 1
}

# ครั้งแรกที่ tailnet ยังไม่เปิด Funnel คำสั่งนี้จะพิมพ์ลิงก์ให้ไปกดเปิดในเว็บ Tailscale แล้วรอ
"$TS" funnel --bg "$PORT"

url=$("$TS" funnel status 2>/dev/null | grep -o 'https://[^ ]*\.ts\.net' | head -n 1 || true)
[ -n "$url" ] || { "$TS" funnel status >&2; echo "ไม่พบลิงก์ Funnel" >&2; exit 1; }

i=0
until curl -fs -o /dev/null --max-time 10 "$url" || [ $i -ge 30 ]; do
    i=$((i + 1))
    sleep 2
done
echo ""
echo "ลิงก์สำหรับแชร์ : $url"
[ $i -lt 30 ] || echo "(ยังเปิดลิงก์จากเครื่องนี้ไม่ได้ ครั้งแรกใบรับรอง HTTPS อาจใช้เวลา 1–2 นาที ลองเปิดอีกครั้ง)"
echo "ปิดลิงก์: sh scripts/funnel.sh off"
