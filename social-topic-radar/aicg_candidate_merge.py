#!/usr/bin/env python3
"""Evidence-only merging for AICG; do not promote accessible snippets to tested tutorials."""
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
import json
import re

ROOT=Path(__file__).resolve().parent/"output"

def load(file):
    try:
        doc=json.loads((ROOT/file).read_text(encoding="utf-8"))
        return doc if isinstance(doc,dict) else {}
    except (OSError,ValueError):return {}

def iso_age(date,now):
    if not date:return None
    try:
        d=datetime.fromisoformat(str(date).replace("Z","+00:00"))
        if d.tzinfo is None:
            # Publication day alone is not precise enough for 24-hour claims.
            return None
        return round((now-d.astimezone(timezone.utc)).total_seconds()/3600,2)
    except (TypeError,ValueError):return None

def canonical(url):
    try:
        x=urlsplit(url)
        if x.scheme!="https" or not x.netloc:return None
        return urlunsplit((x.scheme,x.netloc.lower(),x.path.rstrip("/") or "/","",""))
    except (TypeError,ValueError):return None

def main():
    now=datetime.now(timezone.utc)
    x=load("aicg-x-original-posts.json")
    sites=load("aicg-original-site-items.json")
    records=[]
    seen=set()
    for p in x.get("items",[]):
        url=canonical(p.get("url"))
        if not url or url in seen:continue
        seen.add(url)
        age=iso_age(p.get("published_utc"),now)
        if age is not None and (age<0 or age>72):continue
        media=p.get("media") or []
        records.append({"source":"X","url":url,"published_utc":p.get("published_utc"),
          "age_hours":age,"original_author":p.get("author"),
          "title_or_excerpt":(p.get("text") or "")[:400],
          "category":"video" if any(m.get("type") in ("video","gif") for m in media)
                     else "image" if any(m.get("type") in ("photo","image") for m in media) else "unknown",
          "media_metadata":media[:6],
          "full_post_text":p.get("text"),
          "source_workflow_urls":p.get("external_links") or [],
          "prompt_or_workflow_verified":False,
          "evidence_level":"retrieved_public_x_post_with_optional_media_metadata",
          "freshness_verified":age is not None,
          "ready_to_publish":False})
    for p in sites.get("items",[]):
        url=canonical(p.get("url"))
        if not url or url in seen:continue
        seen.add(url)
        age=iso_age(p.get("published_utc"),now)
        if age is not None and (age<0 or age>72):continue
        records.append({"source":p.get("source"),"url":url,
          "published_utc":p.get("published_utc"),"age_hours":age,
          "original_author":p.get("creator"),
          "title_or_excerpt":p.get("title","")+" — "+(p.get("description") or "")[:350],
          "category":"unknown","media_metadata":[{"type":"preview","url":p["preview_image"]}] if p.get("preview_image") else [],
          "source_workflow_urls":p.get("workflow_download_links") or [],
          "prompt_or_workflow_verified":bool(p.get("workflow_download_links")),
          "evidence_level":p.get("evidence_level","page_metadata"),
          "freshness_verified":age is not None,
          "ready_to_publish":False})
    fresh=[r for r in records if r["freshness_verified"]]
    unknown=[r for r in records if not r["freshness_verified"]]
    fresh.sort(key=lambda x:(bool(x["source_workflow_urls"]),x.get("age_hours") is not None,-(x.get("age_hours") or 0)),reverse=True)
    result={"generated_utc":now.isoformat(),"fresh_72h_candidate_count":len(fresh),
       "undated_or_unverified_candidate_count":len(unknown),
       "items_newest_72h":fresh[:100],
       "items_undated_or_time_unverified":unknown[:100],
       "limitations":["Original source page/post availability does not establish original prompt, images or workflow tested by us",
           "Third-party X timeline completeness not guaranteed",
           "The 20 daily items are an editorial target, not an automatic quota",
           "Cross-run dedupe requires checking the persistent Google Sheet; this file only dedupes the current run"]}
    ROOT.mkdir(parents=True,exist_ok=True)
    (ROOT/"aicg-fresh-candidates.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# AICG evidence-linked candidate pool","",
      "Generated UTC: "+now.isoformat(),
      f"Date-verified within 72h: {len(fresh)}; undated/unverified: {len(unknown)}",
      "No candidate automatically approved for publication.","","## dated candidates"]
    for r in fresh[:35]:
        lines +=["- "+r["title_or_excerpt"][:160], "  "+r["url"],
            "  Published "+str(r["published_utc"])+" / evidence "+r["evidence_level"]]
    (ROOT/"aicg-fresh-candidates.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"dated_candidates":len(fresh),"undated_candidates":len(unknown),
      "candidate_count":len(records)},ensure_ascii=False))

if __name__=="__main__":main()
