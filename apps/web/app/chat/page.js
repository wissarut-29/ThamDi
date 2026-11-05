"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import AppShell, { AsideToggle, useAside } from "../../components/AppShell";
import Mascot from "../../components/Mascot";
import { API_URL, CHAT_TIMEOUT_MS, api, getToken } from "../../lib/api";
import { getSelectedDataset, setSelectedDataset } from "../../lib/datasets";
import { deleteChat, feedbackKey, readChats, upsertChat } from "../../lib/chats";
import { useSettings } from "../../lib/settings";

const SHOW_ROWS = 50; // ตารางบนหน้าจอแสดงไม่เกินนี้ อ่านง่ายตอนเดโม
const STATUS_LABEL = { ok: "ตอบได้", refuse: "ปฏิเสธ", clarify: "ขอข้อมูลเพิ่ม", error: "ตอบไม่ได้" };
// ตัวอย่างคำถามตามตารางในไฟล์ที่เลือก (กดแล้วแค่เติมลงช่องถาม ยังไม่ส่ง)
// บัญชี demo มีไฟล์ตัวอย่างทั้ง 3 ไฟล์ให้ถามได้ทันที (services/api/app/samples)
const EXAMPLES_BY_TABLE = {
  sales: ["ยอดขายรวมทั้งปีเท่าไหร่", "สาขาไหนขายดีที่สุด", "ยอดขายแต่ละหมวดสินค้าเท่าไหร่"],
  // ลองกับโมเดล v2 แล้วตอบถูก · ระวัง: "ค่าไฟรวม/ค่าไฟเฉลี่ย" โมเดลไปใช้คอลัมน์ค่าน้ำ อย่าใช้เป็นตัวอย่าง
  employees: ["พนักงานมีกี่คน", "เงินเดือนเฉลี่ยของพนักงานเท่าไหร่", "จำนวนพนักงานแต่ละสาขา"],
  utility_bills: ["ค่าน้ำรวมทั้งหมดเท่าไหร่", "ค่าไฟฟ้ารวมแต่ละสาขาเท่าไหร่", "ค่าน้ำเฉลี่ยต่อเดือนเท่าไหร่"],
};
const examplesFor = (tables = []) => tables.flatMap((t) => EXAMPLES_BY_TABLE[t] || []).slice(0, 3);
// ตัวอย่างคำถามอันตราย: กดแล้วเติมลงช่องถาม ให้เห็นระบบไม่ยอมแก้/ลบข้อมูล
const DANGER_EXAMPLES = ["ลบตารางยอดขายทิ้งให้หน่อย", "แก้ยอดขายสาขาบางนาเป็น 0"];
const SAMPLE_FILE = { url: "/sample/sales_5_branches.xlsx", name: "sales_5_branches.xlsx" };

function moodOf(item) {
  if (item.pending) return "think";
  if (item.failed || item.status === "refuse" || item.status === "error") return "oops";
  if (item.status === "clarify") return "think";
  return "happy";
}

// ใส่คอมมาให้ตัวเลข (เว้นจำนวนเต็มต่ำกว่า 10,000 เช่น ปี 2569 หรือรหัส)
function formatCell(v) {
  if (v === null || v === undefined) return "-";
  if (typeof v === "number") {
    if (Number.isInteger(v) && Math.abs(v) < 10000) return String(v);
    return v.toLocaleString("en-US", { maximumFractionDigits: 2 });
  }
  return String(v);
}

