#!/usr/bin/env python3
"""Read inline public reply previews already included in top-level comment response.

This does NOT call the platform-blocked /video/comments/replies route. One
bounded normal public-demo /video/comments?include_raw=true read for one
already-verified public AI tutorial. No Douyin account, proxies, CAPTCHA
workarounds, or repeated calls. Save only sanitized excerpt and parent link.
"""
from datetime import datetime,timezone
from pathlib import Path
import json,urllib.parse,re
from public_douyin_demo_test import HTTP,scrub

VIDEO="7692794233737331338"
OUT=Path(__file__).resolve().parent/"output"/"douyin-reply-previews.json"

def items(obj):
    if isinstance(obj,list):return obj
    if not isinstance(obj,dict):return []
    for name in ("items","comments","data","list"):
        val=obj.get(name)
        if isinstance(val,list):return val
        if isinstance(val,dict):
            out=items(val)
            if out:return out
    return []

def raw_of(entry):
    for k in ("raw","raw_payload","original","source"):
        d=entry.get(k)
        if isinstance(d,dict):return d
    return {}

def text_of(e):
    return e.get("text") or e.get("content") or e.get("message") or ""

def count_nested(entry,top_url):
    raw=raw_of(entry)
    nested=raw.get("reply_comment")
    if not isinstance(nested,list):
        nested=entry.get("reply_comment")
    if not isinstance(nested,list):nested=[]
    pid=str(entry.get("comment_id") or entry.get("cid") or entry.get("id") or raw.get("cid") or "")
    output=[]
    for v in nested[:5]:
        if not isinstance(v,dict):continue
        txt=text_of(v)
        cid=str(v.get("cid") or v.get("comment_id") or v.get("id") or "")
        if isinstance(txt,str) and txt.strip():
            output.append({"source_video":top_url,
                "parent_comment_id":pid[:40],"reply_id":cid[:40],
                "text_excerpt":scrub(txt,350),
                "evidence_kind":"inline reply_comment preview in public top-level comment response",
                "is_full_reply_thread":False})
    return output

def run():
    url=f"https://www.douyin.com/video/{VIDEO}"
    rep={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
        "source_video":url,"method":"top-level comments?include_raw=true",
        "uses_account_login":False,"uses_demo_account_not_platform_account":True,
        "comments_verified":0,"parents_reporting_replies":0,
        "comments_with_raw":0,"nested_reply_previews_verified":0,
        "direct_nested_reply_request_made":False,"state":"not_tested"}
    api=HTTP()
    try:
        a,v=api.request("GET","/api/v1/auth/demo",timeout=14)
        pwd=(v.get("data") or {}).get("password") if isinstance(v,dict) else None
        if a!=200 or not pwd:
            rep["state"]="demo_credential_unavailable";return rep
        a,v=api.request("POST","/api/v1/auth/login",{"username":"demo","password":pwd},timeout=15)
        if a!=200 or not v.get("success"):
            rep["state"]="demo_session_unavailable";return rep
        path="/api/v1/douyin/video/comments?"+urllib.parse.urlencode(
             {"aweme_id":VIDEO,"count":16,"include_raw":"true","wait":24})
        status,response=api.request("GET",path,timeout=30)
        rep["http"]=status
        rep["success"]=bool(isinstance(response,dict) and response.get("success"))
        if status!=200 or not rep["success"]:
            rep["state"]="top_level_read_unavailable"
            err=(response or {}).get("error") or {}
            if isinstance(err,dict):rep["error_code"]=scrub(err.get("code"),70)
            return rep
        top=items(response.get("data"))
        previews=[]
        unique=set()
        for comment in top:
            if not isinstance(comment,dict):continue
            txt=text_of(comment)
            if isinstance(txt,str) and txt.strip():rep["comments_verified"]+=1
            raw=raw_of(comment)
            if raw:rep["comments_with_raw"]+=1
            try:
                rc=int(comment.get("reply_count") or raw.get("reply_comment_total") or 0)
            except (ValueError,TypeError):rc=0
            if rc>0:rep["parents_reporting_replies"]+=1
            for child in count_nested(comment,url):
                key=(child["parent_comment_id"],child["reply_id"],child["text_excerpt"])
                if key not in unique:unique.add(key);previews.append(child)
        rep["nested_reply_previews_verified"]=len(previews)
        rep["sample_reply_previews"]=previews[:8]
        rep["state"]="verified_reply_previews" if previews else "no_inline_reply_previews_returned"
    except Exception as e:rep["state"]="exception";rep["error"]=type(e).__name__+":"+scrub(e,120)
    return rep
if __name__=="__main__":
    x=run()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"douyin_inline_reply_preview_audit":{k:v for k,v in x.items() if k!="sample_reply_previews"}},ensure_ascii=False))
