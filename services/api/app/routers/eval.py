"""GET /api/eval/results

เจ้าของ: Wissarut · งาน: W3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

RESULTS_DIR = Path(__file__).resolve().parents[4] / "eval" / "results"

router = APIRouter(prefix="/api/eval", tags=["eval"])


@router.get("/results")
def get_results(simulated: bool = False) -> dict:
    """ผล eval ล่าสุด (eval/results/latest.json) · ?simulated=true ให้ผลจำลองไว้พัฒนาหน้าเว็บ"""
    path = RESULTS_DIR / ("simulated.json" if simulated else "latest.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="ยังไม่มีผล eval")
    return json.loads(path.read_text(encoding="utf-8"))
