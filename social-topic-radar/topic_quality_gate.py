#!/usr/bin/env python3
"""Evidence-first AI topic gate. No network, automatic publishing or invented scores."""
import argparse
import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

WEIGHTS = {"demand":25,"value":25,"evidence":20,"differentiation":15,"audience_fit":10,"feasibility":5}
CONTENT_SCORE_CAPS = {"attraction":25,"spread":30,"payoff":30,"credibility":15}
CONTENT_SCORE_MINS = {"attraction":20,"spread":23,"payoff":21,"credibility":10}
CONTENT_FIELDS = ("attraction","spread_mechanism","payoff_description")
PAYOFF_TYPES = {"utility","learning","save","insight","decision","information","emotion","entertainment","social_expression"}
SPREAD_CLASSES = {"verified_viral","fresh_potential"}
SOCIAL_PLATFORMS = {"x", "xiaohongshu", "douyin"}
SOCIAL_SUPPORT_TYPES = {"own_post", "same_platform_post", "original_work"}
EVIDENCE_KINDS = {"user_post","user_comment","official_release","original_case"}
VALUE_TYPES = {"实用","学习","收藏","决策","认知","信息","情绪","审美娱乐","社交表达"}
STATUSES = ("editorial_candidate","exploratory_only","blocked")
# Nine reader-value dimensions: scan all nine but require only ONE primary.
# This is a disclosure gate, not machine proof of content quality or virality.
VALUE_LABELS = {
    "utility":"实用", "learning":"学习", "save":"收藏", "decision":"决策",
    "insight":"认知", "information":"信息", "emotion":"情绪",
    "entertainment":"审美娱乐", "social_expression":"社交表达",
}
VALUE_PROOF_FIELDS = {
    "utility":("task_input","deliverable_example","success_check"),
    "learning":("teachable_skill","steps_and_prerequisites","learner_verification"),
    "save":("reusable_asset","access_conditions","reuse_scenario"),
    "decision":("options_compared","tradeoffs","decision_rule"),
    "insight":("prior_understanding","new_interpretation","supporting_observation"),
    "information":("new_fact","event_date","reader_impact"),
    "emotion":("specific_story","emotional_turn","audience_connection"),
    "entertainment":("actually_viewed_work","standout_moment","experience_reason"),
    "social_expression":("discussion_question","grounded_positions","reason_to_express"),
}
VALUE_STATES = {"primary","secondary","not_applicable"}
VALUE_SOURCE_ACCESS = {
    "original_read","original_viewed","official_document_read","independently_tested"
}
VALUE_EVIDENCE_STATES = {"source_reviewed","independently_tested"}


def read(path):
    try:
        obj=json.loads(Path(path).read_text(encoding="utf-8"))
        return obj if isinstance(obj,dict) else {}
    except (OSError,ValueError): return {}

def canon(url):
    if not isinstance(url,str): return ""
    try: s=urlsplit(url.strip())
    except ValueError: return ""
    if s.scheme not in ("http","https") or not s.hostname: return ""
    return urlunsplit((s.scheme.lower(),s.netloc.lower(),s.path.rstrip("/") or "/","",""))

def txt(s,n=300):
    return re.sub(r"\s+"," ",s).strip()[:n] if isinstance(s,str) else ""

def context_key(row):
    """Missing author identity: all comments in one post share one independent context."""
    u=canon(row.get("post_url") or row.get("url"))
    author=txt(row.get("author_id"),120)
    return u + ("::"+author if author else "") if u else ""

