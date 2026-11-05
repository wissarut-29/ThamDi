// ประวัติแชท: เก็บบทสนทนาทั้งชุด (คำถาม + คำตอบ + ตาราง) ในเบราว์เซอร์นี้ (localStorage)
// เปิดแชทเก่าแล้วเห็นคำตอบเดิมได้ทันที ไม่ต้องให้โมเดลตอบใหม่ · ไม่ส่งไปที่ API
// แยกตามบัญชี: คนที่ login บัญชีอื่นบนเครื่องเดียวกันไม่เห็นแชทและผลโหวตของกัน
import { currentUser } from "./api";

const LEGACY_KEYS = ["thamdi_chats_v1", "thamdi_feedback_v1"]; // รุ่นก่อนเก็บรวมทุกบัญชี ไม่รู้ว่าเป็นของใคร → ลบทิ้ง
const userPart = () => encodeURIComponent(currentUser() || "anonymous");
const keyOf = () => `thamdi_chats_v2:${userPart()}`;
export const feedbackKey = () => `thamdi_feedback_v2:${userPart()}`;

function dropLegacy() {
  try {
    LEGACY_KEYS.forEach((k) => localStorage.removeItem(k));
  } catch {
    // ไม่มีที่เก็บ
  }
}
const MAX_CHATS = 40;
const MAX_ROWS = 200; // ตัดแถวที่เก็บไว้ กัน localStorage เต็ม (ส่งออกจากแชทเก่าได้ไม่เกินนี้)

export function readChats() {
  dropLegacy();
  try {
    const list = JSON.parse(localStorage.getItem(keyOf()) || "[]");
    return Array.isArray(list) ? list : [];
  } catch {
    return [];
  }
}

function save(list) {
  let next = list.slice(0, MAX_CHATS);
  // พื้นที่ไม่พอ: ทิ้งแชทเก่าสุดทีละอันจนเก็บได้
  while (next.length) {
    try {
      localStorage.setItem(keyOf(), JSON.stringify(next));
      return next;
    } catch {
      next = next.slice(0, -1);
    }
  }
  try {
    localStorage.removeItem(keyOf());
  } catch {
    // ไม่มีที่เก็บ
  }
  return [];
}

const slim = (item) => ({
  id: item.id,
  question: item.question,
  status: item.status,
  answer: item.answer,
  sql: item.sql,
  columns: item.columns,
  rows: item.rows?.slice(0, MAX_ROWS),
  rowCount: item.rowCount ?? item.rows?.length,
  failed: item.failed,
  ms: item.ms,
});

// บันทึกแชท (ไม่เก็บคำถามที่ยังรอคำตอบ) · คืนรายการใหม่ เรียงล่าสุดก่อน
export function upsertChat(chat) {
  const items = chat.items.filter((i) => !i.pending).map(slim);
  const others = readChats().filter((c) => c.id !== chat.id);
  if (!items.length) return save(others);
  const entry = {
    id: chat.id,
    datasetId: chat.datasetId,
    datasetName: chat.datasetName,
    title: items[items.length - 1].question, // items เรียงใหม่สุดก่อน → คำถามแรกอยู่ท้าย
    items,
    updatedAt: new Date().toISOString(),
  };
  return save([entry, ...others]);
}

export function deleteChat(id) {
  return save(readChats().filter((c) => c.id !== id));
}

export function clearChats() {
  return save([]);
}
