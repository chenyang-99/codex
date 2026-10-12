#!/usr/bin/env python3
"""Domestic public-content discovery and *actually retrieved* comment samples.

No login, cookies, paid API, challenge bypass, or attempts to read restricted
Xiaohongshu/Douyin comments. Public index search is NOT native platform search.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json, re, xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent/"output"
HEAD={"User-Agent":"Mozilla/5.0 (compatible; PublicTopicResearch/1.0)",
      "Accept":"application/rss+xml,application/json,application/xml,text/xml",
      "Referer":"https://www.bilibili.com/"}
TERMS=["AI 生图","ChatGPT 教程","AI 视频","豆包 提示词"]
DOMAINS={"xiaohongshu":["xiaohongshu.com/explore","xiaohongshu.com/discovery/item"],
         "douyin":["douyin.com/video"]}
MAX=1_800_000

def clean(s,n=480):
    if s is None:return ""
    return re.sub(r"\s+"," ",unescape(re.sub(r"<[^>]+>"," ",str(s)))).strip()[:n]

def grab(url,timeout=16):
    with urlopen(Request(url,headers=HEAD),timeout=timeout) as res:
        body=res.read(MAX)
        return res.status,body,res.geturl()

def try_json(url):
    status,b,real=grab(url)
    return json.loads(b),status,real

def indexed(site,term):
    # Search-engine indexed links, not direct site search. Can fail/rate-limit.
    query="site:"+DOMAINS[site][0]+" "+term
    url="https://www.bing.com/search?"+urlencode({"q":query,"format":"rss"})
    result={"source":"Bing RSS index","platform":site,"query":term,"status":"not_verified","posts":[]}
    try:
        code,content,landing=grab(url,timeout=18)
        root=ET.fromstring(content)
        items=[]
        for x in root.findall(".//item")[:12]:
            title=clean(x.findtext("title"),190)
            href=(x.findtext("link") or "").strip()
            desc=clean(x.findtext("description"),300)
            if title and href.startswith("https://") and (site=="xiaohongshu" and "xiaohongshu.com" in href or site=="douyin" and "douyin.com" in href):
                items.append({"platform":site,"title":title,"url":href[:600],"excerpt":desc,
                              "verified_scope":"indexed search snippet only","comments_status":"not_retrieved"})
        result.update(status="verified" if items else "empty_index_result",posts=items,
                      http_status=code)
    except (HTTPError,URLError,TimeoutError,ValueError,ET.ParseError,OSError) as e:
        result["error"]=type(e).__name__+": "+clean(e,150)
    return result

def v2ex():
    result={"source":"V2EX public API","platform":"v2ex","status":"not_verified",
            "posts":[],"comments":[]}
    endpoints=[("ai","https://www.v2ex.com/api/topics/show.json?node_name=ai"),
               ("chatgpt","https://www.v2ex.com/api/topics/show.json?node_name=chatgpt")]
    for node,url in endpoints:
        try:
            posts,status,_=try_json(url)
            if not isinstance(posts,list):raise ValueError("unexpected topic shape")
            for p in posts[:12]:
                if not isinstance(p,dict) or not p.get("id") or not p.get("title"):continue
                result["posts"].append({"platform":"v2ex","topic_id":p["id"],
                    "title":clean(p["title"],220),
                    "url":p.get("url") or f"https://www.v2ex.com/t/{p['id']}",
                    "reply_count_reported":p.get("replies"),
                    "created":p.get("created"),
                    "verified_scope":"public V2EX topic JSON"})
            result["status"]="verified" if result["posts"] else "empty"
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
            result.setdefault("errors",[]).append({"node":node,"error":type(e).__name__+": "+clean(e,100)})
    chosen=[p for p in result["posts"] if p.get("reply_count_reported",0)>0][:3]
    for p in chosen:
        url="https://www.v2ex.com/api/replies/show.json?"+urlencode({"topic_id":p["topic_id"],"page":1})
        try:
            rows,_,_=try_json(url)
            if not isinstance(rows,list):raise ValueError("unexpected reply shape")
            for c in rows[:12]:
                text=clean(c.get("content_rendered") or c.get("content"),450) if isinstance(c,dict) else ""
                if text:
                    result["comments"].append({"platform":"v2ex","topic_url":p["url"],
                                                "url":p["url"]+"#reply"+str(c.get("id","")),
                                                "text_excerpt":text,"reply_id":c.get("id"),
                                                "verified_scope":"actual public reply JSON"})
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
            result.setdefault("comments_errors",[]).append(type(e).__name__+": "+clean(e,100))
    result["post_count"]=len(result["posts"])
    result["comments_returned"]=len(result["comments"])
    return result

def bilibili():
    result={"source":"Bilibili public search/replies","platform":"bilibili",
            "status":"not_verified","posts":[],"comments":[]}
    search="https://api.bilibili.com/x/web-interface/search/type?"+urlencode({
        "search_type":"video","keyword":"AI生图","page":1,"page_size":10})
    try:
        obj,_,_=try_json(search)
        code=obj.get("code")
        if code!=0:
            result["status"]="platform_restricted"
            result["error"]="search returned API code "+str(code)+": "+clean(obj.get("message"),100)
        else:
            items=(obj.get("data") or {}).get("result") or []
            for p in items[:10]:
                aid=p.get("aid")
                if not aid:continue
                result["posts"].append({"platform":"bilibili","aid":aid,
                    "bvid":p.get("bvid"),"title":clean(p.get("title"),220),
                    "url":p.get("arcurl") or ("https://www.bilibili.com/video/"+str(p.get("bvid"))),
                    "description":clean(p.get("description"),250),
                    "verified_scope":"public Bilibili search result"})
            result["status"]="verified" if result["posts"] else "empty"
    except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
        result["error"]=type(e).__name__+": "+clean(e,150)
    if result["posts"]:
        for p in result["posts"][:3]:
            url="https://api.bilibili.com/x/v2/reply?"+urlencode({"type":1,"oid":p["aid"],"pn":1,"ps":10})
            try:
                obj,_,_=try_json(url)
                if obj.get("code")!=0:
                    result.setdefault("comment_errors",[]).append("API code "+str(obj.get("code")))
                    continue
                data=obj.get("data") or {}
                rows=data.get("replies") or []
                for x in rows[:8]:
                    if not isinstance(x,dict):continue
                    body=clean((x.get("content") or {}).get("message"),450)
                    if body:
                        result["comments"].append({"platform":"bilibili",
                            "url":p["url"]+"#reply"+str(x.get("rpid_str") or x.get("rpid") or ""),
                            "post_url":p["url"],"text_excerpt":body,
                            "likes":x.get("like"),"verified_scope":"actual public video reply"})
            except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
                result.setdefault("comment_errors",[]).append(type(e).__name__+": "+clean(e,100))
    result["post_count"]=len(result["posts"])
    result["comments_returned"]=len(result["comments"])
    return result

def main():
    tasks=[("bing_"+site+"_"+term,lambda s=site,t=term:indexed(s,t))
           for site in DOMAINS for term in TERMS[:3]]
    tasks += [("v2ex",v2ex),("bilibili",bilibili)]
    outputs={}
    with ThreadPoolExecutor(max_workers=5) as ex:
        future={ex.submit(fn):name for name,fn in tasks}
        for f in as_completed(future):
            name=future[f]
            try:outputs[name]=f.result()
            except Exception as e:outputs[name]={"source":name,"status":"error","error":type(e).__name__+": "+clean(e,100)}
    rows=[{"test":name,**outputs[name]} for name,_ in tasks]
    result={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
        "scope":"Index-only Xiaohongshu/Douyin discovery; real public comments from accessible CN forums",
        "tests":rows,
        "limitations":["Bing index hits are only public search snippets, not native platform search",
                       "Comment samples from V2EX/Bilibili cannot be described as Xiaohongshu/Douyin comments",
                       "No signed login-only APIs, CAPTCHAs or anti-bot circumvention."]}
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/"domestic-discovery.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Domestic public search and comment evidence","",result["checked_at_utc"],"",
      "| Source | Search or content | Notes | Comments |",
      "|---|---|---:|---:|"]
    for row in rows:
        lines.append(f"| {row.get('source','')} | {row.get('status')} | {len(row.get('posts',[]))} | {len(row.get('comments',[]))} |")
    lines+=["","**Limits:** Search-index snippets are not complete platform content. "
            "Actual V2EX/Bilibili comments are not Xiaohongshu or Douyin comments. "
            "If comments cannot be fetched, do not infer users made no comments."]
    (OUT/"domestic-discovery.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"status":"domestic_discovery_complete","sources":[{
        "name":r.get("source"),"platform":r.get("platform"),"status":r.get("status"),
        "posts":len(r.get("posts",[])),"comments":len(r.get("comments",[])),
        "error":r.get("error")} for r in rows]},ensure_ascii=False))
if __name__=="__main__":main()
