#!/usr/bin/env python3
"""Free public news-index discovery for blind spots, NOT native social hot search.

Google News RSS site queries expose only indexed *leads*. Index ranking does
not establish likes, saves, on-platform trends or complete site coverage.
"""
from __future__ import annotations
import datetime as dt
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor,as_completed
from email.utils import parsedate_to_datetime

HERE=Path(__file__).resolve().parent
OUT=HERE/"output"
SEARCHES=[
    ("xiaohongshu_index","site:xiaohongshu.com AI 工具"),
    ("douyin_index","site:douyin.com/video AI 工具"),
    ("x_tool_index","site:x.com AI tools GitHub"),
    ("tiktok_index","site:tiktok.com AI video editing tools"),
    ("youtube_index","site:youtube.com/watch open source AI tools"),
    ("instagram_index","site:instagram.com/reel AI generated video"),
]
def read(url):
    req=Request(url,headers={"User-Agent":"AI-Topic-Radar/3.2; research-only",
                             "Accept":"application/rss+xml,application/xml"})
    with urlopen(req,timeout=12) as resp:
        raw=resp.read(1600001)
    if len(raw)>1600000: raise ValueError("oversize_feed")
    return raw

def normalize_day(value):
    try:return parsedate_to_datetime(value).astimezone(dt.timezone.utc).isoformat()
    except (ValueError,TypeError,OverflowError):return None

def parse(feed,source):
    root=ET.fromstring(feed)
    if not root.tag.endswith("rss"):raise ValueError("expected_rss")
    items=[]
    channel=root.find("channel")
    for entry in (channel.findall("item") if channel is not None else [])[:15]:
        url=(entry.findtext("link") or "").strip()
        title=re.sub(r"\s+"," ",entry.findtext("title") or "").strip()
        if not url.startswith("https://") or not title:continue
        items.append({"source":source,"platform":"public_search_index",
                      "url":url,"title":title[:600],
                      "published_utc":normalize_day(entry.findtext("pubDate")),
                      "retrieved_scope":"Google News indexed result: indirect, title-only, not verified original platform post",
                      "index_target_site":source,
                      "metrics":{}, "editorial_status":"research_candidate_only"})
    return items

def fetch_one(name,query,fetch=read):
    params=urlencode({"q":query+" when:7d","hl":"en-US","gl":"US","ceid":"US:en"})
    data=fetch("https://news.google.com/rss/search?"+params)
    return parse(data,name)

def collect(searches=SEARCHES,fetch=read):
    items,health=[],[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(fetch_one,name,q,fetch):name for name,q in searches[:8]}
        for fut in as_completed(futures):
            name=futures[fut]
            try:
                posts=fut.result()
                items.extend(posts)
                health.append({"source":name,"status":"retrieved" if posts else "empty",
                               "items":len(posts)})
            except (OSError,ValueError,ET.ParseError,TimeoutError) as e:
                health.append({"source":name,"status":"unavailable","items":None,
                               "error":type(e).__name__+":"+str(e)[:90]})
    return items,sorted(health,key=lambda x:x["source"])

def main():
    items,health=collect()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"indexed-social-leads-v3.json").write_text(json.dumps({
       "checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "items":items,"source_health":health,
       "limitations":["Indexed search results are not native search, complete platform coverage or social hot posts.",
                      "Indirect Google News links require independent original source and content verification.",
                      "Missing indexed results do not prove there are no relevant social posts.",
                      "No scraped private content or copied video media."]},
       ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"sources":health,"results":len(items)},ensure_ascii=False))
if __name__=="__main__":main()
