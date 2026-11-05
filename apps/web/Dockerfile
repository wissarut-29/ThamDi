# เว็บ (Next.js standalone) · docker compose build web
FROM node:20-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# ค่าเริ่มต้น: browser เรียก /api ของเว็บ แล้วเว็บส่งต่อไปที่ API_INTERNAL_URL (ชื่อ service ใน compose)
# ทั้งสองค่าถูกฝังตอน build · ตั้ง NEXT_PUBLIC_API_URL เฉพาะเมื่ออยากให้ browser เรียก API ตรง
ARG NEXT_PUBLIC_API_URL=
ARG API_INTERNAL_URL=http://api:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL API_INTERNAL_URL=$API_INTERNAL_URL NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine
WORKDIR /web
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
COPY --from=build /web/.next/standalone ./
COPY --from=build /web/.next/static ./.next/static
# ไฟล์ใน public/ (เช่น ไฟล์ยอดขายตัวอย่าง) standalone ไม่ copy ให้เอง
COPY --from=build /web/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
