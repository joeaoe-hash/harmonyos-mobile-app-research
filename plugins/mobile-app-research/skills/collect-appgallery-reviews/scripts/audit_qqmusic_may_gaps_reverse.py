from __future__ import annotations

import importlib.util
import json
import time
from datetime import datetime
from pathlib import Path

from hypium import UiDriver


ROOT = Path(__file__).resolve().parents[3]
COLLECTOR_PATH = Path(__file__).resolve().with_name(
    "collect_qqmusic_may_june_reviews.py"
)
RAW_DIR = ROOT / "work" / "qqmusic-may-gap-audit"
OUTPUT_DIR = ROOT / "outputs" / "appgallery-qqmusic-reviews"
TARGET_NEWER_INDEX = 1260
MAX_SCREENS = 100


def load_collector():
    spec = importlib.util.spec_from_file_location(
        "qqmusic_may_june_collector", COLLECTOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def month_gap_count(collector, records: dict[int, dict], month: int) -> int:
    rows = collector.rows_for_month(records, month)
    if not rows:
        return 0
    indices = {row["列表位置"] for row in rows}
    return len(set(range(min(indices), max(indices) + 1)) - indices)


def write_progress(
    collector,
    records: dict[int, dict],
    screen: int,
    reason: str,
    complete: bool,
) -> None:
    status = {
        "complete": complete,
        "reason": reason,
        "sort_order": "最新",
        "capture_mode": "UI Tree（无循环截图）",
        "integrity_audit": "5 月缺口定向反向回扫",
        "audit_screens_dumped": screen,
        "may_missing_indices_in_span": month_gap_count(collector, records, 5),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    collector.write_outputs(records, status)
    (RAW_DIR / "progress.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> int:
    collector = load_collector()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records, _, _ = collector.load_existing_records()
    before_gap_count = month_gap_count(collector, records, 5)
    print(
        f"START records={len(records)} may={len(collector.rows_for_month(records, 5))} "
        f"may_gaps={before_gap_count}",
        flush=True,
    )

    driver = UiDriver.connect(device_sn=collector.TARGET, log_level="info")
    complete = False
    screens = 0
    reason = "5 月缺口定向回扫中"
    try:
        for screen in range(MAX_SCREENS):
            path = RAW_DIR / f"reverse_{screen:04d}.json"
            driver.UiTree.dump_to_file(str(path), bundle_name=collector.BUNDLE)
            page = collector.parse_tree(path)
            if not page:
                raise RuntimeError("当前页面未读取到评论控件，定向回扫停止。")
            collector.merge_records(records, page)
            screens = screen + 1

            if screen % 5 == 0:
                gap_count = month_gap_count(collector, records, 5)
                write_progress(
                    collector,
                    records,
                    screens,
                    "5 月缺口定向回扫中",
                    False,
                )
                print(
                    f"PROGRESS screen={screens} current={min(page)}-{max(page)} "
                    f"may={len(collector.rows_for_month(records, 5))} "
                    f"may_gaps={gap_count}",
                    flush=True,
                )

            # 已反向越过加速模式启用前的连续区间，停止定向回扫。
            if min(page) <= TARGET_NEWER_INDEX:
                complete = True
                reason = "已反向回扫至 5 月连续区间并完成缺口补采"
                break

            driver.swipe(
                "DOWN",
                distance=46,
                start_point=(0.5, 0.20),
                swipe_time=0.26,
            )
            time.sleep(0.22)
            driver.wait_for_idle()
        else:
            reason = f"达到最大定向回扫屏数 {MAX_SCREENS}"
    finally:
        driver.close()

    write_progress(collector, records, screens, reason, complete)
    after_gap_count = month_gap_count(collector, records, 5)
    print(
        f"DONE complete={complete} screens={screens} "
        f"may={len(collector.rows_for_month(records, 5))} "
        f"may_gaps={after_gap_count} filled={before_gap_count - after_gap_count}",
        flush=True,
    )
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
