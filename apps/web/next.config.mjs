/** @type {import('next').NextConfig} */
const nextConfig = {
  // standalone ใช้ทำ Docker image ขนาดเล็ก (ดู apps/web/Dockerfile)
  output: "standalone",
  poweredByHeader: false,
};

export default nextConfig;
