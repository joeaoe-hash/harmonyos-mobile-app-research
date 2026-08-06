from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REVIEW_FIELDS = [
    "post_id",
    "post_title",
    "post_url",
    "post_published_at",
    "post_stance",
    "post_stage",
    "query",
    "expected_comments",
    "collected_comments",
    "collection_status",
    "thread_id",
    "root_text",
    "comment_id",
    "parent_id",
    "user_alias",
    "level",
    "text",
    "likes",
    "time_location",
    "rule_sentiment",
    "context_sentiment",
    "final_sentiment",
    "intent",
    "topics",
    "reason",
    "confidence",
    "needs_review",
]

FINAL_LABELS = {"", "正向", "负向", "混合", "中性", "未判定"}
ASSISTED_LABELS = {"正向", "负向", "混合", "中性", "待语境"}

POSITIVE = re.compile(
    r"好看|漂亮|高级|舒服|舒适|丝滑|清爽|清透|通透|质感|喜欢|爱了|不错|真棒|很棒|惊艳|好用|流畅|用心|满意|支持|真香|终于有|终于更新|解决了|更好看|更好用|更流畅|无广告|没有广告",
    re.I,
)
NEGATIVE = re.compile(
    r"丑|难看|土|差评|不喜欢|难受|失望|恶心|后悔|难用|不好用|不如以前|退步|垃圾|越更越拉|bug|问题|故障|异常|闪退|卡顿|割裂|变形|偏移|重复|缺陷|用不了|不能用|不支持|找不到|不显示|没了|缺了|少了|不方便|广告|强制跳|版权不够|音质差",
    re.I,
)
FEATURE_GAP = re.compile(r"什么时候|啥时候|何时|能不能|可以不可以|怎么还|为什么还|希望.{0,20}(加|上|适配|支持|恢复|优化|修)|建议|赶紧", re.I)
FEATURE_WORD = re.compile(
    r"功能|适配|一起听|本地音乐|歌单|排序|批量|导入|皮肤|装扮|图标|背景|歌词|播放器|音效|倍速|搜索|车机|会员|广告|积分|收藏|权限|入口|播放|下载|评论|私信|分享",
    re.I,
)
ABSENCE = re.compile(r"没有|还是没有|依然没有|仍然没有|没了|缺少|不见了|被砍|阉割", re.I)
INFO_QUESTION = re.compile(
    r"什么版本|哪个版本|多少版本|在哪更新|哪里更新|怎么更新|更新了吗|是正式版吗|在哪里|在哪儿|怎么设置|怎么换|如何换|怎么弄|有教程吗|什么机型|鸿蒙几",
    re.I,
)
SOLUTION = re.compile(r"可以.{0,10}(换|改|设置|关闭|打开)|换回|切回|在.{0,12}(设置|播放器|应用市场)|点.{0,10}(这里|进去|右上角)|重新安装|清缓存", re.I)
AGREE = re.compile(r"^(?:回复\s+[^:：]+\s*[:：]\s*)?(是|是的|对|对的|确实|没错|同感|我也是|真的|就是|加一|\+1|赞同|认同|一样)[啊呀呢吧嘛。！!~～…]*$", re.I)
AGREE_PREFIX = re.compile(r"^(?:回复\s+[^:：]+\s*[:：]\s*)?(对|是的|确实|同感|我也是|加一|赞同|认同)[，,。！!：:]", re.I)
DISAGREE = re.compile(r"^(?:回复\s+[^:：]+\s*[:：]\s*)?(不是|不对|没有吧|哪有|明明|我觉得还好|我觉得挺好|我觉得好看)", re.I)
POS_EMOJI = re.compile(r"😍|🥰|😘|👍|❤|❤️|💕|💗|🔥|🎉|🥳|🤩|\[赞R\]|\[色色R\]|\[哇R\]")
NEG_EMOJI = re.compile(r"😡|🤢|🤮|💔|🙄|😤|\[失望R\]|\[生气R\]|\[哭惹R\]")
EMOJI_OR_PUNCT = re.compile(r"^[\W_\d\s\u2600-\u27ff\U0001F000-\U0001FAFF]+$", re.UNICODE)

