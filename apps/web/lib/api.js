// เรียก API ตาม docs/CONTRACT.md หัวข้อ 4 · ทุก request มี timeout ไม่ให้หน้าเว็บค้างเมื่อ API ล่ม/ช้า

// ว่าง = เรียก /api ของเว็บเอง แล้ว next.config.mjs ส่งต่อไปที่ API (ใช้ผ่านลิงก์ tunnel ได้)
// ตั้ง NEXT_PUBLIC_API_URL เมื่ออยากให้ browser เรียก API ตรง ๆ (ต้องตั้ง CORS_ORIGINS ให้ตรงด้วย)
export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

const TOKEN_KEY = "thamdi_token";
const DEFAULT_TIMEOUT_MS = 15000;
// chat รอโมเดลบน CPU ได้นานกว่า (beam 4) และอาจต้องรอคิว
export const CHAT_TIMEOUT_MS = 120000;

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export function getToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // private mode: ใช้ต่อได้แต่ต้อง login ใหม่ทุกครั้งที่รีเฟรช
  }
}

// ชื่อผู้ใช้จาก token (sub ใน JWT) · ใช้แยกข้อมูลในเบราว์เซอร์ของแต่ละบัญชี ไม่ได้ใช้ตรวจสิทธิ์
export function currentUser() {
  const token = getToken();
  if (!token) return null;
  try {
    const part = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const json = decodeURIComponent(
      [...atob(part)].map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0")).join(""),
    );
    return JSON.parse(json).sub || null;
  } catch {
    return null;
  }
}

function friendlyDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "ข้อมูลที่ส่งไม่ถูกต้อง (เช่น คำถามยาวเกิน 500 ตัวอักษร)";
  return null;
}

export async function api(path, { method = "GET", body, form, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  let res;
  let data = null;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: form ?? (body !== undefined ? JSON.stringify(body) : undefined),
      signal: controller.signal,
    });
    // อ่าน body ภายใต้ timeout เดียวกัน (header มาแล้วแต่ body ค้าง ก็ยังตัดตามเวลา)
    try {
      data = await res.json();
    } catch (err) {
      if (err.name === "AbortError") throw err;
      data = null;
    }
  } catch (err) {
    if (err.name === "AbortError") {
      throw new ApiError("เซิร์ฟเวอร์ตอบช้าเกินไป ลองใหม่อีกครั้ง", 0);
    }
    throw new ApiError("ติดต่อเซิร์ฟเวอร์ไม่ได้ ตรวจว่า API เปิดอยู่ แล้วลองใหม่", 0);
  } finally {
    clearTimeout(timer);
  }
  if (!res.ok) {
    if (res.status === 401 && path !== "/api/auth/login") setToken(null);
    const message = friendlyDetail(data?.detail) || `เกิดข้อผิดพลาด (${res.status})`;
    throw new ApiError(message, res.status);
  }
  return data;
}
