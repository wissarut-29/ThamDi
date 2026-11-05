"use client";

import { useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { API_URL, api } from "../../lib/api";
import { clearChats, feedbackKey, readChats } from "../../lib/chats";
import { DEFAULT_SETTINGS, useSettings } from "../../lib/settings";


function Choice({ name, value, options, onChange }) {
  return (
    <div className="seg" role="radiogroup" aria-label={name}>
      {options.map(([v, label]) => (
        <button key={v} type="button" role="radio" aria-checked={value === v} className={value === v ? "on" : ""} onClick={() => onChange(v)}>
          {label}
        </button>
      ))}
    </div>
  );
}

function Toggle({ checked, onChange, label }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={label} className={checked ? "switch on" : "switch"} onClick={() => onChange(!checked)}>
      <span />
    </button>
  );
}

function Row({ title, desc, children }) {
  return (
    <div className="set-row">
      <div>
        <p className="set-title">{title}</p>
        {desc && <p className="set-desc">{desc}</p>}
      </div>
      <div className="set-control">{children}</div>
    </div>
  );
}

export default function SettingsPage() {
  const [s, update] = useSettings();
  const [chatCount, setChatCount] = useState(0);
  const [feedbackCount, setFeedbackCount] = useState(0);
  const [model, setModel] = useState(null);
  const [msg, setMsg] = useState("");
  const [armed, setArmed] = useState(false); // ลบประวัติแชท: กด 2 ครั้ง (ไม่ใช้ window.confirm)

  useEffect(() => {
    if (!armed) return undefined;
    const t = setTimeout(() => setArmed(false), 3000);
    return () => clearTimeout(t);
  }, [armed]);

  useEffect(() => {
    setChatCount(readChats().length);
    try {
      setFeedbackCount(Object.keys(JSON.parse(localStorage.getItem(feedbackKey()) || "{}")).length);
    } catch {
      setFeedbackCount(0);
    }
    api("/api/model")
      .then(setModel)
      .catch(() => setModel(false));
  }, []);

  function flash(text) {
    setMsg(text);
    setTimeout(() => setMsg(""), 2000);
  }

  function wipeChats() {
    if (!armed) {
      setArmed(true);
      return;
    }
    setArmed(false);
    clearChats();
    setChatCount(0);
    flash("ลบประวัติแชทแล้ว");
  }

  function wipeFeedback() {
    try {
      localStorage.removeItem(feedbackKey());
    } catch {
      // ไม่มีที่เก็บ
    }
    setFeedbackCount(0);
    flash("ล้างผลโหวตแล้ว");
  }

  function reset() {
    update({ ...DEFAULT_SETTINGS });
    flash("คืนค่าเริ่มต้นแล้ว");
  }

  return (
    <AppShell>
      <h1 className="page-title">
        <span>ตั้งค่า.</span>
        <span className="accent">ปรับเว็บให้ใช้สะดวก.</span>
      </h1>
      <p className="muted set-note">ค่าทั้งหมดเก็บในเบราว์เซอร์นี้เท่านั้น ไม่ส่งไปที่เซิร์ฟเวอร์</p>
      {msg && (
        <p className="upload-msg" role="status">
          {msg}
        </p>
      )}

      <section className="set-card">
        <h2>การแสดงผล</h2>
        <Row title="ขนาดตัวอักษร" desc="มีผลทุกหน้า">
          <Choice
            name="ขนาดตัวอักษร"
            value={s.fontSize}
            onChange={(v) => update({ fontSize: v })}
            options={[
              ["small", "เล็ก"],
              ["normal", "ปกติ"],
              ["large", "ใหญ่"],
            ]}
          />
        </Row>
        <Row title="พื้นหลัง" desc="สีเรียบอ่านง่ายกว่าบนโปรเจกเตอร์">
          <Choice
            name="พื้นหลัง"
            value={s.background}
            onChange={(v) => update({ background: v })}
            options={[
              ["image", "รูปภาพ"],
              ["plain", "สีเรียบ"],
            ]}
          />
        </Row>
        <Row title="ลดการเคลื่อนไหว" desc="ปิดภาพเคลื่อนไหวของน้องดีและแผงต่าง ๆ">
          <Toggle label="ลดการเคลื่อนไหว" checked={s.reduceMotion} onChange={(v) => update({ reduceMotion: v })} />
        </Row>
      </section>

      <section className="set-card">
        <h2>หน้าถามข้อมูล</h2>
        <Row title="แสดงคำถามตัวอย่าง" desc="ปุ่มคำถามเหนือช่องพิมพ์">
          <Toggle label="แสดงคำถามตัวอย่าง" checked={s.showExamples} onChange={(v) => update({ showExamples: v })} />
        </Row>
        <Row title="แสดงกราฟในคำตอบ" desc="กราฟแท่งเมื่อผลมีหลายแถว">
          <Toggle label="แสดงกราฟในคำตอบ" checked={s.showChart} onChange={(v) => update({ showChart: v })} />
        </Row>
        <Row title="เปิด SQL ไว้เลย" desc="เห็น SQL ที่ระบบรันจริงโดยไม่ต้องกด">
          <Toggle label="เปิด SQL ไว้เลย" checked={s.openSql} onChange={(v) => update({ openSql: v })} />
        </Row>
        <Row title="เปิดตารางผลไว้เลย">
          <Toggle label="เปิดตารางผลไว้เลย" checked={s.openTable} onChange={(v) => update({ openTable: v })} />
        </Row>
        <Row title="แสดงแผงประวัติแชท" desc="จอคอม: ซ่อนแล้วแผงถามข้อมูลกว้างขึ้น">
          <Toggle label="แสดงแผงประวัติแชท" checked={s.historyOpen} onChange={(v) => update({ historyOpen: v })} />
        </Row>
      </section>

      <section className="set-card">
        <h2>ข้อมูลในเบราว์เซอร์นี้</h2>
        <Row title="เก็บประวัติแชท" desc="ปิดแล้วแชทใหม่จะไม่ถูกบันทึก (แชทเดิมยังอยู่)">
          <Toggle label="เก็บประวัติแชท" checked={s.saveChats} onChange={(v) => update({ saveChats: v })} />
        </Row>
        <Row title="ประวัติแชท" desc={`${chatCount} แชท`}>
          <button type="button" className="danger-btn" onClick={wipeChats} disabled={!chatCount}>
            {armed ? "กดอีกครั้งเพื่อลบ" : "ลบทั้งหมด"}
          </button>
        </Row>
        <Row title="ผลโหวต 👍/👎" desc={`${feedbackCount} คำตอบ`}>
          <button type="button" className="ghost-btn" onClick={wipeFeedback} disabled={!feedbackCount}>
            ล้าง
          </button>
        </Row>
      </section>

      <section className="set-card">
        <h2>ระบบ</h2>
        <Row title="เซิร์ฟเวอร์ API" desc={API_URL || "ผ่านเว็บนี้ (/api)"}>
          <span className={model ? "pill ok" : "pill"}>{model === null ? "กำลังตรวจ..." : model ? "เชื่อมต่อแล้ว" : "ติดต่อไม่ได้"}</span>
        </Row>
        <Row title="โมเดล" desc={model ? `${model.name || "-"} · ${model.version || "-"}` : "-"}>
          <span className={model?.loaded ? "pill ok" : "pill"}>{model?.loaded ? "พร้อมตอบ" : "ยังไม่พร้อม"}</span>
        </Row>
        <Row title="คืนค่าเริ่มต้น" desc="ตั้งค่าในหน้านี้กลับเป็นค่าเดิม (ไม่ลบประวัติแชท)">
          <button type="button" className="ghost-btn" onClick={reset}>
            คืนค่า
          </button>
        </Row>
      </section>
    </AppShell>
  );
}
