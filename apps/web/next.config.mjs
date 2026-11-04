/** @type {import('next').NextConfig} */
const nextConfig = {
  // standalone ใช้ทำ Docker image ขนาดเล็ก (ดู apps/web/Dockerfile)
  output: "standalone",
  poweredByHeader: false,
  // ไม่ให้ next dev สร้าง AGENTS.md (ไฟล์ตั้งค่าเครื่องมือ AI ห้ามมีใน repo · W4 issue #14)
  agentRules: false,
};

export default nextConfig;
