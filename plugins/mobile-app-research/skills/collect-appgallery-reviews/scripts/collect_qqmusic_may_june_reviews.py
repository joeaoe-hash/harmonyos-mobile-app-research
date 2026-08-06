from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from hypium import UiDriver


TARGET = os.environ.get("HDC_TARGET", "").strip()
BUNDLE = "com.huawei.hmsapp.appgallery"
COLLECTION_DATE = date.fromisoformat(
    os.environ.get("COLLECTION_DATE", date.today().isoformat())
)
TARGET_YEAR = 2026
TARGET_MONTHS = (6, 5)
STOP_BEFORE = date(TARGET_YEAR, 5, 1)
MAX_SCREENS = int(os.environ.get("MAX_SCREENS", "500"))

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "outputs" / "appgallery-qqmusic-reviews"
RAW_DIR = ROOT / "work" / "qqmusic-may-june-uitree"
PROGRESS_PATH = RAW_DIR / "progress.json"
RESUME_PROBE_PATH = RAW_DIR / "resume_probe.json"
SCREEN_OFFSETS_PATH = RAW_DIR / "screen_offsets.json"

FIELD_PATTERN = re.compile(
    r"CommentDetail(Username|Stars|StarMessage|Text|PostInfo)(\d+)$"
)


def require_target() -> str:
    if not TARGET:
        raise RuntimeError(
            "未配置 HDC_TARGET。请先运行 `hdc list targets -v`，"
            "再把一个 Connected 目标写入 HDC_TARGET。"
        )
    return TARGET


def repair_mojibake(value: str) -> str:
    """修复部分设备 UI Tree 经 GBK 中转后产生的 UTF-8 乱码。"""
    if not value:
        return value

    chunks: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if not current:
            return
        source = "".join(current)
        try:
            chunks.append(source.encode("gbk").decode("utf-8"))
        except (UnicodeEncodeError, UnicodeDecodeError):
            chunks.append(source)
        current.clear()

    for char in value:
        try:
            char.encode("gbk")
            current.append(char)
        except UnicodeEncodeError:
            flush()
            chunks.append(char)
    flush()
    return "".join(chunks).replace("\r\n", "\n").strip()


def walk_tree(node: dict):
    yield node
    for child in node.get("children", []):
        yield from walk_tree(child)


def parse_tree(path: Path) -> dict[int, dict]:
    tree = json.loads(path.read_text(encoding="utf-8"))
    records: dict[int, dict] = {}
    for node in walk_tree(tree):
        attributes = node.get("attributes", {})
        key = attributes.get("key", "")
        match = FIELD_PATTERN.fullmatch(key)
        if not match:
            continue
        field, index_text = match.groups()
        index = int(index_text)
        value = repair_mojibake(attributes.get("text", ""))
        record = records.setdefault(index, {"position_index": index})
        if value:
            record[field] = value
    return records


def merge_records(target: dict[int, dict], incoming: dict[int, dict]) -> None:
    for index, update in incoming.items():
        record = target.setdefault(index, {"position_index": index})
        for key, value in update.items():
            if key == "position_index" or not value:
                continue
            previous = record.get(key, "")
            if key == "Text":
                # 同一条长评论在不同可视位置可能呈现不同截断长度。
                if len(value) >= len(previous):
                    record[key] = value
            else:
                record[key] = value


def parse_displayed_date(post_info: str) -> tuple[date | None, str]:
    if not post_info:
        return None, ""

    first_part = post_info.split("|", 1)[0].strip()
    time_match = re.search(r"\b(\d{1,2}:\d{2})\b", first_part)
    displayed_time = time_match.group(1) if time_match else ""

    if re.search(r"\d+\s*(?:分钟|小时)前", first_part) or first_part.startswith(
        "今天"
    ):
        return COLLECTION_DATE, displayed_time
    if first_part.startswith("昨天"):
        return COLLECTION_DATE - timedelta(days=1), displayed_time
    if first_part.startswith("前天"):
        return COLLECTION_DATE - timedelta(days=2), displayed_time

    numeric_match = re.search(
        r"(?:(\d{4})[./-])?(\d{1,2})[./-](\d{1,2})", first_part
    )
    if numeric_match:
        year_text, month_text, day_text = numeric_match.groups()
        month = int(month_text)
        day = int(day_text)
        year = int(year_text) if year_text else COLLECTION_DATE.year
        if not year_text and month > COLLECTION_DATE.month:
            year -= 1
        try:
            return date(year, month, day), displayed_time
        except ValueError:
            return None, displayed_time

    chinese_match = re.search(r"(\d{1,2})月(\d{1,2})日", first_part)
    if chinese_match:
        month, day = map(int, chinese_match.groups())
        year = COLLECTION_DATE.year - (1 if month > COLLECTION_DATE.month else 0)
        try:
            return date(year, month, day), displayed_time
        except ValueError:
            return None, displayed_time

    return None, displayed_time


