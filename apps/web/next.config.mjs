// เว็บส่งต่อ /api/* ไปที่ API เอง (same origin) · เปิดผ่านลิงก์เดียว (เช่น Cloudflare quick tunnel) ก็ใช้ได้
// ไม่ต้องตั้ง CORS และไม่ต้องรู้ URL ของ API ตอน build · ค่านี้ถูกอ่านตอน build (next build / docker build)
const API_INTERNAL_URL = (process.env.API_INTERNAL_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

/** @type {import('next').NextConfig} */
const nextConfig = {
  // standalone ใช้ทำ Docker image ขนาดเล็ก (ดู apps/web/Dockerfile)
  output: "standalone",
  poweredByHeader: false,
  // ไม่ให้ next dev สร้าง AGENTS.md (ไฟล์ตั้งค่าเครื่องมือ AI ห้ามมีใน repo · W4 issue #14)
  agentRules: false,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_INTERNAL_URL}/api/:path*` }];
  },
  experimental: {
    // /api/chat อาจรอคิวโมเดล 60 วินาที + เวลาตอบ (ค่าเริ่มต้นของ Next ตัดที่ 30 วินาที)
    proxyTimeout: 130_000,
  },
};

export default nextConfig;
