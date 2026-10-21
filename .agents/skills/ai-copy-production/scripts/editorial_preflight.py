#!/usr/bin/env python3
"""Nonblocking preflight hints for human editorial review. No rewrite, score or network.

Runs alongside copy_quality_gate.py. A clean report is NOT content approval.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

PROMO_CLICHES = (
    "在这个飞速发展的时代", "在这个信息爆炸的时代", "颠覆你的认知", "彻底改变行业",
    "不看后悔", "震惊全网", "史上最强", "真正重要的是", "建议先收藏",
    "点赞收藏关注", "看完这篇你就懂了", "开启全新篇章", "赋能千行百业",
)
STRONG_PROMISES = re.compile(
    r"100\s*[%％]\s*(?:成功|准确|有效)|(?:保证|必定)(?:爆火|涨粉|变现|播放)|"
    r"(?:永久免费|完全免费且无限制|随便商用|绕过平台检测|不会被平台检测)"
)
PERSONAL_TEST = re.compile(r"(?:我|本人)(?:亲测|实测|实际跑通|已经跑通|都试过)|亲测有效")
SOURCE_HEAVY = {"tool", "news", "review", "benchmark", "tutorial", "technical", "policy"}


def _norm(txt):
    return re.sub(r"\s+", "", txt).strip(" \t，。！？.!?：:;；")


def analyze(record):
    """Return only actionable hints. Caller must verify all source claims manually."""
    if not isinstance(record, dict):
        raise TypeError("Input must be one JSON object")
    draft = record.get("draft", "")
    if not isinstance(draft, str):
        raise TypeError("draft must be a string")
    hints = []

    def add(code, evidence, suggestion):
        hints.append({"code": code, "evidence": evidence, "suggestion": suggestion})

    if not draft.strip():
        add("empty_draft", "", "没有正文。此工具不代替正式出稿。")
    paragraphs = [_norm(p) for p in re.split(r"\n\s*\n", draft) if _norm(p)]
    counts = Counter(p for p in paragraphs if len(p) >= 18)
    for para, n in counts.items():
        if n > 1:
            add("duplicate_paragraph", para[:65], "确认是否刻意复沓；若无独立表达价值，合并重复段。")
    missing = []
    for fact in record.get("required_facts", []):
        if isinstance(fact, str) and fact and fact.casefold() not in draft.casefold():
            missing.append(fact)
    if missing:
        add("required_facts_missing", missing, "与原始资料逐项核对；不能只靠编辑预先列出的事实清单。")
    for phrase in record.get("protected_phrases", []):
        if isinstance(phrase, str) and phrase and phrase not in draft:
            add("protected_phrase_changed", phrase, "如果属于保真修改，请保留原话或取得用户明确授权。")
    for phrase in PROMO_CLICHES:
        if phrase in draft:
            add("generic_promo_phrase", phrase, "检查它是否增加具体事实或作者真实语气；否则用有证据的细节表达。")
    promise = STRONG_PROMISES.search(draft)
    if promise:
        add("absolute_claim_check", promise.group(), "核对限定条件、证据/商业条款，必要时降低绝对承诺。")
    tested = record.get("test_status", "unknown")
    test_match = PERSONAL_TEST.search(draft)
    if test_match and tested != "user_verified":
        add("first_person_test_unverified", test_match.group(), "仅用户本人已明确提供真实操作证据时才能使用第一人称亲测。")
    genre = record.get("genre", "unknown")
    if genre in SOURCE_HEAVY and not record.get("sources"):
        add("source_gap", genre, "请人工检查关键技术、时间、性能、价格和许可主张的一手来源。")
    if isinstance(record.get("original"), str) and record.get("edit_scope") in {"review_only", "title_only"}:
        if record["original"] != draft:
            add("edit_scope_changed_body", record.get("edit_scope"), "纯审稿或只改标题不能修改正文；以原有质量门禁为准。")
    return {
        "status": "editorial_hints_only",
        "approved": False,
        "claim_verified": False,
        "virality_prediction": None,
        "hints": hints,
        "notice": "仅做机械预检；不重写、不裁定风格或事实、不能证明传播表现。",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="UTF-8 JSON record")
    ap.add_argument("--output", help="Optional output JSON path; default stdout")
    args = ap.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = json.dumps(analyze(data), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(report + "\n", encoding="utf-8")
    else:
        print(report)


if __name__ == "__main__":
    main()
