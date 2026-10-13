#!/usr/bin/env python3
"""Independent no-login OpenWeb Xiaohongshu *public read* smoke test.

Runs only two bounded read operations (searchNotes, getHotSearch). No logging
in, write operations, CAPTCHA processing, retries, cookie persistence or
raw profile collection. A successful CLI exit alone is NOT a data pass.
"""
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
OUT=HERE/"output"/"openweb-xhs-proof.json"
COMMANDS=[
    ("keyword_search","searchNotes",{"keyword":"AI生图"}),
    ("trending_keywords","getHotSearch",{}),
]

def safe(value,limit=120):
    s=re.sub(r"[\x00-\x1f\x7f-\x9f]"," ",str(value or ""))
    return re.sub(r"\s+"," ",s).strip()[:limit]

def collection(obj, keys):
    if isinstance(obj,list):return obj
    if not isinstance(obj,dict):return []
    for key in keys:
        val=obj.get(key)
        if isinstance(val,list):return val
        if isinstance(val,dict):
            nested=collection(val,keys)
            if nested:return nested
    return []

def parse_output(stdout):
    try:
        raw=json.loads(stdout or "{}")
    except ValueError:return None
    if isinstance(raw,dict) and raw.get("output") and raw.get("status"):
        p=Path(raw["output"])
        if p.exists() and p.is_file() and p.stat().st_size<1_000_000:
            try:return json.loads(p.read_text(encoding="utf-8"))
            except ValueError:return None
    return raw

def relevant_posts(obj):
    rows=collection(obj,["notes","items","data","results","list"])
    found=[]
    for it in rows[:30]:
        if not isinstance(it,dict):continue
        note=it.get("noteCard") or it.get("note_card") or it
        if not isinstance(note,dict):continue
        nid=it.get("noteId") or it.get("note_id") or it.get("id") or note.get("noteId") or note.get("note_id")
        title=note.get("displayTitle") or note.get("display_title") or note.get("title")
        token=it.get("xsecToken") or it.get("xsec_token")
        if not nid or not (title or token):continue
        found.append({"note_id":safe(nid,55),"title_excerpt":safe(title,130),
                      "likes":safe(note.get("likedCount") or note.get("liked_count"),35),
                      "has_note_access_token":bool(token)})
    return found

def main():
    result={"checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "tool":"@openweb-org/openweb@0.1.6",
            "platform":"xiaohongshu",
            "account_login":False,
            "personal_cookie_supplied":False,
            "keyword":"AI生图",
            "search_status":"not_tested","verified_posts":0,
            "hot_search_status":"not_tested","verified_hot_terms":0,
            "comments_status":"not_tested","actual_comment_texts":0,
            "note":"Runs only naturally accessible public site read operations, with a clean isolated browser."}
    home=os.environ.get("OPENWEB_HOME","")
    if not home:return dict(result,error="OPENWEB_HOME not set")
    for kind,op,arg in COMMANDS:
        try:
            p=subprocess.run(["openweb","xiaohongshu","exec",op,
                  json.dumps(arg,ensure_ascii=False),"--max-response","1000000"],
                  capture_output=True,text=True,timeout=75,check=False)
            if p.returncode:
                # Abort on auth/captcha/bot block signals rather than attempting another operation.
                err=safe(p.stderr or p.stdout,220)
                result[kind+"_error"]=err
                result["search_status" if kind=="keyword_search" else "hot_search_status"]="failed"
                if any(k in err.lower() for k in
                    ["auth_expired","bot_blocked","login","captcha","验证","登录","permission"]):
                    result["stopped_due_to_login_or_challenge"]=True
                    break
                continue
            data=parse_output(p.stdout)
            if kind=="keyword_search":
                posts=relevant_posts(data)
                result["verified_posts"]=len(posts)
                result["sample_posts"]=posts[:5]
                result["search_status"]="verified_public_post_rows" if posts else "no_structured_posts_verified"
                if not posts:
                    result["response_type"]=type(data).__name__
                    if isinstance(data,dict):
                        result["response_top_level_keys"]=list(data.keys())[:18]
                        result["response_ok"]=data.get("success")
                        result["response_error_type"]=safe(data.get("code") or data.get("error") or data.get("status"),90)
                        if isinstance(data.get("message"),str):
                            result["response_message_excerpt"]=safe(data["message"],170)
                    # No notes: do not make a second access attempt to fetch more XHS data.
                    result["hot_search_status"]="not_attempted_after_empty_keyword_search"
                    break
            else:
                arr=collection(data,["items","data","hotSearch","hot_search","list","keywords","trends"])
                valid=[x for x in arr if isinstance(x,dict) and
                       (x.get("keyword") or x.get("title") or x.get("word"))]
                result["verified_hot_terms"]=len(valid)
                result["hot_search_status"]="verified_terms" if valid else "no_structured_terms_verified"
                result["sample_hot_terms"]=[
                    safe(x.get("keyword") or x.get("title") or x.get("word"),55) for x in valid[:7]]
        except (OSError,ValueError,subprocess.TimeoutExpired) as e:
            result[kind+"_error"]=type(e).__name__+":"+safe(e,130)
            result["search_status" if kind=="keyword_search" else "hot_search_status"]="error"
    return result

if __name__=="__main__":
    output=main()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"openweb_xhs_public_test":output},ensure_ascii=False))
