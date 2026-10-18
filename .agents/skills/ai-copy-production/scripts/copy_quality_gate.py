#!/usr/bin/env python3
"""Preflight contract check for social drafts; never rewrites, publishes or assigns AI/human scores.

The producer/adapter must supply original source text and an explicit factual inventory.
Passing the script establishes only mechanical guardrail coverage, NOT factual truth.
"""
import argparse
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
from typing import Any

EDIT_SCOPES = {
    "new_draft", "review_only", "title_only", "opening_only", "ending_only",
    "minimal", "substantive_rewrite",
}
FACT_STATUSES = {"user_verified", "original_source", "third_party_claim", "proposed", "unknown"}
VALID_PLATFORMS = {"douyin", "xiaohongshu", "x", "multi", "unspecified"}
PAYOFF_TYPES = {"utility", "learning", "save", "insight", "decision", "information", "emotion", "entertainment", "social_expression"}
HARD_BAIT = re.compile(r"(评论区(?:打|扣|留下)(?:1|666|YES)|点赞(?:收藏)?关注三连|求个三连)")
UNSUPPORTED_GUARANTEE = re.compile(r"(100%成功|百分百保证|保证(?:涨粉|播放|变现)|零失误|永久(?:免费|有效))")


def _s(x: Any) -> str:
    return x if isinstance(x, str) else ""


def _has(body: str, term: str) -> bool:
    if not term:
        return False
    return term.casefold() in body.casefold()


