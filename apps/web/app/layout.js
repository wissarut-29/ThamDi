import "./globals.css";

export const metadata = {
  title: "ThamDi · ถามข้อมูลจาก Excel เป็นภาษาไทย",
  description: "ระบบถามข้อมูลภาษาไทยเป็น SQL ด้วยโมเดลที่ทีมเทรนเองและรันในเครื่อง",
};

export default function RootLayout({ children }) {
  return (
    <html lang="th">
      <body>{children}</body>
    </html>
  );
}
