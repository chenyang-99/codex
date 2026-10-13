#!/usr/bin/env python3
"""Small XHS public guest-search probe; no user account or persistent cookies.

Single bounded, read-only request. Stop if the service requires login, returns
a CAPTCHA, or restricts access. No IP/proxy switching or retries.
"""
import datetime, json, pathlib, re
import requests
from xhshow import Xhshow

OUT=pathlib.Path(__file__).resolve().parent/"output"/"xiaohongshu-guest.json"
KEYWORD="AI生图"
ROOT="https://edith.xiaohongshu.com"
URI="/api/sns/web/v1/search/notes"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

def clean(x,n=170):
    return re.sub(r"[\x00-\x1f\x7f-\x9f]"," ",str(x or ""))[:n]

def summarize(response):
    try:obj=response.json()
    except ValueError:
        return {"status":"non_json","http_status":response.status_code}
    success=obj.get("success") is True
    code=obj.get("code")
    result={"status":"unverified","http_status":response.status_code,
            "api_code":code,"message":clean(obj.get("msg") or obj.get("message"),160)}
    if response.status_code in (401,403,406,429) or code in (-101,-100,461,471):
        result["status"]="restricted_or_login_required"
    elif success and response.status_code==200:
        result["status"]="success"
        result["data"]=obj.get("data") or {}
    return result

def main():
    out={"platform":"xiaohongshu","keyword":KEYWORD,
         "checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "source":"single guest signed public web search attempt",
         "used_personal_account":False,"guest_cookies_retained":False,
         "search_status":"not_tested","verified_posts":0,
         "comments_status":"not_tested","verified_first_level_comments":0,
         "verified_second_level_replies":0}
    session=requests.Session()
    session.headers.update({"User-Agent":UA,"Accept":"application/json,text/plain,*/*",
                            "Referer":"https://www.xiaohongshu.com/"})
    try:
        landing=session.get("https://www.xiaohongshu.com/",timeout=12)
        out["landing_http"]=landing.status_code
        if landing.status_code in (401,403,406,429):
            out["search_status"]="public_home_restricted"
            return out
        if session.cookies.get("web_session"):
            out["search_status"]="unexpected_account_cookie_found"
            return out
        signer=Xhshow()
        a1=session.cookies.get("a1") or Xhshow.generate_a1()
        webid=session.cookies.get("webId") or Xhshow.generate_web_id(a1)
        guest={"a1":a1,"webId":webid}
        data={"keyword":KEYWORD,"page":1,"page_size":5,
              "search_id":signer.get_search_id(),
              "sort":"popularity_descending",
              "note_type":0,"ext_flags":[],"geo":"",
              "image_formats":["jpg","webp","avif"]}
        signed=signer.sign_headers_post(uri=URI,cookies=guest,payload=data,x_rap=True)
        response=session.post(ROOT+URI,json=data,headers={**signed,
                   "User-Agent":UA,"Content-Type":"application/json;charset=UTF-8",
                   "Referer":"https://www.xiaohongshu.com/search_result?keyword=AI%E7%94%9F%E5%9B%BE"},
                   cookies=guest,timeout=23)
        status=summarize(response)
        out["search_status"]=status["status"]
        out["search_http"]=status["http_status"]
        out["search_code"]=status.get("api_code")
        out["search_message"]=status.get("message")
        if status["status"]!="success":return out
        items=status["data"].get("items") or []
        if not isinstance(items,list):
            out["search_status"]="unrecognized_response"
            return out
        posts=[]
        for i in items:
            if not isinstance(i,dict):continue
            note=i.get("note_card") or i.get("note") or {}
            nid=i.get("id") or note.get("note_id")
            if not nid:continue
            posts.append({"id":clean(nid,55),
                          "title":clean(note.get("display_title") or note.get("title")),
                          "xsec_token":i.get("xsec_token"),
                          "likes":clean((note.get("interact_info") or {}).get("liked_count"),30)})
        out["verified_posts"]=len(posts)
        out["posts_sample"]=[{k:v for k,v in p.items() if k!="xsec_token"} for p in posts[:5]]
        out["search_status"]="verified_real_posts" if posts else "empty_result"
        # Only one comment call, and only if search yielded an actual public note and token.
        target=next((p for p in posts if p["xsec_token"]),None)
        if not target:
            out["comments_status"]="not_tested_missing_note_token"
            return out
        cpath="/api/sns/web/v2/comment/page"
        params={"note_id":target["id"],"cursor":"","top_comment_id":"",
                "image_formats":"jpg,webp,avif","xsec_token":target["xsec_token"]}
        ch=signer.sign_headers_get(uri=cpath,cookies=guest,params=params,x_rap=True)
        rep=session.get(ROOT+cpath,params=params,headers={**ch,"User-Agent":UA},cookies=guest,timeout=20)
        st=summarize(rep)
        out["comments_status"]=st["status"]
        out["comments_http"]=st["http_status"]
        out["comments_code"]=st.get("api_code")
        if st["status"]!="success":return out
        vals=st["data"].get("comments") or []
        if not isinstance(vals,list):
            out["comments_status"]="unrecognized_response"
            return out
        out["verified_first_level_comments"]=sum(bool(isinstance(c,dict) and c.get("content")) for c in vals)
        out["verified_second_level_replies"]=sum(
            sum(bool(isinstance(sc,dict) and sc.get("content")) for sc in c.get("sub_comments",[]))
            for c in vals if isinstance(c,dict) and isinstance(c.get("sub_comments"),list))
        out["comments_status"]="verified_real_comment_text" if out["verified_first_level_comments"] else "empty"
        out["comment_samples"]=[{"text_excerpt":clean(c.get("content"),180)}
            for c in vals if isinstance(c,dict) and c.get("content")][:3]
    except Exception as exc:
        out["error"]=type(exc).__name__+": "+clean(exc,150)
    finally:
        session.cookies.clear()
    return out

if __name__=="__main__":
    result=main()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    summary={k:v for k,v in result.items() if k not in ("posts_sample","comment_samples")}
    print(json.dumps({"xhs_guest_keyword_probe":summary},ensure_ascii=False))
