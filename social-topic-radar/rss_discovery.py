#!/usr/bin/env python3
"""No-login public RSS fallback: real article metadata, not social comments."""
import datetime as dt
import email.utils
import html
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

OUT=Path(__file__).resolve().parent/"output"
FEEDS={
 "OpenAI news":"https://openai.com/news/rss.xml",
 "Google AI blog":"https://blog.google/technology/ai/rss/",
 "GitHub blog":"https://github.blog/feed/",
}
NS={"atom":"http://www.w3.org/2005/Atom"}
MAX_SIZE=3_500_000
def clean(v,n=340):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",v or ""))).strip()[:n]
def atom_or_child_text(item,tag):
    if item.findtext(tag):return item.findtext(tag) or ""
    return item.findtext(f"atom:{tag}",namespaces=NS) or ""
def parse_date(d):
    if not d:return None
    try:return email.utils.parsedate_to_datetime(d).astimezone(dt.timezone.utc).isoformat()
    except (TypeError,ValueError):
        try:return dt.datetime.fromisoformat(d.replace("Z","+00:00")).isoformat()
        except ValueError:return None

def collect():
    rows=[];health=[]
    for name,url in FEEDS.items():
        try:
            req=Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; AnonymousTopicRadar/1.0)",
                                     "Accept":"application/rss+xml,application/atom+xml,application/xml,text/xml"})
            with urlopen(req,timeout=22) as resp:
                raw=resp.read(MAX_SIZE)
                http=resp.status
            root=ET.fromstring(raw)
            items=root.findall(".//item")
            if not items:
                items=root.findall(".//atom:entry",NS)
            added=0
            for item in items[:15]:
                title=clean(atom_or_child_text(item,"title"),180)
                link=atom_or_child_text(item,"link")
                if not link:
                    node=item.find("atom:link",NS)
                    link=node.get("href","") if node is not None else ""
                date=parse_date(atom_or_child_text(item,"pubDate") or atom_or_child_text(item,"published") or atom_or_child_text(item,"updated"))
                if not title or not link.startswith(("http://","https://")):continue
                rows.append(dict(source=name,title=title,url=link[:600],published_utc=date,
                                 excerpt=clean(atom_or_child_text(item,"description") or atom_or_child_text(item,"summary"),400),
                                 comments_status="not_provided_by_rss"))
                added+=1
            health.append(dict(source=name,status="verified" if added else "empty",http_status=http,items=added))
        except (HTTPError,URLError,OSError,ET.ParseError,TimeoutError) as e:
            health.append(dict(source=name,status="not_verified",error=f"{type(e).__name__}: {str(e)[:100]}"))
    seen=set();uni=[]
    for v in rows:
        if v["url"] not in seen:
            seen.add(v["url"]);uni.append(v)
    # This report is a source index, not a generated article, engagement feed or social sample.
    doc=dict(checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),source_health=health,
             count=len(uni),items=uni[:35],limitations=["RSS posts are not social posts or comments.",
             "Feeds may be delayed or incomplete; a missing story is not evidence of absence."])
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"public-rss-candidates.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8")
    md=["# Public RSS candidate sources","",f"Checked UTC: {doc['checked_at_utc']}","","## Sources"]
    for v in health:md.append(f"- {v['source']}: {v['status']} / {v.get('items',0)} items; {v.get('error','')}")
    md += ["","## Latest public source headlines"]
    for v in uni[:25]:md.extend([f"- [{v['title']}]({v['url']}) ({v['source']}, {v['published_utc'] or 'unknown publication time'})"])
    (OUT/"public-rss-candidates.md").write_text("\n".join(md),encoding="utf-8")
    print(json.dumps({"status":"rss_discovery_complete","sources":health,"items":len(uni)},ensure_ascii=False))
if __name__=="__main__":collect()
