#!/bin/sh
# เปิดเว็บให้คนนอกเข้าผ่านลิงก์ด้วย Cloudflare quick tunnel (ไม่ต้องมีบัญชี ไม่ต้อง login)
#   sh scripts/tunnel.sh            # เว็บที่ http://localhost:3000 (docker compose)
#   PORT=3001 sh scripts/tunnel.sh  # เว็บรันเองที่พอร์ตอื่น
# เปิดหน้าต่างนี้ค้างไว้ · Ctrl+C = ปิดลิงก์ · ลิงก์ https://<สุ่ม>.trycloudflare.com เปลี่ยนทุกครั้งที่รันใหม่
# เว็บส่งต่อ /api ไปที่ API เอง (apps/web/next.config.mjs) จึงเปิดแค่พอร์ตเว็บพอร์ตเดียว · รายละเอียดใน docs/TUNNEL.md
set -eu

PORT=${PORT:-3000}
CF=${CLOUDFLARED:-cloudflared}
if ! command -v "$CF" >/dev/null 2>&1; then
    # Git Bash บน Windows: ตัวติดตั้ง .msi ไม่ได้ใส่ cloudflared ใน PATH ของ Git Bash
    for p in "/c/Program Files (x86)/cloudflared/cloudflared.exe" "/c/Program Files/cloudflared/cloudflared.exe"; do
        [ -x "$p" ] && CF=$p && break
    done
    command -v "$CF" >/dev/null 2>&1 || [ -x "$CF" ] || {
        echo "ไม่พบ cloudflared · ติดตั้ง: winget install --id Cloudflare.cloudflared (หรือดู docs/TUNNEL.md)" >&2
        exit 1
    }
fi

curl -fs -o /dev/null --max-time 5 "http://127.0.0.1:$PORT" || {
    echo "เปิด http://127.0.0.1:$PORT ไม่ได้ · เริ่มเว็บก่อน (docker compose up หรือ next start -p $PORT)" >&2
    exit 1
}

log=$(mktemp "${TMPDIR:-/tmp}/thamdi-tunnel.XXXXXX")
"$CF" tunnel --no-autoupdate --url "http://127.0.0.1:$PORT" >"$log" 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true; rm -f "$log"; echo ""; echo "ปิดลิงก์แล้ว"' EXIT
trap 'exit 0' INT TERM

url=""
i=0
while [ -z "$url" ] && [ $i -lt 30 ]; do
    kill -0 "$pid" 2>/dev/null || { cat "$log" >&2; echo "cloudflared หยุดทำงาน" >&2; exit 1; }
    url=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$log" | head -n 1 || true)
    i=$((i + 1))
    sleep 1
done
[ -n "$url" ] || { cat "$log" >&2; echo "ไม่ได้ลิงก์จาก cloudflared ภายใน 30 วินาที" >&2; exit 1; }

echo ""
echo "ลิงก์สำหรับแชร์ : $url"
echo "(DNS ของลิงก์ใหม่อาจใช้เวลา 10–30 วินาทีกว่าจะเปิดได้) · Ctrl+C = ปิดลิงก์"
wait "$pid"
