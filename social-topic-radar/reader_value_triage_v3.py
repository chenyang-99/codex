#!/usr/bin/env python3
"""Shadow editorial routing, never a publication approval.

Separate new projects, demonstrated works, reusable collections, tutorials,
and posts with time-stamped social signals. Preserve all discoveries in the
unified pool; do not silently discard low-scoring or undated candidates.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"

PATTERNS = {
    "resource_collection": re.compile(r"\b(?:\d{1,3}\s+(?:\w+\s+){0,4}(?:tools|resources|prompts|skills|projects|websites|github)|awesome[- ]|collection|directory|bookmark)\b|合集|清单|资源库|收藏|盘点|开源项目", re.I),
    "tutorial_workflow": re.compile(r"\b(?:how to|tutorial|step by step|guide|walkthrough|workflow|recipe|hands.on)\b|教程|实操|如何|操作步骤|工作流|复刻", re.I),
    "creator_demonstration": re.compile(r"\b(?:demo|showcase|before.?after|generated|rendered|animation|ai film|visual)\b|演示|成片|对比|生成效果|视觉|短片|动效", re.I),
    "tool_launch": re.compile(r"\b(?:open.source|released?|launch|introduc(?:ing|ed)|github|new version|release v)\b|开源|发布|上线|新版本|升级", re.I),
}

def classify(entity):
    posts = entity.get("source_posts", [])
    text = " ".join(str(p.get("title") or "")[:600] for p in posts[:12])
    families = set(entity.get("independent_source_families") or [])
    found = [key for key,pattern in PATTERNS.items() if pattern.search(text)]
    if any(p.get("media") or p.get("media_metadata") for p in posts) and "creator_demonstration" not in found:
        found.append("creator_demonstration")
    has_project = bool(entity.get("project_url"))
    lanes = list(dict.fromkeys(found))
    if has_project and "tool_launch" not in lanes:
        lanes.append("project_lead")
    if not lanes:
        lanes.append("unclassified_research")
    return lanes

def engagement_evidence(entity):
    out = []
    for post in entity.get("source_posts", []):
        # X alone has directly comparable metric names, but this still does NOT
        # prove high performance vs the author's own recent posts.
        metrics = post.get("metrics") or {}
        if post.get("source_family") != "x" or post.get("metric_scope") != "snapshot":
            continue
        views, bookmarks = metrics.get("views"), metrics.get("bookmarks")
        if (isinstance(views, (int,float)) and views >= 5000
                and isinstance(bookmarks, (int,float)) and bookmarks >= 100):
            out.append({
                "post": post.get("source_url"),
                "source": "x_third_party_snapshot",
                "checked_at": post.get("metrics_checked_at"),
                "views": views, "bookmarks": bookmarks,
                "bookmarks_per_1000_views": round(1000*bookmarks/views,2) if views else None,
                "interpretation": "raw high-bookmark signal only, no author baseline or virality proof",
            })
    return out

def review(entities):
    output = []
    for entity in entities:
        if not isinstance(entity,dict):
            continue
        lanes = classify(entity)
        signals = engagement_evidence(entity)
        families = set(entity.get("independent_source_families") or [])
        # Ranking is an editorial look-first triage, not a universal popularity
        # score. Keep every entity regardless of score.
        priority = (
            3 * bool(signals)
            + 2 * ("resource_collection" in lanes or "creator_demonstration" in lanes)
            + 2 * ("tutorial_workflow" in lanes)
            + 1 * bool(entity.get("project_url"))
            + min(2,max(0,len(families)-1))
        )
        needs = [
            "original post and first-party project page verification",
            "concrete reader payoff and platform-native first-screen proof",
            "timestamped independent source and right-to-use check",
            "existing nine-value and social editorial quality gates",
        ]
        output.append({
            "entity_key": entity.get("entity_key"), "project_url": entity.get("project_url"),
            "lanes":lanes,"signals":signals,"source_families":sorted(families),
            "review_priority":priority, "evidence_posts":[p.get("source_url") for p in entity.get("source_posts",[])][:12],
            "state": "needs_human_evidence_review", "publication_approved":False,
            "why": "editorial triage: demo/collection/learning, evidence and independent-source availability",
            "unverified_requirements":needs,
        })
    return sorted(output,key=lambda x:(-x["review_priority"],x["entity_key"] or ""))

def main():
    path=OUT / "unified-topic-candidates-v3.json"
    try:
        src=json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        src={"items":[]}
    items=review(src.get("items") or [])
    OUT.mkdir(parents=True,exist_ok=True)
    result={
        "generated_utc":datetime.now(timezone.utc).isoformat(),
        "total_discovery_entities":len(items), "editorial_review_queue_count":len(items),
        "auto_publishable_count":0,
        "lanes":dict(Counter(lane for item in items for lane in item["lanes"])),
        "top_research":items[:40],
        "remaining_entities_retain_in_unified_json":True,
        "limitations":[
            "Heuristic routing is not independent testing or a scored nine-value review.",
            "X raw bookmark views signals require same-author context and time normalization to call exceptional.",
            "Provider popularity is not portable across X, YouTube, Product Hunt or other platforms.",
            "Nothing is excluded from future consideration by a low heuristic priority.",
            "All publication approvals require the separate existing evidence and editorial gates.",
        ],
    }
    (OUT / "research-opportunity-v3.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:result[key] for key in ("total_discovery_entities","auto_publishable_count","lanes")},ensure_ascii=False))

if __name__=="__main__":main()