DEFAULT_TOPICS = {
    "界面与视觉": r"界面|UI|ui|视觉|好看|漂亮|丑|难看|通透|沉浸|光感|质感|颜色|字体|图标|皮肤|装扮",
    "性能与稳定": r"流畅|卡顿|闪退|崩溃|发热|耗电|加载|性能|稳定|bug|BUG|故障|异常",
    "鸿蒙适配": r"鸿蒙|HarmonyOS|适配|原生鸿蒙|星河版|NEXT|智感握姿|碰一碰",
    "功能缺口": r"没有|缺少|少了|没了|什么时候|啥时候|希望|建议|能不能|不支持|找不到|功能",
    "播放与音质": r"播放|播放器|音质|音效|歌词|倍速|歌单|本地音乐|下载|收藏|一起听",
    "账号与社交": r"登录|账号|私信|好友|评论|分享|关注|动态|bubble|DM|一起听",
    "会员与商业化": r"会员|SVIP|绿钻|广告|付费|收费|价格|积分|权益|商城",
    "版本与更新": r"版本|更新|正式版|测试版|内测|尝鲜|升级|回退|安装包",
}


def pick(mapping: dict[str, Any], *names: str, default: Any = "") -> Any:
    for name in names:
        if name in mapping and mapping[name] not in (None, ""):
            return mapping[name]
    return default


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def cleaned_reply(text: str) -> str:
    return re.sub(r"^回复\s+[^:：]+\s*[:：]\s*", "", text.strip())


