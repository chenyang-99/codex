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
    # Index snippets from a normal public search results feed.
    # This is NOT platform-native search or a guaranteed complete index.
    queries=[
        "site:"+DOMAINS[site][0]+" "+term,
        "site:"+("xiaohongshu.com" if site=="xiaohongshu" else "douyin.com")+" "+term,
    ]
    result={"source":"Bing RSS index","platform":site,"query":term,
            "status":"not_verified","posts":[],"attempts":[]}
    for query in queries:
        url="https://www.bing.com/search?"+urlencode({"q":query,"format":"rss"})
        try:
            status,content,landing=grab(url,timeout=14)
            root=ET.fromstring(content)
            items=[]
            for x in root.findall(".//item")[:16]:
                title=clean(x.findtext("title"),190)
                href=(x.findtext("link") or "").strip()
                desc=clean(x.findtext("description"),300)
                host=(urlsplit(href).hostname or "").lower()
                valid=(host=="xiaohongshu.com" or host.endswith(".xiaohongshu.com")) if site=="xiaohongshu" else (host=="douyin.com" or host.endswith(".douyin.com"))
                if title and href.startswith("https://") and valid:
                    items.append({"platform":site,"title":title,"url":href[:600],
                                  "excerpt":desc,"verified_scope":"search engine indexed snippet, NOT native platform search",
                                  "comments_status":"not_retrieved"})
            result["attempts"].append({"query":query,"http_status":status,"returned_valid_domain":len(items)})
            if items:
                result.update(status="verified",posts=items)
                break
            result["status"]="empty_index_result"
        except (HTTPError,URLError,TimeoutError,ValueError,ET.ParseError,OSError) as e:
            result["attempts"].append({"query":query,"error":type(e).__name__+": "+clean(e,120)})
            result["status"]="not_verified" if not result["posts"] else result["status"]
    return result

def v2ex():
    result={"source":"V2EX public hot/latest topic API","platform":"v2ex",
            "status":"not_verified","posts":[],"comments":[]}
    # Legacy node-scoped V1 endpoint now returns 404; V2 node API requires PAT.
    # Only use public hot/latest endpoints and filter actually relevant posts.
    terms=("ai","gpt","chatgpt","大模型","生图","ai视频","豆包","提示词","comfyui","sora")
    seen=set()
    for label,url in [("hot","https://www.v2ex.com/api/topics/hot.json"),
                      ("latest","https://www.v2ex.com/api/topics/latest.json")]:
        try:
            posts,status,_=try_json(url)
            if not isinstance(posts,list):raise ValueError("unexpected topic shape")
            for p in posts[:40]:
                if not isinstance(p,dict) or not p.get("id") or not p.get("title"):continue
                title=clean(p["title"],220)
                if p["id"] in seen or not any(t in title.lower() for t in terms):continue
                seen.add(p["id"])
                result["posts"].append({"platform":"v2ex","topic_id":p["id"],
                    "title":title,"url":p.get("url") or f"https://www.v2ex.com/t/{p['id']}",
                    "reply_count_reported":p.get("replies"),"created":p.get("created"),
                    "verified_scope":"public V2EX topic JSON"})
            result["status"]="verified" if result["posts"] else "empty"
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
            result.setdefault("errors",[]).append({"source":label,"error":type(e).__name__+": "+clean(e,100)})
    for p in [p for p in result["posts"] if p.get("reply_count_reported",0)>0][:2]:
        url="https://www.v2ex.com/api/replies/show.json?"+urlencode({"topic_id":p["topic_id"]})
        try:
            rows,_,_=try_json(url)
            if not isinstance(rows,list):raise ValueError("unexpected reply shape")
            for v in rows[:12]:
                content=clean(v.get("content_rendered") or v.get("content"),450) if isinstance(v,dict) else ""
                if content:
                    result["comments"].append({"platform":"v2ex","topic_url":p["url"],
                                               "url":p["url"]+"#reply"+str(v.get("id","")),
                                               "text_excerpt":content,"reply_id":v.get("id"),
                                               "verified_scope":"actual public reply JSON"})
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
            result.setdefault("comment_errors",[]).append(type(e).__name__+": "+clean(e,100))
    result["post_count"]=len(result["posts"])
    result["comments_returned"]=len(result["comments"])
    return result

