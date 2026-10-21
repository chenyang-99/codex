#!/usr/bin/env python3
"""Zero-token public Bluesky keyword discovery, native post engagement.

Public API is only a supplementary source for original posts, not an X hot-post
substitute. No credentials, login, third-party paywall, or tracking proxy.
"""
from __future__ import annotations
import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import urlencode,quote
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"
BASE="https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
QUERIES=("AI video open source","AI tools","generative AI design","AI workflow")
def get(query, read=None):
    qs=urlencode({"q":query,"sort":"top","limit":35,"lang":"en"})
    url=BASE+"?"+qs
    if read is not None:
        return read(url)
    req=Request(url,headers={"User-Agent":"AI-Topic-Radar/3.2 (public read-only)",
                             "Accept":"application/json"})
    with urlopen(req,timeout=12) as response:
        raw=response.read(1800001)
    if len(raw)>1800000:raise ValueError("too_large")
    return json.loads(raw)

def normalize(post,checked_at):
    if not isinstance(post,dict):return None
    author=post.get("author") or {}
    record=post.get("record") or {}
    uri=post.get("uri","")
    did=author.get("did")
    handle=author.get("handle")
    if not isinstance(uri,str) or not uri.startswith("at://") or not uri.count("/")>=3: return None
    if not (isinstance(handle,str) and isinstance(did,str) and did.startswith("did:")):return None
    tid=uri.split("/")[-1]
    if not tid or "/" in tid:return None
    text=str(record.get("text") or "").strip()
    if not text:return None
    url="https://bsky.app/profile/"+quote(did,safe=":")+"/post/"+quote(tid,safe="")
    stats={}
    for key,field in (("likes","likeCount"),("reposts","repostCount"),
                      ("replies","replyCount"),("quotes","quoteCount")):
        v=post.get(field)
        if type(v) in (int,float) and v>=0: stats[key]=v
    return {
        "source":"bluesky_public_search",
        "platform":"bluesky","url":url,"title":text[:1600],
        "author":handle,"published_utc":record.get("createdAt"),
        "metrics":stats,"metrics_checked_at":checked_at,
        "retrieved_scope":"public.api.bsky.app native public search; provider ranked top, no site-wide completeness guarantee",
        "editorial_status":"research_candidate_only",
    }

def collect(queries=QUERIES,read=None):
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    rows,health=[],[]
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures={ex.submit(get,q,read):q for q in queries[:4]}
        for future in as_completed(futures):
            query=futures[future]
            try:
                res=future.result()
                posts=res.get("posts") if isinstance(res,dict) else None
                if not isinstance(posts,list): raise ValueError("missing_posts")
                values=[z for p in posts if (z:=normalize(p,now))]
                rows.extend(values)
                health.append({"source":"bluesky_query:"+query,
                               "status":"retrieved" if values else "empty","items":len(values)})
            except (OSError,ValueError,TimeoutError) as exc:
                health.append({"source":"bluesky_query:"+query,"status":"unavailable",
                               "items":None,"error":type(exc).__name__+":"+str(exc)[:100]})
    # dedup across independent keyword searches without fabricating multi-platform success
    unique={p["url"]:p for p in rows}
    return list(unique.values()),sorted(health,key=lambda x:x["source"])

def main():
    rows,health=collect()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"bluesky-public-search-v3.json").write_text(json.dumps({
        "checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"items":rows,
        "source_health":health,
        "limitations":["Uncredentialed Bluesky AppView supports public GET where server permits",
                       "Top ranking is Bluesky's search result, not all-network coverage",
                       "Bluesky replies/likes differ from X and cannot be pooled",
                       "No account access, paid requests or bypass of restrictions"]},
        ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"items":len(rows),"providers":health},ensure_ascii=False))
if __name__=="__main__":main()
