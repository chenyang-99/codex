#!/usr/bin/env python3
"""Low-rate, credential-free public search-index discovery of Douyin AI videos.

Tests ordinary visible search links on three independent search engines.
Search-engine results are only candidates; DO NOT pretend this is native
Douyin search or that an indexed URL still resolves to its original content.
Stop on CAPTCHA, login wall, or HTTP restrictions.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode,urlsplit,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import json,re

OUT=Path(__file__).resolve().parent/"output"/"douyin-public-index-validation.json"
WORDS=("AI生图 教程","AI漫剧 工作流")
ENGINES={
    "Baidu":lambda q:"https://www.baidu.com/s?"+urlencode({"wd":q}),
    "Yahoo":lambda q:"https://search.yahoo.com/search?"+urlencode({"p":q}),
    "360Search":lambda q:"https://www.so.com/s?"+urlencode({"q":q}),
}
UA="Mozilla/5.0 (compatible; PublicResearchIndex/1.0)"

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()!="a":return
        href=dict(attrs).get("href") or ""
        self.links.append(href)

def canonical(href):
    href=unescape(href).replace("\\/","/")
    if href.startswith("//"):href="https:"+href
    if href.startswith("https%3A"):href=unquote(href)
    try:
        p=urlsplit(href)
        host=(p.hostname or "").lower()
        if host not in ("douyin.com","www.douyin.com","v.douyin.com"):return None
        if not re.fullmatch(r"/video/\d{15,22}",p.path):return None
        return "https://www.douyin.com"+p.path
    except ValueError:return None

def check(engine,kw):
    q="site:douyin.com/video/ "+kw
    result={"engine":engine,"keyword":kw,"status":"not_verified","videos":[]}
    try:
        req=Request(ENGINES[engine](q),headers={"User-Agent":UA,"Accept":"text/html"})
        with urlopen(req,timeout=14) as r:
            html=r.read(650000).decode("utf-8",errors="replace")
            result["http"]=r.status
        if any(p in html[:25000].lower() for p in ("captcha","请输入验证码","安全验证","访问过于频繁")):
            result["status"]="challenge";return result
        parser=Links();parser.feed(html)
        seen=set()
        for link in parser.links:
            url=canonical(link)
            if not url or url in seen:continue
            seen.add(url);result["videos"].append(url)
        result["link_count"]=len(result["videos"])
        result["status"]="direct_indexed_video_links" if seen else "none_verified"
    except HTTPError as exc:
        result["http"]=exc.code
        result["status"]="access_restricted" if exc.code in (401,403,429) else "http_error"
    except (URLError,TimeoutError,OSError,ValueError) as exc:
        result["status"]="error";result["error"]=type(exc).__name__
    return result

def main():
    todo=[(e,k) for e in ENGINES for k in WORDS]
    with ThreadPoolExecutor(max_workers=3) as p:
        futs={p.submit(check,*t):i for i,t in enumerate(todo)}
        res=[None]*len(todo)
        for f in as_completed(futs):res[futs[f]]=f.result()
    unique={}
    for record in res:
        for url in record["videos"]:
            unique.setdefault(url,{"url":url,"source_engines":[],"discovery_only":True})["source_engines"].append(record["engine"])
    report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
       "method":"ordinary public search engine HTML anchor links",
       "entries":res,"unique_douyin_video_candidate_count":len(unique),
       "candidates":list(unique.values())[:30],
       "native_douyin_search":False,"original_video_details_verified":False,
       "comments_verified":False,"limitations":[
           "No search index is equivalent to Douyin's internal search/rank.",
           "Do not treat results as video content or comment evidence.",
           "Engine access restrictions or no href results are recorded as such."]}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"douyin_public_search_index_test":{
        "cases":len(res),"results":[{"engine":x["engine"],"keyword":x["keyword"],
        "status":x["status"],"links":len(x["videos"])} for x in res],
        "unique_candidate_count":len(unique)}},ensure_ascii=False))
if __name__=="__main__":main()
