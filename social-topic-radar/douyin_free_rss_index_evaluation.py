#!/usr/bin/env python3
"""One-shot, no-login, low-rate evaluation of published RSS search surfaces.

RSS is a discovery-only index, not native Douyin site-wide search. Never
report complete keyword coverage or comments from this file. Stop on blocks.
No proxy, user login, cookies, retries, or scraped identity.
"""
from datetime import datetime,timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlencode,urlsplit,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import json,re,xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent/"output"/"douyin-free-rss-index-evaluation.json"
QUERIES=["site:douyin.com/video/ AI漫剧 制作 教程","site:douyin.com/video/ 即梦 AI生图 工作流"]
SERVICES={
    "Bing public RSS":lambda q:"https://www.bing.com/search?"+urlencode({"q":q,"format":"rss"}),
    "Google News public RSS":lambda q:"https://news.google.com/rss/search?"+urlencode({"q":q,"hl":"zh-CN","gl":"CN","ceid":"CN:zh-Hans"}),
}
VIDEO=re.compile(r"https?://(?:www\.)?douyin\.com/video/(\d{15,22})")
def extract(text):
    if not isinstance(text,str):return []
    txt=unescape(unquote(text.replace("\\/","/")))
    return ["https://www.douyin.com/video/"+m for m in dict.fromkeys(VIDEO.findall(txt))]

def check(service,query):
    r={"source":service,"query":query,"status":"unverified","http":None,
       "rss_items":0,"direct_video_links":[],"notes":[]}
    try:
        req=Request(SERVICES[service](query),headers={"User-Agent":"Mozilla/5.0 (compatible; ResearchIndexSmokeTest/1.0)","Accept":"application/rss+xml, application/xml"})
        with urlopen(req,timeout=12) as res:
            r["http"]=res.status
            body=res.read(350000)
        # Parse only XML; a CAPTCHA/HTML body is not an RSS result.
        try:root=ET.fromstring(body)
        except ET.ParseError:
            r["status"]="non_rss_response_or_challenge";return r
        items=root.findall(".//item")
        r["rss_items"]=len(items)
        seen=set()
        for item in items[:30]:
            for child in item:
                if child.tag.lower() not in ("link","description","title","guid"):continue
                for url in extract(child.text):
                    if url not in seen:seen.add(url);r["direct_video_links"].append(url)
        r["status"]="direct_original_links" if seen else "no_direct_original_links"
    except HTTPError as e:
        r["http"]=e.code
        r["status"]="restricted_stop" if e.code in (401,403,429) else "http_error"
    except (URLError,TimeoutError,OSError,ValueError) as e:
        r["status"]="network_error";r["notes"]=[type(e).__name__]
    return r

def main():
    entries=[check(service,q) for service in SERVICES for q in QUERIES]
    unique=list(dict.fromkeys(u for e in entries for u in e["direct_video_links"]))
    data={"checked_utc":datetime.now(timezone.utc).isoformat(),
      "purpose":"evaluate two freely published RSS discovery surfaces only",
      "requests":len(entries),"entries":entries,
      "unique_original_douyin_video_candidates":unique[:20],
      "site_wide_search_verified":False,
      "native_keyword_search_verified":False,
      "full_reply_pagination_verified":False,
      "candidate_details_verified":False,
      "discovery_is_not_full_coverage":True}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"douyin_rss_discovery_smoke_test":{
       "cases":[{"source":e["source"],"query":e["query"],"status":e["status"],
         "http":e["http"],"rss_items":e["rss_items"],
         "direct_video_links":len(e["direct_video_links"])} for e in entries],
       "unique_direct_candidates":len(unique),"site_wide_search_verified":False
    }},ensure_ascii=False))
if __name__=="__main__":main()
