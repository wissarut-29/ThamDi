"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "../../components/AppShell";
import { api } from "../../lib/api";
import { getSelectedDataset, setSelectedDataset } from "../../lib/datasets";

const numberFormat = new Intl.NumberFormat("th-TH", { maximumFractionDigits: 1 });
const compactNumberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
const COLUMN_LABELS = {
  monthly_salary: "เงินเดือน",
  full_name: "ชื่อพนักงาน",
  branch: "สาขา",
  position: "ตำแหน่ง",
  start_date: "วันที่เริ่มงาน",
  product_name: "สินค้า",
  category: "หมวดหมู่",
  quantity: "จำนวน",
  sales_amount: "ยอดขาย",
  total_sales: "ยอดขายรวม",
  year: "ปี",
  month: "เดือน",
};

function columnLabel(name) {
  return COLUMN_LABELS[name.toLowerCase()] || name.replaceAll("_", " ");
}

function columnType(type) {
  if (/DATE|TIME/.test(type)) return "วันที่";
  if (/^(TINYINT|SMALLINT|INTEGER|BIGINT|HUGEINT|UTINYINT|USMALLINT|UINTEGER|UBIGINT|FLOAT|DOUBLE|DECIMAL|REAL)/.test(type)) return "ตัวเลข";
  if (/BOOL/.test(type)) return "ใช่/ไม่ใช่";
  return "ข้อความ";
}

const chartKey = (chart, datasetId, table) => `${datasetId}-${table}-${chart.category}-${chart.metric}`;
const canvasFont = (weight, size) => `${weight} ${size}px Inter, Anuphan, "Leelawadee UI", Tahoma, sans-serif`;

function wrapCanvasText(ctx, value, width) {
  const words = typeof Intl.Segmenter === "function"
    ? [...new Intl.Segmenter("th", { granularity: "word" }).segment(String(value))].map((part) => part.segment)
    : [...String(value)];
  const lines = [];
  let line = "";
  for (const word of words) {
    if (ctx.measureText(line + word).width <= width || !line) line += word;
    else { lines.push(line.trimEnd()); line = word.trimStart(); }
  }
  if (line) lines.push(line);
  return lines;
}

