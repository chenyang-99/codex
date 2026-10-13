#!/usr/bin/env python3
"""One nonrepeating async diagnostic of an existing public Douyin reply route.

Uses developer's PUBLIC DEMO user, not a Douyin account. Finds a first-level
comment which reports replies on one known AI video, submits exactly ONE
second-level fetch via the documented REST route (without ?wait), then polls
its *existing task* up to four times to retrieve a stable error.code.
No CAPTCHA, proxy, site account, refresh, forced retry, or user credentials.
"""
import datetime as dt,json,pathlib,re,time,urllib.parse
from public_douyin_demo_test import HTTP,scrub
VIDEO="7692794233737331338"
OUT=pathlib.Path(__file__).resolve().parent/"output"/"douyin-async-reply-root-cause.json"
def list_items(d):
    if isinstance(d,list):return d
    if isinstance(d,dict):
        for key in ("items","comments","comment_list","list","data"):
            if isinstance(d.get(key),list):return d[key]
            if key=="data" and isinstance(d.get(key),dict):return list_items(d["data"])
    return []
def clean_error(obj):
    if not isinstance(obj,dict):return None
    e=obj.get("error")
    if not isinstance(e,dict):return None
    details=e.get("details") if isinstance(e.get("details"),dict) else {}
    keep={k:scrub(v,120) for k,v in details.items() if k in (
         "endpoint","path","rule","reject_reason","field","upstream_status",
         "status_code","classification","cause","reason","origin")}
    return {"code":scrub(e.get("code"),70),"retryable":e.get("retryable"),
            "message_excerpt":scrub(e.get("message"),160),"diagnostic_details":keep}
def main():
    x={"checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "platform":"douyin","video_url":f"https://www.douyin.com/video/{VIDEO}",
       "source":"public demo API async task API; no platform account",
       "first_level_status":"not_tested","parent_reports_replies":False,
       "second_level_status":"not_submitted",
       "second_level_request_count":0,"task_poll_count":0,
       "second_level_actual_comment_texts":0}
    a=HTTP()
    try:
        s,d=a.request("GET","/api/v1/auth/demo",timeout=14)
        pw=(d.get("data") or {}).get("password") if isinstance(d,dict) else None
        if s!=200 or not pw:x["error"]="public demo credentials inaccessible";return x
        s,d=a.request("POST","/api/v1/auth/login",{"username":"demo","password":pw},timeout=14)
        if s!=200 or not isinstance(d,dict) or not d.get("success"):
            x["error"]="public demo login unavailable";return x
        q=urllib.parse.urlencode({"aweme_id":VIDEO,"count":16})
        s,root=a.request("GET","/api/v1/douyin/video/comments?"+q+"&wait=20",timeout=28)
        x["first_level_http"]=s
        x["first_level_status"]="verified" if s==200 and root.get("success") else "not_verified"
        x["parent_error"]=clean_error(root)
        if x["first_level_status"]!="verified":return x
        parents=[]
        for c in list_items(root.get("data")):
            if not isinstance(c,dict):continue
            cid=str(c.get("comment_id") or c.get("cid") or c.get("id") or "")
            reply_count=c.get("reply_count") or c.get("reply_comment_total") or 0
            try:count=int(reply_count)
            except (TypeError,ValueError):count=0
            if count>0 and re.fullmatch(r"\d{5,35}",cid):
                parents.append({"id":cid,"replies":count})
        x["parent_count_reporting_replies"]=len(parents)
        if not parents:return x
        x["parent_reports_replies"]=True
        target=parents[0]
        x["selected_parent_reported_reply_count"]=target["replies"]
        q=urllib.parse.urlencode({"aweme_id":VIDEO,"comment_id":target["id"],"count":5})
        s,d=a.request("GET","/api/v1/douyin/video/comments/replies?"+q,timeout=20)
        x["second_level_request_count"]=1
        x["submit_http"]=s
        x["submit_success"]=d.get("success") if isinstance(d,dict) else None
        x["submit_error"]=clean_error(d)
        if s==200 and d.get("success") and isinstance(d.get("data"),dict):
            x["second_level_status"]="sync_result"
            x["returned_data_keys"]=list(d["data"])[:15]
            x["second_level_actual_comment_texts"]=sum(
                bool(isinstance(i,dict) and (i.get("text") or i.get("content")))
                for i in list_items(d["data"]))
            return x
        task=(d.get("data") or {}).get("task_id") if isinstance(d,dict) else None
        if not isinstance(task,str) or not re.fullmatch(r"[a-fA-F0-9-]{30,40}",task):
            x["second_level_status"]="submit_failed_without_task"
            return x
        x["second_level_status"]="submitted"
        for delay in (1,2,3,4):
            time.sleep(delay)
            s,task_result=a.request("GET","/api/v1/tasks/"+task,timeout=18)
            x["task_poll_count"]+=1
            x["task_http"]=s
            if s!=200 or not isinstance(task_result,dict) or not task_result.get("success"):
                x["task_error"]=clean_error(task_result)
                break
            data=task_result.get("data") or {}
            if not isinstance(data,dict):break
            state=data.get("state")
            x["task_state"]=state
            if state in ("failed","cancelled"):
                x["second_level_status"]="task_"+str(state)
                # Task-level error has same shape but is inside data.
                x["failure"]=clean_error({"error":data.get("error")})
                result_meta=data.get("result_meta")
                if isinstance(result_meta,dict):
                    x["result_meta_keys"]=list(result_meta)[:12]
                break
            if state=="done":
                x["second_level_status"]="task_done"
                payload=data.get("data") or {}
                x["second_level_actual_comment_texts"]=sum(bool(isinstance(i,dict) and
                    (i.get("text") or i.get("content"))) for i in list_items(payload))
                break
        return x
    except Exception as e:
        x["error"]=type(e).__name__+":"+scrub(e,110)
        return x
if __name__=="__main__":
    data=main()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"douyin_second_level_async_root_cause":data},ensure_ascii=False))
