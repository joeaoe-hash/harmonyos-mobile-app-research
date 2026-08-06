from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def validate(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))

    dates = [row.get("发布时间", "")[:10] for row in rows if row.get("发布时间")]
    indices = {
        int(row["列表位置"])
        for row in rows
        if str(row.get("列表位置", "")).isdigit()
    }
    missing_indices = (
        sorted(set(range(min(indices), max(indices) + 1)) - indices)
        if indices
        else []
    )
    identity_fields = ("发布时间", "评分", "评论内容", "地区", "设备")
    identities = [
        tuple(row.get(field, "") for field in identity_fields) for row in rows
    ]

    return {
        "file": str(path),
        "rows": len(rows),
        "date_min": min(dates) if dates else "",
        "date_max": max(dates) if dates else "",
        "stars": dict(sorted(Counter(row.get("评分", "") for row in rows).items())),
        "duplicate_rows": len(rows) - len(set(identities)),
        "missing_indices_in_span": len(missing_indices),
        "missing_index_samples": missing_indices[:30],
        "missing_content": sum(not row.get("评论内容") for row in rows),
        "missing_rating": sum(not row.get("评分") for row in rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="校验应用市场评论 CSV")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    result = [validate(path) for path in args.files]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
