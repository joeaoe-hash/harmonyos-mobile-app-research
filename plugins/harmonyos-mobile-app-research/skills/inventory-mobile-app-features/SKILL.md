---
name: inventory-mobile-app-features
description: Inventory and compare Android and HarmonyOS mobile app features from live devices, screenshots, UI trees, or existing checklists; capture evidence, build hierarchical feature trees, distinguish verified absence from unchecked areas, and export auditable CSV or Markdown difference matrices. Use when Codex needs to audit an app feature map, compare Android and HarmonyOS parity, document version changes, organize page-by-page feature checklists, or update an evidence-backed cross-platform capability matrix.
---

# Inventory Mobile App Features

Build an auditable feature inventory rather than a visual impression. Record what was checked, how deeply it was verified, and which artifact supports every conclusion.

## Read the relevant references

- Read [references/workflow.md](references/workflow.md) before navigating a live device or resuming an audit.
- Read [references/output-schema.md](references/output-schema.md) before creating, validating, merging, or comparing inventories.

## Choose the evidence mode

- Use ADB for Android and HDC/Hypium for HarmonyOS when a live device is available.
- Use supplied screenshots, recordings, UI Trees, product documents, and existing CSV files when device access is unavailable.
- Combine both modes when older versions are represented only by saved artifacts.
- Record the evidence mode and its limitations; do not present artifact-only coverage as a complete behavioral test.

## Core workflow

1. Fix the scope: app, package name, platform, app version/build, OS version, device, account state, region, language, collection date, and comparison target.
2. Create one inventory per platform/version from `assets/feature-inventory-template.csv`.
3. Build a module map before deep inspection. Cover primary navigation, search, playback or core task flow, detail pages, personal area, settings, secondary menus, share sheets, permissions, and logged-in-only areas.
4. Traverse breadth-first. For every entry, open the destination, capture a UI Tree when possible, and take a screenshot for visually meaningful or ambiguous states.
5. Record the feature hierarchy, verification status, verification depth, and evidence file immediately. Preserve raw UI Trees and screenshots.
6. Assign the same `标准功能ID` to equivalent Android and HarmonyOS capabilities even when their labels differ. Do not force unrelated features into one ID.
7. Revisit overflow menus, settings, permission-gated paths, account-gated paths, scroll boundaries, and alternate layouts before declaring a feature absent.
8. Validate each inventory:

   `python scripts/feature_inventory.py validate <inventory.csv>`

9. Build a comparison matrix:

   `python scripts/feature_inventory.py compare --left <android.csv> --left-label Android --right <harmony.csv> --right-label HarmonyOS --out <matrix.csv> --summary <summary.md>`

10. Report coverage gaps separately from product gaps. Treat `未收录`, `未检查`, and `受阻` as unknown, not absent.

## Claim rules

- Use `已验证存在` only after opening the page or exercising the behavior. Record `验证深度`.
- Use `仅入口存在` when an entry is visible but the destination or behavior is not verified.
- Use `部分可用` when the capability exists but a material sub-flow is missing or broken.
- Use `明确缺失` only after checking all reasonable paths on the stated version and account state.
- Use `受阻` for login, permission, network, paywall, region, device, or test-data blockers.
- Never infer feature absence from one screenshot, one search result, or an empty dynamic feed.
- Keep user content, account identifiers, device serials, wireless-debugging addresses, pairing codes, and passwords out of exported evidence.

## Resume and update

- Preserve a checkpoint containing the last completed module, unresolved paths, and evidence IDs.
- Reuse stable `标准功能ID` values across versions so additions, removals, and regressions remain comparable.
- On a new version, retest changed modules and all previously `部分可用`, `明确缺失`, or `受阻` rows; spot-check unchanged modules before carrying their status forward.
- Do not silently overwrite prior inventories. Create a new platform/version file and compare it with the previous one.

## Deliverables

Return, as applicable:

- One validated feature inventory CSV per platform/version.
- One evidence manifest based on `assets/evidence-manifest-template.csv`.
- One cross-platform or cross-version difference matrix.
- A short Markdown summary separating confirmed parity gaps, completeness differences, and unverified areas.
- A coverage note listing modules, account states, devices, and flows not tested.
