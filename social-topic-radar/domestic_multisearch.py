#!/usr/bin/env python3
"""Test independent, publicly accessible web indexes for two domestic platforms.

Index hits are DISCOVERY snippets only. Never use them as evidence that we
read the platform's video/note body or all comments.
Stops on 403, 429 and CAPTCHA/challenge responses; no proxies or bypass.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode,urlsplit,urlunsplit
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import json,re,xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
OUT=HERE/"output"
HOSTS={
 "douyin":("douyin.com",),
 "xiaohongshu":("xiaohongshu.com",)
}
TERMS=("AI生图 教程", "AI视频 提示词")
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; PublicResearch/1.0)",
         "Accept":"text/html,application/xhtml+xml,application/rss+xml,application/xml"}
MAX_BYTES=700_000

def clean(txt,n=250):
    return re.sub(r"\s+"," ",unescape(re.sub(r"<[^>]+>"," ",str(txt or "")))).strip()[:n]

def platform_of_url(url):
    host=(urlsplit(url).hostname or "").lower()
    for platform,hosts in HOSTS.items():
        if any(host==x or host.endswith("."+x) for x in hosts):
            return platform
    return None

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.href=None
        self.chunks=[]
        self.level=0
    def handle_starttag(self,tag,attrs):
        if tag=="a" and self.href is None:
            attrs=dict(attrs)
            href=attrs.get("href")
            if href and href.startswith(("https://","http://")):
                self.href=href; self.chunks=[]
        elif tag=="a" and self.href is not None:
            self.level+=1
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:
            if self.level>0:self.level-=1
            else:
                name=clean("".join(self.chunks),200)
                if name:self.links.append((self.href,name))
                self.href=None;self.chunks=[]
    def handle_data(self,data):
        if self.href is not None:self.chunks.append(data)

def fetch(provider,platform,term):
    query=f"site:{HOSTS[platform][0]} {term}"
    encoded=urlencode({"q":query})
    if provider=="GoogleNewsRSS":
        url="https://news.google.com/rss/search?"+urlencode({"q":query,"hl":"zh-CN","gl":"CN","ceid":"CN:zh-Hans"})
    elif provider=="DuckDuckGoHTML":
        url="https://html.duckduckgo.com/html/?"+encoded
    elif provider=="Mojeek":
        url="https://www.mojeek.com/search?"+encoded
    elif provider=="Sogou":
        url="https://www.sogou.com/web?"+urlencode({"query":query})
    else:raise ValueError("Unknown provider")
    o={"provider":provider,"platform":platform,"query":query,
       "status":"not_verified","source_url":url,"indexed_links":[]}
    try:
        with urlopen(Request(url,headers=HEADERS),timeout=12) as res:
            code=res.status
            raw=res.read(MAX_BYTES)
            final=res.geturl()
        text=raw.decode("utf-8",errors="replace")
        if any(s in text[:15000].lower() for s in ("captcha","机器人验证","安全验证","访问过于频繁","请输入验证码")):
            o.update(status="blocked",note="Index provider returned a challenge; no bypass attempted.")
            return o
        if provider=="GoogleNewsRSS":
            root=ET.fromstring(raw)
            links=[]
            for el in root.findall(".//item")[:25]:
                title=clean(el.findtext("title"),180)
                link=el.findtext("link") or ""
                if platform_of_url(link)==platform:
                    links.append({"url":link,"title":title,"evidence":"index_title_only"})
        else:
            p=Links();p.feed(text)
            links=[{"url":href,"title":title,"evidence":"index_title_only"}
                   for href,title in p.links if platform_of_url(href)==platform]
        seen=set()
        links=[x for x in links if not(x["url"] in seen or seen.add(x["url"]))]
        o.update(http_status=code,status="verified_links" if links else "zero_indexed_links",
                 indexed_links=links[:10],links_count=len(links),
                 note="Search-index links, not actual platform-native search/comments.")
    except HTTPError as exc:
        o.update(status="blocked" if exc.code in (401,403,429) else "error",
                 http_status=exc.code,error="HTTP "+str(exc.code))
    except (URLError,TimeoutError,ET.ParseError,ValueError,OSError) as exc:
        o.update(status="error",error=type(exc).__name__+": "+clean(exc,100))
    return o

def main():
    tasks=[(p,s,t) for p in ("GoogleNewsRSS","DuckDuckGoHTML","Mojeek","Sogou")
                  for s in HOSTS for t in TERMS]
    records=[None]*len(tasks)
    with ThreadPoolExecutor(max_workers=4) as ex:
        jobs={ex.submit(fetch,*t):i for i,t in enumerate(tasks)}
        for f in as_completed(jobs):
            records[jobs[f]]=f.result()
    good=[x for r in records for x in r["indexed_links"]]
    unique={}
    for x in good:unique.setdefault(x["url"],x)
    summary={"checked_utc":datetime.now(timezone.utc).isoformat(),
       "source_types":"public index results, NOT platform API, NOT comment-tree data",
       "tests":records,"unique_indexed_urls":list(unique.values()),
       "verified_sources":sorted({r["provider"] for r in records if r["status"]=="verified_links"})}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"domestic-multisearch.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    md=["# Domestic independent search-index smoke tests",
        f"Checked UTC: {summary['checked_utc']}","",
        "**Links/snippets are discovery evidence, NOT proof of native platform search or comments.**","",
        "| Index | Platform | Status | Indexed links |","|---|---|---|---:|"]
    for r in records:md.append(f"| {r['provider']} | {r['platform']} | {r['status']} | {len(r['indexed_links'])} |")
    md+=["","## Actually indexed individual links"]
    for x in list(unique.values())[:25]:
        md.append(f"- [{x['title']}]({x['url']})")
    if not unique:md.append("No direct platform links verified in this run.")
    (OUT/"domestic-multisearch.md").write_text("\n".join(md),encoding="utf-8")
    print(json.dumps({"status":"domestic_multisearch_complete",
       "tests":len(records),"indexed_links":len(unique),
       "verified_search_providers":summary["verified_sources"],
       "blocked_tests":sum(r["status"]=="blocked" for r in records)},ensure_ascii=False))

if __name__=="__main__":main()
