"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Mascot from "../components/Mascot";
import { api, setToken } from "../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState("login"); // login | register
  const [allowRegister, setAllowRegister] = useState(false);
  const [username, setUsername] = useState("demo");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // แสดงแท็บสมัครบัญชีเฉพาะเมื่อ API เปิดรับสมัคร (ALLOW_REGISTER)
  useEffect(() => {
    api("/api/auth/config")
      .then((c) => setAllowRegister(!!c?.allow_register))
      .catch(() => setAllowRegister(false));
  }, []);

  function switchMode(next) {
    setMode(next);
    setError("");
    setPassword("");
    setConfirm("");
    setUsername(next === "login" ? "demo" : "");
  }

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const { token } = await api("/api/auth/login", { method: "POST", body: { username, password } });
      setToken(token);
      router.replace("/chat");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function register(event) {
    event.preventDefault();
    if (password !== confirm) {
      setError("รหัสผ่านทั้งสองช่องไม่ตรงกัน");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const { token } = await api("/api/auth/register", { method: "POST", body: { username, password } });
      setToken(token);
      router.replace("/chat");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const isLogin = mode === "login";

  return (
    <div className="auth">
      <div className="auth-card">
        <nav className="auth-tabs" aria-label="เลือกหน้า">
          <button type="button" className={isLogin ? "on" : ""} aria-pressed={isLogin} onClick={() => switchMode("login")}>
            เข้าสู่ระบบ
          </button>
          {allowRegister && (
            <button type="button" className={!isLogin ? "on" : ""} aria-pressed={!isLogin} onClick={() => switchMode("register")}>
              สมัครบัญชี
            </button>
          )}
        </nav>

        <section className="auth-form-side">
          <div className="brand">
            <Mascot size={40} decorative />
            ThamDi
          </div>
          <p className="auth-eyebrow">ถามข้อมูลร้านเป็นภาษาไทย ไม่ต้องเขียน SQL</p>
          <h1>{isLogin ? "เข้าสู่ระบบ" : "สมัครบัญชีใหม่"}</h1>
          {allowRegister && (
            <p className="auth-switch">
              {isLogin ? "ยังไม่มีบัญชี? " : "มีบัญชีแล้ว? "}
              <button type="button" className="link" onClick={() => switchMode(isLogin ? "register" : "login")}>
                {isLogin ? "สมัครบัญชี" : "เข้าสู่ระบบ"}
              </button>
            </p>
          )}

          <form className="auth-form" onSubmit={isLogin ? submit : register}>
            <label>
              ชื่อผู้ใช้
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
                minLength={isLogin ? 1 : 3}
                maxLength={isLogin ? 64 : 32}
                placeholder={isLogin ? "" : "เช่น somchai_01"}
              />
            </label>
            <label>
              รหัสผ่าน
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={isLogin ? "current-password" : "new-password"}
                required
                minLength={isLogin ? 1 : 8}
                maxLength={128}
              />
            </label>
            {!isLogin && (
              <label>
                ยืนยันรหัสผ่าน
                <input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  autoComplete="new-password"
                  required
                  minLength={8}
                  maxLength={128}
                />
              </label>
            )}
            <p className="hint">
              {isLogin
                ? allowRegister
                  ? "ใช้บัญชีที่สมัครไว้ หรือบัญชี demo ที่ทีมแจกให้"
                  : "ใช้ชื่อผู้ใช้และรหัสผ่านที่ทีมแจกให้"
                : "ชื่อผู้ใช้ใช้ a-z 0-9 _ . - ยาว 3–32 ตัว · รหัสผ่าน 8 ตัวขึ้นไป · ข้อมูลที่อัปโหลดเห็นเฉพาะบัญชีของคุณ"}
            </p>
            {error && <p className="error">{error}</p>}
            <button type="submit" className="auth-cta" disabled={busy}>
              {busy ? (isLogin ? "กำลังเข้าสู่ระบบ..." : "กำลังสมัคร...") : isLogin ? "เข้าสู่ระบบ" : "สมัครและเริ่มใช้งาน"}
            </button>
          </form>
        </section>

      </div>
    </div>
  );
}
