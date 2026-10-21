#!/usr/bin/env python3
"""Optional Horizon-compatible Apify X keyword search; NEVER paid by default.

No paid API call unless explicit operator authorization + API token + USD cap.
Single query/run; records failures and unknowns, never auto-publishes topics.
"""
import datetime as dt
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE=Path(__file__).resolve().parent
OUT=BASE/"output"
API="https://api.apify.com/v2"

def gate(env):
    if env.get("X_SEARCH_PAID_APPROVED")!="1": return "paid_search_not_approved"
    if env.get("X_SEARCH_APIFY_ENABLE")!="1": return "disabled_by_default"
    if not env.get("APIFY_TOKEN"): return "token_missing"
    try: cap=float(env.get("X_SEARCH_MAX_RUN_USD","0"))
    except ValueError: return "invalid_cap"
    if not 0 < cap <= 1.00: return "cap_missing_or_exceeds_one_dollar"
    return None

def api(method,path,token,payload=None):
    if not path.startswith("/") or "://" in path: raise ValueError("unsafe_api_path")
    req=Request(API+path,method=method,data=(json.dumps(payload).encode() if payload is not None else None),
       headers={"Authorization":"Bearer "+token,"Content-Type":"application/json",
                "Accept":"application/json","User-Agent":"topic-radar/3.2"})
    with urlopen(req,timeout=22) as resp:
        body=resp.read(2500001)
    if len(body)>2500000:raise ValueError("oversized_api_response")
    return json.loads(body)

def normalize(raw,checked_at):
    if not isinstance(raw,dict) or raw.get("noResults"):return None
    tid=str(raw.get("id_str") or raw.get("id") or "").removeprefix("tweet-")
    user=raw.get("user") or {}
    handle=(user.get("screen_name") or user.get("username") or user.get("handle")
            or raw.get("handle") or "") if isinstance(user,dict) else ""
    if not tid.isdigit() or not re.fullmatch(r"[A-Za-z0-9_]{1,15}",str(handle)):return None
    text=str(raw.get("full_text") or raw.get("text") or "").strip()
    if not text:return None
    links=list(dict.fromkeys(m.group(0).rstrip(".,;!") for m in re.finditer(
      r"https://(?:github\.com|huggingface\.co)/[^\s<>\"'，。)）]+",text)))
    metrics={}
    for k,aliases in {"views":("view_count","views"),"likes":("favorite_count","likes"),
                      "reposts":("retweet_count","reposts"),"bookmarks":("bookmark_count","bookmarks"),
                      "replies":("reply_count","replies")}.items():
        for field in aliases:
            value=raw.get(field)
            if type(value) in (int,float) and value>=0:
                metrics[k]=value
                break
    return {"url":f"https://x.com/{handle}/status/{tid}","source":"x_apify_keyword",
            "platform":"x","title":text[:2000],"author":handle,
            "published_utc":raw.get("created_at"),"metrics":metrics,
            "metrics_checked_at":checked_at,"external_links":links[:15],
            "project_url":links[0] if len(links)==1 else "",
            "retrieved_scope":"third_party_apify_search_single_query","editorial_status":"research_candidate_only"}

def query(token,term,cap,call=api,sleep=time.sleep):
    opts=urlencode({"maxTotalChargeUsd":format(cap,".2f"),"maxItems":100,"timeout":90})
    start=call("POST","/acts/altimis~scweet/runs?"+opts,token,
               {"source_mode":"search","search_query":term,"search_sort":"Latest","max_items":100})
    record=(start or {}).get("data") or {}
    run_id,dataset_id=record.get("id"),record.get("defaultDatasetId")
    if not run_id or not dataset_id:raise ValueError("apify_run_ids_missing")
    for _ in range(20):
        status=(call("GET",f"/actor-runs/{run_id}",token).get("data") or {}).get("status")
        if status=="SUCCEEDED":break
        if status in ("FAILED","ABORTED","TIMED-OUT"):raise RuntimeError("apify_run_"+str(status))
        sleep(3)
    else:raise TimeoutError("apify_poll_timeout")
    result=call("GET",f"/datasets/{dataset_id}/items?limit=100",token)
    if not isinstance(result,list):raise ValueError("unexpected_apify_dataset")
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    return [c for raw in result if (c:=normalize(raw,stamp))]

def collect(env=None,call=api):
    env=os.environ if env is None else env
    reason=gate(env)
    if reason:return [],[{"source":"x_apify_keyword","status":"not_configured","items":None,"reason":reason}]
    cfg=json.loads((BASE/"x_discovery_queries_v3.json").read_text(encoding="utf-8"))
    terms=[x for x in cfg.get("queries",[]) if isinstance(x,str) and x.strip()]
    if not terms:return [],[{"source":"x_apify_keyword","status":"empty","items":0,"reason":"no_query"}]
    try:
        rows=query(env["APIFY_TOKEN"],terms[0],float(env["X_SEARCH_MAX_RUN_USD"]),call=call)
        return rows,[{"source":"x_apify_keyword","status":"retrieved" if rows else "empty",
                      "items":len(rows),"query":terms[0]}]
    except (ValueError,RuntimeError,TimeoutError,OSError) as err:
        return [],[{"source":"x_apify_keyword","status":"unavailable","items":None,
                    "error":type(err).__name__+": "+str(err)[:120]}]

def main():
    rows,health=collect()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"x-horizon-apify-v3.json").write_text(json.dumps({
        "checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "items":rows,"source_health":health,
        "limitations":["No paid request without explicit approval+enable+token+spend cap",
                       "Only one paid query/run; not total X coverage; platform-native metrics require verification",
                       "Use first-party or documented actor access; never auto-publish posts"]},
        ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"source":health[0]["source"],"status":health[0]["status"],
                      "items":health[0]["items"],"reason":health[0].get("reason")},
                     ensure_ascii=False))
if __name__=="__main__":main()
