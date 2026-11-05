"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import desk from "../../components/nongdee-desk.webp";
import { api } from "../../lib/api";

const SETS = {
  handwritten: "เขียนด้วยมือ",
  unseen: "schema ที่โมเดลไม่เคยเห็น",
  val: "validation",
  val_unseen: "validation (schema ที่ไม่ได้เทรน)",
  independent: "ชุดทดสอบอิสระ",
};
const pct = (v) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "-");

function ModelInfo({ info }) {
  return (
    <dl className="facts">
      <div>
        <dt>ชื่อโมเดล</dt>
        <dd>{info.name || "-"}</dd>
      </div>
      <div>
        <dt>โมเดลตั้งต้น</dt>
        <dd>{info.base_model || "-"}</dd>
      </div>
      <div>
        <dt>เวอร์ชัน</dt>
        <dd>{info.version || "-"}</dd>
      </div>
      <div>
        <dt>รันแบบ</dt>
        <dd>{info.backend === "local" ? "รันในเครื่องนี้" : info.backend}</dd>
      </div>
      <div>
        <dt>สถานะ</dt>
        <dd>{info.loaded ? "โหลดแล้ว พร้อมตอบ" : "ยังไม่พร้อม (กำลังโหลดหรือไม่พบไฟล์โมเดล)"}</dd>
      </div>
    </dl>
  );
}

function EvalTable({ data }) {
  const results = data.results || [];
  const categories = [...new Set(results.flatMap((r) => Object.keys(r.by_category || {})))];
  return (
    <>
      {data.simulated && (
        <p className="warning">⚠ ผลจำลองสำหรับพัฒนาหน้าเว็บ ไม่ใช่ผลวัดจริงของโมเดล</p>
      )}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>โหมด</th>
              <th>ชุดทดสอบ</th>
              <th className="num">จำนวนข้อ</th>
              <th className="num">ตอบถูก (รันแล้วผลตรง)</th>
              <th className="num">SQL ที่รันได้</th>
              {categories.map((c) => (
                <th key={c} className="num">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={`${r.mode}-${r.set}`}>
                <td>
                  <span className={r.mode === "M3" ? "mode full" : "mode"}>{r.mode}</span>
                </td>
                <td>{SETS[r.set] || r.set}</td>
                <td className="num">{r.n}</td>
                <td className="num">{pct(r.execution_accuracy)}</td>
                <td className="num">{pct(r.valid_sql_rate)}</td>
                {categories.map((c) => (
                  <td key={c} className="num">
                    {pct(r.by_category?.[c])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default function ModelPage() {
  const [info, setInfo] = useState(null);
  const [evalData, setEvalData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      setInfo(await api("/api/model"));
    } catch (err) {
      setError(err.message);
    }
    try {
      setEvalData(await api("/api/eval/results"));
    } catch (err) {
      // ยังไม่มีผลจริง (404) → แสดงผลจำลองพร้อมคำเตือน
      if (err.status === 404) {
        try {
          setEvalData(await api("/api/eval/results?simulated=true"));
        } catch {
          setEvalData(null);
        }
      } else {
        setError(err.message);
      }
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <AppShell>
      {error && (
        <p className="error">
          {error}{" "}
          <button type="button" className="link" onClick={load}>
            ลองใหม่
          </button>
        </p>
      )}
      <h1 className="page-title">
        <span>เกี่ยวกับโมเดล.</span>
        <span className="accent">ทีมเทรนเอง รันในเครื่องนี้.</span>
      </h1>
      <section className="model-hero">
        <figure className="model-photo">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={desk.src} width={desk.width} height={desk.height} alt="น้องดี มาสคอตของ ThamDi นั่งทำงานหน้าโน้ตบุ๊ก" />
          <figcaption>
            <span className={info?.loaded ? "status-dot" : "status-dot off"} />
            {info ? (info.loaded ? "โหลดแล้ว พร้อมตอบ" : "ยังไม่พร้อม") : "กำลังโหลด..."}
          </figcaption>
        </figure>
        {info ? <ModelInfo info={info} /> : !error && <p className="muted">กำลังโหลด...</p>}
      </section>
      <section className="eval">
        <h2>ผลการทดสอบ.</h2>
        {evalData ? <EvalTable data={evalData} /> : <p className="muted">ยังไม่มีผลการทดสอบ</p>}
      </section>
    </AppShell>
  );
}
