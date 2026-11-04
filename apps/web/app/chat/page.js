"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import AppShell from "../../components/AppShell";
import { CHAT_TIMEOUT_MS, api } from "../../lib/api";

const SHOW_ROWS = 50; // ตารางบนหน้าจอแสดงไม่เกินนี้ อ่านง่ายตอนเดโม
const STATUS_LABEL = { ok: "ตอบได้", refuse: "ปฏิเสธ", clarify: "ขอข้อมูลเพิ่ม", error: "ตอบไม่ได้" };

function ResultTable({ columns, rows }) {
  if (!columns?.length || !rows?.length) return null;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, SHOW_ROWS).map((row, i) => (
            <tr key={i}>
              {row.map((v, j) => (
                <td key={j}>{v === null ? "-" : String(v)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > SHOW_ROWS && <p className="muted">แสดง {SHOW_ROWS} จาก {rows.length} แถว</p>}
    </div>
  );
}

function Answer({ item }) {
  return (
    <article className="answer">
      <p className="question">{item.question}</p>
      {item.pending ? (
        <p className="muted pending">กำลังหาคำตอบ... (โมเดลบน CPU อาจใช้เวลาหลายวินาที)</p>
      ) : item.failed ? (
        <p className="error">{item.failed}</p>
      ) : (
        <>
          <p>
            <span className={`badge ${item.status}`}>{STATUS_LABEL[item.status] || item.status}</span> {item.answer}
          </p>
          {item.sql && (
            <details>
              <summary>SQL ที่ระบบรันจริง</summary>
              <pre>{item.sql}</pre>
            </details>
          )}
          <ResultTable columns={item.columns} rows={item.rows} />
        </>
      )}
    </article>
  );
}

export default function ChatPage() {
  const [datasets, setDatasets] = useState([]);
  const [datasetId, setDatasetId] = useState("");
  const [loadError, setLoadError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [question, setQuestion] = useState("");
  const [items, setItems] = useState([]);
  const fileRef = useRef(null);
  const busy = items.some((i) => i.pending);

  const loadDatasets = useCallback(async (selectId) => {
    try {
      const list = await api("/api/datasets");
      setDatasets(list);
      setLoadError("");
      setDatasetId((current) => selectId || current || list[0]?.dataset_id || "");
    } catch (err) {
      setLoadError(err.message);
    }
  }, []);

  useEffect(() => {
    loadDatasets();
  }, [loadDatasets]);

  async function upload(event) {
    event.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    setUploading(true);
    setUploadMsg("");
    try {
      const created = await api("/api/datasets", { method: "POST", form, timeoutMs: 60000 });
      setUploadMsg(`อัปโหลดแล้ว · ตาราง: ${created.tables.join(", ")}`);
      fileRef.current.value = "";
      await loadDatasets(created.dataset_id);
    } catch (err) {
      setUploadMsg(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function ask(event) {
    event.preventDefault();
    const q = question.trim();
    if (!q || !datasetId || busy) return;
    const id = Date.now();
    setItems((prev) => [{ id, question: q, pending: true }, ...prev]);
    setQuestion("");
    try {
      const reply = await api("/api/chat", {
        method: "POST",
        body: { dataset_id: datasetId, question: q },
        timeoutMs: CHAT_TIMEOUT_MS,
      });
      setItems((prev) => prev.map((i) => (i.id === id ? { id, question: q, ...reply } : i)));
    } catch (err) {
      setItems((prev) => prev.map((i) => (i.id === id ? { id, question: q, failed: err.message } : i)));
    }
  }

  return (
    <AppShell>
      <section className="card">
        <h2>1. เลือกหรืออัปโหลดข้อมูล</h2>
        {loadError && (
          <p className="error">
            {loadError}{" "}
            <button type="button" className="link" onClick={() => loadDatasets()}>
              ลองใหม่
            </button>
          </p>
        )}
        <div className="row">
          <select value={datasetId} onChange={(e) => setDatasetId(e.target.value)} disabled={!datasets.length}>
            {!datasets.length && <option value="">ยังไม่มีข้อมูล อัปโหลดไฟล์ก่อน</option>}
            {datasets.map((d) => (
              <option key={d.dataset_id} value={d.dataset_id}>
                {d.name} ({d.tables.join(", ")})
              </option>
            ))}
          </select>
        </div>
        <form className="row" onSubmit={upload}>
          <input type="file" ref={fileRef} accept=".csv,.tsv,.txt,.xlsx,.xls,.ods,.json" required />
          <button type="submit" disabled={uploading}>
            {uploading ? "กำลังอัปโหลด..." : "อัปโหลด"}
          </button>
        </form>
        <p className="hint">รองรับไฟล์ตาราง .csv .xlsx .xls .ods .tsv .txt .json ไม่เกิน 10 MB · ระบบอ่านข้อมูลได้อย่างเดียว ไม่แก้ไฟล์ของคุณ</p>
        {uploadMsg && <p className="muted">{uploadMsg}</p>}
      </section>

      <section className="card">
        <h2>2. ถามเป็นภาษาไทย</h2>
        <form className="row" onSubmit={ask}>
          <input
            className="grow"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="เช่น ยอดขายรวมของแต่ละสาขาเดือนตุลาคม 2569"
            maxLength={500}
            disabled={!datasetId}
          />
          <button type="submit" disabled={!datasetId || busy || !question.trim()}>
            {busy ? "กำลังตอบ..." : "ถาม"}
          </button>
        </form>
      </section>

      {items.map((item) => (
        <Answer key={item.id} item={item} />
      ))}
    </AppShell>
  );
}
