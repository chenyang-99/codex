#!/usr/bin/env python3
"""Bounded public Douyin AI-creator discovery, no Douyin account.

Uses the publicly documented free shared demo service, not an account token.
Each seed is an independently discovered *candidate* video, verified by the
actual content API before its public creator's recent posts are sampled.
Search here is topical filtering within those verified creator feeds, NOT
platform-wide native keyword search. Each run uses at most 3 seed lookups,
3 creator feed lookups and 2 top-level comment-page reads. No retry loops.
"""
import datetime as dt
import json
from pathlib import Path
import re
import sys
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parent/"social-topic-radar"))
from public_douyin_demo_test import HTTP, scrub

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"social-topic-radar"/"output"/"douyin-creator-discovery.json"
SEED_FILE=ROOT/"social-topic-radar"/"douyin_creator_seeds.json"
TERMS=("ai","gpt","生图","绘图","图片","图像","即梦","豆包",
       "视频","教程","提示词","千问","comfyui","seedance","小云雀","漫剧")
METRICS=("digg_count","comment_count","collect_count","share_count")
MAX_CREATORS=3
MAX_COMMENT_PAGES=2

def rows(raw):
    if isinstance(raw,list):return raw
    if isinstance(raw,dict):
        for key in ("items","posts","videos","aweme_list","list"):
            value=raw.get(key)
            if isinstance(value,list):return value
    return []

def idof(item):
    value=str(item.get("content_id") or item.get("aweme_id") or item.get("id") or "")
    return value if re.fullmatch(r"[0-9]{15,22}",value) else None

def to_int(value):
    try:return max(0,int(value))
    except (TypeError,ValueError):return 0

def main():
    report={"checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "platform":"douyin","source":"documented public free shared demo douyin.wtf",
        "login":"public demo website account only; no Douyin personal login",
        "platform_native_keyword_search":False,
        "site_wide_hot_rank":False,
        "source_scope":"up to three verified creators and their first five public posts",
        "seed_verification":[],"verified_author_feeds":0,
        "actual_relevant_video_count":0,"candidate_videos":[],
        "comment_pages_tested":0,"actual_comment_texts":0,
        "comment_samples":[],"comments_status":"not_tested"}
    try:
        cfg=json.loads(SEED_FILE.read_text(encoding="utf-8"))
        seed_ids=[str(s["video_id"]) for s in cfg["seeds"][:MAX_CREATORS]
                  if isinstance(s,dict) and re.fullmatch(r"\d{15,22}",str(s.get("video_id","")))]
        api=HTTP()
        s,auth=api.request("GET","/api/v1/auth/demo",timeout=13)
        pwd=(auth.get("data") or {}).get("password")
        if s!=200 or not pwd:
            report["error"]="public demo credentials unavailable";return report
        s,login=api.request("POST","/api/v1/auth/login",
                            {"username":"demo","password":pwd},timeout=13)
        if s!=200 or not login.get("success"):
            report["error"]="public demo account not available";return report
        report["demo_service_auth"]="verified_public_demo_only"
        seen_users=set()
        videos={}
        for seed in seed_ids:
            link="https://www.douyin.com/video/"+seed
            status,response=api.request("POST","/api/v1/parse?wait=20",
                                        {"url":link},timeout=27)
            data=response.get("data") if isinstance(response,dict) else None
            ok=status==200 and isinstance(response,dict) and response.get("success") and isinstance(data,dict)
            record={"video_url":link,"http":status,"verified_content":bool(ok)}
            report["seed_verification"].append(record)
            if not ok:continue
            author=data.get("author") or {}
            if not isinstance(author,dict):continue
            user=next((author[k] for k in ("sec_uid","sec_user_id","secUid","secUserId")
                       if isinstance(author.get(k),str) and author.get(k)),None)
            if not user or user in seen_users:continue
            seen_users.add(user)
            params=urllib.parse.urlencode({"sec_user_id":user,"count":5,"wait":20})
            code,feed=api.request("GET","/api/v1/douyin/user/posts?"+params,timeout=27)
            result=feed.get("data") if isinstance(feed,dict) else None
            if code!=200 or not feed.get("success"):continue
            report["verified_author_feeds"]+=1
            for item in rows(result)[:5]:
                if not isinstance(item,dict):continue
                vid=idof(item)
                if not vid:continue
                title=item.get("title") or item.get("description") or item.get("desc") or ""
                if not isinstance(title,str) or not any(t in title.lower() for t in TERMS):continue
                stats=item.get("stats") or {}
                if not isinstance(stats,dict):stats={}
                counts={k:to_int(stats.get(k)) for k in METRICS if stats.get(k) is not None}
                engagement=sum(counts.values())
                record={"title":scrub(title,210),
                    "video_url":"https://www.douyin.com/video/"+vid,
                    "published_at":item.get("created_at"),
                    "stats":counts,"sum_reported_engagement":engagement,
                    "engagement_scope":"within sampled creator posts, not all Douyin",
                    "source_seed":link}
                videos.setdefault(vid,record)
        candidates=sorted(videos.values(),
              key=lambda x:x["sum_reported_engagement"],reverse=True)
        report["actual_relevant_video_count"]=len(candidates)
        report["candidate_videos"]=candidates[:15]
        report["creator_sample_ranked"]=bool(candidates)
        targets=[p for p in candidates if p["stats"].get("comment_count",0)>0][:MAX_COMMENT_PAGES]
        report["comments_status"]="no_verifiable_video_with_reported_comments" if not targets else "tested_no_comment_text"
        for post in targets:
            vid=post["video_url"].rsplit("/",1)[-1]
            params=urllib.parse.urlencode({"aweme_id":vid,"count":8,"wait":20})
            status,comment_resp=api.request("GET","/api/v1/douyin/video/comments?"+params,timeout=28)
            report["comment_pages_tested"]+=1
            if status!=200 or not isinstance(comment_resp,dict) or not comment_resp.get("success"):
                report.setdefault("comment_access_failures",[]).append(
                    {"video_url":post["video_url"],"http_status":status})
                if status in (401,403,429):break
                continue
            payload=comment_resp.get("data")
            for entry in rows(payload)[:8]:
                if not isinstance(entry,dict):continue
                msg=entry.get("text") or entry.get("content")
                if not isinstance(msg,str) or not msg.strip():continue
                report["comment_samples"].append({
                    "platform":"douyin","post_url":post["video_url"],
                    "text_excerpt":scrub(msg,450),
                    "reported_reply_count":to_int(entry.get("reply_count") or entry.get("reply_comment_total")),
                    "verified_scope":"actual public first-level comment body",
                    "second_level_retrieved":False})
        report["actual_comment_texts"]=len(report["comment_samples"])
        if report["actual_comment_texts"]:
            report["comments_status"]="verified_first_level_comment_text"
        return report
    except Exception as exc:
        report["error"]=type(exc).__name__+":"+scrub(exc,150)
        return report

if __name__=="__main__":
    result=main()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"douyin_ai_creator_discovery":{
         k:v for k,v in result.items() if k!="comment_samples"}},ensure_ascii=False))