def audit_radar(outdir):
    out=Path(outdir)
    editorial=read(out/"editorial-shortlist.json")
    pain=read(out/"domestic-painpoints.json")
    status=read(out/"domestic-status.json")
    leads=[]; seen_urls=set(); comments=[]; seen_comments=set()
    for x in editorial.get("shortlist",[]):
        if not isinstance(x,dict): continue
        u=canon(x.get("url"))
        if not u or u in seen_urls: continue
        seen_urls.add(u)
        leads.append({"url":u,"source":txt(x.get("source"),100),
                      "headline_or_excerpt":txt(x.get("title") or x.get("excerpt")),
                      "date":x.get("published_utc"),
                      "read_scope":x.get("verified_scope"),
                      "kind":"discovery_lead_only",
                      "status":"requires_original_and_audience_verification"})
    for theme in pain.get("observed_themes",[]):
        if not isinstance(theme,dict): continue
        for row in theme.get("actual_reply_examples",[]):
            if not isinstance(row,dict): continue
            u=canon(row.get("post_url") or row.get("url"))
            quote=txt(row.get("text_excerpt"),250)
            if not u or not quote or (u,quote) in seen_comments: continue
            seen_comments.add((u,quote))
            comments.append({"platform":row.get("platform"),
                             "post_url":u,"quote":quote,
                             "theme_keyword_match":txt(theme.get("theme"),80),
                             "read_scope":row.get("classification_basis"),
                             "context_key":context_key(row),
                             "status":"keyword_match_not_validated_user_need"})
    independent=len({c["context_key"] for c in comments if c["context_key"]})
    result={"mode":"radar_evidence_audit",
            "generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "shortlist_links":len(leads),"comment_examples_visible":len(comments),
            "distinct_comment_post_contexts":independent,
            "qualified_publishable_topics":0,
            "source_status":status.get("tests",[]),
            "leads":leads,"comments":comments,
            "limitations":["RSS/search excerpts are discovery only, not verified user needs.",
                           "Keyword matched comments need contextual review.",
                           "The source report contains only truncated examples, not all comments.",
                           "Multiple comments on one post are NOT independent users.",
                           "Platform coverage is bounded by observed access; zero obtained is not zero demand."]}
    out.mkdir(parents=True,exist_ok=True)
    (out/"topic-research-evidence.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# 选题证据审查｜采集层（不自动批准选题）","",
           f"原雷达候选链接：{len(leads)}；报告实际可见评论：{len(comments)}；帖子语境：{independent}",
           "**自动通过可发布选题：0，仍需真实需求、竞争缺口及成果实测审查。**","",
           "## 实际可见评论样本"]
    lines.extend(f"- [{c['platform']}] {c['quote']} — {c['post_url']}" for c in comments[:12])
    lines.extend(["","## 边界"]+["- "+x for x in result["limitations"]])
    (out/"topic-research-evidence.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return result

def audit_content_values(topic):
    """Attraction + shareability required; reader payoff adapts to content type.

    Preserve evidence rules and accept only explicitly supplied editorial scores.
    No popularity or editorial scores inferred from crawled metadata.
    """
    v=topic.get("content_values")
    issues=[]
    if not isinstance(v,dict):
        return ["missing_content_values"],None
    for k in CONTENT_FIELDS:
        if not txt(v.get(k)): issues.append("missing_content_value_"+k)
    payoff_type=txt(v.get("payoff_type"))
    if payoff_type not in PAYOFF_TYPES:
        issues.append("missing_or_invalid_payoff_type")
    spread_class=txt(v.get("spread_class"))
    if spread_class not in SPREAD_CLASSES:
        issues.append("missing_or_unverified_spread_class")
    if not canon(v.get("spread_source_url")):
        issues.append("missing_spread_primary_source")
    if spread_class=="verified_viral":
        if not txt(v.get("spread_metric")): issues.append("missing_verified_platform_metric")
        if not txt(v.get("spread_checked_at")): issues.append("missing_verified_metric_timestamp")
    elif spread_class=="fresh_potential":
        if not txt(v.get("original_published_at")): issues.append("missing_original_published_at")
        if not txt(v.get("freshness_reason")): issues.append("missing_freshness_reason")
    scores=topic.get("content_scores")
    if scores is None:
        return issues,None
    if not isinstance(scores,dict) or any(not isinstance(scores.get(k),(int,float))
            or isinstance(scores.get(k),bool) or not 0<=scores[k]<=cap
            for k,cap in CONTENT_SCORE_CAPS.items()):
        issues.append("invalid_content_scores")
        return issues,None
    total=round(sum(scores[k] for k in CONTENT_SCORE_CAPS),1)
    for k,minimum in CONTENT_SCORE_MINS.items():
        if scores[k]<minimum: issues.append("content_score_below_minimum_"+k)
    if total<85: issues.append("content_score_total_below_85")
    return issues,total

def audit_nine_values(topic):
    """Demand source-linked, category-specific deliverables, not nine arbitrary scores.

    Checks structured editorial declarations and link consistency only. It cannot
    establish whether the source was actually read, the artwork is good, or the
    promise is fulfilled. A human must verify those claims before recommendation.
    """
    issues=[]
    cv=topic.get("content_values")
    if not isinstance(cv,dict): cv={}
    payoff=txt(cv.get("payoff_type"))
    scan=topic.get("value_scan")
    if not isinstance(scan,dict):
        issues.append("missing_nine_value_scan")
        scan={}
    for key in VALUE_LABELS:
        if scan.get(key) not in VALUE_STATES:
            issues.append("missing_or_invalid_value_scan_"+key)
    if set(scan)-set(VALUE_LABELS):
        issues.append("unknown_value_scan_dimension")
    primaries=[key for key in VALUE_LABELS if scan.get(key)=="primary"]
    if len(primaries)!=1:
        issues.append("nine_value_scan_requires_one_primary")
    if len(primaries)==1 and primaries[0]!=payoff:
        issues.append("primary_value_mismatch")
    if payoff in VALUE_LABELS and txt(topic.get("value_type"))!=VALUE_LABELS[payoff]:
        issues.append("chinese_value_label_mismatch")
    proof=topic.get("value_proof")
    if not isinstance(proof,dict):
        return issues+["missing_value_proof"]
    for key in ("observed_material","reader_deliverable","verification_check","limitations"):
        if not txt(proof.get(key)):
            issues.append("missing_value_proof_"+key)
    if proof.get("evidence_status") not in VALUE_EVIDENCE_STATES:
        issues.append("unverified_value_evidence")
    if proof.get("source_access") not in VALUE_SOURCE_ACCESS:
        issues.append("unverified_value_source_access")
    source=canon(proof.get("source_url"))
    if not source:
        issues.append("missing_value_proof_source_url")
    else:
        signal_links={canon(sig.get("url")) for sig in (topic.get("signals") or [])
                      if isinstance(sig,dict)}
        if source not in signal_links:
            issues.append("unlinked_value_proof_source")
    evidence=proof.get("category_evidence")
    if not isinstance(evidence,dict):
        evidence={}
        issues.append("missing_category_value_evidence")
    for field in VALUE_PROOF_FIELDS.get(payoff,()):
        if not txt(evidence.get(field)):
            issues.append("missing_value_"+payoff+"_"+field)
    if payoff=="entertainment" and proof.get("source_access") not in (
            "original_viewed","independently_tested"):
        issues.append("visual_work_not_viewed")
    return issues

def audit_social_native_pitch(topic):
    """Reject attractive-sounding leads without a concrete, platform-native post concept.

    This validates supplied editorial evidence, NOT the truth of claims, artistic
    quality, audience demand or actual platform reach. Human veto remains required.
    """
    p=topic.get("social_pitch")
    if not isinstance(p,dict):
        return ["missing_social_pitch"]
    issues=[]
    if txt(p.get("platform")) not in SOCIAL_PLATFORMS:
        issues.append("missing_target_platform")
    for key in ("first_screen","proof_object","why_share_or_save","account_fit",
                "support_observation"):
        if not txt(p.get(key)):
            issues.append("missing_social_"+key)
    support=txt(p.get("support_type"))
    if support not in SOCIAL_SUPPORT_TYPES:
        issues.append("missing_or_invalid_social_support_type")
    if not canon(p.get("support_url")):
        issues.append("missing_social_support_url")
    if support in ("own_post","same_platform_post"):
        for key in ("support_metric","support_checked_at"):
            if not txt(p.get(key)):
                issues.append("missing_social_"+key)
    if support=="original_work":
        if not txt(p.get("original_published_at")):
            issues.append("missing_social_original_published_at")
        if not txt(p.get("editorial_hypothesis")):
            issues.append("missing_social_editorial_hypothesis")
    # For B-class original works, do NOT imply that platform distribution was verified.
    return issues

def review_one(topic,rejected,history,seen):
    if not isinstance(topic,dict):
        return {"status":"blocked","blocking_reasons":["invalid_record"]}
    key=txt(topic.get("problem_key"),180).casefold()
    topicid=txt(topic.get("topic_id"),120)
    issues=[]
    if not key or not topicid: issues.append("missing_topic_id_or_problem_key")
    if key in rejected or topicid.casefold() in rejected: issues.append("explicitly_rejected_topic")
    if key in history or topicid.casefold() in history: issues.append("historical_duplicate")
    if key and key in seen: issues.append("duplicate_within_batch")
    if key: seen.add(key)
    for field in ("title","audience","trigger","job","outcome","angle","promise",
                  "proof_plan","competitor_gap","difference_rationale","source_limitations"):
        if not txt(topic.get(field)): issues.append("missing_"+field)
    if topic.get("value_type") not in VALUE_TYPES: issues.append("missing_or_invalid_value_type")
    if topic.get("requires_test") and not txt(topic.get("test_gap")): issues.append("missing_preproduction_test_gap")
    content_issues,content_score=audit_content_values(topic)
    issues.extend(content_issues)
    value_issues=audit_nine_values(topic)
    issues.extend(value_issues)
    social_issues=audit_social_native_pitch(topic)
    issues.extend(social_issues)
    if content_score is not None:
        evidence=topic.get("score_evidence")
        if not isinstance(evidence,dict) or any(
                not txt(evidence.get(k)) for k in CONTENT_SCORE_CAPS):
            issues.append("missing_score_evidence_by_dimension")
    contexts=set(); links=set(); user_evidence=0; official_evidence=0; original_evidence=0
    for sig in (topic.get("signals") or []):
        if not isinstance(sig,dict): continue
        url=canon(sig.get("url")); kind=sig.get("kind"); scope=txt(sig.get("read_scope"))
        if not url or kind not in EVIDENCE_KINDS or not scope or scope in (
            "search_snippet_only","headline_only","unavailable","unknown"): continue
        if kind in ("user_post","user_comment") and not txt(sig.get("quote")): continue
        if kind=="official_release" and not txt(sig.get("claim")): continue
        if kind=="original_case" and not txt(sig.get("observed_result")): continue
        links.add(url)
        k=context_key(sig)
        if k: contexts.add(k)
        user_evidence+=int(kind in ("user_post","user_comment"))
        official_evidence+=int(kind=="official_release")
        original_evidence+=int(kind=="original_case")
    if not links: issues.append("no_recheckable_primary_evidence")
    if not (user_evidence or official_evidence or original_evidence):
        issues.append("no_direct_user_official_or_original_evidence")
    if not contexts: issues.append("no_independent_source_context")
    rating=topic.get("ratings")
    score=None
    if isinstance(rating,dict) and all(isinstance(rating.get(k),(int,float))
           and not isinstance(rating[k],bool) and 0<=rating[k]<=5 for k in WEIGHTS):
        score=round(sum(WEIGHTS[k]*rating[k]/5 for k in WEIGHTS),1)
    confidence="high" if len(contexts)>=3 else ("medium" if len(contexts)==2 else
                ("low" if len(contexts)==1 else "none"))
    # A single verified original creator work/official tutorial can be a primary
    # source; secondary popularity is not required for fresh high-value research.
    primary_source=bool(official_evidence or original_evidence)
    decision="blocked" if issues else ("editorial_candidate"
        if content_score is not None and (len(contexts)>=2 or primary_source)
        else "exploratory_only")
    return {"topic_id":topicid,"problem_key":key,"title":txt(topic.get("title")),
            "status":decision,"blocking_reasons":issues,
            "independent_post_contexts":len(contexts),"evidence_confidence":confidence,
            "source_links":sorted(links),"human_supplied_score":score,
            "content_value_score":content_score,
            "social_native_verdict":"blocked_metadata" if social_issues else "manual_content_review_required",
            "primary_value":txt(topic.get("content_values",{}).get("payoff_type")) if isinstance(topic.get("content_values"),dict) else "",
            "secondary_values":[k for k in VALUE_LABELS if isinstance(topic.get("value_scan"),dict) and topic["value_scan"].get(k)=="secondary"],
            "value_proof_verdict":"blocked_metadata" if value_issues else "manual_value_review_required",
            "human_editorial_approval":False,
            "content_value_verdict":("failed" if content_issues else
                "unscored_exploration" if content_score is None else "passed"),
            "score_note":"not a virality prediction" if score is not None else "unscored; do not invent ratings",
            "requires_test":bool(topic.get("requires_test")),
            "proof_plan":txt(topic.get("proof_plan")),
            "claim":txt(topic.get("promise"))}

def review_file(source,outdir,history_path=None):
    obj=read(source); hist=read(history_path) if history_path else {}
    rejected={str(v).casefold() for v in hist.get("rejected",[])+obj.get("rejected",[])}
    known={str(v).casefold() for v in hist.get("known_problem_keys",[])+obj.get("known_problem_keys",[])}
    seen=set()
    rows=[review_one(t,rejected,known,seen) for t in obj.get("topics",[])]
    order={"editorial_candidate":0,"exploratory_only":1,"blocked":2}
    rows.sort(key=lambda x:(order.get(x["status"],3),
                           -(x.get("content_value_score") if x.get("content_value_score") is not None else -1)))
    counts=Counter(x["status"] for x in rows)
    report={"mode":"curated_topic_review",
            "generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "counts":{k:counts[k] for k in STATUSES},"topics":rows,
            "warning":"Mechanical pass is NOT social-media fit, human editorial approval, model validation, production approval or publication."}
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    (out/"topic-review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# 选题研究档案审核","",f"输入：{len(rows)} 条",
           f"编辑候选 {counts['editorial_candidate']}；仅探索 {counts['exploratory_only']}；拦截 {counts['blocked']}",
           "编辑初审≠实测≠发布；吸引力和传播必备，收藏/学习/认知/情绪按类型选择，无人工分不进入正式编辑候选。",""]
    for r in rows:
        lines.extend([f"## {r['title'] or r['topic_id']}",
                      f"状态：{r['status']}；独立帖子语境：{r['independent_post_contexts']}；置信度：{r['evidence_confidence']}",
                      f"审核原因：{','.join(r['blocking_reasons']) or '基础字段齐全，仍待真人判断'}",
                      f"证据：{' ; '.join(r['source_links']) or '没有有效原始来源'}",""])
    (out/"topic-review.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("radar","review"))
    p.add_argument("--output-dir",default=str(Path(__file__).resolve().parent/"output"))
    p.add_argument("--input");p.add_argument("--history")
    a=p.parse_args()
    if a.mode=="radar":
        r=audit_radar(a.output_dir)
        print(json.dumps({"status":"radar_evidence_audited","links":r["shortlist_links"],
                          "comments":r["comment_examples_visible"],"qualified_topics":0}))
    else:
        if not a.input:p.error("review mode requires an explicitly researched --input JSON")
        print(json.dumps(review_file(a.input,a.output_dir,a.history)["counts"],ensure_ascii=False))
if __name__=="__main__":main()
