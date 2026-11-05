"use client";

// ตั้งค่าพื้นฐานของเว็บ · เก็บในเบราว์เซอร์นี้เท่านั้น (localStorage) ไม่ส่งไปที่ API
import { useCallback, useEffect, useState } from "react";

const KEY = "thamdi_settings_v1";
const EVENT = "thamdi-settings";

export const DEFAULT_SETTINGS = {
  fontSize: "normal", // small · normal · large
  background: "image", // image · plain
  showExamples: true, // ปุ่มตัวอย่างคำถามเหนือช่องพิมพ์
  showChart: true, // กราฟแท่งในคำตอบ
  openSql: false, // เปิดกล่อง SQL ที่ระบบรันจริงไว้เลย
  openTable: false, // เปิดตารางผลไว้เลย
  saveChats: true, // เก็บประวัติแชทในเบราว์เซอร์นี้
  reduceMotion: false, // ปิดการเคลื่อนไหวของมาสคอตและแผง
  historyOpen: true, // แผงประวัติแชทบนจอคอม (จำค่าที่เปิด/ปิดล่าสุด)
};

export function readSettings() {
  try {
    return { ...DEFAULT_SETTINGS, ...JSON.parse(localStorage.getItem(KEY) || "{}") };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

export function writeSettings(patch) {
  const next = { ...readSettings(), ...patch };
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // เบราว์เซอร์ไม่ให้เก็บ: ใช้ได้จนกว่าจะรีเฟรช
  }
  applySettings(next);
  window.dispatchEvent(new CustomEvent(EVENT, { detail: next }));
  return next;
}

// ค่าที่มีผลกับทั้งหน้า ใส่เป็น data-* บน <html> ให้ CSS จัดการ
export function applySettings(s = readSettings()) {
  const root = document.documentElement;
  root.dataset.font = s.fontSize;
  root.dataset.bg = s.background;
  root.dataset.motion = s.reduceMotion ? "reduce" : "full";
}

export function useSettings() {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);

  useEffect(() => {
    const current = readSettings();
    setSettings(current);
    applySettings(current);
    const onChange = (e) => setSettings(e.detail);
    const onStorage = (e) => e.key === KEY && setSettings(readSettings());
    window.addEventListener(EVENT, onChange);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(EVENT, onChange);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  const update = useCallback((patch) => setSettings(writeSettings(patch)), []);
  return [settings, update];
}
