from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def walk(node: dict):
    yield node
    for child in node.get("children", []):
        yield from walk(child)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture the version-history panel from the current Huawei AppGallery app-detail page."
    )
    parser.add_argument("--target", required=True, help="Explicit HDC target returned by hdc list targets -v")
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--bundle", default="com.huawei.hmsapp.appgallery")
    parser.add_argument("--entry-text", default="查看版本")
    parser.add_argument("--wait-seconds", type=float, default=1.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        from hypium import BY, UiDriver
    except ImportError as exc:
        raise SystemExit("Hypium is required. Run this script with the configured HarmonyOS test runtime.") from exc

    args.out_dir.mkdir(parents=True, exist_ok=True)
    tree_path = args.out_dir / "versions-ui-tree.json"
    image_path = args.out_dir / "versions-screen.jpeg"
    text_path = args.out_dir / "visible-text.json"

    driver = UiDriver.connect(device_sn=args.target, log_level="info")
    try:
        entry = driver.find_component(BY.text(args.entry_text))
        if not entry:
            raise RuntimeError(f"Current AppGallery page does not expose {args.entry_text!r}")
        driver.click(entry)
        time.sleep(max(0.0, args.wait_seconds))
        driver.wait_for_idle()
        driver.UiTree.dump_to_file(str(tree_path), bundle_name=args.bundle)
        driver.capture_screen(str(image_path))
    finally:
        driver.close()

    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    seen: set[tuple[str, ...]] = set()
    rows: list[dict[str, str]] = []
    for node in walk(tree):
        attrs = node.get("attributes", {})
        text = str(attrs.get("text") or attrs.get("originalText") or "").strip()
        if not text:
            continue
        identity = (
            str(attrs.get("key", "")),
            text,
            str(attrs.get("bounds", "")),
            str(attrs.get("type", "")),
        )
        if identity in seen:
            continue
        seen.add(identity)
        rows.append(
            {
                "key": identity[0],
                "text": text,
                "bounds": identity[2],
                "type": identity[3],
                "clickable": str(attrs.get("clickable", "")),
                "selected": str(attrs.get("selected", "")),
            }
        )
    text_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"tree": str(tree_path), "screen": str(image_path), "visible_text": str(text_path), "rows": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
