# AppGallery update output schema

## Raw JSON

Pass either a list of records or an object with an `updates` list to `scripts/appgallery_updates.py normalize`.

```json
{
  "updates": [
    {
      "app_name": "示例应用",
      "package_name": "com.example.hm.app",
      "platform": "HarmonyOS",
      "release_channel": "正式版",
      "version": "3.0.0.6",
      "version_code": "",
      "published_at": "2026-08-01",
      "test_start": "",
      "test_end": "",
      "update_text": "修复已知问题并优化体验。",
      "source_type": "AppGallery设备",
      "source": "versions-ui-tree.json",
      "collected_at": "2026-08-02T10:30:00+08:00",
      "evidence_file": "versions-ui-tree.json",
      "verification_status": "已验证",
      "notes": ""
    }
  ]
}
```

The normalizer also accepts common Chinese aliases such as `应用名称`, `包名`, `版本`, `更新内容`, `发布日期`, `测试开始`, `测试结束`, `渠道`, `证据文件`, and `验证状态`.

For a source table that omits repeated scope fields, pass `--app-name`, `--package-name`, `--source-type`, and `--verification-status` to `normalize`. A `时间` value containing two ISO dates is interpreted as a test window; a single date is treated as a public release date for `正式版` and as a test start for other channels.

## Normalized fields

| Field | Meaning |
|---|---|
| `app_name` | Displayed application name. |
| `package_name` | HarmonyOS package name. |
| `platform` | Normally `HarmonyOS`. |
| `release_channel` | `正式版`, `尝鲜版`, `内测版`, `公测版`, `测试计划`, or `未知`. |
| `version` | Displayed version; may be blank only for a plan without a build. |
| `version_code` | Optional internal build or version code. |
| `published_at` | Public release or displayed publication date. |
| `test_start` | Enrollment or rollout start date. |
| `test_end` | Enrollment or rollout end date. |
| `update_text` | Observed release-note text without analyst paraphrase. |
| `source_type` | For example `AppGallery设备`, `AppGallery网页`, or `外部来源`. |
| `source` | URL or stable source identifier. |
| `collected_at` | Evidence collection timestamp. |
| `evidence_file` | Local raw artifact path or evidence ID. |
| `verification_status` | `已验证`, `仅页面可见`, `外部佐证`, or `待核验`. |
| `notes` | Conflict, truncation, scope, or analyst notes. |

## Validation rules

- Require `app_name` or `package_name`.
- Require at least one of `version`, `update_text`, `test_start`, or `test_end`.
- Require `source` or `evidence_file`.
- Accept ISO dates and datetimes; flag invalid values.
- Require allowed channel and verification values.
- Flag test end dates earlier than test start dates.
- Warn when a supposedly verified row lacks update text or a version.
- Deduplicate only exact normalized identities; do not collapse conflicts.

## Deliverables

For a completed task, return:

- normalized UTF-8 BOM CSV;
- normalized JSON;
- Markdown version timeline grouped by channel;
- raw UI Trees, screenshots, HTML, or response JSON;
- a short coverage note listing channels and date ranges not checked.
