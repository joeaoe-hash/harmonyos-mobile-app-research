from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="合并并去重应用市场评论 CSV")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    fieldnames: list[str] = []
    seen: set[tuple[str, ...]] = set()
    identity_fields = ("发布时间", "评分", "评论内容", "地区", "设备")

    for path in args.inputs:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            for field in reader.fieldnames or []:
                if field not in fieldnames:
                    fieldnames.append(field)
            for row in reader:
                identity = tuple(row.get(field, "") for field in identity_fields)
                if identity in seen:
                    continue
                seen.add(identity)
                rows.append(dict(row))

    rows.sort(
        key=lambda row: (
            row.get("发布时间", ""),
            int(row.get("列表位置", "0") or 0),
        ),
        reverse=True,
    )
    for sequence, row in enumerate(rows, start=1):
        if "序号" in fieldnames:
            row["序号"] = str(sequence)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"合并完成：{len(rows)} 条 -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
