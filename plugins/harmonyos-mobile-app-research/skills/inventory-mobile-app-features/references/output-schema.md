# Output schema

## Feature inventory CSV

Use UTF-8 with BOM. Keep these columns in order:

| Column | Meaning |
|---|---|
| 应用 | App name |
| 平台 | Android, HarmonyOS, iOS, or another platform |
| 版本 | User-facing app version |
| 构建号 | Build identifier when available |
| 设备 | Device model or form factor |
| 账号状态 | Logged-out, free, paid, creator, and so on |
| 采集日期 | ISO date |
| 模块 | Top-level product module |
| 标准功能ID | Stable cross-platform capability ID |
| 一级功能…六级功能 | Hierarchical navigation/capability path |
| 验证状态 | Controlled status vocabulary |
| 验证深度 | 入口, 页面, or 行为 |
| 证据ID | Evidence-manifest identifier |
| 证据文件 | Relative or workspace-local artifact path |
| 备注 | Limitations, blockers, or behavior details |

Allowed `验证状态` values:

- `已验证存在`
- `仅入口存在`
- `部分可用`
- `明确缺失`
- `未检查`
- `受阻`

Use a dotted lowercase `标准功能ID` when practical, such as `library.local.scan` or `social.listen-together`. Preserve an established ID even if the visible product label changes.

## Evidence manifest CSV

| Column | Meaning |
|---|---|
| 证据ID | Unique stable identifier |
| 应用 | App name |
| 平台 | Platform |
| 版本 | App version/build |
| 设备 | Device model |
| 账号状态 | Account state |
| 采集时间 | ISO date-time with timezone when available |
| 页面路径 | Navigation path |
| 证据类型 | ui-tree, screenshot, video, document, or note |
| 文件路径 | Artifact path |
| 说明 | State, action, redaction, or limitation |

## Comparison matrix CSV

The bundled comparison script writes:

- `标准功能ID`
- `模块`
- `功能路径`
- `<左侧标签>状态`
- `<右侧标签>状态`
- `差异类型`
- `<左侧标签>证据`
- `<右侧标签>证据`
- `<左侧标签>备注`
- `<右侧标签>备注`

Rows absent from one inventory are shown as `未收录`. This means “not represented in the supplied checklist,” not “confirmed unavailable in the product.”

## Compatibility with earlier inventories

The validator accepts older files that omit app/platform metadata or use `验证状态` and `证据文件` only. Add missing metadata before making a formal cross-version claim. The comparison script prefers `标准功能ID`; if it is missing, it falls back to normalized module and hierarchy text, which may require manual alignment.
