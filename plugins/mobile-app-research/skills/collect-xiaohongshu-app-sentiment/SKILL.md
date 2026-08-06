---
name: collect-xiaohongshu-app-sentiment
description: Collect and organize recent Xiaohongshu posts and comment threads about Android or HarmonyOS apps, releases, features, and user experience; reconstruct parent-comment context, anonymize users, review contextual sentiment and intent, quantify themes and engagement, and export an evidence-backed sentiment report. Use when Codex needs 小红书应用舆情, 版本反馈, 更新口碑, 评论区语境分析, feature-request themes, or a recent app-discussion sample without presenting it as representative of all users.
---

# Collect Xiaohongshu App Sentiment

Use `agent-reach` to retrieve Xiaohongshu content; use this skill to design the sample, preserve evidence, reconstruct comment context, and analyze sentiment without overstating representativeness.

## Environment and dependencies

- Online collection requires Agent Reach to be installed separately and a healthy Xiaohongshu backend reported by `agent-reach doctor --json`.
- A login-required route may use only a user-controlled existing session. This plugin does not read cookies, log in automatically, or loosen browser security settings.
- The bundled normalization and summary script uses Python 3.11+ standard-library modules only.
- Without an online backend, analyze only user-supplied, authorized, anonymized files and report that no online collection occurred.

## Read the relevant references

- Read [references/workflow.md](references/workflow.md) before searching, collecting comments, or resuming a sample.
- Read [references/output-schema.md](references/output-schema.md) before normalizing, manually reviewing, merging, or reporting data.

## Core workflow

1. Fix the scope: app, platform, version or feature, date window, region or device cohort, collection date, and whether posts, comments, or both are required.
2. Build a query matrix containing the app name plus HarmonyOS/鸿蒙 terms, version strings, changed-feature names, complaints, praise terms, and common misspellings. Record which query found each post.
3. Use `agent-reach` and its Xiaohongshu route. Run its health check first. If the wrapper command is unavailable, do not assume the channel is healthy; use an explicitly available backend such as `opencli xiaohongshu` only with an existing user-controlled session.
4. Collect post metadata and visible comments. Prefer a backend that returns structured posts and comment relationships. Use browser control plus `scripts/xhs_visible_comments.js` only as a signed-in, visible-page fallback.
5. Preserve the raw backend output before normalization. Record expected versus collected comment counts, expansion attempts, stop reason, query, URL, and collection time.
6. Run `scripts/xiaohongshu_sentiment.py prepare` to anonymize users, deduplicate comments, reconstruct threads, and produce a context-review CSV.
7. Manually review every row marked `needs_review=yes`, every low-confidence row, the most-liked comments, and a sample from each major topic. Fill `final_sentiment`; do not tune labels to reach a desired overall conclusion.
8. Run `scripts/xiaohongshu_sentiment.py validate`, then `summarize` to generate statistics and a Markdown report.
9. Report raw counts, evaluation-only shares, like-weighted signals, topic distribution, sample coverage, missing comments, and known platform bias separately.

## Context and claim rules

- Link replies to the actual parent or root comment when IDs exist. If the source exposes only flattened order, preserve only the defensible root-thread relationship and state that deeper parentage is unavailable.
- Interpret short replies such as `对`, `确实`, emoji, disagreement, thanks, or solutions against their parent context. Do not classify them in isolation.
- Keep genuine version questions, device questions, settings guidance, and factual explanations neutral.
- Keep unresolved sarcasm, ambiguous emoji, missing-parent replies, and conflicting context as `未判定` until reviewed.
- Distinguish post stance, individual comment sentiment, and whole-thread sentiment.
- Never say “小红书用户整体认为” from a query-driven sample. Say “在本次采集样本中”.
- Present post/comment volume and likes as engagement signals, not population weights.
- Keep collection completeness separate from analytical confidence.

## Privacy and platform integrity

- Replace usernames and profile IDs with stable pseudonyms in exported tables. Keep raw identifiers only in protected raw evidence when necessary for deduplication.
- Never print, export, or store browser cookies, tokens, passwords, or session headers in task artifacts.
- Do not log in automatically, bypass access controls, post, comment, like, follow, or change account state.
- Stop when repeated expansion no longer adds comments; report the remaining gap rather than claiming completeness.

## Bundled resources

- `scripts/xiaohongshu_sentiment.py`: prepare, validate, and summarize structured post/comment data.
- `scripts/xhs_visible_comments.js`: visible-page comment-thread collector for a browser fallback.
- `references/workflow.md`: sampling, acquisition, context review, resumption, and reporting rules.
- `references/output-schema.md`: raw JSON and review CSV schemas.
