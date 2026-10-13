#!/usr/bin/env python3
"""One-time smoke test of the project's explicitly PUBLIC and shared Douyin demo.

Uses demo login publicly documented by https://douyin.wtf/zh/ , *not* a Douyin
login. No platform account, proxy, captcha bypass, browser identity, credit,
payment, or user secret. Respect public demo rate limits and stop on refusal.
Never print or save demo password/cookies. Only summarize actual content.
"""
import datetime as dt
import http.cookiejar
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

HOST="https://demo.douyin.wtf"
OUT=pathlib.Path(__file__).resolve().parent/"output"/"douyin-public-demo.json"
VIDEO="7690880734421326975"  # discovered from real public AI creator latest videos with 16 reported comments

class HTTP:
    def __init__(self):
        self.opener=urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def request(self,method,path,data=None,timeout=23):
        body=json.dumps(data,ensure_ascii=False).encode() if data is not None else None
        req=urllib.request.Request(
            HOST+path,data=body,
            headers={"User-Agent":"FreePublicDemoSmokeTest/1.0",
                     "Accept":"application/json",
                     "Content-Type":"application/json"},
            method=method)
        try:
            with self.opener.open(req,timeout=timeout) as r:
                b=r.read(250000)
                status=r.status
        except urllib.error.HTTPError as e:
            status=e.code;b=e.read(12000)
        try:j=json.loads(b)
        except (ValueError,UnicodeDecodeError):j={}
        return status,j

def scrub(x,n=180):
    return re.sub(r"[\x00-\x1f\x7f]+"," ",str(x or ""))[:n]

def describe(code,data):
    if not isinstance(data,dict):
        return {"http_status":code,"success":False,"error_code":"non_json"}
    err=data.get("error") if isinstance(data.get("error"),dict) else {}
    result={"http_status":code,"success":data.get("success") is True,
            "error_code":err.get("code"),"error_message":scrub(err.get("message"),180),
            "metadata_keys":list((data.get("data") or {}).keys())[:15]
                            if isinstance(data.get("data"),dict) else []}
    if isinstance(data.get("data"),dict):
        d=data["data"]
        if d.get("task_id"):result["task_state"]=scrub(d.get("state"))
    return result

def main():
    o={"checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "service":"demo.douyin.wtf (official public shared demo, not private cloud)",
       "platform":"douyin",
       "documented_public_demo":True,
       "no_douyin_account_used":True,
       "no_user_credentials_used":True,
       "one_video_id":VIDEO,
       "discovered_via":"actual verified public AI creator feed; not native platform keyword search",
       "platform_keyword_search":"not_supported_by_public_demo_contract",
       "comments":{"state":"not_tested","count":0},
       "replies":{"state":"not_tested","count":0}}
    http=HTTP()
    try:
        status,demopass=http.request("GET","/api/v1/auth/demo",timeout=15)
        o["demo_endpoint"]=describe(status,demopass)
        pwd=(demopass.get("data") or {}).get("password")
        if status!=200 or not pwd:
            o["auth_status"]="public_demo_credential_not_available";return o
        status,login=http.request("POST","/api/v1/auth/login",
                                  {"username":"demo","password":pwd},timeout=18)
        o["demo_service_login"]=describe(status,login)
        if status!=200 or not login.get("success"):
            o["auth_status"]="demo_service_login_failed";return o
        o["auth_status"]="public_demo_session_only"
        # One documented public sample; no crawling or repeated failed attempts.
        status,post=http.request("POST","/api/v1/parse?wait=20",
                      {"url":"https://www.douyin.com/video/"+VIDEO},timeout=28)
        o["post"]=describe(status,post)
        d=post.get("data") if isinstance(post,dict) else None
        if isinstance(d,dict):
            o["post"]["returned_data_fields"]=list(d.keys())[:25]
            # Metadata only, no user identity, no large media.
            o["post"]["description_excerpt"]=scrub(
                d.get("description") or d.get("desc"),240)
            s=d.get("stats") or {}
            if isinstance(s,dict):
                o["post"]["actual_stats"]={k:v for k,v in s.items() if k in ("likes","comments","shares","favorites","digg_count","comment_count","share_count","collect_count")}
        if not (status==200 and post.get("success")):
            o["comments"]["state"]="not_tested_after_post_failure";return o
        params=urllib.parse.urlencode({"aweme_id":VIDEO,"count":12,"wait":20})
        status,comments=http.request("GET",
                           "/api/v1/douyin/video/comments?"+params,timeout=28)
        o["comments"].update(describe(status,comments))
        d=comments.get("data") if isinstance(comments,dict) else None
        if not (status==200 and comments.get("success")):
            o["comments"]["state"]="restricted_or_unavailable";return o
        # API supports different envelopes. Count only actual text-bearing records.
        arr=[]
        if isinstance(d,list):arr=d
        if isinstance(d,dict):
            arr=next((v for k,v in d.items() if k in ("comments","comment_list","items")
                       and isinstance(v,list)),[])
        found=[]
        for c in arr[:12]:
            if not isinstance(c,dict):continue
            message=c.get("text") or c.get("content") or c.get("comment_text")
            if not isinstance(message,str) or not message.strip():continue
            found.append({"sample_excerpt":scrub(message,150),
                          "reply_count_reported":c.get("reply_comment_total") or c.get("reply_count") or c.get("reply_comment_count") or 0,
                          "comment_id":str(c.get("cid") or c.get("comment_id") or c.get("id") or "")[:35]})
        o["comments"]["count"]=len(found)
        o["comments"]["samples"]=found[:6]
        o["comments"]["state"]="verified_actual_comment_text" if found else "no_actual_comment_text_verified"
        if not found or not found[0]["comment_id"]:return o
        target=next((x for x in found if x["reply_count_reported"] and x["comment_id"]),found[0])
        params=urllib.parse.urlencode({"aweme_id":VIDEO,
                     "comment_id":target["comment_id"],"count":5,"wait":20})
        status,replies=http.request("GET","/api/v1/douyin/video/comments/replies?"+params,timeout=26)
        o["replies"].update(describe(status,replies))
        d=replies.get("data") if isinstance(replies,dict) else None
        arr=[]
        if isinstance(d,list):arr=d
        if isinstance(d,dict):
            arr=next((v for k,v in d.items() if k in ("comments","replies","items")
                      and isinstance(v,list)),[])
        o["replies"]["count"]=sum(bool(isinstance(c,dict) and
               (c.get("text") or c.get("content") or c.get("comment_text"))) for c in arr)
        o["replies"]["state"]="verified_actual_reply_text" if o["replies"]["count"] else "no_reply_verified"
    except (urllib.error.URLError,OSError,TimeoutError,ValueError) as e:
        o["error"]=type(e).__name__+":"+scrub(e,130)
    return o

if __name__=="__main__":
    result=main()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"public_douyin_demo_verification":result},ensure_ascii=False))
