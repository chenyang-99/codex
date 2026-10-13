#!/usr/bin/env python3
"""One bounded Douyin secondary-reply diagnostic on the public free demo.

No Douyin account, login cookie, evasion, proxies or paid API. This does not
retry failures. One known public AI video, one public comment list, one nested
reply page only when the parent explicitly reports replies.
"""
from __future__ import annotations
import datetime as dt
import json
import pathlib
import re
import urllib.parse
from public_douyin_demo_test import HTTP, scrub, describe

OUT = pathlib.Path(__file__).resolve().parent/"output"/"douyin-reply-diagnostic.json"
VIDEO = "7692794233737331338"  # Previously verified public AI comparison video.
def normalize_list(d):
    if isinstance(d,list): return d
    if not isinstance(d,dict): return []
    for k in ("comments","comment_list","items","replies","list"):
        if isinstance(d.get(k),list): return d[k]
    if isinstance(d.get("data"),(dict,list)):return normalize_list(d["data"])
    return []

def num(v):
    try:return int(v)
    except (TypeError,ValueError):return 0

def main():
    o={"checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "platform":"douyin","video_url":"https://www.douyin.com/video/"+VIDEO,
       "scope":"One top-level page, at most one reply page; public demo, no platform login",
       "first_level_actual_comment_texts":0,
       "parents_reporting_replies":0,
       "nested_actual_reply_texts":0,
       "nested_reply_status":"not_tested",
       "credential_type":"published public service demo credentials only",
       "site_wide_search":False}
    api=HTTP()
    try:
        st,a=api.request("GET","/api/v1/auth/demo",timeout=15)
        p=(a.get("data") or {}).get("password") if isinstance(a,dict) else None
        if st!=200 or not p:
            o["error"]="public demo credential endpoint unavailable";return o
        st,login=api.request("POST","/api/v1/auth/login",
                    {"username":"demo","password":p},timeout=16)
        if st!=200 or not isinstance(login,dict) or not login.get("success"):
            o["error"]="public demo session unavailable";return o
        query=urllib.parse.urlencode({"aweme_id":VIDEO,"count":16,"wait":25})
        st,comments=api.request("GET","/api/v1/douyin/video/comments?"+query,timeout=32)
        o["comment_page"]=describe(st,comments)
        if st!=200 or not isinstance(comments,dict) or not comments.get("success"):
            o["nested_reply_status"]="not_tested_parent_page_failure";return o
        parents=[]
        for item in normalize_list(comments.get("data"))[:16]:
            if not isinstance(item,dict):continue
            msg=item.get("text") or item.get("content")
            if not isinstance(msg,str) or not msg.strip():continue
            cid=str(item.get("comment_id") or item.get("cid") or item.get("id") or "")
            rep=num(item.get("reply_count") or item.get("reply_comment_total") or item.get("reply_comment_count"))
            if cid and re.fullmatch(r"[0-9]{5,35}",cid):
                parents.append({"id":cid,"reply_count":rep,"text_excerpt":scrub(msg,125)})
        o["first_level_actual_comment_texts"]=len(parents)
        o["parents_reporting_replies"]=sum(x["reply_count"]>0 for x in parents)
        o["comment_sample_count"]=len(parents)
        sample=next((x for x in parents if x["reply_count"]>0),None)
        if sample is None:
            o["nested_reply_status"]="no_parent_with_reported_replies"
            return o
        o["selected_parent_reply_count_reported"]=sample["reply_count"]
        q=urllib.parse.urlencode({"aweme_id":VIDEO,
                                  "comment_id":sample["id"],"count":5,"wait":25})
        st,replies=api.request("GET","/api/v1/douyin/video/comments/replies?"+q,timeout=32)
        o["reply_page"]=describe(st,replies)
        if st==200 and isinstance(replies,dict) and replies.get("success"):
            rows=normalize_list(replies.get("data"))
            actual=[scrub(v.get("text") or v.get("content"),220) for v in rows
                    if isinstance(v,dict) and isinstance(v.get("text") or v.get("content"),str)
                    and (v.get("text") or v.get("content")).strip()]
            o["nested_actual_reply_texts"]=len(actual)
            o["nested_reply_status"]="verified_real_second_level_text" if actual else "empty_or_unverified"
            o["nested_reply_samples"]=actual[:3]
        else:
            o["nested_reply_status"]="upstream_or_demo_error"
            if isinstance(replies,dict):
                err=replies.get("error") or {}
                if isinstance(err,dict):
                    o["error_kind"]=scrub(err.get("code"),65)
                    o["error_detail_excerpt"]=scrub(err.get("message"),180)
    except Exception as exc:
        o["error"]=type(exc).__name__+":"+scrub(exc,150)
    return o

if __name__=="__main__":
    result=main()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"douyin_second_level_diagnostic":{
        k:v for k,v in result.items() if k not in ("nested_reply_samples",)}},ensure_ascii=False))