async function downloadSummaryPng(summary, chartTypes) {
  await document.fonts?.ready;
  const width = 1200;
  const pad = 56;
  const metrics = [
    ["จำนวนแถว", summary.row_count],
    ["จำนวนคอลัมน์", summary.column_count],
    ["ช่องตัวเลข", summary.numeric_count],
    ...(summary.numeric_summary ? [[`${columnLabel(summary.numeric_summary.column)}รวม`, summary.numeric_summary.sum, `เฉลี่ย ${formatNumber(summary.numeric_summary.average)}`]] : []),
    ["ข้อมูลที่หาย", summary.missing_count],
    ["แถวซ้ำ", summary.duplicate_rows],
  ];
  const charts = summary.charts || [];
  const chartHeight = (chart) => (chartTypes[chartKey(chart, summary.dataset_id, summary.table)] || chart.suggested) === "horizontal"
    ? Math.max(230, chart.points.length * 38 + 112) : 340;
  const height = pad + 90 + Math.ceil(metrics.length / 3) * 142 + 70 + charts.reduce((sum, chart) => sum + chartHeight(chart) + 18, 0) + 110;
  const canvas = document.createElement("canvas");
  const scale = 2;
  canvas.width = width * scale;
  canvas.height = Math.min(height * scale, 32000);
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("เปิดพื้นที่สร้างรูปไม่ได้");
  ctx.scale(scale, scale);
  ctx.fillStyle = "#f5faf6";
  ctx.fillRect(0, 0, width, height);
  ctx.textAlign = "left";

  let y = pad;
  ctx.fillStyle = "#161613";
  ctx.font = canvasFont(600, 32);
  ctx.fillText("สรุปข้อมูล", pad, y + 34);
  ctx.font = canvasFont(400, 16);
  ctx.fillStyle = "#666b66";
  ctx.fillText(`${summary.name} · ตาราง ${summary.table} · สร้างเมื่อ ${new Date().toLocaleString("th-TH")}`, pad, y + 66);
  y += 100;

  const gap = 16;
  const cardWidth = (width - pad * 2 - gap * 2) / 3;
  metrics.forEach(([label, value, hint], index) => {
    const x = pad + (index % 3) * (cardWidth + gap);
    const top = y + Math.floor(index / 3) * 126;
    ctx.fillStyle = index === 0 ? "#e8f8ee" : "#ffffff";
    ctx.beginPath(); ctx.roundRect(x, top, cardWidth, 110, 14); ctx.fill();
    ctx.fillStyle = "#666b66"; ctx.font = canvasFont(400, 15); ctx.fillText(label, x + 18, top + 28);
    ctx.fillStyle = "#161613"; ctx.font = canvasFont(600, 27); ctx.fillText(formatNumber(value), x + 18, top + 62);
    if (hint) { ctx.fillStyle = "#666b66"; ctx.font = canvasFont(400, 14); ctx.fillText(hint, x + 18, top + 88); }
  });
  y += Math.ceil(metrics.length / 3) * 126 + 30;

  ctx.fillStyle = "#161613"; ctx.font = canvasFont(600, 22); ctx.fillText("กราฟจากข้อมูล", pad, y + 24);
  y += 40;
  charts.forEach((chart) => {
    const type = chartTypes[chartKey(chart, summary.dataset_id, summary.table)] || chart.suggested || "bar";
    const points = type === "pie" ? chart.points.slice(0, 6) : chart.points.slice(0, 8);
    const boxHeight = chartHeight(chart);
    ctx.fillStyle = "#ffffff";
    ctx.beginPath(); ctx.roundRect(pad, y, width - pad * 2, boxHeight, 16); ctx.fill();
    ctx.fillStyle = "#161613"; ctx.font = canvasFont(600, 18);
    ctx.fillText(`${columnLabel(chart.metric)} แยกตาม ${columnLabel(chart.category)}`, pad + 22, y + 32);
    ctx.fillStyle = "#666b66"; ctx.font = canvasFont(400, 13);
    ctx.fillText(chartDescription(chart, type), pad + 22, y + 52);
    const largest = Math.max(...points.map((point) => point.value), 1);

    if (type === "horizontal") {
      const labelWidth = 190;
      const barX = pad + 24 + labelWidth;
      const barWidth = width - pad * 2 - labelWidth - 120;
      points.forEach((point, index) => {
        const rowY = y + 66 + index * 38;
        ctx.font = canvasFont(400, 13); ctx.fillStyle = "#555b56";
        let label = point.label;
        while (ctx.measureText(label).width > labelWidth - 12 && label.length > 2) label = `${label.slice(0, -2)}…`;
        ctx.fillText(label, pad + 24, rowY + 17);
        ctx.fillStyle = "#edf2ee"; ctx.beginPath(); ctx.roundRect(barX, rowY + 2, barWidth, 18, 8); ctx.fill();
        ctx.fillStyle = point.value === largest ? "#58bfe0" : "#a7e4bb"; ctx.beginPath(); ctx.roundRect(barX, rowY + 2, Math.max(3, point.value / largest * barWidth), 18, 8); ctx.fill();
        ctx.fillStyle = "#161613"; ctx.textAlign = "right"; ctx.font = canvasFont(500, 13); ctx.fillText(formatNumber(point.value), width - pad - 22, rowY + 17); ctx.textAlign = "left";
      });
    } else if (type === "pie") {
      const total = points.reduce((sum, point) => sum + point.value, 0) || 1;
      const cx = pad + 150; const cy = y + boxHeight / 2 + 16; const radius = Math.min(104, boxHeight / 2 - 38);
      let angle = -Math.PI / 2;
      points.forEach((point, index) => {
        const end = angle + point.value / total * Math.PI * 2;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, radius, angle, end); ctx.closePath();
        ctx.fillStyle = COLORS[index % COLORS.length]; ctx.fill(); ctx.strokeStyle = "#fff"; ctx.lineWidth = 2; ctx.stroke(); angle = end;
      });
      points.forEach((point, index) => {
        const rowY = y + 74 + index * 34;
        ctx.fillStyle = COLORS[index % COLORS.length]; ctx.beginPath(); ctx.arc(pad + 310, rowY - 4, 5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#161613"; ctx.font = canvasFont(400, 14); ctx.fillText(point.label.slice(0, 42), pad + 324, rowY);
        ctx.textAlign = "right"; ctx.font = canvasFont(600, 14); ctx.fillText(formatNumber(point.value), width - pad - 24, rowY); ctx.textAlign = "left";
      });
    } else {
      const left = pad + 42; const right = width - pad - 32; const top = y + 90; const bottom = y + boxHeight - 54;
      ctx.strokeStyle = "#e5ebe6"; ctx.lineWidth = 1;
      for (let i = 0; i < 4; i++) { const gy = top + i * (bottom - top) / 3; ctx.beginPath(); ctx.moveTo(left, gy); ctx.lineTo(right, gy); ctx.stroke(); }
      const step = (right - left) / points.length;
      if (type === "line") {
        ctx.beginPath();
        points.forEach((point, index) => {
          const px = left + step * (index + .5); const py = bottom - point.value / largest * (bottom - top);
          if (index) ctx.lineTo(px, py); else ctx.moveTo(px, py);
        });
        ctx.strokeStyle = "#40bf73"; ctx.lineWidth = 4; ctx.lineJoin = "round"; ctx.stroke();
      }
      points.forEach((point, index) => {
        const center = left + step * (index + .5); const barH = point.value / largest * (bottom - top);
        if (type === "line") {
          const py = bottom - barH; ctx.fillStyle = "#168c4a"; ctx.beginPath(); ctx.arc(center, py, 5, 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = "#161613"; ctx.font = canvasFont(400, 12); ctx.textAlign = "center"; ctx.fillText(formatNumber(point.value), center, py - 12);
        } else {
          const bw = Math.min(54, step * .54); ctx.fillStyle = point.value === largest ? "#58bfe0" : "#a7e4bb";
          ctx.beginPath(); ctx.roundRect(center - bw / 2, bottom - barH, bw, Math.max(barH, 3), [8, 8, 1, 1]); ctx.fill();
          ctx.fillStyle = "#161613"; ctx.font = canvasFont(400, 12); ctx.textAlign = "center"; ctx.fillText(formatNumber(point.value), center, bottom - barH - 10);
        }
        ctx.fillStyle = "#666b66"; ctx.font = canvasFont(400, 12);
        const axisLabel = point.label.length > 12 ? `${point.label.slice(0, 11)}…` : point.label;
        ctx.fillText(axisLabel, center, bottom + 24);
      });
      ctx.textAlign = "left";
    }
    y += boxHeight + 18;
  });

  const columns = summary.columns.map((column) => columnLabel(column.name)).join(" · ");
  ctx.fillStyle = "#666b66"; ctx.font = canvasFont(400, 14);
  const lines = wrapCanvasText(ctx, `คอลัมน์: ${columns}`, width - pad * 2);
  lines.forEach((line, index) => ctx.fillText(line, pad, y + 20 + index * 22));

  const blob = await new Promise((resolve, reject) => canvas.toBlob((value) => value ? resolve(value) : reject(new Error("สร้างรูปไม่สำเร็จ")), "image/png"));
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `thamdi-summary-${String(summary.name).replace(/[^\p{L}\p{N}._-]+/gu, "-").slice(0, 60)}.png`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function formatNumber(value) {
  if (value == null) return "–";
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `${compactNumberFormat.format(value / 1_000_000)}M`;
  if (abs >= 1_000) return `${compactNumberFormat.format(value / 1_000)}K`;
  return numberFormat.format(value);
}

const COLORS = ["#70d796", "#9ae1b3", "#58bfe0", "#b7e8c7", "#72a6e5", "#cdeed7"];

function Graph({ chart, type }) {
  const title = `${columnLabel(chart.metric)} แยกตาม ${columnLabel(chart.category)}`;
  const points = chart.points || [];
  if (!points.length) return <p className="muted">ยังไม่มีข้อมูลสำหรับกราฟนี้</p>;
  const shown = type === "pie" ? points.slice(0, 6) : points.slice(0, 8);
  const max = Math.max(...shown.map((p) => p.value), 1);
  const largest = shown.reduce((best, point, i) => point.value > shown[best].value ? i : best, 0);

  if (type === "horizontal") {
    return <div className="summary-horizontal" role="img" aria-label={`กราฟแท่งแนวนอน ${title}`}>{shown.map((point, i) => <div className="summary-horizontal-row" key={point.label}><span title={point.label}>{point.label}</span><div><i style={{ width: `${Math.max(1, point.value / max * 100)}%`, background: i === largest ? "#58bfe0" : "#a7e4bb" }} /></div><strong>{formatNumber(point.value)}</strong></div>)}</div>;
  }

  if (type === "pie") {
    const total = shown.reduce((sum, p) => sum + p.value, 0) || 1;
    let angle = 0;
    const slices = shown.map((point, i) => {
      const start = angle;
      angle += (point.value / total) * Math.PI * 2;
      const end = angle;
      const polar = (a) => [100 + 82 * Math.sin(a), 100 - 82 * Math.cos(a)];
      const [x1, y1] = polar(start);
      const [x2, y2] = polar(end);
      const large = end - start > Math.PI ? 1 : 0;
      if (end - start > Math.PI * 2 - 0.001) return <circle key={point.label} cx="100" cy="100" r="82" fill={COLORS[i % COLORS.length]} />;
      return <path key={point.label} d={`M100 100 L${x1} ${y1} A82 82 0 ${large} 1 ${x2} ${y2} Z`} fill={COLORS[i % COLORS.length]} stroke="white" strokeWidth="2" />;
    });
    return <div className="summary-pie-layout"><svg className="summary-pie" viewBox="0 0 200 200" role="img" aria-label={`กราฟวงกลม ${title}`}>{slices}</svg><ul className="summary-legend">{shown.map((p, i) => <li key={p.label}><i style={{ background: COLORS[i % COLORS.length] }} /><span>{p.label}</span><strong>{formatNumber(p.value)}</strong></li>)}</ul></div>;
  }

  if (type === "line") {
    const coordinates = shown.map((p, i) => `${36 + i * (568 / Math.max(1, shown.length - 1))},${172 - (p.value / max) * 132}`).join(" ");
    return <div className="summary-line-wrap"><svg className="summary-line" viewBox="0 0 640 210" role="img" aria-label={`กราฟเส้น ${title}`}><path d="M36 174H604" stroke="#dfe8e1" /><polyline points={coordinates} fill="none" stroke="#40bf73" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />{shown.map((p, i) => { const x = 36 + i * (568 / Math.max(1, shown.length - 1)); const y = 172 - (p.value / max) * 132; return <g key={p.label}><circle cx={x} cy={y} r="5" fill="#168c4a" /><text x={x} y={y - 12} textAnchor="middle" className="chart-value">{formatNumber(p.value)}</text><text x={x} y="198" textAnchor="middle" className="chart-label">{p.label.length > 12 ? `${p.label.slice(0, 11)}…` : p.label}</text></g>; })}</svg></div>;
  }

  return <div className="summary-bars" role="img" aria-label={`กราฟแท่ง ${title}`}>{shown.map((p, i) => <div className="summary-bar-item" key={p.label}><strong>{formatNumber(p.value)}</strong><div className="summary-bar-track"><i style={{ height: `${Math.max(3, (p.value / max) * 100)}%`, background: i === largest ? "#58bfe0" : "#a7e4bb" }} /></div><span title={p.label}>{p.label}</span></div>)}</div>;
}

function chartDescription(chart, type) {
  const metric = columnLabel(chart.metric);
  const category = columnLabel(chart.category);
  if (type === "line") return chart.suggested === "line" ? `ดู${metric}รายเดือน` : `ดูแนวโน้ม${metric}ตาม${category}`;
  if (type === "pie") return `ดูสัดส่วน${metric}ในแต่ละ${category}`;
  if (type === "horizontal") return `เทียบ${metric}ของแต่ละ${category}จากซ้ายไปขวา`;
  return `เทียบ${metric}ของแต่ละ${category}`;
}

function ChartCard({ chart, featured = false, type, onTypeChange }) {
  const pieAllowed = chart.points.every((point) => point.value >= 0) && chart.points.some((point) => point.value > 0);
  return <section className={`summary-chart${featured ? " featured" : ""}`}>
    <header className="summary-chart-head"><h2>{columnLabel(chart.metric)} แยกตาม {columnLabel(chart.category)}</h2><div className="chart-switch" aria-label="ชนิดกราฟ">{[["bar", "แท่งตั้ง"], ["horizontal", "แท่งนอน"], ["line", "เส้น"], ["pie", "วงกลม"]].map(([value, label]) => <button key={value} type="button" className={type === value ? "selected" : ""} aria-pressed={type === value} disabled={value === "pie" && !pieAllowed} title={value === "pie" && !pieAllowed ? "ใช้กราฟวงกลมกับค่าบวก" : undefined} onClick={() => onTypeChange(value)}>{label}</button>)}</div></header>
    <p className="summary-chart-description">{chartDescription(chart, type)}</p>
    <Graph chart={chart} type={type} />
    {type === "pie" && chart.points.length > 6 && <p className="hint">แสดง 6 รายการแรก</p>}
  </section>;
}

function printSummary() {
  const body = document.body;
  const cleanup = () => {
    delete body.dataset.print;
    window.removeEventListener("afterprint", cleanup);
  };
  body.dataset.print = "summary";
  window.addEventListener("afterprint", cleanup);
  window.print();
}

function SummaryExport({ summary, chartTypes }) {
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  async function run(event, format) {
    event.currentTarget.closest("details")?.removeAttribute("open");
    if (format === "pdf") return printSummary();
    setBusy(true);
    try {
      await downloadSummaryPng(summary, chartTypes);
      setStatus("สร้างรูปแล้ว");
    } catch (err) {
      setStatus(err.message || "สร้างรูปไม่สำเร็จ");
    } finally {
      setBusy(false);
      setTimeout(() => setStatus(""), 2500);
    }
  }

  return <span className="export summary-export">
    {status && <span className="export-status" role="status">{status}</span>}
    <details className="menu">
      <summary className="icon-btn" title="พิมพ์หรือบันทึกสรุป">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2M6 14h12v7H6z" /></svg>
        <span>ส่งออก</span>
      </summary>
      <div className="menu-list formats right">
        <p className="menu-title">บันทึกสรุปข้อมูล</p>
        <button type="button" onClick={(event) => run(event, "pdf")}><span className="fmt-label">PDF <code>.pdf</code></span><small>พิมพ์หรือบันทึกจากเบราว์เซอร์</small></button>
        <button type="button" disabled={busy} onClick={(event) => run(event, "png")}><span className="fmt-label">รูปภาพ <code>.png</code></span><small>{busy ? "กำลังสร้างรูป…" : "ดาวน์โหลดกราฟและตัวเลขสรุป"}</small></button>
      </div>
    </details>
  </span>;
}

export default function SummaryPage() {
  const [datasets, setDatasets] = useState([]);
  const [datasetId, setDatasetId] = useState("");
  const [table, setTable] = useState("");
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [retry, setRetry] = useState(0);
  const [chartTypes, setChartTypes] = useState({});

  const loadDatasets = useCallback(async () => {
    try {
      const list = await api("/api/datasets");
      setDatasets(list);
      const remembered = list.find((d) => d.dataset_id === getSelectedDataset());
      const preferred = list.find((d) => d.tables.includes("sales")) || list[0];
      const chosen = remembered?.duplicate_of || remembered?.dataset_id || preferred?.duplicate_of || preferred?.dataset_id || "";
      setDatasetId(chosen);
      setSelectedDataset(chosen);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => { loadDatasets(); }, [loadDatasets]);

  const selected = datasets.find((d) => d.dataset_id === datasetId);
  useEffect(() => {
    if (!datasetId) { setSummary(null); return; }
    let cancelled = false;
    setLoading(true);
    setError("");
    api(`/api/datasets/${datasetId}/summary${table ? `?table=${encodeURIComponent(table)}` : ""}`)
      .then((data) => { if (!cancelled) { setSummary(data); setTable(data.table); } })
      .catch((err) => { if (!cancelled) { setSummary(null); setError(err.message); } })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [datasetId, table, retry]);

  return <AppShell><div className="summary-page">
    <header className="summary-header"><div><h1>สรุปข้อมูล</h1><p>สรุปจากไฟล์ที่เลือก</p>{summary && <p className="summary-print-meta">ไฟล์ {summary.name} · ตาราง {summary.table}</p>}</div><div className="summary-selectors"><label>ไฟล์ข้อมูล<select value={datasetId} onChange={(e) => { setDatasetId(e.target.value); setTable(""); setSelectedDataset(e.target.value); }}><option value="">เลือกไฟล์</option>{datasets.filter((d) => !d.duplicate_of).map((d) => <option key={d.dataset_id} value={d.dataset_id}>{d.name}</option>)}</select></label>{selected?.tables?.length > 1 && <label>ตาราง<select value={table || selected.tables[0]} onChange={(e) => setTable(e.target.value)}>{selected.tables.map((name) => <option key={name} value={name}>{name}</option>)}</select></label>}{summary && !loading && <SummaryExport summary={summary} chartTypes={chartTypes} />}</div></header>
    {error && <div className="summary-message"><p className="error">{error}</p><button type="button" className="icon-btn" onClick={() => datasetId ? setRetry((value) => value + 1) : loadDatasets()}>ลองอีกครั้ง</button></div>}
    {!datasets.length && !error && <div className="summary-empty"><h2>ยังไม่มีไฟล์ข้อมูล</h2><p>อัปโหลดไฟล์ตารางในหน้าแชท แล้วกลับมาดูสรุปได้ที่นี่</p><Link href="/chat">ไปหน้าแชท</Link></div>}
    {loading && <p className="summary-loading" role="status">กำลังสรุปข้อมูล…</p>}
    {summary && !loading && <>
      <section className="summary-stats" aria-label="ตัวเลขสรุป">
        <div className="summary-stat primary"><span>จำนวนแถว</span><strong>{formatNumber(summary.row_count)}</strong></div>
        <div className="summary-stat"><span>จำนวนคอลัมน์</span><strong>{formatNumber(summary.column_count)}</strong></div>
        <div className="summary-stat"><span>ช่องตัวเลข</span><strong>{formatNumber(summary.numeric_count)}</strong></div>
        {summary.numeric_summary && <div className="summary-stat"><span>{columnLabel(summary.numeric_summary.column)}รวม</span><strong>{formatNumber(summary.numeric_summary.sum)}</strong><small>เฉลี่ย {formatNumber(summary.numeric_summary.average)}</small></div>}
        <div className="summary-stat"><span>ข้อมูลที่หาย</span><strong>{formatNumber(summary.missing_count)}</strong></div>
        <div className="summary-stat"><span>แถวซ้ำ</span><strong>{formatNumber(summary.duplicate_rows)}</strong></div>
      </section>
      {summary.charts.length ? <><div className="summary-section-title"><h2>กราฟจากข้อมูล</h2></div><div className="summary-chart-grid">{summary.charts.map((chart, i) => { const key = chartKey(chart, summary.dataset_id, summary.table); return <ChartCard key={key} chart={chart} featured={i === 0} type={chartTypes[key] || chart.suggested || "bar"} onTypeChange={(type) => setChartTypes((current) => ({ ...current, [key]: type }))} />; })}</div></> : <div className="summary-empty"><h2>ยังไม่มีข้อมูลพอทำกราฟ</h2><p>ต้องมีช่องตัวเลขกับหมวดหมู่หรือวันที่</p></div>}
      <section className="summary-columns"><h2>คอลัมน์</h2><div>{summary.columns.map((col) => <span key={col.name}><strong>{columnLabel(col.name)}</strong><small>{columnType(col.type)}</small></span>)}</div></section>
    </>}
  </div></AppShell>;
}
