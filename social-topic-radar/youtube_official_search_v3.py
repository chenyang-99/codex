#!/usr/bin/env python3
"""Optional OFFICIAL YouTube Data API keyword search for new and popular videos.

Only used when YOUTUBE_SEARCH_ENABLED=1 and YOUTUBE_DATA_API_KEY is provided.
Does not scrape video media or comments; preserves platform-native view/like counts.
"""
import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

HERE=Path(__file__).resolve().parent
OUT=HERE/"output"
API="https://www.googleapis.com/youtube/v3"
QUERIES=("AI video editor tutorial","AI design tools workflow","open source AI animation")
def request(endpoint, params, key):
    # Only endpoints selected by local code.
    if endpoint not in ("search","videos"):raise ValueError("unsupported_endpoint")
    url=f"{API}/{endpoint}?"+urlencode({**params,"key":key})
    req=Request(url,headers={"User-Agent":"AI-topic-radar/3.2","Accept":"application/json"})
    with urlopen(req,timeout=16) as response:
        data=response.read(2000001)
    if len(data)>2000000:raise ValueError("youtube_response_too_large")
    return json.loads(data)

def collect(env=None,api=request,clock=None):
    e=os.environ if env is None else env
    if e.get("YOUTUBE_SEARCH_ENABLED")!="1":
        return [],[{"source":"youtube_api_keyword","status":"not_configured",
                    "items":None,"reason":"disabled_by_default"}]
    if not e.get("YOUTUBE_DATA_API_KEY"):
        return [],[{"source":"youtube_api_keyword","status":"not_configured",
                    "items":None,"reason":"api_key_missing"}]
    now=clock or dt.datetime.now(dt.timezone.utc)
    since=(now-dt.timedelta(days=7)).isoformat().replace("+00:00","Z")
    checked=now.isoformat()
    key=e["YOUTUBE_DATA_API_KEY"]
    found={}
    reports=[]
    for term in QUERIES[:3]:
        try:
            data=api("search",{"part":"snippet","q":term,"type":"video","maxResults":20,
                  "order":"viewCount","safeSearch":"moderate","publishedAfter":since},key)
            items=data.get("items") if isinstance(data,dict) else None
            if not isinstance(items,list):raise ValueError("no_items_array")
            matched=0
            for raw in items:
                vid=(raw.get("id") or {}).get("videoId")
                snip=raw.get("snippet") or {}
                if not isinstance(vid,str) or not vid:continue
                matched+=1
                found[vid]={"url":"https://www.youtube.com/watch?v="+vid,
                    "source":"youtube_official_keyword","platform":"youtube",
                    "title":str(snip.get("title") or "")[:600],
                    "author":snip.get("channelTitle") or "",
                    "published_utc":snip.get("publishedAt"),"metrics_checked_at":checked,
                    "metrics":{},"retrieved_scope":"official YouTube search snippet; video not watched",
                    "editorial_status":"research_candidate_only"}
            reports.append({"source":"youtube_query:"+term,
                            "status":"retrieved" if matched else "empty","items":matched})
        except (OSError,ValueError,TimeoutError) as err:
            reports.append({"source":"youtube_query:"+term,"status":"unavailable","items":None,
                            "error":type(err).__name__+": "+str(err)[:90]})
    ids=list(found)
    # One videos.list request for all IDs; missing/private stats remain unknown.
    if ids:
        try:
            data=api("videos",{"part":"statistics","id":",".join(ids[:50]),"maxResults":50},key)
            for item in data.get("items",[]):
                vid=item.get("id")
                if vid not in found:continue
                stats=item.get("statistics") or {}
                native={}
                for name,field in (("views","viewCount"),("likes","likeCount"),("comments","commentCount")):
                    val=stats.get(field)
                    if isinstance(val,str) and val.isdecimal():native[name]=int(val)
                found[vid]["platform_native_metrics"]=native
                found[vid]["metrics_checked_at"]=checked
            reports.append({"source":"youtube_video_stats","status":"retrieved","items":len(data.get("items",[]))})
        except (OSError,ValueError,TimeoutError) as err:
            reports.append({"source":"youtube_video_stats","status":"unavailable","items":None,
                            "error":type(err).__name__+": "+str(err)[:90]})
    return list(found.values()),reports

def main():
    rows,health=collect()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"youtube-official-keyword-v3.json").write_text(json.dumps({
        "checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "items":rows,"source_health":health,
        "limitations":["Requires user-provided official YouTube Data API key and opt-in",
                       "Search snippets and native metrics are not actual video content inspection",
                       "Published-after + most-viewed search can omit significant videos",
                       "Three searches plus one statistics call per run; platform quota limits apply"]},
        ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"sources":health,"rows":len(rows)},ensure_ascii=False))
if __name__=="__main__":main()
