from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


FIELDS = [
    "app_name",
    "package_name",
    "platform",
    "release_channel",
    "version",
    "version_code",
    "published_at",
    "test_start",
    "test_end",
    "update_text",
    "source_type",
    "source",
    "collected_at",
    "evidence_file",
    "verification_status",
    "notes",
]

ALIASES = {
    "应用名称": "app_name",
    "应用": "app_name",
    "包名": "package_name",
    "平台": "platform",
    "渠道": "release_channel",
    "版本类型": "release_channel",
    "版本性质": "release_channel",
    "版本": "version",
    "版本号": "version",
    "版本代码": "version_code",
    "发布日期": "published_at",
    "发布时间": "published_at",
    "测试开始": "test_start",
    "测试结束": "test_end",
    "更新内容": "update_text",
    "应用市场更新说明": "update_text",
    "来源类型": "source_type",
    "来源": "source",
    "证据来源": "source",
    "采集时间": "collected_at",
    "证据文件": "evidence_file",
    "验证状态": "verification_status",
    "备注": "notes",
    "本次分析判断": "notes",
}

CHANNELS = {"正式版", "尝鲜版", "内测版", "公测版", "测试计划", "未知"}
STATUSES = {"已验证", "仅页面可见", "外部佐证", "待核验"}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


CHANNEL_ALIASES = {
    "正式": "正式版",
    "正式版本": "正式版",
    "尝鲜": "尝鲜版",
    "测试版": "测试计划",
    "测试": "测试计划",
    "内测": "内测版",
    "公测": "公测版",
}


def canonical(record: dict[str, Any], defaults: dict[str, str] | None = None) -> dict[str, str]:
    mapped = {ALIASES.get(str(key), str(key)): value for key, value in record.items()}
    row = {field: clean(mapped.get(field, "")) for field in FIELDS}
    for field, value in (defaults or {}).items():
        if field in row and not row[field]:
            row[field] = clean(value)
    raw_time = clean(record.get("时间", ""))
    if raw_time and not (row["published_at"] or row["test_start"] or row["test_end"]):
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", raw_time)
        if len(dates) >= 2:
            row["test_start"], row["test_end"] = dates[0], dates[1]
        elif len(dates) == 1:
            if CHANNEL_ALIASES.get(row["release_channel"], row["release_channel"]) == "正式版":
                row["published_at"] = dates[0]
            else:
                row["test_start"] = dates[0]
    row["platform"] = row["platform"] or "HarmonyOS"
    row["release_channel"] = CHANNEL_ALIASES.get(row["release_channel"], row["release_channel"] or "未知")
    row["verification_status"] = row["verification_status"] or "待核验"
    return row


def load_records(path: Path, defaults: dict[str, str] | None = None) -> list[dict[str, str]]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return [canonical(row, defaults) for row in csv.DictReader(handle)]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("updates", payload.get("records", []))
    if not isinstance(payload, list):
        raise ValueError("Input must be a JSON list, an object with updates/records, or a CSV file")
    return [canonical(item, defaults) for item in payload if isinstance(item, dict)]


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None