def split_post_info(post_info: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in post_info.split("|")]
    displayed_date = parts[0] if parts else ""
    region = parts[1] if len(parts) > 1 else ""
    device = " | ".join(parts[2:]) if len(parts) > 2 else ""
    return displayed_date, region, device


def rows_for_month(records: dict[int, dict], month: int) -> list[dict]:
    rows: list[dict] = []
    for index in sorted(records):
        record = records[index]
        parsed_date, displayed_time = parse_displayed_date(
            record.get("PostInfo", "")
        )
        if not parsed_date:
            continue
        if parsed_date.year != TARGET_YEAR or parsed_date.month != month:
            continue

        displayed_date, region, device = split_post_info(
            record.get("PostInfo", "")
        )
        try:
            stars: int | str = int(float(record.get("Stars", "")))
        except (TypeError, ValueError):
            stars = ""
        normalized_time = parsed_date.isoformat()
        if displayed_time:
            normalized_time += f" {displayed_time}"

        rows.append(
            {
                "序号": len(rows) + 1,
                "列表位置": index,
                "发布时间": normalized_time,
                "页面显示时间": displayed_date,
                "评分": stars,
                "评分描述": record.get("StarMessage", ""),
                "评论内容": record.get("Text", ""),
                "地区": region,
                "设备": device,
                "用户": "匿名用户",
            }
        )
    return rows