def validate(item: Any) -> dict:
    if not isinstance(item, dict):
        return {"status": "blocked", "blocking_reasons": ["record_not_object"],
                "warnings": [], "preserved": {}, "manually_verified": False}
    mode = _s(item.get("edit_scope"))
    original = _s(item.get("original"))
    draft = _s(item.get("draft"))
    headline_original = _s(item.get("headline_original"))
    headline_new = _s(item.get("headline_new"))
    reasons, warnings = [], []
    if mode not in EDIT_SCOPES:
        reasons.append("invalid_or_missing_edit_scope")
    if item.get("platform") not in VALID_PLATFORMS:
        warnings.append("platform_unset_or_invalid")
    if not _s(item.get("audience")).strip():
        reasons.append("missing_target_audience")
    if not _s(item.get("central_claim")).strip():
        reasons.append("missing_central_claim")
    if mode != "review_only" and not draft.strip():
        reasons.append("empty_draft")
    if mode in (EDIT_SCOPES - {"new_draft"}) and not original.strip():
        reasons.append("missing_original_for_edit")
    if mode == "review_only":
        if draft != original:
            reasons.append("review_only_must_not_rewrite")
        if headline_new != headline_original:
            reasons.append("review_only_must_not_change_title")
    if mode == "title_only" and draft != original:
        reasons.append("title_only_body_changed")
    if mode in {"opening_only", "ending_only"} and draft != original:
        warnings.append("partial_scope_requires_human_diff_review")
    if mode == "minimal" and original:
        # Ratio is an alert, not a quality score. Substantive corrections may justify changes.
        similarity = round(SequenceMatcher(None, original, draft).ratio(), 3)
        if similarity < 0.80:
            reasons.append("minimal_edit_extensively_rewritten")
    else:
        similarity = None
    keep = item.get("protected_phrases", [])
    required = item.get("required_terms", [])
    if not isinstance(keep, list) or not all(isinstance(x, str) for x in keep):
        reasons.append("invalid_protected_phrases")
        keep = []
    if not isinstance(required, list) or not all(isinstance(x, str) for x in required):
        reasons.append("invalid_required_terms")
        required = []
    absent_protected = [x for x in keep if not _has(draft, x)]
    absent_required = [x for x in required if not _has(draft, x)]
    if absent_protected:
        reasons.append("protected_content_lost")
    if absent_required:
        reasons.append("required_content_missing")
    if mode in {"minimal", "title_only", "opening_only", "ending_only"} and not keep:
        warnings.append("no_explicitly_protected_author_voice_fragments")
    # Declarative claim inventory: writers must classify assertions from the real record,
    # not create fake anecdotes for the sake of a high score.
    assertions = item.get("claims", [])
    if not isinstance(assertions, list):
        reasons.append("claims_not_a_list")
        assertions = []
    for idx, a in enumerate(assertions):
        if not isinstance(a, dict):
            reasons.append(f"claim_{idx}_invalid")
            continue
        ctext = _s(a.get("text")).strip()
        status = a.get("evidence_status")
        if not ctext or status not in FACT_STATUSES:
            reasons.append(f"claim_{idx}_missing_evidence_provenance")
        if a.get("presented_as_tested") and status != "user_verified":
            reasons.append(f"claim_{idx}_unverified_experience_claim")
        if status in {"proposed", "unknown"} and a.get("presented_as_fact"):
            reasons.append(f"claim_{idx}_unverified_statement_of_fact")
        if status == "third_party_claim" and a.get("first_person_experience"):
            reasons.append(f"claim_{idx}_source_laundered_as_personal_experience")
    if item.get("content_type") == "tutorial":
        if not _s(item.get("proof_plan")):
            warnings.append("tutorial_missing_verification_plan")
        if not assertions:
            warnings.append("tutorial_no_claim_inventory")
    # V2: structure-only preflight for fresh articles and substantive rewrites.
    # This does NOT confirm source authenticity or actual content value.
    if mode in {"new_draft", "substantive_rewrite"}:
        research = item.get("research")
        if not isinstance(research, dict):
            reasons.append("research_dossier_missing")
        else:
            for key in ("question", "summary", "limitations"):
                if not _s(research.get(key)).strip():
                    reasons.append(f"research_{key}_missing")
            sources = research.get("sources")
            if not isinstance(sources, list) or not sources:
                reasons.append("research_sources_missing")
            else:
                for idx, source in enumerate(sources):
                    if not isinstance(source, dict) or not _s(source.get("locator")).strip() or not _s(source.get("supports")).strip():
                        reasons.append(f"research_source_{idx}_incomplete")
        delivery = item.get("value_delivery")
        if not isinstance(delivery, dict):
            reasons.append("value_delivery_missing")
        else:
            for key in ("hook", "shareability", "readability", "primary_payoff"):
                if not _s(delivery.get(key)).strip():
                    reasons.append(f"value_{key}_missing")
            payoff_type = _s(delivery.get("primary_payoff_type")).strip()
            if not payoff_type:
                reasons.append("value_primary_payoff_type_missing")
            elif payoff_type not in PAYOFF_TYPES:
                reasons.append("value_primary_payoff_type_invalid")
            secondary = delivery.get("secondary_payoffs", [])
            if not isinstance(secondary, list) or any(not isinstance(x, str) or x not in PAYOFF_TYPES for x in secondary):
                reasons.append("value_secondary_payoffs_invalid")
    if UNSUPPORTED_GUARANTEE.search(draft):
        warnings.append("absolute_promise_detected_check_if_supported")
    if HARD_BAIT.search(draft):
        warnings.append("formulaic_engagement_bait")
    warnings.append("semantic_truth_author_voice_and_platform_compliance_require_human_review")
    # Machine results must never be called approved or published.
    return {
        "case_id": _s(item.get("case_id")),
        "status": "blocked" if reasons else "requires_editorial_review",
        "blocking_reasons": list(dict.fromkeys(reasons)),
        "warnings": list(dict.fromkeys(warnings)),
        "preserved": {
            "protected_count": len(keep) - len(absent_protected),
            "protected_total": len(keep),
            "missing_protected": absent_protected,
            "missing_required": absent_required,
            "minimal_similarity_diagnostic": similarity,
        },
        "manually_verified": False,
        "published": False,
    }


def audit(obj: Any) -> dict:
    if not isinstance(obj, dict) or not isinstance(obj.get("cases"), list):
        return {"error": "expected a JSON object containing cases[]", "cases": []}
    results = [validate(case) for case in obj["cases"]]
    return {
        "mode": "copy_preflight_only",
        "cases": results,
        "counts": {
            "blocked": sum(x["status"] == "blocked" for x in results),
            "requires_editorial_review": sum(x["status"] == "requires_editorial_review" for x in results),
        },
        "warning": "Not a blind review, factual truth test, model comparison or publication approval.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="copy-preflight-output")
    args = parser.parse_args()
    try:
        content = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        parser.error("Unable to read valid JSON input: " + str(exc))
    report = audit(content)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "copy-preflight-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report.get("counts", {"error": report.get("error")}), ensure_ascii=False))
    return 1 if report.get("error") or report["counts"]["blocked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
