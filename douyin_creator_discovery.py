#!/usr/bin/env python3
"""Bounded public Douyin AI-creator discovery, no Douyin account.

Uses the publicly documented free shared demo service, not an account token.
Each seed is an independently discovered *candidate* video, verified by the
actual content API before its public creator's recent posts are sampled.
Search here is topical filtering within those verified creator feeds, NOT
platform-wide native keyword search. Each run uses at most 3 seed lookups,
3 creator feed lookups and 3 normal top-level comment-page reads. No retry loops.
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
MAX_COMMENT_PAGES=3
MAX_COMMENT_VIDEOS=2

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
        "comment_samples":[],"comments_status":"not_tested",
        "actual_reply_preview_texts":0,"reply_preview_samples":[],
        "direct_nested_reply_access":"not_called_due_to_upstream_risk_control"}
    try:
        cfg=json.loads(SEED_FILE.read_text(encoding="utf-8"))
        # Keep a proven baseline and rotate two other public-index candidates
        # by date, so the fixed 3-request budget covers more AI creators over time.
        valid_seeds=[str(s["video_id"]) for s in cfg["seeds"]
                     if isinstance(s,dict) and re.fullmatch(r"\d{15,22}",str(s.get("video_id","")))]
        day=dt.datetime.now(dt.timezone.utc).date().toordinal()
        baseline=valid_seeds[:1]
        fresh=valid_seeds[1:]
        rotating=[fresh[(day*2+i)%len(fresh)] for i in range(min(MAX_CREATORS-1,len(fresh)))] if fresh else []
        seed_ids=list(dict.fromkeys(baseline+rotating))[:MAX_CREATORS]
        report["seed_rotation"]="one baseline + two day-rotated candidate seeds; all unverified until public demo read"
        report["selected_seed_video_urls"]=["https://www.douyin.com/video/"+v for v in seed_ids]
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
        targets=[p for p in candidates if p["stats"].get("comment_count",0)>0][:MAX_COMMENT_VIDEOS]
        report["comments_status"]="no_verifiable_video_with_reported_comments" if not targets else "tested_no_comment_text"
        remaining_budget=MAX_COMMENT_PAGES
        seen_comments=set()
        seen_replies=set()
        report["comment_page_evidence"]=[]
        stop_for_access=False
        for ti,post in enumerate(targets):
            if stop_for_access or remaining_budget<=0:break
            vid=post["video_url"].rsplit("/",1)[-1]
            max_this_video=2 if ti==0 else 1
            cursor=None
            for page_num in range(max_this_video):
                if remaining_budget<=0:break
                params={"aweme_id":vid,"count":16 if ti==0 else 8,
                        "wait":20,"include_raw":"true"}
                if cursor is not None:params["cursor"]=cursor
                query=urllib.parse.urlencode(params)
                status,comment_resp=api.request("GET","/api/v1/douyin/video/comments?"+query,timeout=28)
                remaining_budget-=1
                report["comment_pages_tested"]+=1
                if status!=200 or not isinstance(comment_resp,dict) or not comment_resp.get("success"):
                    report.setdefault("comment_access_failures",[]).append(
                        {"video_url":post["video_url"],"page":page_num+1,"http_status":status})
                    if status in (401,403,429):stop_for_access=True
                    break
                payload=comment_resp.get("data") or {}
                page_rows=rows(payload)
                page_new=0;preview_new=0
                for entry in page_rows[:16]:
                    if not isinstance(entry,dict):continue
                    msg=entry.get("text") or entry.get("content")
                    if not isinstance(msg,str) or not msg.strip():continue
                    raw=entry.get("raw") or {}
                    if not isinstance(raw,dict):raw={}
                    comment_id=str(entry.get("comment_id") or entry.get("cid") or raw.get("cid") or "")
                    parent_key=(post["video_url"],comment_id or msg)
                    if parent_key in seen_comments:continue
                    seen_comments.add(parent_key);page_new+=1
                    report["comment_samples"].append({
                        "platform":"douyin","post_url":post["video_url"],
                        "text_excerpt":scrub(msg,450),
                        "comment_id":comment_id[:42],
                        "reported_reply_count":to_int(entry.get("reply_count") or raw.get("reply_comment_total")),
                        "verified_scope":"actual public first-level comment body",
                        "second_level_retrieved":False})
                    inline=raw.get("reply_comment") or entry.get("reply_comment") or []
                    if not isinstance(inline,list):continue
                    for reply in inline[:5]:
                        if not isinstance(reply,dict):continue
                        content=reply.get("text") or reply.get("content")
                        if not isinstance(content,str) or not content.strip():continue
                        reply_id=str(reply.get("cid") or reply.get("comment_id") or reply.get("id") or "")
                        child_key=(post["video_url"],comment_id,reply_id or content)
                        if child_key in seen_replies:continue
                        seen_replies.add(child_key);preview_new+=1
                        report["reply_preview_samples"].append({
                            "platform":"douyin","post_url":post["video_url"],
                            "text_excerpt":scrub(content,450),
                            "parent_comment_id":comment_id[:42],
                            "reply_id":reply_id[:42],
                            "verified_scope":"actual inline reply_comment preview from first-level API raw",
                            "is_full_thread":False})
                has_more=payload.get("has_more") is True if isinstance(payload,dict) else False
                next_cursor=payload.get("cursor") if has_more else None
                if next_cursor in (None,"",0,"0") or not isinstance(next_cursor,(str,int)):
                    next_cursor=None
                report["comment_page_evidence"].append({
                    "video_url":post["video_url"],"page":page_num+1,
                    "http":status,"page_rows":len(page_rows),
                    "unique_new_first_level":page_new,
                    "unique_new_inline_reply_previews":preview_new,
                    "has_more":has_more,"next_cursor_available":next_cursor is not None})
                if next_cursor is None or str(next_cursor)==str(cursor):break
                cursor=str(next_cursor)
        report["actual_comment_texts"]=len(report["comment_samples"])
        report["reply_preview_samples"]=list({
            (r["post_url"],r["parent_comment_id"],r["reply_id"],r["text_excerpt"]):r
            for r in report["reply_preview_samples"]}.values())
        report["actual_reply_preview_texts"]=len(report["reply_preview_samples"])
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