def bilibili():
    result={"source":"Bilibili public search/replies","platform":"bilibili",
            "status":"not_verified","posts":[],"comments":[]}
    # Multiple consumer-AI topic areas; bounded to 3 searches / 9 comment pages.
    terms=("AI生图","AI视频生成","ChatGPT教程")
    seen=set()
    targets=[]
    for term in terms:
        search="https://api.bilibili.com/x/web-interface/search/type?"+urlencode({
            "search_type":"video","keyword":term,"page":1,"page_size":10})
        try:
            obj,_,_=try_json(search)
            if obj.get("code")!=0:
                result.setdefault("search_errors",[]).append({"query":term,
                    "api_code":obj.get("code"),"note":clean(obj.get("message"),100)})
                continue
            items=(obj.get("data") or {}).get("result") or []
            candidates=[]
            for p in items[:10]:
                aid=p.get("aid")
                if not aid or str(aid) in seen:continue
                seen.add(str(aid))
                entry={"platform":"bilibili","aid":aid,"bvid":p.get("bvid"),
                       "search_query":term,"title":clean(p.get("title"),220),
                       "url":p.get("arcurl") or ("https://www.bilibili.com/video/"+str(p.get("bvid"))),
                       "description":clean(p.get("description"),250),
                       "verified_scope":"public Bilibili search result"}
                result["posts"].append(entry)
                candidates.append(entry)
            targets += candidates[:3]
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
            result.setdefault("search_errors",[]).append({"query":term,
                         "error":type(e).__name__+": "+clean(e,100)})
            if isinstance(e,HTTPError) and e.code in (403,412,429):
                result["restriction_detected"]=True
                break  # stop further search; never evade platform access restrictions
    # Fallback uses previously verified public video IDs; do not mislabel as live search.
    try:
        seeds=json.loads((Path(__file__).resolve().parent/"bilibili_seeds.json").read_text(encoding="utf-8"))
        existing={str(x.get("aid")) for x in result["posts"]}
        for s in seeds.get("items",[]):
            if str(s.get("aid")) in existing:continue
            if not isinstance(s.get("aid"),int):continue
            entry={"platform":"bilibili","aid":s["aid"],"bvid":s.get("bvid"),
                   "search_query":"curated_verified_seed","title":clean(s.get("title"),200),
                   "url":"https://www.bilibili.com/video/"+str(s.get("bvid")),
                   "verified_scope":"historical public video seed, NOT a fresh search result",
                   "seed_verified_on":seeds.get("verified_on")}
            result["posts"].append(entry)
            targets.append(entry)
            if len(targets)>=9:break
    except (OSError,ValueError,TypeError) as e:
        result.setdefault("seed_errors",[]).append(type(e).__name__)
    result["status"]="verified" if result["posts"] and any(p.get("verified_scope")=="public Bilibili search result" for p in result["posts"]) else "seed_only" if result["posts"] else "not_verified"
    for p in targets[:7]:
        url="https://api.bilibili.com/x/v2/reply?"+urlencode({
            "type":1,"oid":p["aid"],"pn":1,"ps":20,"sort":1})
        try:
            obj,_,_=try_json(url)
            if obj.get("code")!=0:
                result.setdefault("comment_errors",[]).append({
                    "video_id":p["aid"],"api_code":obj.get("code")})
                continue
            data=obj.get("data") or {}
            for entry in (data.get("replies") or [])[:20]:
                if not isinstance(entry,dict):continue
                body=clean((entry.get("content") or {}).get("message"),550)
                if not body:continue
                result["comments"].append({"platform":"bilibili","search_query":p["search_query"],
                    "post_title":p["title"],"url":p["url"]+"#reply"+
                    str(entry.get("rpid_str") or entry.get("rpid") or ""),
                    "post_url":p["url"],"text_excerpt":body,"likes":entry.get("like"),
                    "verified_scope":"actual public video reply"})
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as e:
            result.setdefault("comment_errors",[]).append({
                "video_id":p["aid"],"error":type(e).__name__+": "+clean(e,110)})
    result["post_count"]=len(result["posts"])
    result["comments_returned"]=len(result["comments"])
    result["videos_with_replies"]=len({x["post_url"] for x in result["comments"]})
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