def parse_count(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    text = clean(value).replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*([万千kK]?)", text)
    if not match:
        return 0
    number = float(match.group(1))
    suffix = match.group(2)
    if suffix == "万":
        number *= 10000
    elif suffix in {"千", "k", "K"}:
        number *= 1000
    return int(number)


def stable_id(*parts: Any) -> str:
    payload = "|".join(clean(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def pseudonym(comment: dict[str, Any], salt: str) -> str:
    basis = pick(comment, "user_id", "profile_url", "author", "user_name", default="anonymous")
    return "用户-" + stable_id(salt, basis)[:8]


def load_posts(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("posts", payload.get("items", payload.get("data", [])))
    if not isinstance(payload, list):
        raise ValueError("Input must be a JSON list or an object with posts/items/data")
    return [post for post in payload if isinstance(post, dict)]


def nested_lists(comment: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("replies", "sub_comments", "children"):
        value = comment.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def flatten_comments(comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    last_root = ""

    def append_comment(comment: dict[str, Any], parent_id: str, root_id: str, level: int) -> str:
        comment_id = clean(pick(comment, "comment_id", "id")) or stable_id(
            pick(comment, "user_id", "profile_url", "author"),
            pick(comment, "text", "content"),
            pick(comment, "time_location", "date", "time"),
        )
        explicit_parent = clean(pick(comment, "parent_id", "parent_comment_id", default=parent_id))
        explicit_root = clean(pick(comment, "root_comment_id", "root_id", default=root_id))
        actual_root = explicit_root or (comment_id if level == 0 and not explicit_parent else root_id or explicit_parent or comment_id)
        actual_parent = explicit_parent or (parent_id if level > 0 else "")
        row = dict(comment)
        row.update({"_comment_id": comment_id, "_parent_id": actual_parent, "_root_id": actual_root, "_level": level})
        rows.append(row)
        for reply in nested_lists(comment):
            append_comment(reply, comment_id, actual_root, level + 1)
        return actual_root

    for comment in comments:
        is_reply = bool(comment.get("is_reply")) or bool(pick(comment, "parent_id", "parent_comment_id"))
        explicit_root = clean(pick(comment, "root_comment_id", "root_id"))
        if is_reply:
            root = explicit_root or last_root or clean(pick(comment, "parent_id", "parent_comment_id"))
            append_comment(comment, clean(pick(comment, "parent_id", "parent_comment_id")), root, int(comment.get("level") or 1))
        else:
            last_root = append_comment(comment, "", explicit_root, int(comment.get("level") or 0))
    return rows


def direct_classify(text: str) -> tuple[str, str, str, str]:
    value = cleaned_reply(text)
    positive = bool(POSITIVE.search(value))
    negative = bool(NEGATIVE.search(value))
    if ABSENCE.search(value) and FEATURE_WORD.search(value) and not re.search(r"没有.{0,4}广告|无广告", value, re.I):
        negative = True
    if positive and negative:
        return "混合", "褒贬并陈", "同一评论同时包含明确认可与问题或保留意见", "高"
    if positive:
        return "正向", "赞美/认可", "文本包含直接正向评价或正向比较", "高"
    if negative:
        intent = "功能缺口/投诉" if FEATURE_WORD.search(value) else "批评/不满"
        return "负向", intent, "文本包含直接负向评价、功能缺失或使用阻碍", "高"
    if FEATURE_GAP.search(value) and FEATURE_WORD.search(value):
        return "负向", "功能需求/期待改进", "以询问或建议表达当前能力尚未满足", "中"
    if INFO_QUESTION.search(value):
        return "中性", "求助/版本询问", "主要询问版本、设备、入口或操作方法", "高"
    if SOLUTION.search(value):
        return "中性", "解释/解决方案", "主要提供设置、切换或修复方法", "高"
    if POS_EMOJI.search(value) and not NEG_EMOJI.search(value):
        return "正向", "情绪表达", "使用明确正向表情", "中"
    if NEG_EMOJI.search(value) and not POS_EMOJI.search(value):
        return "负向", "情绪表达", "使用明确负向表情", "中"
    return "待语境", "待语境", "文本本身缺少足够极性，需要结合帖子或上级评论", "低"


def contextualize(
    text: str,
    direct: tuple[str, str, str, str],
    root_result: tuple[str, str, str, str] | None,
    post_stance: str,
    is_root: bool,
) -> tuple[str, str, str, str]:
    sentiment, intent, reason, confidence = direct
    if sentiment != "待语境":
        return direct
    value = cleaned_reply(text)
    if is_root:
        if (AGREE.match(value) or AGREE_PREFIX.match(value)) and post_stance in {"正向", "负向", "混合"}:
            return post_stance, "回应帖子/赞同", f"简短赞同表达结合帖子{post_stance}立场判断", "中"
        if EMOJI_OR_PUNCT.fullmatch(value) and post_stance in {"正向", "负向", "混合"}:
            return post_stance, "回应帖子/情绪表达", f"纯表情或标点结合帖子{post_stance}立场判断", "低"
        return sentiment, intent, reason, confidence

    root_sentiment = (root_result or ("待语境", "", "", ""))[0]
    if AGREE.match(value) or AGREE_PREFIX.match(value):
        if root_sentiment in {"正向", "负向", "混合"}:
            return root_sentiment, "赞同上级评论", f"简短赞同表达继承根评论的{root_sentiment}立场", "高"
        if root_sentiment == "中性":
            return "中性", "赞同中性信息", "赞同的是事实或操作信息，并非产品褒贬", "中"
    if DISAGREE.match(value) and root_sentiment == "负向":
        return "正向", "反驳负面评价", "回复反驳根评论的负面判断", "中"
    if DISAGREE.match(value) and root_sentiment == "正向":
        return "负向", "反驳正面评价", "回复反驳根评论的正面判断", "中"
    if re.search(r"谢谢|感谢|明白|好的|收到|解决了|可以了", value) and root_sentiment == "负向":
        return "正向", "问题缓解", "回复表明上级问题获得解释或解决", "中"
    if SOLUTION.search(value):
        return "中性", "解释/解决方案", "针对上级问题提供方法，未直接评价产品", "高"
    if EMOJI_OR_PUNCT.fullmatch(value) and root_sentiment in {"正向", "负向", "混合"}:
        return root_sentiment, "回应上级评论/情绪表达", f"纯表情或标点结合根评论的{root_sentiment}立场判断", "低"
    return sentiment, intent, reason, confidence


def load_topic_patterns(path: Path | None) -> dict[str, re.Pattern[str]]:
    source = DEFAULT_TOPICS
    if path:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in payload.items()):
            raise ValueError("Topic config must be a JSON object mapping topic names to regex strings")
        source = payload
    return {name: re.compile(pattern, re.I) for name, pattern in source.items()}


def topics_for(text: str, patterns: dict[str, re.Pattern[str]]) -> str:
    matched = [name for name, pattern in patterns.items() if pattern.search(text)]
    return "；".join(matched) if matched else "其他/未归类"


def prepare_rows(posts: list[dict[str, Any]], salt: str, topic_config: Path | None) -> list[dict[str, str]]:
    topic_patterns = load_topic_patterns(topic_config)
    result: list[dict[str, str]] = []
    seen_comments: set[tuple[str, str]] = set()
    for post in posts:
        post_id = clean(pick(post, "note_id", "post_id", "id")) or stable_id(pick(post, "url", "link"), pick(post, "title"))
        post_title = clean(pick(post, "title", "帖子标题"))
        post_url = clean(pick(post, "url", "link", "帖子链接"))
        post_published = clean(pick(post, "published_at", "发布日期", "date"))
        post_stance = clean(pick(post, "stance", "帖子态度（人工编码）", "post_stance"))
        post_stage = clean(pick(post, "stage", "phase", "阶段"))
        query = clean(pick(post, "query", "搜索词"))
        comments = post.get("comments") if isinstance(post.get("comments"), list) else []
        flattened = flatten_comments([item for item in comments if isinstance(item, dict)])
        expected = parse_count(pick(post, "expected_comments", "expected_total", "页面评论总数（采集开始时）", default=len(flattened)))
        collected = parse_count(pick(post, "collected_comments", "collected_total", "已取得可见评论数", default=len(flattened))) or len(flattened)
        status = clean(pick(post, "collection_status", "status")) or ("完整" if expected and collected >= expected else "部分")
        root_texts: dict[str, str] = {}
        root_results: dict[str, tuple[str, str, str, str]] = {}
        for comment in flattened:
            comment_id = comment["_comment_id"]
            dedup_key = (post_id, comment_id)
            if dedup_key in seen_comments:
                continue
            seen_comments.add(dedup_key)
            root_id = comment["_root_id"] or comment_id
            level = int(comment["_level"])
            text = clean(pick(comment, "text", "content"))
            image_urls = comment.get("image_urls") if isinstance(comment.get("image_urls"), list) else []
            if not text and image_urls:
                text = f"[图片评论：{len(image_urls)}张]"
            if not text:
                continue
            direct = direct_classify(text)
            context = contextualize(text, direct, root_results.get(root_id), post_stance, level == 0)
            if level == 0:
                root_texts[root_id] = text
                root_results[root_id] = context
            root_text = root_texts.get(root_id, "")
            final_sentiment = context[0] if context[0] != "待语境" else ""
            needs_review = "yes" if not final_sentiment or context[3] == "低" or not root_text else "no"
            result.append(
                {
                    "post_id": post_id,
                    "post_title": post_title,
                    "post_url": post_url,
                    "post_published_at": post_published,
                    "post_stance": post_stance,
                    "post_stage": post_stage,
                    "query": query,
                    "expected_comments": str(expected),
                    "collected_comments": str(collected),
                    "collection_status": status,
                    "thread_id": root_id,
                    "root_text": root_text or (text if level == 0 else ""),
                    "comment_id": comment_id,
                    "parent_id": comment["_parent_id"],
                    "user_alias": pseudonym(comment, salt),
                    "level": "一级评论" if level == 0 else f"回复{level}级",
                    "text": text,
                    "likes": str(parse_count(pick(comment, "likes", "like_count"))),
                    "time_location": clean(pick(comment, "time_location", "date", "time")),
                    "rule_sentiment": direct[0],
                    "context_sentiment": context[0],
                    "final_sentiment": final_sentiment,
                    "intent": context[1],
                    "topics": topics_for(text, topic_patterns),
                    "reason": context[2],
                    "confidence": context[3],
                    "needs_review": needs_review,
                }
            )
    return result


def write_review_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def load_review_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def validate_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(rows, start=2):
        for field in ("post_id", "thread_id", "comment_id", "text", "context_sentiment"):
            if not row.get(field):
                errors.append(f"row {index}: missing {field}")
        if row.get("final_sentiment", "") not in FINAL_LABELS:
            errors.append(f"row {index}: unsupported final_sentiment {row.get('final_sentiment')!r}")
        if row.get("context_sentiment", "") not in ASSISTED_LABELS:
            errors.append(f"row {index}: unsupported context_sentiment {row.get('context_sentiment')!r}")
        key = (row.get("post_id", ""), row.get("comment_id", ""))
        if key in seen:
            errors.append(f"row {index}: duplicate post/comment id {key}")
        seen.add(key)
        if row.get("needs_review") == "yes" and not row.get("final_sentiment"):
            warnings.append(f"row {index}: unresolved review")
        if row.get("level") != "一级评论" and not row.get("root_text"):
            warnings.append(f"row {index}: reply lacks root_text")
    return {"rows": len(rows), "errors": errors, "warnings": warnings}


def effective_label(row: dict[str, str]) -> str:
    label = row.get("final_sentiment") or row.get("context_sentiment") or "未判定"
    return "未判定" if label == "待语境" else label


def thread_label(labels: Iterable[str]) -> str:
    counts = Counter(labels)
    positive, negative, mixed = counts["正向"], counts["负向"], counts["混合"]
    if not (positive or negative or mixed):
        return "中性/未判定"
    if positive and not negative and not mixed:
        return "正向"
    if negative and not positive and not mixed:
        return "负向"
    if positive >= max(2, negative * 2 + mixed):
        return "正向为主"
    if negative >= max(2, positive * 2 + mixed):
        return "负向为主"
    return "正负并存"


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    sentiment = Counter(effective_label(row) for row in rows)
    likes = Counter()
    topic_stats: dict[str, Counter[str]] = defaultdict(Counter)
    threads: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    posts: dict[str, dict[str, str]] = {}
    post_comment_counts = Counter()
    post_like_counts = Counter()
    for row in rows:
        label = effective_label(row)
        like_count = parse_count(row.get("likes", 0))
        likes[label] += like_count
        threads[(row["post_id"], row["thread_id"])].append(row)
        posts.setdefault(row["post_id"], row)
        post_comment_counts[row["post_id"]] += 1
        post_like_counts[row["post_id"]] += like_count
        for topic in filter(None, row.get("topics", "").split("；")):
            topic_stats[topic]["comments"] += 1
            topic_stats[topic]["likes"] += like_count
            topic_stats[topic][label] += 1
    directional_total = sum(sentiment[label] for label in ("正向", "负向", "混合"))
    coverage = {
        "expected_comments": sum(parse_count(row.get("expected_comments", 0)) for row in posts.values()),
        "collected_comments_reported": sum(parse_count(row.get("collected_comments", 0)) for row in posts.values()),
        "normalized_comments": len(rows),
    }
    top_posts = [
        {
            "post_id": post_id,
            "title": posts[post_id].get("post_title", ""),
            "url": posts[post_id].get("post_url", ""),
            "comments": post_comment_counts[post_id],
            "comment_likes": post_like_counts[post_id],
        }
        for post_id in sorted(post_comment_counts, key=lambda item: (post_comment_counts[item], post_like_counts[item]), reverse=True)
    ]
    thread_sentiment = Counter(
        thread_label(effective_label(row) for row in members) for members in threads.values()
    )
    return {
        "posts": len(posts),
        "threads": len(threads),
        "comments": len(rows),
        "coverage": coverage,
        "sentiment": dict(sentiment),
        "directional_total": directional_total,
        "directional_share": {
            label: round(sentiment[label] / directional_total, 4) if directional_total else 0
            for label in ("正向", "负向", "混合")
        },
        "positive_to_negative_ratio": round(sentiment["正向"] / sentiment["负向"], 4) if sentiment["负向"] else None,
        "likes_by_sentiment": dict(likes),
        "thread_sentiment": dict(thread_sentiment),
        "topics": {topic: dict(counts) for topic, counts in sorted(topic_stats.items(), key=lambda item: item[1]["comments"], reverse=True)},
        "needs_review": sum(row.get("needs_review") == "yes" for row in rows),
        "unresolved": sentiment["未判定"],
        "top_posts": top_posts[:15],
    }


def write_report(path: Path, stats: dict[str, Any]) -> None:
    sentiment = stats["sentiment"]
    shares = stats["directional_share"]
    lines = [
        "# 小红书应用舆情样本报告",
        "",
        "## 样本与覆盖",
        "",
        f"- 帖子：{stats['posts']} 篇",
        f"- 评论线程：{stats['threads']} 个",
        f"- 规范化评论：{stats['comments']} 条",
        f"- 页面/后端报告已采集评论：{stats['coverage']['collected_comments_reported']} 条",
        f"- 页面/后端显示预期评论：{stats['coverage']['expected_comments']} 条",
        f"- 待重点复核：{stats['needs_review']} 条；未判定：{stats['unresolved']} 条",
        "",
        "## 情绪结果",
        "",
        f"- 正向：{sentiment.get('正向', 0)}；负向：{sentiment.get('负向', 0)}；混合：{sentiment.get('混合', 0)}；中性：{sentiment.get('中性', 0)}；未判定：{sentiment.get('未判定', 0)}",
        f"- 在具有评价方向的评论中：正向 {shares.get('正向', 0):.1%}，负向 {shares.get('负向', 0):.1%}，混合 {shares.get('混合', 0):.1%}",
        f"- 正负比：{stats['positive_to_negative_ratio'] if stats['positive_to_negative_ratio'] is not None else '负向为0，无法计算'}",
        "- 点赞是互动信号，不等同于用户人口权重。详见统计 JSON 的 likes_by_sentiment。",
        "",
        "## 主要主题",
        "",
        "| 主题 | 评论数 | 点赞 | 正向 | 负向 | 混合 | 中性 | 未判定 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for topic, values in list(stats["topics"].items())[:15]:
        lines.append(
            f"| {topic} | {values.get('comments', 0)} | {values.get('likes', 0)} | {values.get('正向', 0)} | {values.get('负向', 0)} | {values.get('混合', 0)} | {values.get('中性', 0)} | {values.get('未判定', 0)} |"
        )
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            "- 本报告描述的是本次关键词、时间窗、排序机制和登录状态下取得的样本，不代表全部小红书用户或全部应用用户。",
            "- 热门帖子、评论删除、推荐排序、无法展开的回复和跨时段新增评论会影响样本分布。",
            "- 规则标签只用于初筛；最终结论应以已完成的语境复核字段为准。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def prepare_command(args: argparse.Namespace) -> int:
    rows = prepare_rows(load_posts(args.input), args.salt, args.topic_config)
    write_review_csv(args.out, rows)
    report = validate_rows(rows)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


def validate_command(args: argparse.Namespace) -> int:
    report = validate_rows(load_review_csv(args.input))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


def summarize_command(args: argparse.Namespace) -> int:
    rows = load_review_csv(args.input)
    validation = validate_rows(rows)
    if validation["errors"]:
        print(json.dumps(validation, ensure_ascii=False, indent=2))
        return 1
    stats = summarize(rows)
    args.stats.parent.mkdir(parents=True, exist_ok=True)
    args.stats.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(args.report, stats)
    print(json.dumps({"validation": validation, "stats": stats}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare and summarize context-aware Xiaohongshu app sentiment data")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("input", type=Path)
    prepare_parser.add_argument("--out", required=True, type=Path)
    prepare_parser.add_argument("--salt", default="harmonyos-mobile-app-research", help="Local pseudonymization salt; do not publish it with raw identifiers")
    prepare_parser.add_argument("--topic-config", type=Path)
    prepare_parser.set_defaults(func=prepare_command)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("input", type=Path)
    validate_parser.set_defaults(func=validate_command)
    summarize_parser = subparsers.add_parser("summarize")
    summarize_parser.add_argument("input", type=Path)
    summarize_parser.add_argument("--stats", required=True, type=Path)
    summarize_parser.add_argument("--report", required=True, type=Path)
    summarize_parser.set_defaults(func=summarize_command)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
