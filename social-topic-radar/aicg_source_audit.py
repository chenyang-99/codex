#!/usr/bin/env python3
"""Read-only AICG access smoke test. One page or bounded X timeline != full corpus."""
import concurrent.futures as cf
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser

ROOT=pathlib.Path(__file__).resolve().parent
DATA=json.loads((ROOT/"aicg-sources.json").read_text(encoding="utf-8"))
OUTPUT=ROOT/"output"
UPSTREAM=ROOT/"x_upstream.py"

class PageTitle(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title=""
        self.active=False
    def handle_starttag(self,tag,attrs):
        if tag=="title": self.active=True
    def handle_endtag(self,tag):
        if tag=="title": self.active=False
    def handle_data(self,s):
        if self.active:self.title+=s

def probe_x(handle):
    result={"handle":handle,"status":"not_verified","returned":0,
            "method":"pinned upstream X-Aggregate-Data public timeline; 7-day sample"}
    if not UPSTREAM.is_file():
        result["error"]="x_upstream_missing"
        return result
    try:
        p=subprocess.run([sys.executable,str(UPSTREAM),"tweets",handle,"--limit","4","--since","7d"],
                         capture_output=True,text=True,timeout=16)
        j=json.loads(p.stdout.strip() or "{}")
        if p.returncode or not isinstance(j,dict) or j.get("error"):
            result["error"]=str(j.get("error") or p.stderr or "upstream_exit")[:150]
            return result
        tweets=[t for t in j.get("tweets",[]) if isinstance(t,dict) and t.get("id") and t.get("text")]
        result["status"]="verified_sample" if tweets else "empty_or_unavailable"
        result["returned"]=len(tweets)
        result["samples"]=[{"id":str(t.get("id")),"url":t.get("url"),"created_at":t.get("created_at"),
                            "text_excerpt":str(t.get("text",""))[:280]} for t in tweets[:2]]
    except (OSError,ValueError,subprocess.TimeoutExpired) as e:
        result["error"]=type(e).__name__
    return result

def probe_site(site):
    result={"name":site["name"],"url":site["url"],"status":"not_verified",
            "method":"single public landing-page GET; not gallery pagination, prompts, or all works"}
    try:
        req=Request(site["url"],headers={"User-Agent":"Mozilla/5.0 (AICG Source Audit/1.0)",
                   "Accept":"text/html,application/xhtml+xml,application/xml"})
        with urlopen(req,timeout=11) as f:
            code=f.status
            final=f.geturl()
            body=f.read(240000)
        html=body.decode("utf-8",errors="replace")
        parser=PageTitle()
        parser.feed(html)
        title=re.sub(r"\s+"," ",parser.title).strip()[:130]
        challenged=bool(re.search(r"captcha|verify you are human|access denied|cf-challenge",html[:40000],re.I))
        result.update(http_status=code,final_url=final,title=title,bytes_sampled=len(body),
                      status="challenge" if challenged else "landing_accessible_only" if code==200 and title else "partial_html")
    except HTTPError as e:
        result.update(status="http_error",http_status=e.code,error=f"HTTP {e.code}")
    except (URLError,TimeoutError,OSError,ValueError) as e:
        result.update(status="connection_error",error=f"{type(e).__name__}: {str(e)[:110]}")
    return result

def main():
    OUTPUT.mkdir(exist_ok=True)
    with cf.ThreadPoolExecutor(max_workers=5) as pool:
        x_results=list(pool.map(probe_x,DATA["x_handles"]))
    with cf.ThreadPoolExecutor(max_workers=7) as pool:
        site_results=list(pool.map(probe_site,DATA["sites"]))
    verdict={"checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "access_audit_only":True,"x_targets":len(x_results),
       "x_samples_returned":sum(z["returned"] for z in x_results),
       "x_handles_with_posts":sum(z["status"]=="verified_sample" for z in x_results),
       "site_targets":len(site_results),
       "site_landing_pages_accessible":sum(z["status"]=="landing_accessible_only" for z in site_results),
       "x":x_results,"sites":site_results,
       "limitations":["Returned samples never imply all posts/media/replies accessible.",
          "HTTP 200 only proves a landing page responded, not gallery item or prompt access.",
          "No logins, cookies, paid APIs, pagination or policy bypass used.",
          "23 distinct non-X sources were not provided; 18 documented sources tested."]}
    (OUTPUT/"aicg-source-audit.json").write_text(json.dumps(verdict,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# AICG first-party source capability audit","",
       f"UTC {verdict['checked_at_utc']}",
       f"X handles with readable 7-day post samples: {verdict['x_handles_with_posts']}/{len(x_results)}",
       f"Non-X landing pages returned HTML title: {verdict['site_landing_pages_accessible']}/{len(site_results)}",
       "","## X creator samples"]
    for x in x_results:
        lines.append(f"- @{x['handle']}: {x['status']}, rows={x['returned']} {x.get('error','')}")
    lines+=["","## Non-X site entrypoints"]
    for s in site_results:
        lines.append(f"- {s['name']}: {s['status']}, HTTP {s.get('http_status','?')} {s.get('error','')}")
    lines+=["","No claims of complete tweet histories, media, source galleries, prompts, comments, or publishable ideas are made."]
    (OUTPUT/"aicg-source-audit.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({k:verdict[k] for k in ("x_targets","x_samples_returned","x_handles_with_posts","site_targets","site_landing_pages_accessible")}))
if __name__=="__main__":
    main()
