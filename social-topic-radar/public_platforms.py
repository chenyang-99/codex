#!/usr/bin/env python3
"""Public-platform capability tests: no platform account/cookies/paid API.

This module performs a small number of read-only requests; it never attempts
restricted endpoints, CAPTCHA bypasses, or Reddit's OAuth-requiring Data API.
"""
import datetime as dt
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent / "output"
HEADERS = {"User-Agent": "OpenAIResearchExample/0.1 (anonymous public-source health check)",
           "Accept": "application/json,application/atom+xml,text/html"}
MAX_BYTES = 1_000_000

def load(url, timeout=16):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as r:
        return r.status, r.read(MAX_BYTES), r.geturl()

def cleaned(s, n=450):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()[:n]

def result(name, surface, *, status="not_verified", count=0, comments=0, sample=None, error=None, url=None, note=None):
    o = dict(platform=name, surface=surface, status=status,
             records_returned=count, comment_records_returned=comments)
    if sample is not None: o["sample"] = sample
    if error is not None: o["error"] = cleaned(str(error), 150)
    if url is not None: o["source_url"] = url
    if note is not None: o["note"] = note
    return o

def test_hn():
    name="Hacker News"
    origin="https://hacker-news.firebaseio.com/v0/topstories.json"
    try:
        status, data, _ = load(origin)
        ids = json.loads(data)
        if status != 200 or not isinstance(ids, list) or not ids:
            return result(name,"official API stories and comments",url=origin,note="No actual stories verified.")
        sample = []
        comments = []
        for iid in ids[:5]:
            _, body, _ = load(f"https://hacker-news.firebaseio.com/v0/item/{iid}.json")
            item = json.loads(body)
            if not isinstance(item,dict) or not item.get("title"): continue
            sample.append(dict(id=item.get("id"),title=cleaned(item.get("title"),170),
                               url=item.get("url") or f"https://news.ycombinator.com/item?id={iid}",
                               posted_at=item.get("time"),comment_count=item.get("descendants")))
            for cid in (item.get("kids") or [])[:2]:
                _, cb, _ = load(f"https://hacker-news.firebaseio.com/v0/item/{cid}.json")
                co=json.loads(cb)
                if isinstance(co,dict) and co.get("type")=="comment" and co.get("text") and not co.get("deleted"):
                    comments.append(dict(id=cid, url=f"https://news.ycombinator.com/item?id={cid}",
                                         excerpt=cleaned(co.get("text"))))
            if comments: break
        return result(name,"official API stories and comments",status="verified" if sample else "empty",
                      count=len(sample),comments=len(comments),
                      sample={"posts":sample[:5],"comments":comments[:3]},url=origin,
                      note="Samples only; no claim of exhaustive story/comment coverage.")
    except (HTTPError,URLError,TimeoutError,ValueError,ET.ParseError,OSError) as e:
        return result(name,"official API stories and comments",url=origin,error=e)

def test_github():
    name="GitHub"
    origin="https://api.github.com/repos/ollama/ollama/issues?state=open&per_page=15"
    try:
        _, b, _ = load(origin)
        issues=json.loads(b)
        if not isinstance(issues,list):raise ValueError("unexpected response")
        posts=[]
        comments=[]
        for i in issues:
            if not isinstance(i,dict) or "pull_request" in i:continue
            posts.append(dict(url=i.get("html_url"),title=cleaned(i.get("title"),175),
                              comments_reported=i.get("comments"),created_at=i.get("created_at")))
            if i.get("comments",0)>0 and len(comments)==0:
                _,cb,_=load(i["comments_url"]+"?per_page=3")
                c=json.loads(cb)
                if isinstance(c,list):
                    comments=[dict(url=x.get("html_url"),excerpt=cleaned(x.get("body")))
                              for x in c if isinstance(x,dict) and x.get("body")][:3]
            if len(posts)>=5 and comments:break
        return result(name,"public issues and issue comments",
                      status="verified" if posts else "empty",count=len(posts),comments=len(comments),
                      sample={"issues":posts[:5],"comments":comments},url=origin,
                      note="Repository issue sample; unauthenticated API has its own rate limits.")
    except (HTTPError,URLError,TimeoutError,ValueError,OSError,KeyError) as e:
        return result(name,"public issues and issue comments",url=origin,error=e)

