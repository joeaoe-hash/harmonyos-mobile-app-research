# Page-by-page feature audit workflow

## 1. Establish the audit boundary

Record before navigation:

- App name and package name.
- Platform, app version/build, OS version, device model, screen form factor, language, and region.
- Logged-out, free, paid, family, creator, or other account state.
- Network and permission state.
- Audit date and the platform/version used as the comparison baseline.

When the request does not require every account tier, audit the available tier and list the untested tiers in the coverage note.

## 2. Prepare evidence

Create separate folders for each platform and version. Use stable filenames:

`<platform>_<module>_<page>_<state>_<sequence>.<ext>`

Prefer UI Trees for labels, hierarchy, control state, and reproducible extraction. Add screenshots for layout, animation, visual effects, charts, artwork, and any state whose meaning is not preserved in the UI Tree.

Record every artifact in the evidence manifest. Redact usernames, account IDs, device serials, wireless-debugging addresses, pairing codes, and private content before sharing.

## 3. Build the module map

Start with breadth, then deepen:

1. Primary navigation and home tabs.
2. Search, discovery, and recommendation.
3. The app's core task flow, such as playback, purchase, upload, messaging, or booking.
4. Content/detail pages.
5. Library, history, favorites, downloads, and local content.
6. Profile, social, notifications, and messaging.
7. Settings, accessibility, privacy, storage, quality, and permissions.
8. Overflow menus, long-press menus, share sheets, widgets, car, tablet, foldable, watch, and other device scenarios.
9. Login-, membership-, region-, or test-data-gated paths.

Do not declare the audit complete while a visible navigation branch remains unexplored.

## 4. Traverse and record

For each feature:

1. Record the visible navigation path.
2. Open the entry.
3. Exercise the primary behavior when safe and reversible.
4. Record secondary actions and important configuration options.
5. Capture the evidence artifact and evidence ID.
6. Add one inventory row at the most useful functional depth.

Avoid turning every label into a feature. Prefer user goals and meaningful actions. Use child rows for materially different sub-capabilities, not decorative text.

## 5. Classify status

- `已验证存在`: destination or behavior verified.
- `仅入口存在`: entry visible, destination or behavior not verified.
- `部分可用`: main capability exists, but a material sub-flow is missing, blocked, or broken.
- `明确缺失`: checked reasonable paths and confirmed the capability is unavailable in this scoped version/state.
- `未检查`: deliberately outside current coverage.
- `受阻`: verification prevented by login, permission, network, paywall, region, device, or missing test data.

Set `验证深度` to `入口`, `页面`, or `行为`. A high-confidence parity claim normally requires `页面` or `行为`.

## 6. Normalize equivalent features

Use the same `标准功能ID` across platforms and versions. Base it on the user capability, not the displayed label. For example, Android “一起听” and HarmonyOS “好友同听” may share `social.listen-together` after verifying they represent the same capability.

Keep separate IDs when:

- One label opens materially different behavior.
- One platform combines capabilities that are separate on the other.
- Similar-looking controls serve different user goals.

When uncertain, keep rows separate and note `待人工对齐`.

## 7. Compare

Run the comparison script only after both inventories validate. Interpret results as:

- `能力对齐`: both sides verified.
- `完整度差异`: one side is entry-only or partial.
- `明确缺失`: one side was exhaustively checked and marked absent.
- `待核验`: a side is missing from the inventory, unchecked, blocked, or has conflicting records.

Do not convert “only one inventory contains this row” into “the other platform lacks it.”

## 8. Quality gates

Before handoff, confirm:

- Every verified or partial row has evidence or an explicit evidence limitation.
- Feature IDs are stable and equivalent across both sides.
- No duplicate ID has conflicting status without a conflict note.
- Missing account tiers and device scenarios are listed.
- Dynamic content and regional experiments are not presented as permanent product differences.
- Existing source artifacts remain unchanged.