function ResultTable({ columns, rows }) {
  if (!columns?.length || !rows?.length) return null;
  return (
    <>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((c, j) => (
                <th key={c} className={typeof rows[0]?.[j] === "number" ? "num" : undefined}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, SHOW_ROWS).map((row, i) => (
              <tr key={i}>
                {row.map((v, j) => (
                  <td key={j} className={typeof v === "number" ? "num" : undefined}>
                    {formatCell(v)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > SHOW_ROWS && <p className="muted">แสดง {SHOW_ROWS} จาก {rows.length} แถว</p>}
    </>
  );
}

// ---------- อ่านผลลัพธ์เพื่อทำกราฟและสรุปเป็นประโยค (ใช้ข้อมูลจริงจากตารางเท่านั้น) ----------
const CHART_MAX_BARS = 12;
const CHART_MAX_ROWS = 200;

// คอลัมน์รหัส (employee_id, id ...) ไม่ใช่ค่าที่ควรเอามาทำกราฟ
const isIdColumn = (name) => /(^|_)id$/i.test(String(name)) || /รหัส/.test(String(name));

// เลือกคอลัมน์ป้าย (ข้อความคอลัมน์แรก) กับคอลัมน์ค่า (ตัวเลขคอลัมน์สุดท้ายที่ไม่ใช่รหัส)
function pickSeries(columns, rows) {
  if (!columns?.length || !rows?.length) return null;
  const all = (j, test) => rows.every((r) => test(r[j]));
  const labelIdx = columns.findIndex((_, j) => all(j, (v) => typeof v === "string" && v !== ""));
  let valueIdx = -1;
  columns.forEach((c, j) => {
    if (!isIdColumn(c) && all(j, (v) => typeof v === "number")) valueIdx = j;
  });
  if (valueIdx < 0) return { labelIdx, valueIdx: -1 };
  return { labelIdx, valueIdx };
}

function chartData(columns, rows) {
  if (!rows || rows.length < 2 || rows.length > CHART_MAX_ROWS) return null;
  const pick = pickSeries(columns, rows);
  if (!pick || pick.labelIdx < 0 || pick.valueIdx < 0) return null;
  let points = rows.map((r) => ({ label: r[pick.labelIdx], value: r[pick.valueIdx] }));
  if (points.some((p) => p.value < 0)) return null;
  const total = points.length;
  // มากกว่า 12 แถว: เรียงจากมากไปน้อย แสดง 12 อันดับแรก
  if (total > CHART_MAX_BARS) points = [...points].sort((a, b) => b.value - a.value).slice(0, CHART_MAX_BARS);
  const max = Math.max(...points.map((p) => p.value));
  if (!(max > 0)) return null;
  return { points, max, total, labelName: columns[pick.labelIdx], valueName: columns[pick.valueIdx] };
}

function BarChart({ columns, rows }) {
  const data = chartData(columns, rows);
  if (!data) return null;
  const topValue = data.max;
  return (
    <figure className="bars" aria-label={`กราฟ ${data.valueName} แยกตาม ${data.labelName}`}>
      <figcaption className="bars-caption">
        {data.valueName} แยกตาม {data.labelName}
        {data.total > data.points.length && ` · ${data.points.length} อันดับแรกจาก ${data.total.toLocaleString("en-US")}`}
      </figcaption>
      {data.points.map((p, i) => (
        <div className="bar-row" key={i}>
          <span className="bar-label" title={p.label}>
            {p.label}
          </span>
          <span className="bar-track">
            <span className={p.value === topValue ? "bar-fill top" : "bar-fill"} style={{ width: `${Math.max((p.value / data.max) * 100, 1)}%` }} />
          </span>
          <span className="bar-value">{formatCell(p.value)}</span>
        </div>
      ))}
    </figure>
  );
}

// ข้อความตอบแบบแชท: แทนประโยคกลาง ๆ "พบ N รายการ (ดูในตารางด้านล่าง)" ด้วยสรุปจากข้อมูลจริง
function chatAnswer(item) {
  const { answer, columns, rows } = item;
  if (!/^พบ [\d,]+ รายการ/.test(answer || "") || !rows?.length || rows.length < 2) return answer;
  const n = rows.length.toLocaleString("en-US");
  const pick = pickSeries(columns, rows);
  const labelIdx = pick && pick.labelIdx >= 0 ? pick.labelIdx : 0;
  const label = (r) => formatCell(r[labelIdx]);

  if (pick && pick.labelIdx >= 0 && pick.valueIdx >= 0) {
    const v = pick.valueIdx;
    if (rows.length <= 5) {
      return `ได้ ${n} รายการ: ` + rows.map((r) => `${label(r)} ${formatCell(r[v])}`).join(" · ");
    }
    const sorted = [...rows].sort((a, b) => b[v] - a[v]);
    const hi = sorted[0];
    const lo = sorted[sorted.length - 1];
    const avg = rows.reduce((sum, r) => sum + r[v], 0) / rows.length;
    return (
      `ได้ ${n} รายการ · ${columns[v]} มากที่สุดคือ ${label(hi)} (${formatCell(hi[v])}) ` +
      `น้อยที่สุดคือ ${label(lo)} (${formatCell(lo[v])}) · เฉลี่ย ${formatCell(Math.round(avg * 100) / 100)}`
    );
  }

  if (rows.length <= 8) return `ได้ ${n} รายการ: ` + rows.map(label).join(", ");
  const names = rows.slice(0, 3).map(label).join(", ");
  return `ได้ ${n} รายการ เช่น ${names} และอีก ${(rows.length - 3).toLocaleString("en-US")} รายการ`;
}

// คัดลอกข้อความ (ใช้ได้ทั้ง https/localhost และหน้าที่ไม่ใช่ https)
async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return ok;
  }
}

function CopySqlButton({ sql }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    if (await copyText(sql)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }
  return (
    <button type="button" className="mini" onClick={copy} aria-live="polite">
      {copied ? "คัดลอกแล้ว" : "คัดลอก SQL"}
    </button>
  );
}

// ---------- ส่งออก: สร้างไฟล์จากข้อมูลบนหน้าเว็บ (Excel ให้ API จัดรูปแบบ) ----------
// ทุกฟังก์ชันรับรายการคำตอบ (เรียงเก่า → ใหม่) ใช้ได้ทั้งคำตอบเดียวและทั้งบทสนทนา
function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

const done = (items) => items.filter((i) => !i.pending);
const hasRows = (i) => i.columns?.length > 0 && i.rows?.length > 0;
const statusText = (i) => (i.failed ? "ตอบไม่ได้" : STATUS_LABEL[i.status] || i.status || "");
const answerText = (i) => i.failed || chatAnswer(i) || "";
const stamp = () => new Date().toLocaleString("th-TH", { dateStyle: "long", timeStyle: "short" });

const tsvCell = (v) => (v === null || v === undefined ? "" : String(v).replace(/[\t\r\n]+/g, " "));
const toTsv = (columns, rows) => [columns, ...rows].map((r) => r.map(tsvCell).join("\t")).join("\n");

function csvCell(v) {
  const text = v === null || v === undefined ? "" : String(v);
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}
const toCsv = (columns, rows) => [columns, ...rows].map((r) => r.map(csvCell).join(",")).join("\r\n");

// CSV ใส่ BOM ให้ Excel เปิดภาษาไทยได้ · หลายคำถาม: คั่นแต่ละตารางด้วยบรรทัดคำถาม
function exportCsv(items, base) {
  const tables = done(items).filter(hasRows);
  if (!tables.length) throw new Error("ไม่มีตารางผลให้ส่งออก");
  const text =
    tables.length === 1
      ? toCsv(tables[0].columns, tables[0].rows)
      : tables.map((i) => `${csvCell(`# ${i.question}`)}\r\n${toCsv(i.columns, i.rows)}`).join("\r\n\r\n");
  downloadBlob(new Blob(["﻿" + text], { type: "text/csv;charset=utf-8" }), `${base}.csv`);
}

const itemJson = (i) => ({
  question: i.question,
  status: i.failed ? "error" : i.status,
  answer: answerText(i),
  sql: i.sql || null,
  columns: i.columns || [],
  rows: i.rows || [],
  seconds: i.ms != null ? Math.round(i.ms) / 1000 : null,
});

function exportJson(items, base, datasetName) {
  const list = done(items);
  const data =
    list.length === 1
      ? { ...itemJson(list[0]), dataset: datasetName || null, exported_at: new Date().toISOString() }
      : { dataset: datasetName || null, exported_at: new Date().toISOString(), items: list.map(itemJson) };
  downloadBlob(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }), `${base}.json`);
}

// SQL ที่ระบบรันจริงทุกข้อ (มีคำถามเป็นคอมเมนต์กำกับ) เอาไปรันใน DuckDB ต่อได้
function exportSql(items, base, datasetName) {
  const list = done(items);
  if (!list.some((i) => i.sql)) throw new Error("คำตอบนี้ไม่มี SQL ให้ส่งออก");
  const oneLine = (s) => String(s).replace(/[\r\n]+/g, " ");
  const head = `-- ThamDi · SQL ที่ระบบรันจริง\n-- ไฟล์ข้อมูล: ${oneLine(datasetName || "-")}\n-- ส่งออกเมื่อ ${stamp()}\n`;
  const body = list
    .map((i, n) => {
      const q = `-- ${n + 1}. ${oneLine(i.question)}`;
      return i.sql ? `${q}\n${i.sql.trim().replace(/;?\s*$/, ";")}` : `${q}\n-- (ไม่มี SQL · ${statusText(i)})`;
    })
    .join("\n\n");
  downloadBlob(new Blob([`${head}\n${body}\n`], { type: "application/sql;charset=utf-8" }), `${base}.sql`);
}

// ข้อความล้วน: คำถาม คำตอบ SQL และตาราง (คั่นด้วยแท็บ) อ่านได้ทุกโปรแกรม
function exportTxt(items, base, datasetName) {
  const list = done(items);
  const parts = [`ThamDi · บทสนทนา`, `ไฟล์ข้อมูล: ${datasetName || "-"}`, `ส่งออกเมื่อ ${stamp()}`, ""];
  list.forEach((i, n) => {
    parts.push(`ข้อ ${n + 1}: ${i.question}`, `คำตอบ (${statusText(i)}): ${answerText(i)}`);
    if (i.sql) parts.push(`SQL: ${i.sql.trim()}`);
    if (hasRows(i)) parts.push("ตาราง:", toTsv(i.columns, i.rows));
    if (i.ms != null) parts.push(`ตอบใน ${(i.ms / 1000).toFixed(1)} วินาที`);
    parts.push("");
  });
  downloadBlob(new Blob(["﻿" + parts.join("\r\n").replace(/\r?\n/g, "\r\n")], { type: "text/plain;charset=utf-8" }), `${base}.txt`);
}

// Excel ของจริง: API ใช้ openpyxl สร้างไฟล์ (ตัวเลขยังเป็นตัวเลข หัวตารางตัวหนา)
// คำตอบเดียว → /xlsx · หลายคำตอบ → /xlsx-book (1 คำถาม = 1 ชีต + สารบัญ)
async function exportXlsx(items, base) {
  const tables = done(items).filter(hasRows).slice(0, 30);
  if (!tables.length) throw new Error("ไม่มีตารางผลให้ส่งออก");
  const sheet = (i) => ({ columns: i.columns, rows: i.rows, question: i.question, sql: i.sql || null });
  const [path, body] = tables.length === 1 ? ["/api/export/xlsx", sheet(tables[0])] : ["/api/export/xlsx-book", { sheets: tables.map(sheet) }];
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30000);
  try {
    const res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken() || ""}` },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`สร้างไฟล์ Excel ไม่สำเร็จ (${res.status})`);
    downloadBlob(await res.blob(), `${base}.xlsx`);
  } catch (err) {
    if (err.name === "AbortError") throw new Error("สร้างไฟล์ Excel นานเกินไป ลองใหม่");
    if (err instanceof TypeError) throw new Error("ติดต่อเซิร์ฟเวอร์ไม่ได้ ส่งออก Excel ไม่สำเร็จ");
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

// ---------- รูป PNG: วาดคำถาม คำตอบ และกราฟเองบน canvas (ใช้ฟอนต์ของหน้าเว็บ ภาษาไทยไม่เพี้ยน) ----------
const canvasFont = (w, px) => `${w} ${px}px Inter, Anuphan, "Leelawadee UI", Tahoma, sans-serif`;

// ตัดบรรทัดตามคำ (ภาษาไทยไม่มีเว้นวรรค → ใช้ Intl.Segmenter ถ้ามี ไม่งั้นตัดทีละตัวอักษร)
function wrapLines(ctx, text, maxW) {
  const seg = typeof Intl !== "undefined" && Intl.Segmenter ? new Intl.Segmenter("th", { granularity: "word" }) : null;
  const tokens = seg ? [...seg.segment(String(text))].map((s) => s.segment) : [...String(text)];
  const lines = [];
  let line = "";
  for (const t of tokens) {
    if (ctx.measureText(line + t).width <= maxW || !line) line += t;
    else {
      lines.push(line.trimEnd());
      line = t.trimStart();
    }
  }
  if (line) lines.push(line);
  return lines.length ? lines : [""];
}

function paintReport(ctx, items, title, W, draw) {
  const pad = 36;
  const inner = W - pad * 2;
  let y = pad;
  const text = (str, w, px, color, lh) => {
    ctx.font = canvasFont(w, px);
    const lines = wrapLines(ctx, str, inner);
    lines.forEach((l) => {
      if (draw) {
        ctx.fillStyle = color;
        ctx.fillText(l, pad, y + px);
      }
      y += lh;
    });
  };
  text(title, 600, 22, "#161613", 32);
  text(`${stamp()} · ThamDi (รันในเครื่อง)`, 400, 13, "#6f6f6a", 22);
  y += 10;
  items.forEach((i) => {
    if (draw) {
      ctx.fillStyle = "#e8e8e3";
      ctx.fillRect(pad, y, inner, 1);
    }
    y += 18;
    text(i.question, 600, 17, "#161613", 26);
    text(`${statusText(i)} · ${answerText(i)}`, 400, 15, i.failed || i.status === "refuse" ? "#b8322a" : "#11603b", 24);
    const chart = !i.failed && chartData(i.columns, i.rows);
    if (chart) {
      y += 8;
      const labelW = 180;
      const valueW = 120;
      const barX = pad + labelW;
      const barW = inner - labelW - valueW;
      chart.points.forEach((p) => {
        if (draw) {
          ctx.font = canvasFont(400, 14);
          ctx.fillStyle = "#161613";
          let label = String(p.label);
          while (ctx.measureText(label).width > labelW - 12 && label.length > 1) label = label.slice(0, -1);
          if (label !== String(p.label)) label = label.slice(0, -1) + "…";
          ctx.fillText(label, pad, y + 17);
          ctx.fillStyle = "#f2f2ee";
          ctx.beginPath();
          ctx.roundRect(barX, y + 5, barW, 14, 7);
          ctx.fill();
          ctx.fillStyle = p.value === chart.max ? "#22d35c" : "#9fe6b6";
          ctx.beginPath();
          ctx.roundRect(barX, y + 5, Math.max((p.value / chart.max) * barW, 6), 14, 7);
          ctx.fill();
          ctx.font = canvasFont(600, 14);
          ctx.fillStyle = "#161613";
          ctx.textAlign = "right";
          ctx.fillText(formatCell(p.value), W - pad, y + 17);
          ctx.textAlign = "left";
        }
        y += 30;
      });
    }
    if (i.sql) {
      y += 4;
      text(`SQL: ${i.sql.replace(/\s+/g, " ").trim()}`, 400, 12, "#6f6f6a", 18);
    }
    y += 10;
  });
  return y + pad - 10;
}

function exportPng(items, base, title) {
  const list = done(items);
  if (!list.length) throw new Error("ยังไม่มีคำตอบให้ส่งออก");
  const W = 900;
  const measure = document.createElement("canvas").getContext("2d");
  const H = Math.ceil(paintReport(measure, list, title, W, false));
  const scale = H * 2 > 30000 ? 1 : 2; // canvas สูงได้จำกัด: บทสนทนายาวมากใช้ความละเอียดปกติ
  const canvas = document.createElement("canvas");
  canvas.width = W * scale;
  canvas.height = Math.min(H * scale, 32000);
  const ctx = canvas.getContext("2d");
  ctx.scale(scale, scale);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, W, H);
  paintReport(ctx, list, title, W, true);
  return new Promise((resolve, reject) =>
    canvas.toBlob((blob) => {
      if (!blob) return reject(new Error("สร้างรูปไม่สำเร็จ"));
      downloadBlob(blob, `${base}.png`);
      resolve();
    }, "image/png"),
  );
}

// พิมพ์ / บันทึก PDF: ใช้หน้าต่างพิมพ์ของเบราว์เซอร์ (one = คำตอบเดียว · ไม่ระบุ = ทั้งบทสนทนา)
function printReport(oneId) {
  const body = document.body;
  const opened = [];
  document.querySelectorAll(".thread details:not([open])").forEach((d) => {
    d.open = true;
    opened.push(d);
  });
  body.dataset.print = oneId ? "one" : "all";
  if (oneId) document.querySelector(`[data-answer-id="${oneId}"]`)?.classList.add("print-target");
  const cleanup = () => {
    opened.forEach((d) => (d.open = false));
    delete body.dataset.print;
    document.querySelectorAll(".print-target").forEach((el) => el.classList.remove("print-target"));
    window.removeEventListener("afterprint", cleanup);
  };
  window.addEventListener("afterprint", cleanup);
  window.print();
}

const esc = (v) =>
  String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// รายงาน HTML ไฟล์เดียว เปิดได้ทุกเครื่องแม้ไม่มีเน็ต
function exportHtml(items, base, datasetName) {
  const list = done(items);
  const blocks = list
    .map((i) => {
      const chart = chartData(i.columns, i.rows);
      const bars = chart
        ? `<div class="bars">${chart.points
            .map(
              (p) =>
                `<div class="bar"><span>${esc(p.label)}</span><i><b style="width:${Math.max((p.value / chart.max) * 100, 1)}%"></b></i><strong>${esc(formatCell(p.value))}</strong></div>`,
            )
            .join("")}</div>`
        : "";
      const table = hasRows(i)
        ? `<table><thead><tr>${i.columns.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${i.rows
            .map((r) => `<tr>${r.map((v) => `<td>${esc(formatCell(v))}</td>`).join("")}</tr>`)
            .join("")}</tbody></table>`
        : "";
      return `<section><h2>${esc(i.question)}</h2><p class="ans"><span class="badge">${esc(statusText(i))}</span> ${esc(
        answerText(i),
      )}</p>${bars}${i.sql ? `<pre>${esc(i.sql)}</pre>` : ""}${table}${
        i.ms != null ? `<p class="meta">ตอบใน ${(i.ms / 1000).toFixed(1)} วินาที</p>` : ""
      }</section>`;
    })
    .join("");
  const html = `<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ThamDi รายงานคำตอบ</title><style>
body{font-family:Inter,Anuphan,"Leelawadee UI","Noto Sans Thai",Tahoma,sans-serif;color:#161613;background:#eef9f2;margin:0;padding:32px 16px;line-height:1.7}
main{max-width:860px;margin:0 auto}header{margin-bottom:24px}h1{margin:0;font-size:28px}header p{margin:4px 0 0;color:#6f6f6a}
section{background:#fff;border-radius:18px;padding:20px 24px;margin-bottom:18px;box-shadow:0 4px 18px rgba(39,120,78,.06)}
h2{margin:0 0 6px;font-size:18px}.ans{margin:0;font-size:17px}.badge{background:#e9f7ee;color:#11603b;font-size:12px;font-weight:600;border-radius:999px;padding:1px 10px}
.bars{margin:12px 0;display:grid;gap:6px}.bar{display:grid;grid-template-columns:minmax(80px,10rem) 1fr auto;gap:12px;align-items:center;font-size:14px}
.bar i{height:12px;background:#f2f2ee;border-radius:99px;overflow:hidden}.bar b{display:block;height:100%;background:#3fcf7d;border-radius:99px}
pre{background:#161613;color:#ddefe4;padding:10px 12px;border-radius:10px;white-space:pre-wrap;font-size:13px}
table{border-collapse:collapse;width:100%;font-size:14px;margin-top:10px}th,td{text-align:left;padding:6px 10px;border-top:1px solid #e8e8e3}th{background:#fafaf8;border-top:none}
.meta{color:#6f6f6a;font-size:13px;margin:8px 0 0}footer{color:#6f6f6a;font-size:13px;text-align:center}
</style></head><body><main><header><h1>ThamDi · รายงานคำตอบ</h1><p>ไฟล์ข้อมูล: ${esc(datasetName || "-")} · สร้างเมื่อ ${esc(stamp())} · ${list.length} คำถาม</p></header>${blocks}<footer>สร้างจาก ThamDi · โมเดลที่ทีมเทรนเองและรันในเครื่อง ไม่ส่งข้อมูลออกไปภายนอก</footer></main></body></html>`;
  downloadBlob(new Blob([html], { type: "text/html;charset=utf-8" }), `${base}.html`);
}

// รูปแบบไฟล์ที่ส่งออกได้ · needs: rows = ต้องมีตารางผล · sql = ต้องมี SQL
const FORMATS = [
  { key: "pdf", label: "PDF", ext: ".pdf", hint: "พิมพ์ / บันทึกเป็น PDF" },
  { key: "xlsx", label: "Excel", ext: ".xlsx", hint: "ตัวเลขเป็นตัวเลข", needs: "rows" },
  { key: "csv", label: "CSV", ext: ".csv", hint: "ตารางผล", needs: "rows" },
  { key: "json", label: "JSON", ext: ".json", hint: "คำถาม คำตอบ SQL ตาราง" },
  { key: "sql", label: "SQL", ext: ".sql", hint: "SQL ที่ระบบรันจริง", needs: "sql" },
  { key: "txt", label: "ข้อความ", ext: ".txt", hint: "อ่านได้ทุกโปรแกรม" },
  { key: "png", label: "รูปภาพ", ext: ".png", hint: "คำตอบพร้อมกราฟ" },
  { key: "html", label: "รายงาน HTML", ext: ".html", hint: "เปิดได้ทุกเครื่อง" },
];

function runExport(key, list, { oneId, base, datasetName, title }) {
  switch (key) {
    case "pdf":
      return printReport(oneId);
    case "xlsx":
      return exportXlsx(list, base);
    case "csv":
      return exportCsv(list, base);
    case "json":
      return exportJson(list, base, datasetName);
    case "sql":
      return exportSql(list, base, datasetName);
    case "txt":
      return exportTxt(list, base, datasetName);
    case "png":
      return exportPng(list, base, title);
    case "html":
      return exportHtml(list, base, datasetName);
    default:
      return undefined;
  }
}

function closeMenu(event) {
  event.currentTarget.closest("details")?.removeAttribute("open");
}

// เมนูส่งออก · item = คำตอบเดียว (ในคำตอบ) · items = ทั้งบทสนทนา (แถบด้านบน)
function ExportMenu({ item, items, datasetName, variant = "mini" }) {
  const [status, setStatus] = useState("");
  const list = done(item ? [item] : items || []);
  const can = { rows: list.some(hasRows), sql: list.some((i) => i.sql) };
  const one = !!item;

  async function run(event, fn, msg) {
    closeMenu(event);
    try {
      await fn();
      if (msg) {
        setStatus(msg);
        setTimeout(() => setStatus(""), 1600);
      }
    } catch (err) {
      setStatus(err.message || "ส่งออกไม่สำเร็จ");
      setTimeout(() => setStatus(""), 3000);
    }
  }

  const opts = {
    oneId: one ? item.id : undefined,
    base: one ? `thamdi-${item.id}` : `thamdi-chat-${Date.now()}`,
    datasetName,
    title: one ? "ThamDi · คำตอบ" : `ThamDi · บทสนทนา (${datasetName || "-"})`,
  };

  return (
    <span className="export">
      {status && (
        <span className="export-status" role="status">
          {status}
        </span>
      )}
      <details className="menu">
        {variant === "mini" ? (
          <summary className="mini-summary">ส่งออก</summary>
        ) : (
          <summary className={list.length ? "icon-btn" : "icon-btn is-disabled"} title="ส่งออกบทสนทนาทั้งหมด" aria-disabled={!list.length}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 4v11M7 10l5 5 5-5M5 20h14" />
            </svg>
            <span>ส่งออก</span>
          </summary>
        )}
        <div className={variant === "mini" ? "menu-list formats" : "menu-list formats right"}>
          <p className="menu-title">{one ? "ส่งออกคำตอบนี้เป็น" : list.length ? `ส่งออกทั้งบทสนทนา (${list.length} คำถาม)` : "ยังไม่มีคำตอบให้ส่งออก"}</p>
          {one && can.rows && (
            <button type="button" className="menu-wide" onClick={(e) => run(e, () => copyText(toTsv(item.columns, item.rows)), "คัดลอกตารางแล้ว")}>
              <span className="fmt-label">คัดลอกตาราง</span>
              <small>วางใน Excel/Word ได้</small>
            </button>
          )}
          {FORMATS.map((f) => (
            <button
              key={f.key}
              type="button"
              disabled={!list.length || (f.needs && !can[f.needs])}
              title={f.needs === "rows" && !can.rows ? "ไม่มีตารางผล" : f.needs === "sql" && !can.sql ? "ไม่มี SQL" : f.hint}
              onClick={(e) => run(e, () => runExport(f.key, list, opts), f.key === "pdf" ? "" : "ส่งออกแล้ว")}
            >
              <span className="fmt-label">
                {f.label} <code>{f.ext}</code>
              </span>
              <small>{f.hint}</small>
            </button>
          ))}
        </div>
      </details>
    </span>
  );
}

// 👍/👎 เก็บไว้ในเบราว์เซอร์นี้เท่านั้น (localStorage) ไม่ส่งไปที่ไหน
function readFeedback() {
  try {
    return JSON.parse(localStorage.getItem(feedbackKey()) || "{}");
  } catch {
    return {};
  }
}

function Feedback({ item }) {
  const [vote, setVote] = useState(null);

  useEffect(() => {
    setVote(readFeedback()[item.id]?.vote ?? null);
  }, [item.id]);

  function choose(next) {
    const value = vote === next ? null : next;
    setVote(value);
    try {
      const all = readFeedback();
      if (value) {
        all[item.id] = { vote: value, question: item.question, status: item.status, sql: item.sql || null, at: new Date().toISOString() };
      } else {
        delete all[item.id];
      }
      localStorage.setItem(feedbackKey(), JSON.stringify(all));
    } catch {
      // เบราว์เซอร์ไม่ให้เก็บ: ปุ่มยังกดได้ แค่ไม่จำ
    }
  }

  return (
    <span className="feedback" title="เก็บไว้ในเบราว์เซอร์นี้เท่านั้น">
      <span className="muted">คำตอบนี้ถูกไหม</span>
      <button type="button" className={vote === "up" ? "mini vote on" : "mini vote"} aria-pressed={vote === "up"} aria-label="ถูก" onClick={() => choose("up")}>
        <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 11v9H4v-9h3Zm3 9h7.5a2 2 0 0 0 2-1.6l1.2-6A2 2 0 0 0 18.7 10H14l.7-3.6A2 2 0 0 0 12.8 4L10 11v9Z" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
        </svg>
      </button>
      <button type="button" className={vote === "down" ? "mini vote on bad" : "mini vote"} aria-pressed={vote === "down"} aria-label="ผิด" onClick={() => choose("down")}>
        <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" style={{ transform: "rotate(180deg)" }}>
          <path d="M7 11v9H4v-9h3Zm3 9h7.5a2 2 0 0 0 2-1.6l1.2-6A2 2 0 0 0 18.7 10H14l.7-3.6A2 2 0 0 0 12.8 4L10 11v9Z" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
        </svg>
      </button>
    </span>
  );
}

function Answer({ item, settings, datasetName }) {
  const tone = item.pending ? "" : item.failed ? "failed" : item.status || "";
  const rowCount = item.rowCount ?? item.rows?.length ?? 0;
  return (
    <article className="answer" data-answer-id={item.id}>
      <p className="question">{item.question}</p>
      <div className="reply">
        <Mascot mood={moodOf(item)} size={42} decorative />
        <div className={`reply-body ${tone}`}>
          {item.pending ? (
            <p className="pending">กำลังหาคำตอบ... (โมเดลบน CPU อาจใช้เวลาหลายวินาที)</p>
          ) : item.failed ? (
            <p className="error">{item.failed}</p>
          ) : (
            <>
              <p className="answer-text">
                <span className={`badge ${item.status}`}>{STATUS_LABEL[item.status] || item.status}</span>
                {chatAnswer(item)}
              </p>
              {settings.showChart && <BarChart columns={item.columns} rows={item.rows} />}
              <div className="answer-more">
                {item.sql && (
                  <details open={settings.openSql || undefined}>
                    <summary>SQL ที่ระบบรันจริง</summary>
                    <pre>{item.sql}</pre>
                    <div className="tools">
                      <CopySqlButton sql={item.sql} />
                    </div>
                  </details>
                )}
                {item.rows?.length > 0 && (
                  <details open={settings.openTable || undefined}>
                    <summary>ดูตาราง ({rowCount.toLocaleString("en-US")} แถว)</summary>
                    <ResultTable columns={item.columns} rows={item.rows} />
                    {rowCount > item.rows.length && <p className="muted">แชทเก่าเก็บไว้ {item.rows.length} แถวแรก</p>}
                  </details>
                )}
              </div>
              <div className="answer-foot">
                <span className="foot-left">
                  {item.ms != null && <span className="muted">ตอบใน {(item.ms / 1000).toFixed(1)} วิ</span>}
                  <Feedback item={item} />
                </span>
                <ExportMenu item={item} datasetName={datasetName} />
              </div>
            </>
          )}
        </div>
      </div>
    </article>
  );
}

// ---------- ประวัติแชท: บทสนทนาที่เก็บในเบราว์เซอร์นี้ · กดแล้วเปิดแชทเดิมพร้อมคำตอบ ----------
function formatTime(iso) {
  try {
    return new Date(iso).toLocaleString("th-TH", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

function dayGroup(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "ก่อนหน้านี้";
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  const diff = (start - new Date(d.getFullYear(), d.getMonth(), d.getDate())) / 86400000;
  if (diff <= 0) return "วันนี้";
  if (diff === 1) return "เมื่อวาน";
  if (diff < 7) return "7 วันที่ผ่านมา";
  return "ก่อนหน้านี้";
}

function ChatHistory({ chats, currentId, saving, onOpen, onDelete }) {
  const [query, setQuery] = useState("");
  // ลบ 2 จังหวะในปุ่มเอง (ไม่ใช้ window.confirm: เบราว์เซอร์บางตัวบล็อกกล่องถาม แล้วตอบ "ยกเลิก" ให้ทันที)
  const [armed, setArmed] = useState(null);
  useEffect(() => {
    if (!armed) return undefined;
    const t = setTimeout(() => setArmed(null), 3000);
    return () => clearTimeout(t);
  }, [armed]);
  const q = query.trim().toLowerCase();
  const shown = q ? chats.filter((c) => c.items.some((i) => i.question.toLowerCase().includes(q))) : chats;
  const groups = [];
  shown.forEach((c) => {
    const g = dayGroup(c.updatedAt);
    if (!groups.length || groups[groups.length - 1].name !== g) groups.push({ name: g, items: [] });
    groups[groups.length - 1].items.push(c);
  });

  return (
    <section className="history-panel" aria-labelledby="history-title">
      <div className="side-head">
        <h2 id="history-title">ประวัติแชท</h2>
        <span className="count-pill">{chats.length}</span>
        <AsideToggle className="side-collapse" />
      </div>
      <label className="search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="ค้นหาในประวัติแชท..." aria-label="ค้นหาในประวัติแชท" />
      </label>
      {!saving && (
        <p className="hint">
          ปิดการเก็บประวัติแชทอยู่ · เปิดได้ที่ <Link href="/settings">ตั้งค่า</Link>
        </p>
      )}
      {saving && !chats.length && <p className="hint">ยังไม่มีแชท ถามแล้วแชทจะขึ้นที่นี่</p>}
      {chats.length > 0 && !shown.length && <p className="hint">ไม่พบแชทที่ค้นหา</p>}
      <div className="history-scroll">
        {groups.map((g) => (
          <div key={g.name} className="history-group">
            <p className="group-label">{g.name}</p>
            <ul className="history-list">
              {g.items.map((c) => (
                <li key={c.id} className="chat-row">
                  <button
                    type="button"
                    className={c.id === currentId ? "history-item current" : "history-item"}
                    aria-current={c.id === currentId ? "true" : undefined}
                    onClick={() => onOpen(c)}
                    title="เปิดแชทนี้"
                  >
                    <span className="history-q">{c.title}</span>
                    <span className="history-meta">
                      {c.items.length} คำถาม{c.datasetName ? ` · ${c.datasetName}` : ""} · {formatTime(c.updatedAt)}
                    </span>
                  </button>
                  <button
                    type="button"
                    className={armed === c.id ? "chat-delete armed" : "chat-delete"}
                    onClick={() => {
                      if (armed === c.id) {
                        setArmed(null);
                        onDelete(c);
                      } else setArmed(c.id);
                    }}
                    onBlur={() => armed === c.id && setArmed(null)}
                    aria-label={armed === c.id ? `กดอีกครั้งเพื่อลบแชท ${c.title}` : `ลบแชท ${c.title}`}
                    title={armed === c.id ? "กดอีกครั้งเพื่อลบ" : "ลบแชทนี้"}
                  >
                    {armed === c.id ? (
                      "ลบ?"
                    ) : (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M5 7h14M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" />
                    </svg>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

// ปุ่มแสดงประวัติแชทในหัวแผงหลัก: ขึ้นเฉพาะจอคอมตอนซ่อนแผงประวัติไว้
function ShowHistoryButton() {
  const { open, narrow } = useAside();
  if (open || narrow) return null;
  return <AsideToggle />;
}

const newChatId = () => `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;

export default function ChatPage() {
  const [settings] = useSettings();
  const [datasets, setDatasets] = useState([]);
  const [datasetId, setDatasetId] = useState("");
  const [loadError, setLoadError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [question, setQuestion] = useState("");
  const [items, setItems] = useState([]);
  const [fileName, setFileName] = useState(""); // แสดงชื่อไฟล์ที่เลือกในช่องวางไฟล์เท่านั้น
  const [chatId, setChatId] = useState(newChatId);
  const [chats, setChats] = useState([]);
  const [chatNote, setChatNote] = useState("");
  const fileRef = useRef(null);
  const needsSave = useRef(false);
  const busy = items.some((i) => i.pending);
  const threadRef = useRef(null);
  const thread = [...items].reverse();
  const dataset = datasets.find((d) => d.dataset_id === datasetId);
  const datasetName = dataset?.name || "";
  const examples = examplesFor(dataset?.tables);

  useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [items]);

  useEffect(() => {
    setChats(readChats());
  }, []);

  const loadDatasets = useCallback(async (selectId) => {
    try {
      const list = await api("/api/datasets");
      setDatasets(list);
      setLoadError("");
      // เปิดครั้งแรก: เลือกไฟล์ยอดขายก่อน (ไฟล์หลักของเดโม) ไม่มีก็เลือกไฟล์ล่าสุด
      const preferred = list.find((d) => d.tables.includes("sales")) || list[0];
      setDatasetId((current) => {
        const remembered = list.find((d) => d.dataset_id === getSelectedDataset());
        const active = list.find((d) => d.dataset_id === current);
        const next = selectId || active?.duplicate_of || current || remembered?.duplicate_of || remembered?.dataset_id || preferred?.dataset_id || "";
        setSelectedDataset(next);
        return next;
      });
    } catch (err) {
      setLoadError(err.message);
    }
  }, []);

  useEffect(() => {
    loadDatasets();
  }, [loadDatasets]);

  // ได้คำตอบครบแล้ว → บันทึกแชทนี้ลงประวัติ (เฉพาะตอนเปิดการเก็บประวัติในตั้งค่า)
  useEffect(() => {
    if (!needsSave.current || busy) return;
    needsSave.current = false;
    if (!settings.saveChats) return;
    setChats(upsertChat({ id: chatId, datasetId, datasetName, items }));
  }, [items, busy, chatId, datasetId, datasetName, settings.saveChats]);

  function newChat() {
    if (busy) return;
    setItems([]);
    setChatId(newChatId());
    setChatNote("");
    setQuestion("");
  }

  function openChat(c) {
    if (busy) return;
    setItems(c.items);
    setChatId(c.id);
    setQuestion("");
    if (datasets.some((d) => d.dataset_id === c.datasetId)) {
      setDatasetId(c.datasetId);
      setSelectedDataset(c.datasetId);
      setChatNote("");
    } else {
      setChatNote(`ไฟล์ของแชทนี้ (${c.datasetName || "-"}) ไม่มีแล้ว ถามต่อจะใช้ไฟล์ที่เลือกอยู่`);
    }
  }

  function removeChat(c) {
    setChats(deleteChat(c.id));
    if (c.id === chatId) newChat();
  }

  // อัปโหลดเสร็จ (มีข้อความผล) → ล้างชื่อไฟล์ที่แสดง
  useEffect(() => {
    if (uploadMsg) setFileName("");
  }, [uploadMsg]);

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

  // ปุ่ม "ลองด้วยไฟล์ยอดขายตัวอย่าง": โหลดไฟล์จากเว็บนี้เอง แล้วอัปโหลดผ่าน API เดิม
  async function uploadSample() {
    setUploading(true);
    setUploadMsg("");
    try {
      const res = await fetch(SAMPLE_FILE.url);
      if (!res.ok) throw new Error("โหลดไฟล์ตัวอย่างไม่สำเร็จ");
      const form = new FormData();
      form.append("file", new File([await res.blob()], SAMPLE_FILE.name));
      const created = await api("/api/datasets", { method: "POST", form, timeoutMs: 60000 });
      setUploadMsg(`อัปโหลดไฟล์ตัวอย่างแล้ว · ตาราง: ${created.tables.join(", ")}`);
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
    setChatNote("");
    const started = performance.now();
    try {
      const reply = await api("/api/chat", {
        method: "POST",
        body: { dataset_id: datasetId, question: q },
        timeoutMs: CHAT_TIMEOUT_MS,
      });
      const ms = performance.now() - started;
      needsSave.current = true;
      setItems((prev) => prev.map((i) => (i.id === id ? { id, question: q, ...reply, ms } : i)));
    } catch (err) {
      needsSave.current = true;
      setItems((prev) => prev.map((i) => (i.id === id ? { id, question: q, failed: err.message } : i)));
    }
  }

  const historyPanel = <ChatHistory chats={chats} currentId={chatId} saving={settings.saveChats} onOpen={openChat} onDelete={removeChat} />;

  return (
    <AppShell aside={historyPanel} asideLabel="ประวัติแชท">
      <div className="chat">
        <header className="panel-head">
          <div className="head-left">
            <ShowHistoryButton />
            <h1>ถามข้อมูล</h1>
            <button type="button" className="icon-btn new-chat" onClick={newChat} disabled={!items.length || busy} title="เริ่มแชทใหม่ (แชทเดิมอยู่ในประวัติแชท)">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
                <path d="M12 5v14M5 12h14" />
              </svg>
              <span>แชทใหม่</span>
            </button>
          </div>
          <form className="file-bar" onSubmit={upload}>
            <label className="file-select">
              <span className="sr-only">ไฟล์ที่ใช้ถาม</span>
              <select value={datasetId} onChange={(e) => { setDatasetId(e.target.value); setSelectedDataset(e.target.value); }} disabled={!datasets.length}>
                {!datasets.length && <option value="">ยังไม่มีข้อมูล อัปโหลดไฟล์ก่อน</option>}
                {datasets.filter((d) => !d.duplicate_of).map((d) => (
                  <option key={d.dataset_id} value={d.dataset_id}>
                    {d.name} ({d.tables.join(", ")})
                  </option>
                ))}
              </select>
            </label>
            <input
              id="file-input"
              className="sr-only"
              type="file"
              ref={fileRef}
              accept=".csv,.tsv,.txt,.xlsx,.xls,.ods,.json"
              required
              onChange={(e) => {
                setFileName(e.target.files?.[0]?.name || "");
                if (e.target.files?.length) e.target.form.requestSubmit();
              }}
            />
            <label htmlFor="file-input" className={uploading ? "icon-btn busy" : "icon-btn"} title="อัปโหลดไฟล์ตาราง">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M12 16V4M7 9l5-5 5 5M5 20h14" />
              </svg>
              <span>{uploading ? "กำลังอัปโหลด..." : "อัปโหลด"}</span>
            </label>
            <ExportMenu items={thread} datasetName={datasetName} variant="bar" />
          </form>
        </header>

        {(loadError || uploadMsg || fileName || chatNote) && (
          <div className="notice-row">
            {loadError && (
              <p className="error">
                {loadError}{" "}
                <button type="button" className="link" onClick={() => loadDatasets()}>
                  ลองใหม่
                </button>
              </p>
            )}
            {chatNote && <p className="upload-msg">{chatNote}</p>}
            {fileName && <p className="upload-msg">กำลังอัปโหลด {fileName}</p>}
            {uploadMsg && !fileName && <p className="upload-msg">{uploadMsg}</p>}
          </div>
        )}

        <div className="thread" ref={threadRef}>
          <div className="print-head">
            <strong>ThamDi · รายงานคำตอบ</strong>
            <span>
              ไฟล์ข้อมูล: {datasetName || "-"} · พิมพ์เมื่อ {stamp()}
            </span>
          </div>
          {!items.length && (
            <div className="welcome">
              <Mascot mood="happy" size={150} />
              <h2>สวัสดี ฉันชื่อน้องดี</h2>
              <p className="muted">
                {datasetId
                  ? "พิมพ์คำถามเป็นภาษาไทยด้านล่าง หรือกดตัวอย่างก็ได้ น้องดีจะตอบพร้อมกราฟ SQL ที่ใช้ และตารางผล"
                  : "อัปโหลดไฟล์ตารางของร้าน (.csv .xlsx .xls .ods .tsv .txt .json ไม่เกิน 10 MB) แล้วค่อยถามได้เลย"}
              </p>
              <button type="button" className="sample" onClick={uploadSample} disabled={uploading}>
                ไม่มีไฟล์? ลองด้วยไฟล์ยอดขายตัวอย่าง
              </button>
              <p className="hint">ระบบอ่านข้อมูลได้อย่างเดียว ไม่แก้ไฟล์ของคุณ</p>
            </div>
          )}
          {thread.map((item) => (
            <Answer key={item.id} item={item} settings={settings} datasetName={datasetName} />
          ))}
        </div>

        <div className="composer-wrap">
          {settings.showExamples && datasetId && (
            <div className="chips" aria-label="ตัวอย่างคำถาม">
              {examples.map((q) => (
                <button key={q} type="button" onClick={() => setQuestion(q)} disabled={!datasetId}>
                  {q}
                </button>
              ))}
              {DANGER_EXAMPLES.map((q) => (
                <button key={q} type="button" className="danger" onClick={() => setQuestion(q)} disabled={!datasetId} title="ลองสั่งแก้/ลบข้อมูล">
                  {q}
                </button>
              ))}
            </div>
          )}
          <form className="composer" onSubmit={ask}>
            <label htmlFor="file-input" className="composer-icon" title="อัปโหลดไฟล์ตาราง">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="m21 11-8.5 8.5a5 5 0 0 1-7-7L14 4a3.5 3.5 0 0 1 5 5l-8.5 8.5a2 2 0 0 1-3-3L15 7" />
              </svg>
              <span className="sr-only">อัปโหลดไฟล์</span>
            </label>
            <input
              className="grow"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="ถามเป็นภาษาไทย เช่น ยอดขายรวมของแต่ละสาขาเดือนตุลาคม 2569"
              aria-label="คำถาม"
              maxLength={500}
              disabled={!datasetId}
            />
            <button type="submit" className="send" disabled={!datasetId || busy || !question.trim()}>
              <span>{busy ? "กำลังตอบ..." : "ถาม"}</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </button>
          </form>
        </div>
      </div>
    </AppShell>
  );
}