def test_youtube():
    name="YouTube"
    url="https://www.youtube.com/feeds/videos.xml?channel_id=UCBR8-60-B28hp2BmDPdntcQ"
    try:
        status,b,_=load(url)
        root=ET.fromstring(b)
        ns={"a":"http://www.w3.org/2005/Atom"}
        entries=root.findall("a:entry",ns)
        sample=[]
        for e in entries[:6]:
            title=e.findtext("a:title",default="",namespaces=ns)
            link=e.find("a:link",ns)
            sample.append({"title":cleaned(title,200),"url":link.get("href") if link is not None else None,
                          "published":e.findtext("a:published",default=None,namespaces=ns)})
        return result(name,"public channel uploads Atom feed",status="verified" if sample else "empty",
                      count=len(sample),comments=0,sample=sample,url=url,
                      note="Video upload metadata only. Comments/transcripts are not included in this feed.")
    except (HTTPError,URLError,TimeoutError,ValueError,ET.ParseError,OSError) as e:
        return result(name,"public channel uploads Atom feed",url=url,error=e)

def test_v2ex():
    name="V2EX"
    url="https://www.v2ex.com/api/topics/hot.json"
    try:
        status,b,_=load(url)
        j=json.loads(b)
        if not isinstance(j,list): raise ValueError("unexpected shape")
        entries=[{"title":cleaned(x.get("title"),140),"url":x.get("url"),
                  "replies_reported":x.get("replies")} for x in j[:6] if isinstance(x,dict)]
        return result(name,"public hot topics API",status="verified" if entries else "empty",
                      count=len(entries),comments=0,sample=entries,url=url,
                      note="Reply counts only; no individual replies fetched.")
    except (HTTPError,URLError,TimeoutError,ValueError,OSError) as e:
        return result(name,"public hot topics API",url=url,error=e)

class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.intitle=False
        self.title=""
    def handle_starttag(self,tag,attrs):
        if tag=="title":self.intitle=True
    def handle_endtag(self,tag):
        if tag=="title":self.intitle=False
    def handle_data(self,data):
        if self.intitle:self.title+=data[:260]

def test_reddit():
    name="Reddit"
    url="https://www.reddit.com/r/LocalLLaMA/"
    try:
        status,b,final=load(url)
        p=TitleParser()
        p.feed(b.decode("utf-8",errors="replace"))
        title=cleaned(p.title,240)
        valid=("reddit.com" in final and status==200 and title and
               "login" not in title.lower() and "blocked" not in title.lower())
        return result(name,"single public HTML page only",status="partial" if valid else "not_verified",
                      count=0,comments=0,sample={"page_title":title},url=url,
                      note=("Accessible HTML page, but posts/comments were NOT structurally verified."
                            if valid else "Page returned but platform content wasn't verified. "
                            "No OAuth-requiring Reddit Data API endpoint was called."))
    except (HTTPError,URLError,TimeoutError,ValueError,OSError) as e:
        return result(name,"single public HTML page only",url=url,error=e,
                      note="Reddit Data API requires OAuth and provider-IP access may be restricted.")

def main():
    tests=[test_hn,test_github,test_youtube,test_v2ex,test_reddit]
    rows=[]
    for fn in tests:
        try:rows.append(fn())
        except Exception as e:
            rows.append(result(fn.__name__,"probe",error=f"{type(e).__name__}: {str(e)[:140]}"))
    report=dict(checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                anonymous=True,no_platform_cookie=True,paid_api=False,
                scope="Public-data capability smoke test only; never full platform coverage.",
                results=rows)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"public-platforms.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Other Public Platform Verification",f"UTC: {report['checked_at_utc']}","",
           "| Platform | Surface | Access | Actual posts | Actual comments |",
           "|---|---|---|---:|---:|"]
    for x in rows:
        lines.append(f"| {x['platform']} | {x['surface']} | {x['status']} | {x['records_returned']} | {x['comment_records_returned']} |")
    lines+=["","## Notes"]
    for x in rows:lines.append(f"- {x['platform']}: {x.get('note','')} {x.get('error','')}")
    (OUT/"public-platforms.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"status":"public_platform_probe_complete",
                      "results":[{"platform":x["platform"],"status":x["status"],
                                  "records":x["records_returned"],
                                  "comments":x["comment_records_returned"],
                                  "error":x.get("error")} for x in rows]},ensure_ascii=False))
if __name__=="__main__":main()
