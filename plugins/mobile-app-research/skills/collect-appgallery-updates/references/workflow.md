# AppGallery update collection workflow

## 1. Define the collection contract

Record the app name, HarmonyOS package name, region, language, requested date window, collection date, and requested channels. Treat these channels separately:

- `正式版`: publicly released build.
- `尝鲜版`: opt-in trial build or early-access release.
- `内测版`: restricted test build.
- `公测版`: public test build.
- `测试计划`: enrollment window or plan without a confirmed installed build.
- `未知`: visible entry whose channel cannot be determined.

## 2. Device route

1. Confirm exactly one intended HDC target with `hdc list targets -v`.
2. Confirm AppGallery is foregrounded and the correct app-detail page is visible.
3. Capture the unexpanded page first.
4. Open `查看版本`; separately inspect `尝鲜`, `内测`, or `测试计划` when present.
5. Dump a UI Tree and screenshot at every materially different panel or scroll position.
6. Scroll with overlap. Stop when the oldest visible entry is older than the requested window or the panel clearly ends.
7. Never infer a row from a button label alone. A visible `查看版本` button proves only that history exists.

Use `scripts/capture_appgallery_versions.py` only after the correct app-detail page is open. The script deliberately requires an explicit target and does not search, enroll, install, or update the app.

## 3. Official webpage route

1. Start with the exact AppGallery detail URL for the package.
2. If the page is a JavaScript shell, inspect the rendered page or its own network/detail response rather than treating empty HTML as absence.
3. Record response URL, retrieval time, region parameters, and the fields that directly supplied version, date, and release notes.
4. A webpage's `wonderfulCommentInfos` or other selected-review field is unrelated to version-history completeness.
5. If the web surface exposes only the current version, report that limit and switch to the device route for history.

## 4. External corroboration

Use first-party developer posts and Huawei support pages before news reports. External sources may confirm a rollout date or feature wording, but keep their rows at `外部佐证` until AppGallery evidence confirms them.

## 5. Reconcile records

- Keep different channels as different rows.
- Keep conflicting dates or update text as separate rows with notes.
- Deduplicate only when package, version, channel, relevant dates, and normalized update text match.
- Sort by the most specific available date: publish date, then test start, then test end, then collection date.
- Preserve raw wording. Put analyst summaries in notes, not in `update_text`.

## 6. Stop and report uncertainty

Stop instead of guessing when the package is ambiguous, the panel belongs to another app, the UI Tree is stale, a network response is region-mismatched, or dates cannot be aligned. Report what is verified, what is visible only, and what remains unchecked.
