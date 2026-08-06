---
name: collect-appgallery-updates
description: Collect and organize recent HarmonyOS app release notes, public-version changes, beta or trial plans, rollout windows, and version timelines from Huawei AppGallery using a live device, official AppGallery pages or APIs, and preserved evidence. Use when Codex needs to inspect an app's 更新内容, 查看版本, 尝鲜, 测试计划, version history, release dates, or compare changes across recent HarmonyOS versions without treating third-party reports as official release notes.
---

# Collect AppGallery Updates

Build an auditable HarmonyOS release timeline. Keep public releases, trial builds, beta plans, and external corroboration separate.

## Environment and dependencies

- Web-only evidence can be collected without HDC when the official page exposes the required fields.
- Live-device collection requires Python 3.11+, HDC on `PATH`, an authorized HarmonyOS test device, and Hypium from `requirements-harmony.txt`.
- Always obtain the target from the current `hdc list targets -v` output. Do not retain device addresses, pairing codes, or targets in reusable files.
- Installation and troubleshooting commands are documented in the repository's `DEPENDENCIES.md`.

## Read the relevant references

- Read [references/workflow.md](references/workflow.md) before navigating a device or official webpage.
- Read [references/output-schema.md](references/output-schema.md) before normalizing, validating, merging, or exporting records.

## Choose the evidence route

1. Prefer a connected HarmonyOS device when AppGallery exposes `查看版本`, `尝鲜`, or test-plan panels that the public webpage omits.
2. Use the official AppGallery webpage or its own detail response for fields exposed online. Use `agent-reach` for web retrieval and a browser-control skill only when the SPA requires rendered state.
3. Use developer announcements, support pages, or reputable reporting only as corroboration. Label them `外部佐证`; never silently promote them to AppGallery evidence.
4. Combine routes when needed, but retain the source and verification status of every row.

## Core workflow

1. Fix the scope: app name, package name, region, date window, collection date, and whether public, trial, beta, or all channels are needed.
2. Capture the current AppGallery detail page before expanding version history. Record app version, release date, update text, and source artifact.
3. Open `查看版本`, `尝鲜`, or the test-plan panel and capture UI Trees plus screenshots before scrolling.
4. For device collection, adapt and run `scripts/capture_appgallery_versions.py` with an explicit HDC target and output directory. Do not retain a historical target address in a reusable script.
5. Transcribe observed records into the raw JSON shape in `references/output-schema.md`. Preserve update text verbatim in raw evidence; normalize whitespace only in the exported table.
6. Run `scripts/appgallery_updates.py normalize` to deduplicate, sort, and export CSV, JSON, and Markdown.
7. Run `scripts/appgallery_updates.py validate` on the normalized result. Resolve errors before reporting.
8. Report public releases, test plans, date uncertainty, and missing history separately.

## Claim rules

- Use `已验证` only when the version and update text were observed in AppGallery evidence.
- Use `仅页面可见` when an entry is visible but its details were not expanded.
- Use `外部佐证` for non-AppGallery sources, even when they appear reliable.
- Use `待核验` for remembered, inferred, truncated, or conflicting records.
- Do not claim a complete history from the current-version card or from a webpage that exposes only one release.
- Do not merge a trial build into the public-version row merely because their update text is similar.
- Preserve conflicts as separate rows and explain them; do not choose a date or version silently.

## Safety and evidence

- Limit live-device actions to reversible navigation. Do not join beta programs, install builds, submit forms, or change account state unless explicitly requested.
- Keep device addresses, account identifiers, pairing codes, and passwords out of exported artifacts.
- Preserve raw UI Trees, screenshots, HTML or JSON responses, and collection timestamps so the timeline can be re-audited.

## Bundled resources

- `scripts/capture_appgallery_versions.py`: capture a version-history panel from the current AppGallery app-detail page.
- `scripts/appgallery_updates.py`: normalize, deduplicate, validate, and summarize release records.
- `references/workflow.md`: detailed device, webpage, reconciliation, and stopping rules.
- `references/output-schema.md`: raw and normalized schemas plus validation rules.
