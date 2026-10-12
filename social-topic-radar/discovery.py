#!/usr/bin/env python3
"""Bounded, no-login X creator watchlist for social topic research.

A successful run produces candidate evidence, not claims of complete coverage
or model-generated conclusions. Public replies are sampled, never exhaustive.
"""
import datetime as dt
import json
import math
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
UPSTREAM=HERE/"x_upstream.py"
OUT=HERE/"output"
WATCH=["thsottiaux","karpathy","levelsio","gregisenberg","swyx","egeberkina"]
KEYWORDS=("ai","chatgpt","prompt","image","video","workflow","model",
          "agent","codex","sora","gpt","gemini","claude","creative","openai")

def call(args,seconds=33):
    if not UPSTREAM.exists():
        return None,"upstream_script_missing"
    try:
        p=subprocess.run([sys.executable,str(UPSTREAM),*args],
                         capture_output=True,text=True,timeout=seconds)
        j=json.loads(p.stdout.strip() or "{}")
        if p.returncode or not isinstance(j,dict) or j.get("error"):
            return None, str(j.get("error") if isinstance(j,dict) else f"exit_{p.returncode}")[:180]
        return j,None
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        return None, type(exc).__name__

def engagement(t):
    likes=int(t.get("likes") or 0)
    replies=int(t.get("replies") or 0)
    bookmarks=int(t.get("bookmarks") or 0)
    return round(4*math.log1p(likes)+2*math.log1p(replies)+math.log1p(bookmarks),2)

def compact(t):
    return {
        "id":str(t.get("id") or ""),
        "url":str(t.get("url") or "")[:200],
        "created_at":t.get("created_at"),
        "author":(t.get("author") or {}).get("handle") if isinstance(t.get("author"),dict) else None,
        "text_excerpt":str(t.get("text") or "")[:700],
        "likes":t.get("likes"),
        "replies":t.get("replies"),
        "bookmarks":t.get("bookmarks"),
        "views":t.get("views"),
        "heuristic_engagement_score":engagement(t),
    }

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    results=[]
    status=[]
    for handle in WATCH:
        raw,err=call(["tweets",handle,"--limit","8","--since","3d"])
        if err:
            status.append({"handle":handle,"status":"not_verified","error":err})
            continue
        posts=raw.get("tweets",[]) if isinstance(raw.get("tweets"),list) else []
        own=[p for p in posts if isinstance(p,dict) and p.get("id") and p.get("text")]
        status.append({"handle":handle,"status":"verified" if own else "empty",
                       "returned":len(own),"more":bool(raw.get("more",False))})
        for p in own:
            txt=str(p.get("text") or "").lower()
            if any(k in txt for k in KEYWORDS):
                c=compact(p)
                c["source_type"]="public_x_creator_timeline"
                results.append(c)
        time.sleep(0.4)
    seen=set()
    unique=[]
    for p in sorted(results,key=lambda r:r["heuristic_engagement_score"],reverse=True):
        if p["id"] in seen:continue
        seen.add(p["id"]);unique.append(p)
    # Avoid per-post requests if the upstream is degraded.
    for p in unique[:2]:
        raw,err=call(["tweet",p["url"],"--replies","6"])
        if err:
            p["comment_status"]="not_verified"
            p["comment_error"]=err
            continue
        replies=raw.get("replies",[]) if isinstance(raw.get("replies"),list) else []
        p["comment_status"]="sample_returned" if replies else "empty_or_unavailable"
        p["comments_returned"]=len(replies)
        p["comments_reported_by_x"]=(raw.get("replies_info") or {}).get("on_x")
        p["comment_samples"]=[{"url":r.get("url"),"text_excerpt":str(r.get("text") or "")[:260]}
                               for r in replies if isinstance(r,dict)][:6]
        time.sleep(0.4)
    doc={"checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
         "method":"no-login public creator timeline; bounded sample",
         "watchlist":status, "candidate_count":len(unique),
         "selection":"heuristic based on reported engagement, not an AI quality score or virality prediction",
         "candidates":unique[:20],
         "limitations":["No platform-wide search coverage implied.",
                        "Public third-party endpoints may change or return empty.",
                        "Only up to six public replies sampled per top post.",
                        "No Xiaohongshu/Douyin comment access is implied."]}
    (OUT/"topic-candidates.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8")
    md=["# X 创作者免登录选题候选","",f"获取时间（UTC）：{doc['checked_at_utc']}","",
        "本报告仅列出可实际获取的公开数据，热度评分为简单启发式排序，不是爆款预测。","",
        "## 采集覆盖"]
    for s in status:
        md.append(f"- @{s['handle']}：{s['status']}；取得 {s.get('returned','?')} 条；{s.get('error','')}")
    md+=["","## 优先研究的候选帖"]
    for i,p in enumerate(unique[:15],1):
        md +=[f"### {i}. @{p['author']}（分数 {p['heuristic_engagement_score']}）",
              f"- 原帖：{p['url']}",f"- 发布时间：{p['created_at']}",
              f"- 互动：赞 {p['likes']} / 回复 {p['replies']} / 收藏 {p['bookmarks']}",
              f"- 摘要：{p['text_excerpt'][:320]}",
              f"- 实际评论抽样：{p.get('comments_returned',0)} 条；{p.get('comment_status','未读取')}",""]
    md +=["","⚠️ 未取得评论时，不代表用户没有发表评论；未核实的内容不得标记为已实测。"]
    (OUT/"topic-candidates.md").write_text("\n".join(md),encoding="utf-8")
    print(json.dumps({"status":"discovery_complete","creators_tested":len(status),
          "creators_verified":sum(s["status"]=="verified" for s in status),
          "candidates":len(unique),"comments_samples":sum(p.get("comments_returned",0) for p in unique[:2])},ensure_ascii=False))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
