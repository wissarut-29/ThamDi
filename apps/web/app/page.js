"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, setToken } from "../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("demo");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

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

  return (
    <main className="login">
      <form className="card" onSubmit={submit}>
        <h1>ThamDi</h1>
        <p className="muted">ถามข้อมูลจากไฟล์ Excel/CSV เป็นภาษาไทย ไม่ต้องเขียน SQL</p>
        <label>
          ชื่อผู้ใช้
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
        </label>
        <label>
          รหัสผ่าน
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        <p className="hint">ผู้ใช้เดโมใช้รหัสจากค่า DEMO_PASSWORD ในไฟล์ .env ของเครื่องที่รัน API</p>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "กำลังเข้าสู่ระบบ..." : "เข้าสู่ระบบ"}
        </button>
      </form>
    </main>
  );
}
