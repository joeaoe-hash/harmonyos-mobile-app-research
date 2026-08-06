---
name: collect-appgallery-reviews
description: Collect Huawei AppGallery user reviews from a HarmonyOS test device through HDC and Hypium, using UI Tree extraction instead of repeated screenshots. Use when Codex needs to open an app's “评分与评论” page, select “最新”, collect one or more calendar months, resume after interruption, fast-seek to a date or checkpoint, anonymize usernames, export CSV/JSON/Markdown, or audit gaps caused by virtualized review lists.
---

# Collect AppGallery Reviews

Use a connected HarmonyOS device to collect AppGallery reviews by month. Prefer semantic UI controls and UI Tree dumps; use screenshots only for initial confirmation or diagnosing an unexpected page.

## Environment and dependencies

- Required for live collection: Python 3.11+, HDC on `PATH`, an authorized HarmonyOS test device, and Hypium installed from the plugin's `requirements-harmony.txt`.
- Set `HDC_TARGET` from the current `hdc list targets -v` output; never store a device target in a reusable script or committed file.
- Without a connected device, use supplied screenshots, UI Trees, or the synthetic fixture for validation only and state that live collection was not performed.
- Installation and troubleshooting commands are documented in the repository's `DEPENDENCIES.md`.

## Read the relevant references

- Read [references/workflow.md](references/workflow.md) before controlling the device or resuming a run.
- Read [references/output-schema.md](references/output-schema.md) before exporting, combining, or evaluating CSV files.

## Core workflow

1. Confirm one online HDC target with `hdc list targets -v`.
2. Confirm the screen is unlocked and AppGallery is foregrounded.
3. Navigate through UI controls: search for the app, open its detail page, click `查看全部`, then click `最新`.
4. Dump one UI Tree and verify the first `CommentDetailPostInfo*` values are recent. Do not assume the sort click succeeded.
5. Copy and configure `scripts/collect_qqmusic_may_june_reviews.py` in the workspace. Update the app name, target months, collection date, output paths, and device target before using it for another app or period.
6. Run the collector in a hidden background process and monitor its progress file and stdout log.
7. Stop only after a full visible page is older than the earliest requested month.
8. Run `scripts/validate_review_csv.py` against every CSV.
9. If index gaps are material, run a targeted reverse pass based on `scripts/audit_qqmusic_may_gaps_reverse.py`; do not rescan unaffected months.
10. Combine monthly files with `scripts/combine_review_csv.py` only after monthly validation.

## Resume requirements

Treat “resume” as device-state recovery plus data recovery:

- Rebuild records from saved `screen_####.json` files.
- Probe the current UI Tree before scrolling.
- Compare current review indices and content fingerprints with the saved tail.
- If the list returned to the top, fast-seek toward the saved index.
- If new reviews shifted indices, calculate and persist an index offset before merging.
- If the page is older than the checkpoint, seek in the opposite direction.
- Stop rather than merging when no reliable alignment is found.
- Write a lightweight checkpoint after every screen and full exports every few screens.

## Speed and coverage

- When outside the requested dates, use fast inertial scrolling and inspect dates between jumps.
- Within requested months, use overlapping 55%–65% swipes for high coverage.
- Use up to about 72% only when speed is explicitly prioritized, then always run a gap audit.
- Near month boundaries or a resume checkpoint, reduce the swipe distance.
- Never use image recognition repeatedly when `CommentDetail*` controls are available.

## Privacy and integrity

- Replace displayed usernames with `匿名用户` in exported data.
- Keep masked usernames only in raw UI Trees when needed for record matching.
- Deduplicate using time, rating, content, region, and device rather than username.
- Report remaining index gaps and partial rows; do not claim perfect completeness when the virtual list did not instantiate every item.
- Preserve raw UI Trees and progress files so results remain auditable.

## Bundled resources

- `scripts/collect_qqmusic_may_june_reviews.py`: proven QQ Music monthly collector with checkpoint seeking and index-offset handling.
- `scripts/audit_qqmusic_may_gaps_reverse.py`: targeted reverse integrity pass.
- `scripts/validate_review_csv.py`: date, duplicate, missing-field, and index-gap audit.
- `scripts/combine_review_csv.py`: UTF-8 BOM CSV merge and deduplication.
- `assets/samples/synthetic_reviews.csv`: synthetic fixture for schema and validator checks; it is not evidence from a real app or user.

The collector and reverse-audit scripts are a reference implementation with QQ Music constants. Adapt their configuration deliberately; do not run them unchanged for another app or month.
