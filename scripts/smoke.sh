#!/bin/sh
# ทดสอบครบเส้นกับ API ที่รันอยู่: 401 → login → อัปโหลด → chat → GET /api/model
#   API_URL=http://localhost:8000 DEMO_PASSWORD=... sh scripts/smoke.sh
# ไม่พิมพ์ token/รหัสผ่าน · ขั้นไหนพังจบทันทีด้วย exit code ไม่เป็น 0
set -eu

API_URL=${API_URL:-http://localhost:8000}
: "${DEMO_PASSWORD:?ตั้ง DEMO_PASSWORD (ค่าเดียวกับใน .env ของ API)}"
PYTHON=${PYTHON:-python}

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fail() { echo "FAIL: $1" >&2; exit 1; }
# อ่าน key จาก JSON ด้วย python (ไม่ต้องลง jq)
json_get() { "$PYTHON" -c "import json,sys; print(json.load(open(sys.argv[1], encoding='utf-8'))[sys.argv[2]])" "$1" "$2"; }

# 1) ไม่มี token ต้องได้ 401
code=$(curl -s -o /dev/null -w '%{http_code}' "$API_URL/api/datasets")
[ "$code" = 401 ] || fail "GET /api/datasets ไม่มี token ได้ $code (ควรเป็น 401)"
echo "ok   ไม่มี token → 401"

# 2) login · ส่ง body ผ่านไฟล์ UTF-8 (curl บน Windows ส่งภาษาไทยใน -d แล้วเพี้ยน)
"$PYTHON" -c "import json,sys; json.dump({'username':'demo','password':sys.argv[1]}, open(sys.argv[2],'w',encoding='utf-8'))" \
    "$DEMO_PASSWORD" "$tmp/login.json"
code=$(curl -s -o "$tmp/token.json" -w '%{http_code}' -X POST "$API_URL/api/auth/login" \
    -H 'Content-Type: application/json' --data-binary "@$tmp/login.json")
[ "$code" = 200 ] || fail "login ได้ $code"
token=$(json_get "$tmp/token.json" token)
auth="Authorization: Bearer $token"
echo "ok   login"

# 3) อัปโหลด CSV ตัวอย่าง
printf 'สาขา,ยอดขาย\nสาขา 1,100\nสาขา 2,250\nสาขา 3,75\n' > "$tmp/shop.csv"
code=$(curl -s -o "$tmp/upload.json" -w '%{http_code}' -X POST "$API_URL/api/datasets" \
    -H "$auth" -F "file=@$tmp/shop.csv")
[ "$code" = 201 ] || fail "อัปโหลดได้ $code: $(cat "$tmp/upload.json")"
dataset_id=$(json_get "$tmp/upload.json" dataset_id)
echo "ok   อัปโหลด dataset $dataset_id"

# 4) chat
printf '{"dataset_id": "%s", "question": "มีกี่สาขา"}' "$dataset_id" > "$tmp/chat.json"
code=$(curl -s -o "$tmp/answer.json" -w '%{http_code}' -X POST "$API_URL/api/chat" \
    -H "$auth" -H 'Content-Type: application/json' --data-binary "@$tmp/chat.json")
[ "$code" = 200 ] || fail "chat ได้ $code: $(cat "$tmp/answer.json")"
status=$(json_get "$tmp/answer.json" status)
echo "ok   chat status=$status"

# 5) ข้อมูลโมเดล
code=$(curl -s -o "$tmp/model.json" -w '%{http_code}' "$API_URL/api/model" -H "$auth")
[ "$code" = 200 ] || fail "GET /api/model ได้ $code"
echo "ok   model backend=$(json_get "$tmp/model.json" backend) loaded=$(json_get "$tmp/model.json" loaded)"

echo "smoke: ผ่านทุกขั้น"
