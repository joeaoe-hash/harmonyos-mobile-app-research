#!/usr/bin/env python3
"""Validate and compare evidence-backed mobile-app feature inventories."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path


LEVEL_COLUMNS = [f"{label}功能" for label in ("一级", "二级", "三级", "四级", "五级", "六级")]
ALLOWED_STATUSES = {
    "已验证存在",
    "仅入口存在",
    "部分可用",
    "明确缺失",
    "未检查",
    "受阻",
}
STATUS_ALIASES = {
    "页面已验证": "已验证存在",
    "入口已验证": "仅入口存在",
    "功能已验证": "已验证存在",
    "控件已验证": "已验证存在",
    "流程页已验证": "已验证存在",
    "流程已验证": "已验证存在",
    "状态已验证": "已验证存在",
    "链路已验证": "已验证存在",
    "交互已验证": "已验证存在",
    "存在": "已验证存在",
    "缺失": "明确缺失",
    "未验证": "未检查",
}
PRESENT = {"已验证存在"}
PARTIAL = {"仅入口存在", "部分可用"}
ABSENT = {"明确缺失"}
UNKNOWN = {"未检查", "受阻", "未收录", "状态冲突"}
STATUS_RANK = {
    "状态冲突": 6,
    "明确缺失": 5,
    "部分可用": 4,
    "已验证存在": 3,
    "仅入口存在": 2,
    "受阻": 1,
    "未检查": 0,
}


def clean(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def normalize_legacy_row(values: list[str], headers: list[str]) -> dict[str, str]:
    """Repair older 11-column inventories whose empty hierarchy cells shifted status."""
    status_index = headers.index("验证状态")
    level_start = headers.index("一级功能")
    recognized = ALLOWED_STATUSES | set(STATUS_ALIASES)
    detected = next(
        (
            index
            for index in range(level_start, len(values))
            if clean(values[index]) in recognized
        ),
        None,
    )
    if detected is None:
        padded = values + [""] * max(0, len(headers) - len(values))
        return dict(zip(headers, padded[: len(headers)]))

    prefix = values[:level_start]
    levels = [clean(value) for value in values[level_start:detected]]
    while len(levels) > len(LEVEL_COLUMNS) and levels and not levels[-1]:
        levels.pop()
    while len(levels) > len(LEVEL_COLUMNS) and "" in levels:
        levels.pop(len(levels) - 1 - levels[::-1].index(""))
    if len(levels) > len(LEVEL_COLUMNS):
        levels = levels[: len(LEVEL_COLUMNS) - 1] + [" / ".join(levels[len(LEVEL_COLUMNS) - 1 :])]
    levels += [""] * (len(LEVEL_COLUMNS) - len(levels))

    repaired = [""] * len(headers)
    repaired[:level_start] = prefix[:level_start]
    repaired[level_start:status_index] = levels
    repaired[status_index] = clean(values[detected])
    if "证据文件" in headers and detected + 1 < len(values):
        repaired[headers.index("证据文件")] = clean(values[detected + 1])
    if "备注" in headers and detected + 2 < len(values):
        repaired[headers.index("备注")] = "；".join(
            clean(value) for value in values[detected + 2 :] if clean(value)
        )
    return dict(zip(headers, repaired))


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        raw_headers = next(reader, [])
        headers = [clean(item) for item in raw_headers]
        raw_rows = list(reader)

    is_legacy = (
        "验证状态" in headers
        and "一级功能" in headers
        and "平台" not in headers
        and "验证深度" not in headers
    )
    if is_legacy:
        rows = [normalize_legacy_row(values, headers) for values in raw_rows]
    else:
        rows = []
        for values in raw_rows:
            padded = values + [""] * max(0, len(headers) - len(values))
            rows.append(dict(zip(headers, [clean(value) for value in padded[: len(headers)]])))
    return rows, headers


def status_of(row: dict[str, str]) -> str:
    raw = clean(row.get("验证状态") or row.get("状态"))
    return STATUS_ALIASES.get(raw, raw)


def hierarchy(row: dict[str, str]) -> list[str]:
    levels = [clean(row.get(column)) for column in LEVEL_COLUMNS]
    if not any(levels):
        path = clean(row.get("功能路径"))
        levels = [part.strip() for part in re.split(r"\s*(?:>|/|→)\s*", path) if part.strip()]
    return [value for value in levels if value]


def display_path(row: dict[str, str]) -> str:
    values = hierarchy(row)
    return " > ".join(values)


def normalized_key(row: dict[str, str]) -> str:
    explicit = clean(row.get("标准功能ID"))
    if explicit:
        return explicit.casefold()
    parts = hierarchy(row) or [clean(row.get("模块"))]
    raw = "|".join(part.casefold() for part in parts if part)
    return re.sub(r"[\s\W_]+", "", raw, flags=re.UNICODE)


def validate_rows(rows: list[dict[str, str]], headers: list[str], source: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []

    if "模块" not in headers:
        errors.append("缺少“模块”列")
    if "验证状态" not in headers and "状态" not in headers:
        errors.append("缺少“验证状态”列")
    if not any(column in headers for column in LEVEL_COLUMNS) and "功能路径" not in headers:
        errors.append("缺少功能层级列或“功能路径”列")

    by_key: dict[str, list[tuple[int, str]]] = {}
    for index, row in enumerate(rows, start=2):
        key = normalized_key(row)
        status = status_of(row)
        evidence = clean(row.get("证据文件") or row.get("证据ID"))

        if not key:
            errors.append(f"第 {index} 行缺少标准功能ID和可用功能路径")
            continue
        if not display_path(row) and not clean(row.get("标准功能ID")):
            errors.append(f"第 {index} 行缺少功能层级")
        if status not in ALLOWED_STATUSES:
            errors.append(f"第 {index} 行验证状态无效：{status or '<空>'}")
        if status in PRESENT | PARTIAL and not evidence:
            warnings.append(f"第 {index} 行为“{status}”但未填写证据")
        by_key.setdefault(key, []).append((index, status))

    for key, records in by_key.items():
        statuses = {status for _, status in records}
        if len(records) > 1:
            line_numbers = ", ".join(str(line) for line, _ in records)
            if len(statuses) > 1:
                warnings.append(f"功能ID {key} 在第 {line_numbers} 行状态冲突")
            else:
                warnings.append(f"功能ID {key} 在第 {line_numbers} 行重复")

    return {
        "source": str(source),
        "rows": len(rows),
        "errors": errors,
        "warnings": warnings,
        "status_counts": dict(Counter(status_of(row) or "<空>" for row in rows)),
    }


def merge_records(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        key = normalized_key(row)
        if key:
            grouped.setdefault(key, []).append(row)

    result: dict[str, dict[str, str]] = {}
    for key, records in grouped.items():
        statuses = {status_of(row) for row in records}
        if len(statuses) > 1:
            status = "状态冲突"
        else:
            status = next(iter(statuses), "未检查")
        representative = max(records, key=lambda row: STATUS_RANK.get(status_of(row), -1))
        evidence = "；".join(
            dict.fromkeys(
                clean(row.get("证据文件") or row.get("证据ID"))
                for row in records
                if clean(row.get("证据文件") or row.get("证据ID"))
            )
        )
        notes = "；".join(
            dict.fromkeys(clean(row.get("备注")) for row in records if clean(row.get("备注")))
        )
        result[key] = {
            "标准功能ID": clean(representative.get("标准功能ID")) or key,
            "模块": clean(representative.get("模块")),
            "功能路径": display_path(representative),
            "验证状态": status,
            "证据": evidence,
            "备注": notes,
        }
    return result


def diff_type(left: str, right: str, left_label: str, right_label: str) -> str:
    if left in UNKNOWN or right in UNKNOWN:
        return "待核验"
    if left in ABSENT and right in ABSENT:
        return "双方均明确缺失"
    if left in ABSENT and right in PRESENT | PARTIAL:
        return f"{left_label}明确缺失"
    if right in ABSENT and left in PRESENT | PARTIAL:
        return f"{right_label}明确缺失"
    if left in PRESENT and right in PRESENT:
        return "能力对齐"
    if left in PRESENT | PARTIAL and right in PRESENT | PARTIAL:
        return "完整度差异"
    return "待核验"


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_validate(args: argparse.Namespace) -> int:
    source = Path(args.inventory)
    rows, headers = read_rows(source)
    report = validate_rows(rows, headers, source)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


def run_compare(args: argparse.Namespace) -> int:
    left_path = Path(args.left)
    right_path = Path(args.right)
    left_rows, left_headers = read_rows(left_path)
    right_rows, right_headers = read_rows(right_path)
    left_report = validate_rows(left_rows, left_headers, left_path)
    right_report = validate_rows(right_rows, right_headers, right_path)
    errors = [*left_report["errors"], *right_report["errors"]]
    if errors:
        print(json.dumps({"errors": errors}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    left = merge_records(left_rows)
    right = merge_records(right_rows)
    output_rows: list[dict[str, str]] = []
    for key in sorted(set(left) | set(right)):
        lrow = left.get(key, {})
        rrow = right.get(key, {})
        lstatus = lrow.get("验证状态", "未收录")
        rstatus = rrow.get("验证状态", "未收录")
        output_rows.append(
            {
                "标准功能ID": lrow.get("标准功能ID") or rrow.get("标准功能ID") or key,
                "模块": lrow.get("模块") or rrow.get("模块", ""),
                "功能路径": lrow.get("功能路径") or rrow.get("功能路径", ""),
                f"{args.left_label}状态": lstatus,
                f"{args.right_label}状态": rstatus,
                "差异类型": diff_type(lstatus, rstatus, args.left_label, args.right_label),
                f"{args.left_label}证据": lrow.get("证据", ""),
                f"{args.right_label}证据": rrow.get("证据", ""),
                f"{args.left_label}备注": lrow.get("备注", ""),
                f"{args.right_label}备注": rrow.get("备注", ""),
            }
        )

    fields = [
        "标准功能ID",
        "模块",
        "功能路径",
        f"{args.left_label}状态",
        f"{args.right_label}状态",
        "差异类型",
        f"{args.left_label}证据",
        f"{args.right_label}证据",
        f"{args.left_label}备注",
        f"{args.right_label}备注",
    ]
    out_path = Path(args.out)
    write_csv(out_path, output_rows, fields)

    counts = Counter(row["差异类型"] for row in output_rows)
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 功能清单对比摘要",
        "",
        f"- 左侧：{args.left_label}（{left_path}）",
        f"- 右侧：{args.right_label}（{right_path}）",
        f"- 合并功能数：{len(output_rows)}",
        "",
        "## 差异统计",
        "",
    ]
    lines.extend(f"- {label}：{count}" for label, count in sorted(counts.items()))
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            "- “未收录、未检查、受阻、状态冲突”统一归入待核验，不等同于功能缺失。",
            "- “明确缺失”只来自清单中显式填写的核验结论。",
            "- 显示名称不同的等价功能需要使用同一标准功能ID才能自动对齐。",
            "",
        ]
    )
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "matrix": str(out_path),
                "summary": str(summary_path),
                "rows": len(output_rows),
                "diff_counts": dict(counts),
                "warnings": [*left_report["warnings"], *right_report["warnings"]],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and compare evidence-backed mobile-app feature inventories."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate one inventory CSV.")
    validate_parser.add_argument("inventory")
    validate_parser.set_defaults(func=run_validate)

    compare_parser = subparsers.add_parser("compare", help="Compare two inventory CSV files.")
    compare_parser.add_argument("--left", required=True)
    compare_parser.add_argument("--left-label", default="Android")
    compare_parser.add_argument("--right", required=True)
    compare_parser.add_argument("--right-label", default="HarmonyOS")
    compare_parser.add_argument("--out", required=True)
    compare_parser.add_argument("--summary", required=True)
    compare_parser.set_defaults(func=run_compare)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