def identity(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(
        row[field].casefold()
        for field in ("package_name", "app_name", "release_channel", "version", "published_at", "test_start", "test_end", "update_text")
    )


def sort_key(row: dict[str, str]) -> tuple[str, str, str]:
    date = row["published_at"] or row["test_start"] or row["test_end"] or row["collected_at"]
    return date, row["version"], row["release_channel"]


def deduplicate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, ...]] = set()
    result: list[dict[str, str]] = []
    for row in sorted(rows, key=sort_key, reverse=True):
        key = identity(row)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def validate(rows: list[dict[str, str]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    identities: dict[tuple[str, ...], int] = {}
    for index, row in enumerate(rows, start=2):
        if not (row["app_name"] or row["package_name"]):
            errors.append(f"row {index}: app_name or package_name is required")
        if not (row["version"] or row["update_text"] or row["test_start"] or row["test_end"]):
            errors.append(f"row {index}: version, update_text, test_start, or test_end is required")
        if not (row["source"] or row["evidence_file"]):
            errors.append(f"row {index}: source or evidence_file is required")
        if row["release_channel"] not in CHANNELS:
            errors.append(f"row {index}: unsupported release_channel {row['release_channel']!r}")
        if row["verification_status"] not in STATUSES:
            errors.append(f"row {index}: unsupported verification_status {row['verification_status']!r}")
        parsed: dict[str, datetime] = {}
        for field in ("published_at", "test_start", "test_end", "collected_at"):
            if row[field]:
                value = parse_date(row[field])
                if value is None:
                    errors.append(f"row {index}: invalid ISO date/datetime in {field}: {row[field]!r}")
                else:
                    parsed[field] = value
        if parsed.get("test_start") and parsed.get("test_end") and parsed["test_end"] < parsed["test_start"]:
            errors.append(f"row {index}: test_end precedes test_start")
        if row["verification_status"] == "已验证" and not row["update_text"]:
            warnings.append(f"row {index}: verified row has no update_text")
        if row["verification_status"] == "已验证" and not row["version"] and row["release_channel"] != "测试计划":
            warnings.append(f"row {index}: verified non-plan row has no version")
        key = identity(row)
        if key in identities:
            warnings.append(f"row {index}: duplicate of row {identities[key]}")
        else:
            identities[key] = index
    return {"rows": len(rows), "errors": errors, "warnings": warnings}


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text(json.dumps({"updates": rows}, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown(path: Path, rows: list[dict[str, str]]) -> None:
    lines = ["# AppGallery 版本更新时间线", ""]
    for channel in ("正式版", "尝鲜版", "内测版", "公测版", "测试计划", "未知"):
        selected = [row for row in rows if row["release_channel"] == channel]
        if not selected:
            continue
        lines.extend([f"## {channel}", ""])
        for row in selected:
            when = row["published_at"] or row["test_start"] or row["test_end"] or "日期未确认"
            version = row["version"] or "未标版本"
            lines.append(f"- {when} · {version} · {row['verification_status']}")
            if row["update_text"]:
                lines.append(f"  - 更新内容：{row['update_text']}")
            if row["test_start"] or row["test_end"]:
                lines.append(f"  - 测试窗口：{row['test_start'] or '未知'} 至 {row['test_end'] or '未知'}")
            lines.append(f"  - 证据：{row['source'] or row['evidence_file']}")
            if row["notes"]:
                lines.append(f"  - 备注：{row['notes']}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def normalize_command(args: argparse.Namespace) -> int:
    defaults = {
        "app_name": args.app_name or "",
        "package_name": args.package_name or "",
        "source_type": args.source_type or "",
        "verification_status": args.verification_status or "",
    }
    rows = deduplicate(load_records(args.input, defaults))
    report = validate(rows)
    prefix = args.out_prefix
    prefix.parent.mkdir(parents=True, exist_ok=True)
    write_csv(prefix.with_suffix(".csv"), rows)
    write_json(prefix.with_suffix(".json"), rows)
    write_markdown(prefix.with_suffix(".md"), rows)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


def validate_command(args: argparse.Namespace) -> int:
    report = validate(load_records(args.input))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize and validate AppGallery HarmonyOS update records")
    subparsers = parser.add_subparsers(dest="command", required=True)
    normalize_parser = subparsers.add_parser("normalize")
    normalize_parser.add_argument("input", type=Path)
    normalize_parser.add_argument("--out-prefix", required=True, type=Path)
    normalize_parser.add_argument("--app-name")
    normalize_parser.add_argument("--package-name")
    normalize_parser.add_argument("--source-type")
    normalize_parser.add_argument("--verification-status", choices=sorted(STATUSES))
    normalize_parser.set_defaults(func=normalize_command)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("input", type=Path)
    validate_parser.set_defaults(func=validate_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
