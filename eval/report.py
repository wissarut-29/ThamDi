"""สร้างตาราง Markdown + กราฟจาก eval/results/

เจ้าของ: Wissarut · งาน: W3, W5 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

    python eval/report.py                 # จาก results/latest.json
    python eval/report.py --simulated     # จาก results/simulated.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"
CATEGORY_TH = {
    "filter": "กรองข้อมูล", "aggregate": "รวม/นับ/เฉลี่ย", "group": "จัดกลุ่ม",
    "rank": "จัดอันดับ", "thai_date": "วันที่ภาษาไทย", "join": "หลายตาราง", "refuse": "ปฏิเสธ/ถามกลับ",
}


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def build_markdown(data: dict) -> str:
    results = data["results"]
    modes = sorted({r["mode"] for r in results})
    sets = list(dict.fromkeys(r["set"] for r in results))
    cell = {(r["mode"], r["set"]): r for r in results}

    lines = []
    if data.get("simulated"):
        lines += ["> ⚠️ **ผลจำลอง** ไม่ใช่ผลจากโมเดลจริง ห้ามใช้ใน README หรือสไลด์", ""]
    model = data["model"]
    lines += [
        f"โมเดล: {model.get('name') or '-'} {model.get('version') or ''} · "
        f"วันที่: {data['generated_at']} · เครื่อง: {data['machine']}",
        "",
        "**Execution accuracy** (ในวงเล็บ: สัดส่วน SQL ที่รันได้)",
        "",
        "| โหมด | " + " | ".join(f"{s} (n={cell[(modes[0], s)]['n']})" for s in sets) + " |",
        "|---|" + "---|" * len(sets),
    ]
    for m in modes:
        row = [f"{pct(cell[(m, s)]['execution_accuracy'])} ({pct(cell[(m, s)]['valid_sql_rate'])})" for s in sets]
        lines.append(f"| {m} | " + " | ".join(row) + " |")

    lines += ["", "**แยกตามหมวด** (ชุด handwritten)", "",
              "| หมวด | " + " | ".join(modes) + " |", "|---|" + "---|" * len(modes)]
    for cat, name in CATEGORY_TH.items():
        if cat in cell[(modes[0], "handwritten")]["by_category"]:
            row = [pct(cell[(m, "handwritten")]["by_category"][cat]) for m in modes]
            lines.append(f"| {name} | " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def build_chart(data: dict, path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    results = data["results"]
    modes = sorted({r["mode"] for r in results})
    sets = list(dict.fromkeys(r["set"] for r in results))
    cell = {(r["mode"], r["set"]): r["execution_accuracy"] * 100 for r in results}
    width = 0.8 / len(sets)
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, s in enumerate(sets):
        xs = [m + (i - (len(sets) - 1) / 2) * width for m in range(len(modes))]
        ax.bar(xs, [cell[(m, s)] for m in modes], width, label=s)
    ax.set_xticks(range(len(modes)), modes)
    ax.set_ylabel("Execution accuracy (%)")
    ax.set_ylim(0, 100)
    ax.legend()
    ax.set_title("ThamDi eval" + (" (SIMULATED)" if data.get("simulated") else ""))
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulated", action="store_true")
    args = parser.parse_args()
    stem = "simulated" if args.simulated else "latest"
    src = RESULTS_DIR / f"{stem}.json"
    if not src.exists():
        print(f"ไม่พบ {src} — รัน eval/run.py ก่อน")
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))
    md_path = RESULTS_DIR / f"{stem}_report.md"
    md_path.write_text(build_markdown(data), encoding="utf-8")
    print(f"ตาราง: {md_path.relative_to(RESULTS_DIR.parent.parent)}")
    png_path = RESULTS_DIR / f"{stem}_accuracy.png"
    if build_chart(data, png_path):
        print(f"กราฟ: {png_path.relative_to(RESULTS_DIR.parent.parent)}")
    else:
        print("ข้ามกราฟ (ไม่มี matplotlib)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
