#!/usr/bin/env python3
"""Release preflight for copy/paste-ready social content.

Enforces *declared* editorial signoff, minimal package completeness and a
conservative X short-post length bound. It cannot judge truth, originality,
aesthetic quality or actual account entitlements. No content rewriting.
"""
import argparse
import json
from pathlib import Path
import re
from typing import Any

GATES = (
    "audience_promise",
    "primary_payoff",
    "original_angle",
    "specificity_and_completeness",
    "truth_and_provenance",
    "structure_and_pacing",
    "natural_voice",
    "platform_publishability",
    "delivery_package",
    "rights_and_authorization",
)
CONTENT_ANCHORED = {
    "audience_promise", "primary_payoff", "original_angle",
    "specificity_and_completeness", "structure_and_pacing", "natural_voice",
}
EXTERNAL_FACT_GENRES = {"tool", "news", "review", "benchmark", "tutorial", "technical", "policy"}
PLATFORMS = {"x", "xiaohongshu", "douyin", "multi"}
X_FORMS = {"short_text", "image_post", "thread", "long_post", "article"}
URL = re.compile(r"https?://[^\s<>\u3000]+", re.I)
PLACEHOLDER = re.compile(
    r"\[(?:待补|待填|插入图片|这里放|TODO|待核)[^\]]{0,30}\]"
    r"|(?:【(?:此处插|待补|待填)[^】]{0,30}】)"
    r"|(?:<\s*(?:insert|replace|placeholder)\s*>|待补链接|待核实后补上)", re.I
)
BAIT = re.compile(r"(?:评论区(?:打|扣)(?:1|666)|点赞收藏关注三连)")
PLAIN_URL_PLACEHOLDER = "\uFFF0"

def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""

def x_weighted_length(txt: str) -> int:
    """Conservative bound, not an implementation of Twitter's official twitter-text."""
    replaced = URL.sub(PLAIN_URL_PLACEHOLDER, txt)
    return sum(23 if ch == PLAIN_URL_PLACEHOLDER
               else 1 if ord(ch) < 128
               else 2 for ch in replaced)

def validate(item: Any) -> dict:
    if not isinstance(item, dict):
        return {"status": "blocked", "blocking_reasons": ["release_packet_not_object"],
                "warnings": [], "machine_approval": False}
    reasons = []
    warnings = []
    def block(code):
        if code not in reasons:
            reasons.append(code)

    platform = _text(item.get("platform"))
    form = _text(item.get("format"))
    if platform not in PLATFORMS:
        block("invalid_or_missing_platform")
    if platform == "x" and form not in X_FORMS:
        block("invalid_x_format")
    if not form:
        block("missing_publish_format")

    parts = item.get("posts")
    if platform == "x" and form == "thread":
        if not isinstance(parts, list) or len(parts) < 2 or any(
            not isinstance(p, str) or not p.strip() for p in parts
        ):
            block("thread_requires_complete_posts")
            parts = []
        if _text(item.get("draft")).strip():
            block("thread_draft_must_use_posts_only")
        body = "\n\n".join(parts)
    else:
        body = _text(item.get("draft"))
        if parts is not None:
            block("single_post_must_not_include_parts")
        parts = [body]
    if not body.strip():
        block("empty_release_body")
    if PLACEHOLDER.search(body):
        block("unresolved_publish_placeholder")
    if BAIT.search(body):
        warnings.append("engagement_bait_must_be_removed_or_justified")

    if platform == "x":
        if form in {"short_text", "image_post", "thread"}:
            for index, part in enumerate(parts):
                limit = x_weighted_length(part)
                if limit > 280:
                    block(f"x_post_{index+1}_over_280_conservative_weight")
                elif limit > 265:
                    warnings.append(f"x_post_{index+1}_close_to_limit_verify_in_composer")
        if form == "long_post" and item.get("account_long_posts_confirmed") is not True:
            block("x_long_post_entitlement_not_confirmed")
        if form == "article" and item.get("account_articles_confirmed") is not True:
            block("x_article_entitlement_not_confirmed")

    if item.get("media_required") is True:
        assets = item.get("media_assets")
        if not isinstance(assets, list) or not assets:
            block("required_media_unavailable")
        else:
            for i, asset in enumerate(assets):
                if not isinstance(asset, dict) or asset.get("ready") is not True or asset.get("rights_cleared") is not True:
                    block(f"required_media_{i+1}_not_ready_or_rights_uncleared")
    if item.get("disclosure_required") is True:
        phrase = _text(item.get("disclosure_text")).strip()
        if not phrase or phrase not in body:
            block("mandatory_disclosure_not_in_publish_text")

    genre = _text(item.get("genre"))
    if genre in EXTERNAL_FACT_GENRES:
        sources = item.get("sources")
        if not isinstance(sources, list) or not sources or any(
            not isinstance(x, dict) or not _text(x.get("locator")).strip()
            or not _text(x.get("supports")).strip() for x in sources
        ):
            block("no_claim_specific_external_sources")

    scope = _text(item.get("edit_scope"))
    if scope == "review_only":
        block("review_only_is_not_release")
    if scope in {"title_only", "opening_only", "ending_only", "minimal"}:
        if not isinstance(item.get("original"), str) or not item["original"].strip():
            block("missing_original_for_scoped_edit")
        elif scope == "title_only" and body != item["original"]:
            block("title_only_modified_body")
        elif scope in {"opening_only", "ending_only", "minimal"}:
            warnings.append("human_must_verify_scoped_edit_against_original")

    for phrase in item.get("protected_phrases", []):
        if not isinstance(phrase, str) or (phrase and phrase not in body):
            block("protected_phrase_lost")

    checklist = item.get("acceptance")
    if not isinstance(checklist, dict):
        block("acceptance_record_missing")
        checklist = {}
    for gate in GATES:
        check = checklist.get(gate)
        if not isinstance(check, dict) or check.get("status") != "pass":
            block(f"{gate}_not_signed_off")
            continue
        explanation = _text(check.get("evidence")).strip()
        if len(explanation) < 12:
            block(f"{gate}_evidence_insufficient")
        if gate in CONTENT_ANCHORED:
            anchor = _text(check.get("anchor")).strip()
            if len(anchor) < 4 or anchor not in body:
                block(f"{gate}_missing_real_draft_anchor")
    reviewer = item.get("reviewer")
    if not isinstance(reviewer, dict) or any(
        reviewer.get(k) is not True for k in
        ("editorial_reviewed", "facts_and_rights_checked", "final_publish_previewed")
    ):
        block("reviewer_attestation_incomplete")

    return {
        "status": "blocked" if reasons else "eligible_for_delivery",
        "blocking_reasons": reasons,
        "warnings": warnings,
        "x_conservative_weights": [x_weighted_length(p) for p in parts] if platform == "x" else [],
        "machine_approval": False,
        "user_approved": False,
        "published": False,
        "notice": (
            "eligible_for_delivery requires actual human/editorial verification; "
            "the program only validates attestations, package shape and conservative length. "
            "Twitter composer and current account entitlements remain authoritative."
        ),
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="UTF-8 JSON release packet")
    parser.add_argument("--output", help="Optional path for JSON report")
    args = parser.parse_args()
    packet = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = validate(packet)
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 1 if report["status"] == "blocked" else 0

if __name__ == "__main__":
    raise SystemExit(main())
