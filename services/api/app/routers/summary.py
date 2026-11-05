"""สรุปไฟล์ข้อมูลและเตรียมชุดข้อมูลสำหรับกราฟ."""

import math
import re
from contextlib import closing

from fastapi import APIRouter, Depends, HTTPException

from .. import db
from ..security import current_user, require_dataset_owner

router = APIRouter(prefix="/api/datasets", tags=["summary"])


def _ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _number(value) -> float | None:
    if value is None:
        return None
    result = float(value)
    return result if math.isfinite(result) else None


@router.get("/{dataset_id}/summary")
def summarize(
    dataset_id: str,
    table: str | None = None,
    username: str = Depends(current_user),
) -> dict:
    meta = require_dataset_owner(dataset_id, username)
    tables = meta["tables"]
    selected = table if table in tables else (tables[0] if tables else None)
    if selected is None:
        raise HTTPException(status_code=404, detail="ไม่พบตารางในไฟล์นี้")

    try:
        _, con = db.open_dataset(dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ไม่พบ dataset") from exc

    with closing(con):
        quoted_table = _ident(selected)
        description = con.execute(f"SELECT * FROM {quoted_table} LIMIT 0").description
        columns = [{"name": col[0], "type": str(col[1]).upper()} for col in description]
        row_count = con.execute(f"SELECT COUNT(*) FROM {quoted_table}").fetchone()[0]
        if columns:
            missing_terms = []
            for column in columns:
                field = _ident(column["name"])
                blank = (
                    f" OR TRIM(CAST({field} AS VARCHAR)) = ''"
                    if column["type"].startswith(("VARCHAR", "TEXT", "STRING"))
                    else ""
                )
                missing_terms.append(f"COUNT(*) FILTER (WHERE {field} IS NULL{blank})")
            query = f"SELECT {' + '.join(missing_terms)} FROM {quoted_table}"
            missing_count = con.execute(query).fetchone()[0]
        else:
            missing_count = 0
        distinct_query = (
            f"SELECT COUNT(*) FROM (SELECT DISTINCT * FROM {quoted_table}) AS unique_rows"
        )
        distinct_count = con.execute(distinct_query).fetchone()[0]
        identifiers = {
            c["name"]
            for c in columns
            if c["name"].casefold() == "id"
            or c["name"].casefold().endswith(("_id", "รหัส"))
            or c["name"].endswith(("Id", "ID"))
        }
        numeric_types = (
            r"(TINYINT|SMALLINT|INTEGER|BIGINT|HUGEINT|UTINYINT|USMALLINT|UINTEGER|"
            r"UBIGINT|FLOAT|DOUBLE|DECIMAL|REAL)"
        )
        numeric = [
            c
            for c in columns
            if c["name"] not in identifiers and re.search(numeric_types, c["type"])
        ]
        categories = [c for c in columns if c["name"] not in identifiers and c not in numeric]

        stats = None
        if numeric:
            metric = numeric[0]
            field = _ident(metric["name"])
            total, average = con.execute(
                f"SELECT SUM({field}), AVG({field}) FROM {quoted_table}"
            ).fetchone()
            stats = {"column": metric["name"], "sum": _number(total), "average": _number(average)}

        charts = []
        if numeric:
            for category in categories:
                x = _ident(category["name"])
                for metric in numeric:
                    y = _ident(metric["name"])
                    temporal = "DATE" in category["type"] or "TIMESTAMP" in category["type"]
                    group = f"date_trunc('month', {x})" if temporal else x
                    label = f"strftime({group}, '%Y-%m')" if temporal else f"CAST({x} AS VARCHAR)"
                    order = group if temporal else f"SUM({y}) DESC"
                    points = con.execute(
                        f"SELECT {label}, SUM({y}) FROM {quoted_table} "
                        f"WHERE {x} IS NOT NULL GROUP BY {group} ORDER BY {order} LIMIT 10"
                    ).fetchall()
                    if len(points) > 1:
                        charts.append({
                            "title": f"{metric['name']} แยกตาม {category['name']}",
                            "category": category["name"],
                            "metric": metric["name"],
                            "suggested": "line" if temporal else "bar",
                            "points": [
                                {"label": str(label), "value": _number(value) or 0}
                                for label, value in points
                            ],
                        })
                    if len(charts) == 4:
                        break
                if len(charts) == 4:
                    break

        return {
            "dataset_id": dataset_id,
            "name": meta["name"],
            "tables": tables,
            "table": selected,
            "row_count": row_count,
            "missing_count": missing_count,
            "duplicate_rows": row_count - distinct_count,
            "column_count": len(columns),
            "columns": columns,
            "numeric_count": len(numeric),
            "numeric_summary": stats,
            "charts": charts,
        }
