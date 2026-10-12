#!/usr/bin/env python3
"""Anonymous international AI source index, from configured RSS / Atom feeds.

Read-only. Never assume titles are viral. Items are candidates for later verification.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import email.utils
import html
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
OUT=HERE/"output"
CONFIG=HERE/"sources.json"
NS={"atom":"http://www.w3.org/2005/Atom","dc":"http://purl.org/dc/elements/1.1/"}
MAX_BYTES=3_500_000
MAX_WORKERS=6

def clean(v,n=450):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",v or ""))).strip()[:n]

def text(item,*paths):
    for tag in paths:
        found=item.findtext(tag,namespaces=NS)
        if found:return found.strip()
    return ""

def parse_date(v):
    if not v:return None
    try:return email.utils.parsedate_to_datetime(v).astimezone(dt.timezone.utc).isoformat()
    except (TypeError,ValueError):
        try:return dt.datetime.fromisoformat(v.replace("Z","+00:00")).astimezone(dt.timezone.utc).isoformat()
        except (ValueError,TypeError):return None

def norm_url(url):
    u=urlsplit(url)
    return urlunsplit((u.scheme,u.netloc,u.path,u.query,""))

def fetch(feed):
    name=feed["name"]
    src=feed["url"]
    info={"source":name,"url":src,"kind":feed["kind"],"status":"not_verified"}
    try:
        r=Request(src,headers={"User-Agent":"Mozilla/5.0 (compatible; PublicAIResearch/1.0)",
                               "Accept":"application/atom+xml,application/rss+xml,application/xml,text/xml"})
        with urlopen(r,timeout=13) as stream:
            raw=stream.read(MAX_BYTES)
            status=stream.status
        root=ET.fromstring(raw)
        items=root.findall(".//item")
        if not items:items=root.findall(".//atom:entry",NS)
        records=[]
        for e in items[:10]:
            title=clean(text(e,"title","atom:title"),210)
            link=text(e,"link")
            if not link:
                tag=e.find("atom:link",NS)
                link=tag.attrib.get("href","") if tag is not None else ""
            date=parse_date(text(e,"pubDate","atom:published","atom:updated","dc:date"))
            detail=clean(text(e,"description","atom:summary","atom:content"),400)
            if title and link.startswith(("https://","http://")):
                records.append({"title":title,"url":norm_url(link)[:600],"excerpt":detail,
                                "published_utc":date,"source":name,
                                "source_type":feed["kind"],"priority":feed["priority"],
                                "comments_status":"not_provided_by_feed"})
        info.update(status="verified" if records else "empty",http_status=status,items=len(records))
        return info,records
    except (HTTPError,URLError,TimeoutError,OSError,ET.ParseError,ValueError) as e:
        info["error"]=f"{type(e).__name__}: {str(e)[:120]}"
        return info,[]

def collect():
    feeds=json.loads(CONFIG.read_text(encoding="utf-8"))["feeds"]
    if not feeds:raise ValueError("No feeds configured")
    results={}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        jobs={ex.submit(fetch,feed):i for i,feed in enumerate(feeds)}
        for future in as_completed(jobs):
            results[jobs[future]]=future.result()
    stats=[]
    items=[]
    seen=set()
    for i in range(len(feeds)):
        health,entries=results[i]
        stats.append(health)
        for e in entries:
            if e["url"] not in seen:
                seen.add(e["url"]);items.append(e)
    # Simple transparent prioritization, not engagement or editorial quality.
    def score(e):
        recent=0
        try:
            age=(dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(e["published_utc"])).total_seconds()/86400
            recent=2 if 0<=age<=3 else 1 if 0<=age<=14 else 0
        except (TypeError,ValueError):pass
        return e["priority"]+recent
    for e in items:e["discovery_score"]=score(e)
    items.sort(key=lambda e:(e["discovery_score"],e["published_utc"] or ""),reverse=True)
    OUT.mkdir(parents=True,exist_ok=True)
    report={"checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "configured_feeds":len(feeds),"verified_feeds":sum(x["status"]=="verified" for x in stats),
            "source_health":stats,"unique_candidates":len(items),"items":items[:140],
            "limitations":["Only entries available in RSS/Atom at execution time",
                           "Headline presence doesn't establish virality or tutorial replicability",
                           "Full article, engagement, comments, rights require separate verification"]}
    (OUT/"public-rss-candidates.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    md=["# Global public AI source discovery","",
        f"UTC: {report['checked_at_utc']}",
        f"Verified feeds: {report['verified_feeds']}/{report['configured_feeds']}. Unique titles: {report['unique_candidates']}",
        "","## Per-source health"]
    for x in stats:
        md.append(f"- {x['source']}: {x['status']} ({x.get('items',0)} items) {x.get('error','')}")
    md+=["","## Priority candidates (headline-level evidence only)"]
    for e in items[:50]:
        md.append(f"- [{e['title']}]({e['url']}) — {e['source']} / {e['published_utc'] or 'time unknown'}")
    (OUT/"public-rss-candidates.md").write_text("\n".join(md),encoding="utf-8")
    print(json.dumps({"status":"global_rss_discovery_complete",
                      "configured_feeds":len(feeds),"verified_feeds":report["verified_feeds"],
                      "candidates":len(items),
                      "failed_sources":[x["source"] for x in stats if x["status"]!="verified"]},ensure_ascii=False))
if __name__=="__main__":collect()
