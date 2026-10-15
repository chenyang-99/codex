#!/usr/bin/env python3
"""AICG original project discovery using only designated public entrypoints.

First-party Hub API + bounded, publicly exposed item links; no auth-gated scraping.
HTML landing accessibility alone is never counted as an original project.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit,urlunsplit,urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from pathlib import Path
import html
import json
import re

HERE=Path(__file__).resolve().parent
OUT=HERE/"output"
LIMIT=360000
UA="AICG-Topic-Research/1.0 (public metadata, no authentication)"
SRC=[
 {"name":"ComfyUI Workflows","root":"https://comfy.org/workflows/",
  "host":"comfy.org","path":r"^/workflows/[a-f0-9-]{12,}/?$","cap":7},
 {"name":"Runway Academy","root":"https://academy.runway.com/courses",
  "host":"academy.runway.com","path":r"^/courses/[^/]+/?$","cap":4},
 {"name":"Luma Learning Center","root":"https://lumalabs.ai/learning-center",
  "host":"lumalabs.ai","path":r"^/learning-center/[^/?#]+/?$","cap":4},
 {"name":"Replicate Collections","root":"https://replicate.com/collections",
  "host":"replicate.com","path":r"^/collections/[^/?#]+/?$","cap":4},
 {"name":"Recraft Blog","root":"https://www.recraft.ai/blog",
  "host":"www.recraft.ai","path":r"^/blog/[^/?#]+/?$","cap":4},
 {"name":"Google DeepMind Blog","root":"https://deepmind.google/blog/",
  "host":"deepmind.google","path":r"^/blog/[^/?#]+/?$","cap":4},
 {"name":"Black Forest Labs Blog","root":"https://bfl.ai/blog/",
  "host":"bfl.ai","path":r"^/blog/[^/?#]+/?$","cap":4},
 {"name":"Higgsfield Community","root":"https://higgsfield.ai/community",
  "host":"higgsfield.ai","path":r"^/community/(?!$)[a-z0-9/_-]+/?$","cap":3},
 {"name":"Krea Community Apps","root":"https://www.krea.ai/apps/community",
  "host":"www.krea.ai","path":r"^/apps/(?!community|background-remover)[a-z0-9/_-]+/?$","cap":3},
 {"name":"Runway AI Festival","root":"https://aif.runwayml.com/",
  "host":"aif.runwayml.com","path":r"^/(?:films|film|projects|winners)/[^/]+/?$","cap":3}
]

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title=""
        self._title=False
        self._a=None
        self._a_text=[]
        self.links=[]
        self.meta={}
        self.canonical=None
        self.headers=[]
        self._h=False
        self._htext=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="title":self._title=True
        if tag=="a" and a.get("href"):
            self._a=a.get("href");self._a_text=[]
        if tag in ("h1","h2"):
            self._h=True;self._htext=[]
        if tag=="meta":
            k=a.get("property") or a.get("name")
            if k:self.meta[k.lower()]=a.get("content","")
        if tag=="link" and a.get("rel")=="canonical":
            self.canonical=a.get("href")
    def handle_endtag(self,tag):
        if tag=="title":self._title=False
        if tag=="a" and self._a:
            self.links.append((self._a," ".join(self._a_text).strip()[:170]))
            self._a=None
            self._a_text=[]
        if tag in ("h1","h2") and self._h:
            self.headers.append(" ".join(self._htext).strip()[:260])
            self._h=False
    def handle_data(self,data):
        if self._title:self.title+=data
        if self._a is not None:self._a_text.append(data)
        if self._h:self._htext.append(data)

def fetch(url,timeout=13):
    req=Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,application/json"})
    with urlopen(req,timeout=timeout) as f:
        content=f.read(LIMIT)
        return f.status,f.geturl(),f.headers.get("content-type",""),content

def norm_url(s):
    parts=urlsplit(s)
    return urlunsplit((parts.scheme,parts.netloc,parts.path,"",""))

def item_date(raw,p):
    for k in ("article:published_time","datepublished","datecreated","citation_date"):
        v=p.meta.get(k)
        if v:return v[:40]
    for pattern in (r'"datePublished"\s*:\s*"([^"]+)"',r'"dateCreated"\s*:\s*"([^"]+)"'):
        m=re.search(pattern,raw[:LIMIT],flags=re.I)
        if m:return m.group(1)[:40]
    return None

def read_page(spec,url):
    code,final,ctype,contents=fetch(url)
    if code!=200 or "html" not in ctype.lower():
        return {"url":url,"status":"not_html","http_status":code},None
    raw=contents.decode("utf-8",errors="replace")
    p=Page()
    p.feed(raw)
    return {"url":url,"status":"metadata_read",
        "title":html.unescape(p.meta.get("og:title") or p.title).strip()[:260],
        "description":html.unescape(p.meta.get("og:description") or p.meta.get("description") or "").strip()[:700],
        "published_utc":item_date(raw,p),
        "preview_image":(p.meta.get("og:image") or "")[:1300],
        "creator":None,"source":spec["name"],
        "workflow_download_links":[],
        "prompt_status":"not_verified",
        "media_status":"preview_metadata_only",
        "evidence_level":"public_page_metadata_not_full_project",
        "source_kind":"original_project_page"},p

def check_site(spec):
    health={"source":spec["name"],"entrypoint":spec["root"],"status":"unverified"}
    try:
        entry,p=read_page(spec,spec["root"])
        if not p:
            health.update(status="entrypoint_not_html",error=entry["status"])
            return health,[]
        pattern=re.compile(spec["path"],re.I)
        links={}
        for raw,title in p.links:
            u=urljoin(spec["root"],html.unescape(raw))
            sp=urlsplit(u)
            if sp.scheme!="https" or sp.netloc.lower()!=spec["host"]:continue
            if not pattern.match(sp.path):continue
            links.setdefault(norm_url(u),title)
        health.update(status="item_links_found" if links else "landing_only",linked_items=len(links))
        selected=list(links.keys())[:spec["cap"]]
        items=[]
        for url in selected:
            try:
                item,detail=read_page(spec,url)
                if detail and item.get("title"):
                    item["title"]=item["title"] or links[url]
                    if spec["name"]=="ComfyUI Workflows":
                        downloads=[]
                        for href,_ in detail.links:
                            d=urljoin(url,href)
                            if re.match(r"^https://comfy\.org/workflows/download/[a-z0-9-]+\.json",d):
                                if d not in downloads:downloads.append(d)
                        item["workflow_download_links"]=downloads[:3]
                        if downloads:item["evidence_level"]="official_downloadable_workflow_link_verified"
                    items.append(item)
            except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
                continue
        health["detail_items"]=len(items)
        return health,items
    except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
        health.update(status="access_unavailable",error=f"{type(e).__name__}: {str(e)[:100]}")
        return health,[]

def hf_discovery():
    health={"source":"Hugging Face Hub API","status":"unverified"}
    datasets=[
      ("spaces","https://huggingface.co/api/spaces?sort=createdAt&direction=-1&limit=100"),
      ("image-to-video models","https://huggingface.co/api/models?pipeline_tag=image-to-video&sort=lastModified&direction=-1&limit=40"),
      ("text-to-image models","https://huggingface.co/api/models?pipeline_tag=text-to-image&sort=lastModified&direction=-1&limit=40")]
    items=[]
    signals=("image","photo","video","visual","comfy","flux","wan","cinema","3d","seedance","anime","draw","portrait","motion","edit","control","recraft","kling","text-to","diffusion","banana")
    errors=[]
    for typ,url in datasets:
        try:
            code,final,ctype,content=fetch(url,timeout=15)
            data=json.loads(content.decode("utf-8"))
            if not isinstance(data,list):
                errors.append(typ+": unexpected_response");continue
            count=0
            for x in data:
                if not isinstance(x,dict):continue
                name=x.get("id") or x.get("modelId")
                if not name or "/" not in name:continue
                keywords=" ".join([str(name)]+[str(y) for y in x.get("tags",[])])
                if typ=="spaces" and not any(k in keywords.lower() for k in signals):continue
                if x.get("private"):continue
                dest="https://huggingface.co/"+("spaces/" if typ=="spaces" else "")+name
                items.append({"source":"Hugging Face API","source_kind":typ,
                    "url":dest,"title":name,"creator":name.split("/")[0],
                    "published_utc":x.get("createdAt"),
                    "updated_utc":x.get("lastModified"),
                    "likes_reported":x.get("likes"),
                    "tags":x.get("tags",[])[:15],
                    "description":(x.get("cardData") or {}).get("description","")[:400] if isinstance(x.get("cardData"),dict) else "",
                    "preview_image":"","workflow_download_links":[],
                    "prompt_status":"not_verified","media_status":"not_requested",
                    "evidence_level":"first_party_public_hub_api_metadata",
                    "note":"modified date is not original publication date"})
                count+=1
                if count>=12:break
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
            errors.append(typ+": "+type(e).__name__)
    health.update(status="items_retrieved" if items else "source_unavailable",
                  items=len(items),errors=errors)
    return health,items

def main():
    with ThreadPoolExecutor(max_workers=5) as pool:
        batches=list(pool.map(check_site,SRC))
    hf_health,hf_items=hf_discovery()
    health=[x[0] for x in batches]+[hf_health]
    all_items=[item for x in batches for item in x[1]]+hf_items
    seen=set()
    all_items=[i for i in all_items if not(i["url"] in seen or seen.add(i["url"]))]
    report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
        "scope":"Whitelisted public detail pages and Hugging Face official APIs",
        "configured_site_targets":18,
        "sites_attempted_for_item_discovery":len(SRC),
        "individual_item_links":len(all_items),
        "comfy_downloadable_workflows":sum(bool(p.get("workflow_download_links")) for p in all_items),
        "source_health":health,
        "items":all_items,
        "blocked_or_manual_only":["Midjourney Explore: no unauthorized automation per Midjourney terms",
          "Behance AI Advertising: automated requests were HTTP403",
          "Ideogram: automated requests were HTTP403"],
        "limitations":["Not a complete crawl of any platform; detail pages sampled only",
          "Landing pages without public item links do not count as content",
          "Prompt, downloads, author identity, image/video bytes and rights only verified where explicitly returned",
          "Hugging Face modified time differs from release/publication time",
          "No credentials, login bypass or browser stealth"]}
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/"aicg-original-site-items.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# AICG public original project discovery",
      "UTC "+report["checked_at_utc"],
      "Items "+str(len(all_items))+", downloadable workflow links "+str(report["comfy_downloadable_workflows"]),"",
      "## source health"]
    lines +=[f"- {h['source']}: {h['status']}, individual detail pages {h.get('detail_items',0)}" for h in health]
    lines+=["","## original project links"]
    for item in all_items[:55]:
        lines+=["- "+item["title"]+" — "+item["url"]+"; original published: "+str(item.get("published_utc") or "unknown")+"; evidence: "+item["evidence_level"]]
        if item.get("workflow_download_links"):
            lines+=["  - workflow JSON: "+item["workflow_download_links"][0]]
    (OUT/"aicg-original-site-items.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("configured_site_targets","sites_attempted_for_item_discovery","individual_item_links","comfy_downloadable_workflows")},ensure_ascii=False))

if __name__=="__main__":
    main()
