#!/usr/bin/env python3
"""Collect actual public AICG creator posts, retaining media and source provenance.

Read-only; bounded samples, not a guarantee of complete X coverage.
The pinned upstream reader is already installed by anonymous-social-probe.yml.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import subprocess
import sys

HERE=Path(__file__).resolve().parent
OUT=HERE/"output"
UPSTREAM=HERE/"x_upstream.py"
SOURCES=HERE/"aicg-sources.json"
MAX_TEXT=7000
URL_RE=re.compile(r"https?://[^\s<>\u3000\"']+")
PROMPT_RE=re.compile(r"\bprompt(?:s|ing)?\b|提示词|workflow|工作流|comfyui|step.by.step|behind.the.scenes",re.I)

def take(s,lim):
    return str(s or "")[:lim]

def urls_from_text(s):
    return list(dict.fromkeys(m.group(0).rstrip(".,;!?）)") for m in URL_RE.finditer(s or "")))[:12]

def call_upstream(args,timeout=22):
    if not UPSTREAM.is_file():
        return None,"pinned_reader_not_installed"
    try:
        p=subprocess.run([sys.executable,str(UPSTREAM),*args],
                         capture_output=True,text=True,timeout=timeout)
        j=json.loads(p.stdout.strip() or "{}")
        if p.returncode or not isinstance(j,dict) or j.get("error"):
            return None,take((j.get("error") if isinstance(j,dict) else "") or p.stderr or f"exit_{p.returncode}",180)
        return j,None
    except (OSError,ValueError,subprocess.TimeoutExpired) as e:
        return None,type(e).__name__

def public_media(t):
    out=[]
    for m in (t.get("media") or [])[:10]:
        if not isinstance(m,dict):
            continue
        typ=take(m.get("type"),25)
        url=take(m.get("url"),1500)
        if not url.startswith("https://"):continue
        out.append({"type":typ,"url":url,
                    "thumbnail_url":take(m.get("thumb"),1500),
                    "duration_seconds":m.get("seconds")})
    return out

def normalize(t,handle):
    if not isinstance(t,dict) or not t.get("id") or not t.get("text"):
        return None
    author=t.get("author") or {}
    if not isinstance(author,dict):author={}
    username=take(author.get("handle") or handle,45)
    if username.lower()!=handle.lower():
        return None
    if t.get("reposted_by") or t.get("reply_to"):
        return None
    url=t.get("url") or f"https://x.com/{handle}/status/{t['id']}"
    if urlsplit(str(url)).hostname not in ("x.com","twitter.com"):return None
    art=t.get("article") or {}
    if not isinstance(art,dict):art={}
    txt=take(t.get("text"),MAX_TEXT)
    art_text=take(art.get("text"),20000)
    return {
      "id":str(t["id"]),"url":url,"source":"X",
      "author":username,"published_utc":t.get("created_at"),
      "text":txt,"text_truncated":len(str(t.get("text") or ""))>MAX_TEXT,
      "article":{"title":take(art.get("title"),300),
                 "text":art_text,"has_full_text":bool(art_text)},
      "media":public_media(t),"media_count":len(public_media(t)),
      "external_links":urls_from_text(txt+" "+art_text),
      "engagement_reported":{"likes":t.get("likes"),"replies":t.get("replies"),
                             "bookmarks":t.get("bookmarks"),"views":t.get("views")},
      "method":"pinned_public_reader", "retrieved_scope":
          "public post text and media metadata, not media bytes or full conversation",
      "prompt_workflow_hint":bool(PROMPT_RE.search(txt+" "+art_text)),
      "prompt_workflow_verified":False,
      "rights_status":"not_verified"
    }

def scan_creator(handle):
    data,err=call_upstream(["tweets",handle,"--limit","8","--since","4d"])
    s={"handle":handle,"status":"error" if err else "empty",
       "error":err,"returned":0}
    if err:return s,[]
    tweets=data.get("tweets",[])
    if not isinstance(tweets,list):tweets=[]
    items=[]
    for t in tweets:
        item=normalize(t,handle)
        if item:items.append(item)
    s.update(status="retrieved" if items else "no_originals_in_sample",
             error=None,returned=len(items),
             more_available=bool(data.get("more",False)))
    return s,items

def main():
    cfg=json.loads(SOURCES.read_text(encoding="utf-8"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        batches=list(pool.map(scan_creator,cfg["x_handles"]))
    statuses=[a for a,b in batches]
    posts=[p for a,b in batches for p in b]
    seen=set()
    posts=[p for p in posts if not (p["id"] in seen or seen.add(p["id"]))]
    posts.sort(key=lambda x:x.get("published_utc") or "",reverse=True)
    # Inspect a small number of public author-owned follow-up replies and threads
    # where the original post explicitly signals a prompt or long-form article.
    article_enriched=0
    author_followups=0
    targets=[p for p in posts if (p["article"]["title"] and not p["article"]["has_full_text"])
             or (p["prompt_workflow_hint"] and p["media"])][:12]
    def enrich(p):
        j,err=call_upstream(["tweet",p["url"],"--thread","--replies","8"],timeout=20)
        if err or not j:return None
        t=j.get("tweet") or {}
        base=normalize(t,p["author"])
        own=[]
        for reply in (j.get("thread") or [])+(j.get("replies") or []):
            if not isinstance(reply,dict):continue
            a=reply.get("author") or {}
            if not isinstance(a,dict) or str(a.get("handle","")).lower()!=p["author"].lower():continue
            text=take(reply.get("text"),3500)
            if not text:continue
            own.append({"url":reply.get("url"),
                        "created_at":reply.get("created_at"),
                        "text":text,
                        "media":public_media(reply),
                        "external_links":urls_from_text(text),
                        "retrieved_scope":"actual public author-owned reply, not verified complete thread"})
        dedup={x.get("url"):x for x in own if x.get("url")}
        return base,list(dedup.values())[:8]
    if targets:
        with ThreadPoolExecutor(max_workers=3) as pool:
            full=list(pool.map(enrich,targets))
        for old,result in zip(targets,full):
            if not result:continue
            new,own_replies=result
            if new and new["article"]["has_full_text"]:
                old["article"]=new["article"]
                old["external_links"]=list(dict.fromkeys(old["external_links"]+new["external_links"]))[:12]
                article_enriched+=1
            if own_replies:
                old["author_followup_replies"]=own_replies
                old["author_followup_scope"]="bounded_public_reply_sample_not_complete"
                old["external_links"]=list(dict.fromkeys(old["external_links"]+
                     [u for rp in own_replies for u in rp["external_links"]]))[:12]
                author_followups+=1
    OUT.mkdir(exist_ok=True,parents=True)
    report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
            "scope":"20 named original authors, bounded 4-day public timeline; 8 items max per author",
            "creators_configured":len(statuses),
            "creators_with_original_posts":sum(x["returned"]>0 for x in statuses),
            "posts":len(posts),
            "posts_with_media_metadata":sum(bool(x["media"]) for x in posts),
            "posts_with_external_links":sum(bool(x["external_links"]) for x in posts),
            "long_articles_enriched":article_enriched,
            "posts_with_author_followup_replies":author_followups,
            "source_health":statuses,"items":posts,
            "limitations":["Third-party reader: may omit posts and fail for accounts.",
             "Media URLs and thumbnails are referenced; media files not downloaded.",
             "Prompt presence is not proven by a keyword hint.",
             "Not authorized to read private, removed or subscriber-only posts.",
             "Original content licenses and reproducibility are unverified."]}
    (OUT/"aicg-x-original-posts.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    md=[f"# AICG X original posts (sampled)",f"UTC: {report['checked_at_utc']}",
        f"Creators: {report['creators_with_original_posts']}/{len(statuses)}; posts: {len(posts)}; posts with media: {report['posts_with_media_metadata']}",""]
    for p in posts[:35]:
        md+=["### @"+p["author"]+" — "+str(p["published_utc"]),
             p["url"],p["text"][:450],
             "Media: "+", ".join(m["type"] for m in p["media"]) if p["media"] else "Media: not returned",
             "Prompt/workflow: not independently verified",""]
    (OUT/"aicg-x-original-posts.md").write_text("\n".join(md),encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("creators_configured","creators_with_original_posts","posts","posts_with_media_metadata","posts_with_external_links","long_articles_enriched","posts_with_author_followup_replies")},ensure_ascii=False))

if __name__=="__main__":
    main()
