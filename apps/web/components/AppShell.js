"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getToken, setToken } from "../lib/api";

// โครงหน้าที่ต้อง login · ไม่มี token ส่งกลับหน้า login ทันที (ไม่ค้างรอ API)
export default function AppShell({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) router.replace("/");
    else setReady(true);
  }, [router]);

  function logout() {
    setToken(null);
    router.replace("/");
  }

  if (!ready) return null;

  return (
    <div className="shell">
      <header className="topbar">
        <span className="brand">ThamDi</span>
        <nav>
          <Link href="/chat" className={pathname === "/chat" ? "active" : ""}>
            ถามข้อมูล
          </Link>
          <Link href="/model" className={pathname === "/model" ? "active" : ""}>
            เกี่ยวกับโมเดล
          </Link>
        </nav>
        <button type="button" className="link" onClick={logout}>
          ออกจากระบบ
        </button>
      </header>
      <main className="content">{children}</main>
    </div>
  );
}
