#!/usr/bin/env python3
"""Single-shot, read-only Xiaohongshu SSR explore proof (no personal account).

New independent route based on tamnd/xiaohongshu-cli @
b60f9a384ed32d002aaacbbff95fedb2bdc96682 (Apache-2.0).
Only naturally served public HTML window.__INITIAL_STATE__ is read. At most
two explore page GETs and one AI note detail GET; no signed JSON API, cookies,
challenge handling, redirects to login, retries, proxies or identity cycling.
"""
from __future__ import annotations
import datetime as dt
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

OUT=pathlib.Path(__file__).resolve().parent/"output"/"xiaohongshu-ssr-public.json"
HOST="https://www.xiaohongshu.com"
TERMS=("ai","aigc","生图","即梦","豆包","提示词","绘图","图片生成","comfyui","seedance","漫剧","chatgpt","人工智能")
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        return None

def clean(x,n=220):
    return re.sub(r"[\x00-\x1f\x7f]+"," ",str(x or "")).strip()[:n]

def get(path):
    opener=urllib.request.build_opener(NoRedirect)
    request=urllib.request.Request(HOST+path,headers={
        "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language":"zh-CN,zh;q=0.9","Accept-Encoding":"identity"})
    try:
        with opener.open(request,timeout=18) as resp:
            return resp.status,resp.geturl(),resp.read(3_000_000)
    except urllib.error.HTTPError as e:
        return e.code,e.headers.get("Location",""),b""

def state_from_html(body):
    marker=b"window.__INITIAL_STATE__"
    i=body.find(marker)
    if i<0:return None
    j=i+len(marker)
    while j<len(body) and body[j] in b" =\t\n":j+=1
    if j>=len(body) or body[j]!=123:return None
    depth=0;quoted=False;escaped=False;buf=bytearray()
    for ch in body[j:]:
        buf.append(ch)
        if quoted:
            if escaped:escaped=False
            elif ch==92:escaped=True
            elif ch==34:quoted=False
        else:
            if ch==34:quoted=True
            elif ch==123:depth+=1
            elif ch==125:
                depth-=1
                if depth==0:break
    if depth:return None
    raw=bytes(buf)
    # SSR serializes bare undefined/NaN. Rewrite only outside quoted strings.
    out=bytearray();i=0;quoted=False;escaped=False
    while i<len(raw):
        ch=raw[i]
        if quoted:
            out.append(ch)
            if escaped:escaped=False
            elif ch==92:escaped=True
            elif ch==34:quoted=False
            i+=1;continue
        if ch==34:quoted=True;out.append(ch);i+=1;continue
        token=next((t for t in (b"undefined",b"-Infinity",b"Infinity",b"NaN")
                    if raw.startswith(t,i)),None)
        if token:
            out.extend(b"null");i+=len(token)
        else:out.append(ch);i+=1
    try:return json.loads(out)
    except (ValueError,UnicodeError):return None

def extract_feed(state):
    feeds=((state.get("feed") or {}).get("feeds") or []) if isinstance(state,dict) else []
    if not isinstance(feeds,list):return []
    rows=[]
    for it in feeds:
        if not isinstance(it,dict):continue
        card=it.get("noteCard") or {}
        if not isinstance(card,dict):continue
        ident=str(it.get("id") or card.get("noteId") or "")
        title=card.get("displayTitle") or ""
        if not re.fullmatch(r"[a-fA-F0-9]{18,30}",ident) or not isinstance(title,str):continue
        rows.append({"id":ident,"title":clean(title,160),
                     "liked_count_raw":clean((card.get("interactInfo") or {}).get("likedCount"),20),
                     "token":it.get("xsecToken") or "",
                     "url":HOST+"/explore/"+ident})
    return rows

def main():
    result={"checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "platform":"xiaohongshu","route":"public server-rendered /explore state, not keyword search",
            "upstream":"tamnd/xiaohongshu-cli@b60f9a384ed32d002aaacbbff95fedb2bdc96682",
            "no_login":True,"no_personal_cookie":True,"no_signed_api":True,
            "actual_feed_notes":0,"ai_relevant_feed_notes":0,
            "actual_ai_note_details":0,"actual_comments":0,
            "keyword_search_verified":False,"comments_verified":False,
            "pages":[],"samples":[],"status":"not_tested"}
    try:
        for path in ("/explore","/explore?channel_id=homefeed.career_v3"):
            status,url,html=get(path)
            page={"path":path,"http_status":status,"redirect":clean(url,180) if status in (301,302,303,307,308) else None,
                  "html_bytes":len(html),"has_state_marker":b"window.__INITIAL_STATE__" in html}
            result["pages"].append(page)
            if status in (301,302,303,307,308,401,403,412,429):
                result["status"]="restricted_or_redirect";break
            if status!=200:
                result["status"]="http_unavailable";break
            st=state_from_html(html)
            if not st:
                result["status"]="no_parseable_public_state";break
            rows=extract_feed(st)
            page["parsed_note_count"]=len(rows)
            result["actual_feed_notes"]+=len(rows)
            ai=[r for r in rows if any(t in r["title"].lower() for t in TERMS)]
            result["ai_relevant_feed_notes"]+=len(ai)
            result["samples"].extend([{k:v for k,v in r.items() if k!="token"} for r in ai[:8]])
            if ai:
                chosen=next((r for r in ai if r["token"]),None)
                if chosen:
                    detail_path="/explore/"+chosen["id"]+"?"+urllib.parse.urlencode(
                        {"xsec_token":chosen["token"],"xsec_source":"pc_feed"})
                    sc,u,html=get(detail_path)
                    result["detail_http_status"]=sc
                    if sc==200:
                        detail=state_from_html(html)
                        mp=(((detail or {}).get("note") or {}).get("noteDetailMap") or {})
                        note=(mp.get(chosen["id"]) or {}).get("note") if isinstance(mp,dict) else None
                        if isinstance(note,dict) and note.get("noteId")==chosen["id"] and (note.get("title") or note.get("desc")):
                            result["actual_ai_note_details"]=1
                            result["verified_detail"]={"url":chosen["url"],
                                "title":clean(note.get("title"),200),
                                "description_excerpt":clean(note.get("desc"),300),
                                "comment_count_reported":clean((note.get("interactInfo") or {}).get("commentCount"),25)}
                result["status"]="verified_public_ai_feed" if ai else "verified_public_feed"
                break
            result["status"]="verified_public_feed" if rows else "empty_feed"
        result["samples"]=result["samples"][:8]
    except (OSError,TimeoutError,ValueError) as e:
        result["status"]="network_or_parse_error"
        result["error"]=type(e).__name__+":"+clean(e,130)
    return result

if __name__=="__main__":
    result=main()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"xhs_public_ssr_probe":result},ensure_ascii=False))
