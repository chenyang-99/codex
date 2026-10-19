#!/usr/bin/env python3
"""Offline editorial preflight for V2.1 source/date/duplication/score claims.

Expects {"history":[{"title":"...", "source_url":"...", "entity":"..."}],
         "candidates":[{"id":"1","title":"...", "source_url":"...",
                        "entity":"...", "original_published_at":"YYYY-MM-DD",
                        "original_read_scope":"original_page",
                        "value_delivery":"...", "spread_basis":"...",
                        "spread_class":"fresh_potential", "source_metric_platform":"...",
                        "counterevidence_reviewed":true,
                        "editorial_status":"research_candidate",
                        "scores":{...}}]}
Does not browse; results are deterministic warnings, NOT evidence verification or
approval to publish. Human must assess semantic duplication, factual accuracy,
counterevidence completeness and actual content value.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

CAPS = {"attraction":25, "spread":30, "payoff":30, "credibility":15}
MINS = {"attraction":20, "spread":23, "payoff":21, "credibility":10}
CLASSES = {"verified_viral", "fresh_potential", "unverified"}
def canon(url):
    if not isinstance(url,str): return ""
    try: p=urlsplit(url.strip())
    except ValueError: return ""
    if p.scheme not in {"http","https"} or not p.hostname: return ""
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip("/") or "/","",""))
def normalized(x):
    return " ".join(str(x or "").casefold().split())
def check(candidate, history, today):
    flags=[]
    if not isinstance(candidate,dict):
        return {"id":None,"status":"blocked_metadata","flags":["invalid_record"]}
    title=normalized(candidate.get("title"))
    url=canon(candidate.get("source_url"))
    entity=normalized(candidate.get("entity"))
    if not title: flags.append("title_missing")
    if not url: flags.append("original_source_missing")
    if not candidate.get("original_read_scope"): flags.append("actual_read_scope_missing")
    collisions=[]
    for i,old in enumerate(history):
        if not isinstance(old,dict):continue
        sameurl=url and url==canon(old.get("source_url"))
        sameentity=entity and entity==normalized(old.get("entity"))
        sametitle=title and title==normalized(old.get("title"))
        if sameurl or sameentity or sametitle:
            collisions.append({"row":old.get("row",i+1),"kind":"source_url" if sameurl else ("same_entity" if sameentity else "exact_title")})
    if collisions:
        flags.append("historical_collision_requires_editor_review")
        if not candidate.get("novelty_delta") or not candidate.get("novelty_source_url"):
            flags.append("distinct_new_facts_not_documented")
    date_value=candidate.get("original_published_at")
    try:
        published=dt.date.fromisoformat(date_value)
        age=(today-published).days
        if age<0: flags.append("source_date_in_future")
        if age>3 and candidate.get("timeliness_label")!="evergreen_or_ongoing":
            flags.append("older_than_72_hours_not_labeled")
    except (ValueError,TypeError):flags.append("exact_original_date_missing_or_invalid")
    spread=candidate.get("spread_class")
    if spread not in CLASSES: flags.append("spread_class_missing_or_invalid")
    if spread=="verified_viral":
        if not candidate.get("viral_post_url") or not candidate.get("viral_metrics") or not candidate.get("metrics_checked_at"):
            flags.append("verified_viral_without_same_post_measures")
        if candidate.get("source_metric_platform") in {"producthunt","github"}:
            flags.append("product_votes_or_stars_are_not_social_virality")
    if spread=="fresh_potential" and not candidate.get("spread_basis"):
        flags.append("potential_spread_mechanism_missing")
    if not candidate.get("counterevidence_reviewed"):
        flags.append("counterevidence_not_reviewed")
    if not candidate.get("value_delivery"):
        flags.append("concrete_reader_delivery_missing")
    status=candidate.get("editorial_status","research_candidate")
    scores=candidate.get("scores")
    if status=="formal_recommendation":
        if not isinstance(scores,dict) or any(not isinstance(scores.get(k),int) or isinstance(scores.get(k),bool) or not 0<=scores[k]<=CAPS[k] for k in CAPS):
            flags.append("four_component_scores_missing_or_invalid")
        else:
            if any(scores[k]<MINS[k] for k in CAPS) or sum(scores.values())<85:
                flags.append("does_not_meet_v12_editorial_thresholds")
        if candidate.get("scores_evidence") is None:
            flags.append("score_evidence_missing")
        if spread=="unverified":
            flags.append("unverified_spread_cannot_be_formal")
    elif scores and not candidate.get("scores_evidence"):
        flags.append("numeric_scores_without_evidence")
    return {"id":candidate.get("id"),"status":"requires_manual_review" if not flags else "metadata_blocked","flags":flags,
            "history_collisions":collisions,"automatically_approved":False}
def audit(data,today=None):
    if not isinstance(data,dict):raise ValueError("expected JSON object")
    history=data.get("history",[])
    candidates=data.get("candidates",[])
    if not isinstance(history,list) or not isinstance(candidates,list):raise ValueError("history and candidates must be arrays")
    day=dt.date.fromisoformat(today) if today else dt.date.today()
    return {"checked_date":day.isoformat(),"checked_history_rows":len(history),
            "results":[check(c,history+[x for x in candidates[:i] if isinstance(x,dict)],day) for i,c in enumerate(candidates)],
            "notes":["no semantic dedup or online verification","no automatic topic approval","every quantitative tradeoff requires human source review"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--date",help="YYYY-MM-DD in target editorial timezone")
    p.add_argument("--output")
    args=p.parse_args()
    result=audit(json.loads(Path(args.input).read_text(encoding="utf-8")),args.date)
    serialized=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:Path(args.output).write_text(serialized+"\n",encoding="utf-8")
    print(serialized)
if __name__=="__main__":main()
