"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { api } from "../../lib/api";

const SETS = { handwritten: "เขียนด้วยมือ", unseen: "schema ที่โมเดลไม่เคยเห็น", val: "validation", independent: "ชุดทดสอบอิสระ" };
const pct = (v) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "-");

function ModelInfo({ info }) {
  return (
    <dl className="facts">
      <dt>ชื่อโมเดล</dt>
      <dd>{info.name || "-"}</dd>
      <dt>โมเดลตั้งต้น</dt>
      <dd>{info.base_model || "-"}</dd>
      <dt>เวอร์ชัน</dt>
      <dd>{info.version || "-"}</dd>
      <dt>รันแบบ</dt>
      <dd>{info.backend === "local" ? "รันในเครื่องนี้" : info.backend}</dd>
      <dt>สถานะ</dt>
      <dd>{info.loaded ? "โหลดแล้ว พร้อมตอบ" : "ยังไม่พร้อม (กำลังโหลดหรือไม่พบไฟล์โมเดล)"}</dd>
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
      <p className="muted">
        วัดเมื่อ {data.generated_at || "-"} · โมเดล {data.model?.name || "-"} {data.model?.version || ""} · เครื่อง{" "}
        {data.machine || "-"}
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>โหมด</th>
              <th>ชุดทดสอบ</th>
              <th>จำนวนข้อ</th>
              <th>ตอบถูก (รันแล้วผลตรง)</th>
              <th>SQL ที่รันได้</th>
              {categories.map((c) => (
                <th key={c}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={`${r.mode}-${r.set}`}>
                <td>{r.mode}</td>
                <td>{SETS[r.set] || r.set}</td>
                <td>{r.n}</td>
                <td>{pct(r.execution_accuracy)}</td>
                <td>{pct(r.valid_sql_rate)}</td>
                {categories.map((c) => (
                  <td key={c}>{pct(r.by_category?.[c])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="hint">M0 = โมเดลอย่างเดียว · M3 = ระบบเต็ม (แปลงวันที่ไทย + beam 4 + sql_guard + ลองรันก่อนเลือก)</p>
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
      <section className="card">
        <h2>เกี่ยวกับโมเดล</h2>
        <p>
          โมเดลแปลงคำถามภาษาไทยเป็น SQL ที่ทีมเทรนเองและรันในเครื่องนี้ ไม่ส่งข้อมูลออกไปภายนอก ทุกคำตอบมาจากการรัน SQL
          กับข้อมูลจริง แล้วเขียนเป็นประโยคด้วยแม่แบบ
        </p>
        {info ? <ModelInfo info={info} /> : !error && <p className="muted">กำลังโหลด...</p>}
      </section>
      <section className="card">
        <h2>ผลการทดสอบ</h2>
        {evalData ? <EvalTable data={evalData} /> : <p className="muted">ยังไม่มีผลการทดสอบ</p>}
      </section>
    </AppShell>
  );
}