def write_month_outputs(records: dict[int, dict], month: int, status: dict) -> None:
    rows = rows_for_month(records, month)
    period = f"{TARGET_YEAR}-{month:02d}"
    payload = {
        "app": "QQ音乐",
        "source": "华为应用市场 - QQ音乐 - 评分与评论 - 最新",
        "collection_date": COLLECTION_DATE.isoformat(),
        "target_period": period,
        "collection_status": status,
        "privacy_note": "应用市场显示的掩码用户名统一替换为“匿名用户”。",
        "review_count": len(rows),
        "reviews": rows,
    }

    json_path = OUTPUT_DIR / f"qqmusic_reviews_{period}.json"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    fieldnames = [
        "序号",
        "列表位置",
        "发布时间",
        "页面显示时间",
        "评分",
        "评分描述",
        "评论内容",
        "地区",
        "设备",
        "用户",
    ]
    csv_path = OUTPUT_DIR / f"qqmusic_reviews_{period}.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    stars = Counter(str(row["评分"]) for row in rows if row["评分"] != "")
    dated = [row["发布时间"] for row in rows]
    content_count = sum(bool(row["评论内容"]) for row in rows)
    lines = [
        f"# QQ音乐 {TARGET_YEAR} 年 {month} 月应用市场用户评论",
        "",
        f"- 数据来源：{payload['source']}",
        f"- 采集日期：{COLLECTION_DATE.isoformat()}",
        f"- 采集状态：{status.get('reason', '')}",
        f"- 评论记录：{len(rows)} 条，其中有文本内容 {content_count} 条",
        f"- 时间范围：{min(dated) if dated else '无'} 至 {max(dated) if dated else '无'}",
        (
            "- 星级分布："
            + "、".join(f"{star} 星 {stars.get(str(star), 0)}" for star in range(1, 6))
        ),
        "- 隐私处理：页面中的掩码用户名统一替换为“匿名用户”。",
        "",
        "| 序号 | 发布时间 | 评分 | 评论内容 | 地区 | 设备 |",
        "|---:|---|---:|---|---|---|",
    ]
    for row in rows:
        content = (
            str(row["评论内容"]).replace("\n", "<br>").replace("|", "\\|")
        )
        region = str(row["地区"]).replace("|", "\\|")
        device = str(row["设备"]).replace("|", "\\|")
        lines.append(
            f"| {row['序号']} | {row['发布时间']} | {row['评分']} | "
            f"{content} | {region} | {device} |"
        )
    (OUTPUT_DIR / f"qqmusic_reviews_{period}.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_outputs(records: dict[int, dict], status: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for month in TARGET_MONTHS:
        write_month_outputs(records, month, status)

    progress = {
        **status,
        "records_seen": len(records),
        "june_review_count": len(rows_for_month(records, 6)),
        "may_review_count": len(rows_for_month(records, 5)),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    PROGRESS_PATH.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_checkpoint(records: dict[int, dict], status: dict) -> None:
    """每屏写轻量断点，避免输出大文件的开销。"""
    progress = {
        **status,
        "records_seen": len(records),
        "record_index_min": min(records) if records else None,
        "record_index_max": max(records) if records else None,
        "june_review_count": len(rows_for_month(records, 6)),
        "may_review_count": len(rows_for_month(records, 5)),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    PROGRESS_PATH.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def page_dates(page: dict[int, dict]) -> list[date]:
    dates: list[date] = []
    for record in page.values():
        parsed_date, _ = parse_displayed_date(record.get("PostInfo", ""))
        if parsed_date:
            dates.append(parsed_date)
    return dates


def page_signature(page: dict[int, dict]) -> tuple:
    return tuple(
        sorted(
            (
                index,
                record.get("PostInfo", ""),
                record.get("Text", ""),
            )
            for index, record in page.items()
        )
    )


def normalize_page_indices(
    page: dict[int, dict], index_offset: int
) -> dict[int, dict]:
    if index_offset == 0:
        return page
    normalized: dict[int, dict] = {}
    for current_index, record in page.items():
        saved_index = current_index + index_offset
        if saved_index < 0:
            continue
        normalized[saved_index] = {
            **record,
            "position_index": saved_index,
        }
    return normalized


def records_compatible(saved: dict, current: dict) -> bool:
    """用稳定字段匹配同一条评论，允许长文本在可视区中被不同程度截断。"""
    saved_post = saved.get("PostInfo", "")
    current_post = current.get("PostInfo", "")
    if not saved_post or not current_post or saved_post != current_post:
        return False

    saved_stars = saved.get("Stars", "")
    current_stars = current.get("Stars", "")
    if saved_stars and current_stars and saved_stars != current_stars:
        return False

    saved_text = saved.get("Text", "")
    current_text = current.get("Text", "")
    if saved_text and current_text:
        return (
            saved_text == current_text
            or saved_text.startswith(current_text)
            or current_text.startswith(saved_text)
        )
    return bool(saved_stars and current_stars)


def detect_index_offset(
    saved_records: dict[int, dict], current_page: dict[int, dict]
) -> int | None:
    """检测列表刷新后因新增评论造成的全局索引偏移。"""
    offsets: Counter[int] = Counter()
    for current_index, current in current_page.items():
        for saved_index, saved in saved_records.items():
            if records_compatible(saved, current):
                offsets[saved_index - current_index] += 1
    if not offsets:
        return None
    return offsets.most_common(1)[0][0]


def dump_resume_probe(driver: UiDriver) -> dict[int, dict]:
    driver.UiTree.dump_to_file(str(RESUME_PROBE_PATH), bundle_name=BUNDLE)
    return parse_tree(RESUME_PROBE_PATH)


def seek_to_checkpoint(
    driver: UiDriver,
    records: dict[int, dict],
    status: dict,
) -> tuple[dict[int, dict], int]:
    """
    将评论列表快速定位到断点。

    - 应用仍停在断点附近：立即续跑；
    - 页面回到顶部：大距离快速上滑，接近断点后减速；
    - 页面已滑过断点：反向快速下滑；
    - 列表刷新且出现新评论：按评论指纹计算索引偏移。
    """
    page = dump_resume_probe(driver)
    if not page:
        raise RuntimeError(
            "当前不是 QQ音乐“评分与评论”的评论列表，"
            "请重新进入该页面并选择“最新”后重试。"
        )
    if not records:
        status["resume_action"] = "无历史断点，从当前“最新”列表开始"
        return page, 0

    saved_max = max(records)
    index_offset = detect_index_offset(records, page)
    if index_offset is None:
        index_offset = 0

    for attempt in range(240):
        normalized = normalize_page_indices(page, index_offset)
        current_min = min(normalized)
        current_max = max(normalized)
        overlap = set(normalized).intersection(records)
        content_overlap = any(
            index in records and records_compatible(records[index], record)
            for index, record in normalized.items()
        )

        if current_max >= saved_max - 12 and (
            current_min <= saved_max + 20 or overlap or content_overlap
        ):
            status["resume_action"] = (
                f"已定位断点：历史末端 {saved_max}，"
                f"当前 {current_min}-{current_max}，索引偏移 {index_offset}"
            )
            status["resume_seek_steps"] = attempt
            status["index_offset"] = index_offset
            return normalized, index_offset

        gap = saved_max - current_max
        direction = "UP" if gap > 0 else "DOWN"
        absolute_gap = abs(gap)

        # 离断点很远时使用快速惯性滚动；接近后改为短滑，避免跨过断点。
        if absolute_gap > 160:
            driver.fling(direction, distance=95, speed="fast")
            time.sleep(0.25)
        elif absolute_gap > 45:
            driver.swipe(
                direction,
                distance=88,
                start_point=(0.5, 0.80 if direction == "UP" else 0.20),
                swipe_time=0.26,
            )
            time.sleep(0.25)
        else:
            driver.swipe(
                direction,
                distance=48,
                start_point=(0.5, 0.72 if direction == "UP" else 0.28),
                swipe_time=0.34,
            )
            time.sleep(0.3)
        driver.wait_for_idle()
        page = dump_resume_probe(driver)
        if not page:
            continue
        detected = detect_index_offset(records, page)
        if detected is not None:
            index_offset = detected

        if attempt % 10 == 0:
            normalized_probe = normalize_page_indices(page, index_offset)
            print(
                f"RESUME_SEEK step={attempt + 1} direction={direction} "
                f"current={min(normalized_probe)}-{max(normalized_probe)} "
                f"target={saved_max} offset={index_offset}",
                flush=True,
            )

    raise RuntimeError(
        f"在 240 次快速定位后仍未找到历史断点 {saved_max}，停止以避免错位合并。"
    )


def load_screen_offsets() -> dict[str, int]:
    if not SCREEN_OFFSETS_PATH.exists():
        return {}
    try:
        payload = json.loads(SCREEN_OFFSETS_PATH.read_text(encoding="utf-8"))
        return {str(key): int(value) for key, value in payload.items()}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}


def save_screen_offsets(offsets: dict[str, int]) -> None:
    SCREEN_OFFSETS_PATH.write_text(
        json.dumps(offsets, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_existing_records() -> tuple[dict[int, dict], int, dict[str, int]]:
    records: dict[int, dict] = {}
    offsets = load_screen_offsets()
    paths = sorted(
        path
        for path in RAW_DIR.glob("screen_*.json")
        if re.fullmatch(r"screen_\d+\.json", path.name)
    )
    valid_paths: list[Path] = []
    for path in paths:
        try:
            page = parse_tree(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            print(f"RESUME_SKIP invalid_tree={path.name} error={error}", flush=True)
            continue
        page = normalize_page_indices(page, offsets.get(path.name, 0))
        merge_records(records, page)
        valid_paths.append(path)
    if not valid_paths:
        return records, 0, offsets
    last_number = max(int(path.stem.rsplit("_", 1)[1]) for path in valid_paths)
    return records, last_number + 1, offsets


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records, screen_start, screen_offsets = load_existing_records()
    existing_dates = page_dates(records)
    status = {
        "complete": False,
        "reason": "采集中",
        "screens_dumped": screen_start,
        "oldest_date_seen": min(existing_dates).isoformat() if existing_dates else "",
        "sort_order": "最新",
        "capture_mode": "UI Tree（无循环截图）",
        "resume_supported": True,
    }
    write_outputs(records, status)

    print(
        f"START resume_screen={screen_start} records={len(records)} "
        f"june={len(rows_for_month(records, 6))} "
        f"may={len(rows_for_month(records, 5))}",
        flush=True,
    )

    driver = UiDriver.connect(device_sn=require_target(), log_level="info")
    _, index_offset = seek_to_checkpoint(driver, records, status)
    write_checkpoint(records, status)
    previous_signature: tuple = ()
    repeat_count = 0
    boundary_reached = False
    try:
        for offset in range(MAX_SCREENS - screen_start):
            screen = screen_start + offset
            raw_path = RAW_DIR / f"screen_{screen:04d}.json"
            driver.UiTree.dump_to_file(str(raw_path), bundle_name=BUNDLE)
            page = parse_tree(raw_path)
            page = normalize_page_indices(page, index_offset)
            screen_offsets[raw_path.name] = index_offset
            save_screen_offsets(screen_offsets)
            if screen == 0 and not page:
                raise RuntimeError(
                    "当前页面未读取到评论控件，请先进入“评分与评论”并选择“最新”。"
                )
            merge_records(records, page)

            dates = page_dates(page)
            if dates:
                oldest = min(dates)
                if (
                    not status["oldest_date_seen"]
                    or oldest.isoformat() < status["oldest_date_seen"]
                ):
                    status["oldest_date_seen"] = oldest.isoformat()
            status["screens_dumped"] = screen + 1
            status["last_visible_index_min"] = min(page) if page else None
            status["last_visible_index_max"] = max(page) if page else None
            status["last_visible_date_min"] = (
                min(dates).isoformat() if dates else ""
            )
            status["last_visible_date_max"] = (
                max(dates).isoformat() if dates else ""
            )
            write_checkpoint(records, status)

            signature = page_signature(page)
            if signature and signature == previous_signature:
                repeat_count += 1
            else:
                repeat_count = 0
            previous_signature = signature

            if screen % 5 == 0:
                write_outputs(records, status)
                print(
                    f"PROGRESS screen={screen + 1} seen={len(records)} "
                    f"june={len(rows_for_month(records, 6))} "
                    f"may={len(rows_for_month(records, 5))} "
                    f"oldest={status['oldest_date_seen'] or 'unknown'}",
                    flush=True,
                )

            # 新到旧排序下，整页进入 4 月后，5 月边界即采集完成。
            if dates and max(dates) < STOP_BEFORE:
                boundary_reached = True
                status["complete"] = True
                status["reason"] = "已进入 4 月评论，完成 6 月和 5 月边界采集"
                break
            if repeat_count >= 4:
                status["reason"] = "评论列表连续多屏未移动，采集提前停止"
                break

            # 非目标月份只用于定位，使用快速惯性滚动；进入 6 月后
            # 改为 72% 快速滑动，并保留相邻页面重叠。
            entered_target_period = bool(
                dates and min(dates) <= date(TARGET_YEAR, 6, 30)
            ) or bool(status["oldest_date_seen"] and status["oldest_date_seen"] <= "2026-06-30")
            days_to_target = (
                (min(dates) - date(TARGET_YEAR, 6, 30)).days if dates else 0
            )
            if not entered_target_period and days_to_target > 7:
                driver.fling("UP", distance=95, speed="fast")
                time.sleep(0.20)
            else:
                distance = 72 if entered_target_period else 90
                driver.swipe(
                    "UP",
                    distance=distance,
                    start_point=(0.5, 0.82),
                    swipe_time=0.28,
                )
                time.sleep(0.22)
            driver.wait_for_idle()
        else:
            status["reason"] = (
                f"达到最大采集屏数 {MAX_SCREENS}，尚未确认 5 月下边界"
            )
    finally:
        driver.close()

    write_outputs(records, status)
    print(
        f"DONE complete={status['complete']} reason={status['reason']} "
        f"screens={status['screens_dumped']} records={len(records)} "
        f"june={len(rows_for_month(records, 6))} "
        f"may={len(rows_for_month(records, 5))}",
        flush=True,
    )
    return 0 if boundary_reached else 2


if __name__ == "__main__":
    sys.exit(main())
