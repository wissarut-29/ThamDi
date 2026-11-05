import full from "./nongdee.webp";
import face from "./nongdee-face.webp";

// น้องดี — มาสคอตของ ThamDi (รูปตัดพื้นหลังแล้ว)
// ขนาดเล็ก (< 80px) ใช้รูปเฉพาะหน้าในกรอบวงกลม · ขนาดใหญ่ใช้รูปเต็มตัว
// mood: idle · happy · think (ขยับเบา ๆ ตอนกำลังคิด) · oops
export default function Mascot({ mood = "idle", size = 96, className = "", title, decorative = false }) {
  const small = size < 80;
  const img = small ? face : full;
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      className={`mascot mascot-${mood}${small ? " mascot-avatar" : ""} ${className}`}
      src={img.src}
      width={size}
      height={size}
      alt={decorative ? "" : title || "น้องดี มาสคอตของ ThamDi"}
      aria-hidden={decorative || undefined}
      draggable={false}
      style={{ objectFit: small ? "cover" : "contain" }}
    />
  );
}
