"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";
import { getToken, setToken } from "../lib/api";
import { useSettings } from "../lib/settings";
import Mascot from "./Mascot";

const Icon = {
  chat: (
    <path d="M5 5h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H10l-4 3v-3H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z M8 10h8M8 13h5" />
  ),
  summary: (
    <path d="M4 19h16M6 16V9m6 7V5m6 11v-4" />
  ),
  history: <path d="M4 12a8 8 0 1 0 2.3-5.6M4 4v4h4 M12 8v4l3 2" />,
  settings: (
    <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
  ),
  logout: <path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4 M10 16l4-4-4-4 M14 12H4" />,
};

function Svg({ d }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {d}
    </svg>
  );
}

// ปุ่มเปิด/ปิดแผงประวัติ (ไอคอนแผงด้านซ้าย)
export function AsideToggle({ className = "" }) {
  const { open, setOpen } = useAside();
  return (
    <button
      type="button"
      className={`aside-toggle ${className}`}
      onClick={() => setOpen(!open)}
      aria-expanded={open}
      title={open ? "ซ่อนประวัติแชท" : "แสดงประวัติแชท"}
      aria-label={open ? "ซ่อนประวัติแชท" : "แสดงประวัติแชท"}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <rect x="3.5" y="4.5" width="17" height="15" rx="3" />
        <path d="M9.5 4.5v15" />
        <path d={open ? "m15.5 10-2 2 2 2" : "m13.5 10 2 2-2 2"} />
      </svg>
    </button>
  );
}

const AsideContext = createContext({ open: false, setOpen: () => {}, narrow: false });
export const useAside = () => useContext(AsideContext);

function useNarrow(query = "(max-width: 1099px)") {
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const on = () => setNarrow(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [query]);
  return narrow;
}

// โครงหน้าที่ต้อง login: แถบไอคอนซ้าย · คอลัมน์รอง (เช่น ประวัติแชท) · แผงหลัก
// จอคอม: คอลัมน์รองเปิด/ปิดได้ แผงหลักขยายตาม (จำค่าไว้ในตั้งค่า) · จอเล็ก: เลื่อนออกมาทับ
// ไม่มี token ส่งกลับหน้า login ทันที (ไม่ค้างรอ API)
export default function AppShell({ children, aside = null, asideLabel = "ประวัติ" }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [overlayOpen, setOverlayOpen] = useState(false);
  const [settings, updateSettings] = useSettings();
  const narrow = useNarrow();

  useEffect(() => {
    if (!getToken()) router.replace("/");
    else setReady(true);
  }, [router]);

  function logout() {
    setToken(null);
    router.replace("/");
  }

  if (!ready) return null;

  const open = narrow ? overlayOpen : settings.historyOpen;
  const setOpen = (v) => (narrow ? setOverlayOpen(v) : updateSettings({ historyOpen: v }));
  const frameClass = ["app-frame", aside && "has-aside", aside && !narrow && !open && "aside-collapsed"].filter(Boolean).join(" ");
  const navItem = (href) => (pathname === href ? "rail-item active" : "rail-item");

  return (
    <AsideContext.Provider value={{ open, setOpen, narrow }}>
      <div className="app-bg">
        <div className={frameClass}>
          <nav className="rail" aria-label="เมนู">
            <Link href="/chat" className="rail-logo" aria-label="ThamDi">
              <Mascot size={44} decorative />
            </Link>
            <div className="rail-group">
              <Link href="/chat" className={navItem("/chat")}>
                <Svg d={Icon.chat} />
                <span>ถามข้อมูล</span>
              </Link>
              <Link href="/summary" className={navItem("/summary")}>
                <Svg d={Icon.summary} />
                <span>สรุปข้อมูล</span>
              </Link>
              <Link href="/settings" className={navItem("/settings")}>
                <Svg d={Icon.settings} />
                <span>ตั้งค่า</span>
              </Link>
              {aside && (
                <button
                  type="button"
                  className={overlayOpen ? "rail-item rail-aside-toggle active" : "rail-item rail-aside-toggle"}
                  aria-expanded={overlayOpen}
                  onClick={() => setOverlayOpen((v) => !v)}
                >
                  <Svg d={Icon.history} />
                  <span>{asideLabel}</span>
                </button>
              )}
            </div>
            <button type="button" className="rail-item rail-logout" onClick={logout}>
              <Svg d={Icon.logout} />
              <span>ออกจากระบบ</span>
            </button>
          </nav>

          {aside && (
            <>
              <aside
                className={overlayOpen ? "side open" : "side"}
                aria-hidden={!narrow && !open ? true : undefined}
                onClick={(e) => narrow && e.target.closest("button.history-item") && setOverlayOpen(false)}
              >
                {aside}
              </aside>
              {narrow && overlayOpen && <button type="button" className="side-scrim" aria-label="ปิด" onClick={() => setOverlayOpen(false)} />}
            </>
          )}

          <main className="panel">{children}</main>
        </div>
      </div>
    </AsideContext.Provider>
  );
}
