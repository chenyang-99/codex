#!/usr/bin/env python3
"""Bounded Douyin AI creator discovery through the free documented demo.

No user Douyin login or payment. One known AI tutorial URL -> public author ->
up to five public recent videos. Keyword relevance and stats are verified only
when actually returned; no statement of platform-wide native keyword search.
"""
import datetime as dt,json,pathlib,re,sys,urllib.parse
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent/"social-topic-radar"))
from public_douyin_demo_test import HTTP,describe,scrub

OUT=pathlib.Path(__file__).resolve().parent/"social-topic-radar"/"output"/"douyin-creator-discovery.json"
SEED="7688717725015404726"
WORDS=("ai","gpt","生图","绘图","图片","图像","即梦","豆包","视频","教程","提示词","千问")
def rows(data):
    if isinstance(data,list):return data
    if not isinstance(data,dict):return []
    for k in ("items","posts","videos","aweme_list","list"):
        if isinstance(data.get(k),list):return data[k]
    return []

def main():
    doc={"checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
         "platform":"douyin","source":"public developer demo service douyin.wtf",
         "login":"public demo credentials only; no Douyin account",
         "sample_seed":"https://www.douyin.com/video/"+SEED,
         "topic":"AI创作",
         "author_feed_status":"not_tested","actual_relevant_video_count":0,
         "platform_native_keyword_search":False,
         "comments_status":"not_tested"}
    api=HTTP()
    try:
        s,grant=api.request("GET","/api/v1/auth/demo",timeout=12)
        pw=(grant.get("data") or {}).get("password")
        if s!=200 or not pw:doc["error"]="demo credentials unavailable";return doc
        s,login=api.request("POST","/api/v1/auth/login",{"username":"demo","password":pw},timeout=12)
        if s!=200 or not login.get("success"):doc["error"]="demo service refused access";return doc
        s,post=api.request("POST","/api/v1/parse?wait=20",
                            {"url":doc["sample_seed"]},timeout=25)
        doc["seed_status"]=describe(s,post)
        data=post.get("data") if isinstance(post,dict) else {}
        author=data.get("author") if isinstance(data,dict) else {}
        if not isinstance(author,dict):author={}
        doc["author_fields"]=list(author)[:25]
        uid=next((author[k] for k in ("sec_user_id","sec_uid","secUid","secUserId")
                  if isinstance(author.get(k),str) and author.get(k)),None)
        profile=next((author[k] for k in ("profile_url","url","web_url")
                      if isinstance(author.get(k),str) and author.get(k).startswith("https://")),None)
        if not uid and not profile:
            doc["author_feed_status"]="no_public_feed_identifier_returned"
            return doc
        params={"count":5,"wait":20}
        if uid:params["sec_user_id"]=uid
        else:params["url"]=profile
        path="/api/v1/douyin/user/posts?"+urllib.parse.urlencode(params)
        st,response=api.request("GET",path,timeout=28)
        doc["author_feed_status"]="api_success" if (st==200 and response.get("success")) else "not_verified"
        doc["author_feed_http"]=st
        payload=response.get("data") if isinstance(response,dict) else None
        doc["feed_field_names"]=list(payload)[:20] if isinstance(payload,dict) else []
        entries=rows(payload)
        matches=[]
        for item in entries[:8]:
            if not isinstance(item,dict):continue
            title=item.get("title") or item.get("description") or item.get("desc") or ""
            if not isinstance(title,str):continue
            if not any(t in title.lower() for t in WORDS):continue
            vid=str(item.get("content_id") or item.get("aweme_id") or item.get("id") or "")
            stats=item.get("stats") or {}
            if not isinstance(stats,dict):stats={}
            matches.append({"title":scrub(title,200),
                            "video_url":"https://www.douyin.com/video/"+vid if vid.isdigit() else None,
                            "published_at":item.get("created_at"),
                            "stats":{k:stats.get(k) for k in ("digg_count","comment_count","collect_count","share_count") if stats.get(k) is not None}})
        doc["actual_relevant_video_count"]=len(matches)
        doc["candidate_videos"]=matches[:5]
        if matches:doc["author_feed_status"]="verified_relevant_author_videos"
    except Exception as e:doc["error"]=type(e).__name__+":"+scrub(e,140)
    return doc
if __name__=="__main__":
    result=main()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"douyin_ai_creator_discovery":result},ensure_ascii=False))
