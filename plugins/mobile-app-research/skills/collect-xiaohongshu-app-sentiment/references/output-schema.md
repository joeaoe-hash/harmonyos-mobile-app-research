# Xiaohongshu sentiment schemas

## Raw JSON

Pass a JSON list of posts or an object with a `posts` list.

```json
{
  "posts": [
    {
      "note_id": "post-1",
      "title": "示例应用更新体验",
      "url": "https://www.xiaohongshu.com/explore/post-1",
      "published_at": "2026-08-01",
      "stance": "正向",
      "stage": "正式版发布后",
      "query": "示例应用 鸿蒙 更新",
      "expected_comments": 12,
      "collected_comments": 10,
      "collection_status": "部分",
      "comments": [
        {
          "comment_id": "c1",
          "parent_id": "",
          "root_comment_id": "c1",
          "author": "用户A",
          "user_id": "opaque-user-id",
          "text": "这版更流畅了",
          "likes": 3,
          "time_location": "昨天 广东",
          "replies": []
        }
      ]
    }
  ]
}
```

Common aliases from structured backends are accepted: `post_id`, `link`, `发布日期`, `帖子态度（人工编码）`, `phase`, `sub_comments`, `reply_to`, and `is_reply`.

Image-only comments are preserved as `[图片评论：N张]` and marked for review. Records containing neither text nor images are skipped.

## Context-review CSV

| Field | Meaning |
|---|---|
| `post_id` | Stable post identifier. |
| `post_title`, `post_url`, `post_published_at` | Post evidence. |
| `post_stance`, `post_stage`, `query` | Post-level context and sampling source. |
| `expected_comments`, `collected_comments`, `collection_status` | Coverage fields. |
| `thread_id` | Root comment ID or defensible generated thread ID. |
| `root_text` | Root comment text. |
| `comment_id`, `parent_id`, `level` | Comment relationship. |
| `user_alias` | Stable anonymized user label. |
| `text`, `likes`, `time_location` | Observed comment data. |
| `rule_sentiment` | Text-only first pass. |
| `context_sentiment` | Parent/post-aware assisted label. |
| `final_sentiment` | Human-reviewed label used for final statistics. |
| `intent`, `topics`, `reason`, `confidence` | Review explanation. |
| `needs_review` | `yes` for unresolved or low-confidence rows. |

Allowed `final_sentiment` values: `正向`, `负向`, `混合`, `中性`, `未判定`, or blank before review.

## Deliverables

- raw backend JSON;
- post inventory with query and coverage fields;
- anonymized context-review CSV;
- validated statistics JSON;
- Markdown sentiment report;
- coverage and bias note.

Do not expose usernames, user IDs, profile URLs, session data, or authentication material in exported review tables.
