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
MARKDOWN_FILES = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "README.en.md",
    REPO_ROOT / "examples" / "workflow-methodology" / "README.md",
    REPO_ROOT
    / "plugins"
    / "harmonyos-mobile-app-research"
    / "skills"
    / "app-satisfaction-report"
    / "references"
    / "example-reports.md",
)
PLUGIN_JSON = (
    REPO_ROOT
    / "plugins"
    / "harmonyos-mobile-app-research"
    / ".codex-plugin"
    / "plugin.json"
)
SOCIAL_PREVIEW = REPO_ROOT / "docs" / "assets" / "social-preview.png"
ROOT_LICENSE = REPO_ROOT / "LICENSE"
LICENSE_SCOPE = REPO_ROOT / "LICENSE-SCOPE.md"
REPORT_LICENSES = (
    REPO_ROOT / "examples" / "workflow-methodology" / "LICENSE",
    REPO_ROOT
    / "plugins"
    / "harmonyos-mobile-app-research"
    / "skills"
    / "app-satisfaction-report"
    / "references"
    / "examples"
    / "LICENSE",
)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def validate_markdown_links(errors: list[str]) -> int:
    checked = 0
    for source in MARKDOWN_FILES:
        if not source.is_file():
            errors.append(f"missing Markdown file: {source.relative_to(REPO_ROOT)}")
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


def validate_license_scope(errors: list[str]) -> int:
    if not ROOT_LICENSE.is_file():
        errors.append("missing root LICENSE")
    else:
        root_text = ROOT_LICENSE.read_text(encoding="utf-8")
        if not root_text.startswith("MIT License\n"):
            errors.append("root LICENSE is not the canonical MIT text")

    if not LICENSE_SCOPE.is_file():
        errors.append("missing LICENSE-SCOPE.md")
    else:
        scope_text = LICENSE_SCOPE.read_text(encoding="utf-8")
        for excluded_path in (
            "examples/workflow-methodology/**",
            "plugins/harmonyos-mobile-app-research/skills/app-satisfaction-report/references/examples/**",
        ):
            if excluded_path not in scope_text:
                errors.append(f"license scope is missing exclusion: {excluded_path}")

    for report_license in REPORT_LICENSES:
        if not report_license.is_file():
            errors.append(
                f"missing report license: {report_license.relative_to(REPO_ROOT)}"
            )
            continue
        notice = report_license.read_text(encoding="utf-8")
        if "expressly excluded from the MIT" not in notice or "All rights reserved" not in notice:
            errors.append(
                f"incomplete report license: {report_license.relative_to(REPO_ROOT)}"
            )
    return len(REPORT_LICENSES)


def main() -> int:
    errors: list[str] = []
    links = validate_markdown_links(errors)
    forms = validate_issue_forms(errors)
    version = validate_plugin_metadata(errors)
    width, height, preview_bytes = validate_social_preview(errors)
    report_licenses = validate_license_scope(errors)

    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Repository validation passed")
    print(f"- plugin version: {version}")
    print(f"- local Markdown links checked: {links}")
    print(f"- issue YAML files checked: {forms}")
    print(f"- social preview: {width}x{height}, {preview_bytes} bytes")
    print(f"- report-license exclusions checked: {report_licenses}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
