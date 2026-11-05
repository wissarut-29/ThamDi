const KEY = "thamdi_selected_dataset";

export function getSelectedDataset() {
  try {
    return sessionStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export function setSelectedDataset(id) {
  try {
    if (id) sessionStorage.setItem(KEY, id);
    else sessionStorage.removeItem(KEY);
  } catch {
    // ถ้า storage ถูกปิด ยังใช้ dataset ในหน้านี้ได้
  }
}
