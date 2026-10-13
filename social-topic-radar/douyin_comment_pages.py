#!/usr/bin/env python3
"""Bounded read-only Douyin top-level comment pagination with inline reply previews.

No personal Douyin login. Use documented, freely published demo-service
credentials. This does not call the blocked /comments/replies endpoint.
At most two normal comment pages, for one previously verified AI video.
Stop on any error/limit/challenge. Do not store author identity or cookies.
"""
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import json
from public_douyin_demo_test import HTTP, scrub

VIDEO="7692794233737331338"
OUT=Path(__file__).resolve().parent/"output"/"douyin-bounded-comment-pages.json"
MAX_PAGES=2

def top_items(obj):
    if isinstance(obj,list):return obj
    if not isinstance(obj,dict):return []
    for key in ("items","comments","list"):
        value=obj.get(key)
        if isinstance(value,list):return value
    return []

def find_cursor(obj):
    if not isinstance(obj,dict):return None
    # The public demo returns a normalized Page in data. Never invent cursors.
    cursor=obj.get("cursor")
    more=obj.get("has_more")
    if more is not True or cursor in (None,"",0,"0"):return None
    if not isinstance(cursor,(str,int)):return None
    return str(cursor)[:100]

def raw_entry(comment):
    d=comment.get("raw")
    return d if isinstance(d,dict) else {}

def main():
    record={"platform":"douyin","checked_utc":datetime.now(timezone.utc).isoformat(),
      "source_video":"https://www.douyin.com/video/"+VIDEO,
      "scope":"at most two normal top-level comment pages; includes inline reply previews only",
      "platform_account_used":False,"dedicated_reply_endpoint_called":False,
      "pages_retrieved":0,"actual_first_level_text_count":0,
      "actual_inline_reply_preview_count":0,"status":"not_tested"}
    api=HTTP()
    try:
        st,p=api.request("GET","/api/v1/auth/demo",timeout=14)
        pw=(p.get("data") or {}).get("password") if isinstance(p,dict) else None
        if st!=200 or not pw:record["status"]="demo_public_login_unavailable";return record
        st,p=api.request("POST","/api/v1/auth/login",{"username":"demo","password":pw},timeout=14)
        if st!=200 or not p.get("success"):record["status"]="public_demo_session_unavailable";return record
        seen=set();inline=set();cursor=None
        for page in range(MAX_PAGES):
            params={"aweme_id":VIDEO,"count":16,"include_raw":"true","wait":22}
            if cursor is not None:params["cursor"]=cursor
            st,obj=api.request("GET","/api/v1/douyin/video/comments?"+urlencode(params),timeout=30)
            if st!=200 or not isinstance(obj,dict) or not obj.get("success"):
                record["status"]="page_unavailable"
                record["failure_at_page"]=page+1
                record["failed_http"]=st
                err=obj.get("error") if isinstance(obj,dict) else None
                if isinstance(err,dict):record["error_code"]=scrub(err.get("code"),70)
                break
            data=obj.get("data") or {}
            batch=top_items(data)
            page_main=0;page_replies=0
            for c in batch[:16]:
                if not isinstance(c,dict):continue
                raw=raw_entry(c)
                body=c.get("text") or c.get("content")
                pid=str(c.get("comment_id") or c.get("cid") or raw.get("cid") or "")
                if isinstance(body,str) and body.strip():
                    key=pid or body
                    if key not in seen:seen.add(key);page_main+=1
                children=raw.get("reply_comment") or c.get("reply_comment") or []
                if not isinstance(children,list):continue
                for child in children[:6]:
                    if not isinstance(child,dict):continue
                    message=child.get("text") or child.get("content")
                    if not isinstance(message,str) or not message.strip():continue
                    ident=str(child.get("cid") or child.get("comment_id") or "") or message
                    token=(pid,ident)
                    if token in inline:continue
                    inline.add(token);page_replies+=1
                    if len(record.get("reply_previews",[]))<9:
                        record.setdefault("reply_previews",[]).append(
                            {"post_url":record["source_video"],
                             "parent_comment_id":pid[:45],
                             "reply_id":ident[:45] if ident!=message else "",
                             "text_excerpt":scrub(message,230),
                             "scope":"inline preview, not complete thread"})
            record["pages_retrieved"]+=1
            record["actual_first_level_text_count"]+=page_main
            record["actual_inline_reply_preview_count"]+=page_replies
            nxt=find_cursor(data)
            record.setdefault("page_summary",[]).append({"index":page+1,
                "http":st,"returned_items":len(batch),"new_first_level":page_main,
                "new_inline_reply_previews":page_replies,
                "has_more":data.get("has_more") if isinstance(data,dict) else None,
                "cursor_present":bool(nxt)})
            if not nxt:
                record["status"]="no_additional_page" if page==0 else "verified_two_pages"
                break
            if nxt==cursor:
                record["status"]="cursor_not_advancing"
                break
            cursor=nxt
        else:
            record["status"]="verified_two_pages"
    except Exception as e:
        record["status"]="error"
        record["error"]=type(e).__name__+":"+scrub(e,160)
    return record
if __name__=="__main__":
    result=main()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    summary={k:v for k,v in result.items() if k!="reply_previews"}
    print(json.dumps({"douyin_normal_comment_pagination":summary},ensure_ascii=False))
