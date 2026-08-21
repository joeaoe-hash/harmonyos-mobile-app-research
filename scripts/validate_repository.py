#!/usr/bin/env python3
"""Validate public repository links, metadata, issue forms, and preview asset."""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
README_FILES = (REPO_ROOT / "README.md", REPO_ROOT / "README.en.md")
PLUGIN_JSON = (
    REPO_ROOT
    / "plugins"
    / "harmonyos-mobile-app-research"
    / ".codex-plugin"
    / "plugin.json"
)
SOCIAL_PREVIEW = REPO_ROOT / "docs" / "assets" / "social-preview.png"
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def validate_markdown_links(errors: list[str]) -> int:
    checked = 0
    for source in README_FILES:
        if not source.is_file():
            errors.append(f"missing README: {source.relative_to(REPO_ROOT)}")
            continue
        for target in MARKDOWN_LINK.findall(source.read_text(encoding="utf-8")):
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            checked += 1
            relative = unquote(target.split("#", 1)[0])
            if not (source.parent / relative).exists():
                errors.append(
                    f"broken link in {source.name}: {target}"
                )
    return checked


def validate_issue_forms(errors: list[str]) -> int:
    issue_root = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
    forms = sorted(issue_root.glob("*.yml"))
    for form in forms:
        try:
            parsed = yaml.safe_load(form.read_text(encoding="utf-8"))
        except Exception as exc:  # PyYAML reports exact file/line details.
            errors.append(f"invalid YAML in {form.relative_to(REPO_ROOT)}: {exc}")
            continue
        if not isinstance(parsed, dict):
            errors.append(f"issue form is not a mapping: {form.relative_to(REPO_ROOT)}")
    return len(forms)


def validate_plugin_metadata(errors: list[str]) -> str:
    try:
        metadata = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid plugin.json: {exc}")
        return "unknown"

    for field in ("name", "version", "description", "skills", "interface"):
        if field not in metadata:
            errors.append(f"plugin.json is missing: {field}")
    keywords = metadata.get("keywords", [])
    if not isinstance(keywords, list) or len(keywords) < 8:
        errors.append("plugin.json should contain at least eight discovery keywords")
    return str(metadata.get("version", "unknown"))


def validate_social_preview(errors: list[str]) -> tuple[int, int, int]:
    if not SOCIAL_PREVIEW.is_file():
        errors.append("missing docs/assets/social-preview.png")
        return 0, 0, 0

    data = SOCIAL_PREVIEW.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        errors.append("social-preview.png is not a valid PNG")
        return 0, 0, len(data)
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (1280, 640):
        errors.append(
            f"social-preview.png must be 1280x640, got {width}x{height}"
        )
    if len(data) >= 1_000_000:
        errors.append("social-preview.png must remain under 1 MB")
    return width, height, len(data)


def main() -> int:
    errors: list[str] = []
    links = validate_markdown_links(errors)
    forms = validate_issue_forms(errors)
    version = validate_plugin_metadata(errors)
    width, height, preview_bytes = validate_social_preview(errors)

    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Repository validation passed")
    print(f"- plugin version: {version}")
    print(f"- local README links checked: {links}")
    print(f"- issue YAML files checked: {forms}")
    print(f"- social preview: {width}x{height}, {preview_bytes} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
