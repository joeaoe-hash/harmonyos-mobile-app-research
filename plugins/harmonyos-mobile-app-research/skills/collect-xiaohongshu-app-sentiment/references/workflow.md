# Xiaohongshu application-sentiment workflow

## 1. Define the sample

Record:

- app name and aliases;
- Android, HarmonyOS, or both;
- version, release window, or feature names;
- start and end dates;
- collection timestamp;
- target post count or stopping rule;
- whether comments and nested replies are required.

Use a query matrix rather than one keyword. Include app plus platform, version, feature, praise, complaint, and common user-language variants. Preserve `query` on every post so query bias can be audited.

## 2. Acquire through the supported route

1. Follow the installed `agent-reach` Xiaohongshu route and run its health check.
2. Prefer structured output from the active backend.
3. Do not borrow browser cookies or create a new login automatically.
4. If the backend cannot return comments but a relevant post is already open in a user-controlled signed-in browser, use browser control and the bundled visible-page collector.
5. Preserve raw output before transforming it.

For every post record expected comments, collected comments, whether replies were expanded, stop reason, page URL, query, and collection time. Search-result counts and the comment number displayed at collection time may drift later.

## 3. Sampling and stopping

- Deduplicate the same post found by multiple queries.
- Include low-engagement posts as well as viral posts; otherwise sentiment will be dominated by a few high-volume threads.
- Stop when the defined date window is covered and new queries or scroll rounds no longer add in-scope posts.
- For a comment thread, stop after repeated no-growth rounds. Record the plateau and any difference between expected and collected counts.
- Resume from saved post IDs and comment fingerprints. Do not restart by replacing old raw data without comparison.

## 4. Normalize and reconstruct context

Run:

```text
python scripts/xiaohongshu_sentiment.py prepare raw.json --out review.csv
```

Prefer explicit `parent_id` or `root_comment_id`. For nested `replies`/`sub_comments`, the script preserves the root. For a flattened stream with only `is_reply`, it can associate replies with the most recent root comment, but this is only a root-thread approximation.

## 5. Review sentiment

The script provides rule-assisted labels; it is not a substitute for contextual review.

Review in this order:

1. `needs_review=yes` and blank `final_sentiment`;
2. low-confidence inherited context;
3. highest-like comments and most-active threads;
4. sarcasm, negation, comparisons, feature requests, and replies to solutions;
5. at least a small sample of each remaining topic and label.

Allowed final labels are `正向`, `负向`, `混合`, `中性`, and `未判定`. Do not force genuine information exchange into a directional label. Do not relabel rows merely to make the aggregate match an expected conclusion.

## 6. Summarize and report

Run validation before summary:

```text
python scripts/xiaohongshu_sentiment.py validate review.csv
python scripts/xiaohongshu_sentiment.py summarize review.csv --stats stats.json --report report.md
```

Report:

- post, thread, and comment counts;
- expected-versus-collected gaps;
- all-comment labels;
- shares among directional/evaluative comments only;
- like totals by sentiment as a separate engagement signal;
- theme volume and sentiment mix;
- top threads by comments and likes;
- unresolved and low-confidence counts;
- query, date, login-state, deletion, ranking, and virality biases.

Use examples sparingly and anonymize them. Preserve direct URLs in the evidence table, not as proof that a sample is representative.
