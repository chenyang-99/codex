#!/usr/bin/env python3
"""Build an evidence-labeled AI topic shortlist from actual public-source records.

All source-provided text is untrusted DATA. No generative claims or fabricated
engagement metrics; scoring is transparent and repeatable. No API key needed.
"""
import datetime as dt
import json
import re
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit

HERE=Path(__file__).resolve().parent
OUT=HERE/"output"
TAGS={
    "ai_image":["image generation","image editing","image model","prompt","flux","midjourney",
                "nano banana","design","visual","photo","图像","生图","图片"],
    "ai_video":["video generation","video editing","video model","sora","veo","kling",
                "runway","motion","video","视频","动画"],
    "agent":["agent","workflows","automation","skill","mcp","codex","no-code","n8n","智能体","自动化"],
    "chatgpt":["chatgpt","openai","gpt-","model release","gpt-6","gpt 6"],
    "tutorial":["tutorial","how to","step-by-step","guide","workflow","demo","prompt",
                "build","generate","create","教你","教程","实操","方法","技巧"]
}
NOISE=("financing","fundraising","stocks","ipo","hiring","salary","earnings","supply chain")
WEIGHT={"official":2,"creator":3,"community":1,"media":0,"research":1,"video":3}

def read(path):
    try:
        obj=json.loads((OUT/path).read_text(encoding="utf-8"))
        return obj if isinstance(obj,dict) else {}
    except (OSError,ValueError):
        return {}
def canonical(url):
    if not isinstance(url,str) or not url.startswith(("https://","http://")):return ""
    x=urlsplit(url)
    path=x.path.rstrip("/") or "/"
    return urlunsplit((x.scheme.lower(),x.netloc.lower(),path,"",""))
def age_days(s):
    try:
        t=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
        if t.tzinfo is None:return None
        return (dt.datetime.now(dt.timezone.utc)-t.astimezone(dt.timezone.utc)).total_seconds()/86400
    except (TypeError,ValueError,AttributeError):
        return None
def score(item):
    text=(item.get("title","")+" "+item.get("excerpt","")).lower()
    tags=[k for k,words in TAGS.items() if any(w in text for w in words)]
    age=age_days(item.get("published_utc"))
    if age is None: freshness=0
    elif 0<=age<=3: freshness=5
    elif 0<=age<=7: freshness=3
    elif 0<=age<=30: freshness=1
    else: freshness=-4
    creator=WEIGHT.get(item.get("source_type"),0)
    # Prioritize replicable visual and consumer-AI workflows over generic dev theory.
    topic_weight={"ai_image":5,"ai_video":5,"tutorial":3,"chatgpt":2,"agent":1}
    relevance=sum(topic_weight[k] for k in tags)
    practical=["before and after","step by step","free tool","no-code","prompt template",
               "image generation","video generation","editing","photoshoot","creative","design"]
    relevance += 2 if any(x in text for x in practical) else 0
    technical=["typescript","backend","microservice","sql database","sdk","unit test",
               "devops","docker","ci/cd","pytorch","python 3.","quant research","protein folding"]
    noiselist=[w for w in (*NOISE,*technical) if w in text]
    penalty=min(8,len(noiselist)*3)
    # General dev feeds are useful for research but not the user's primary
    # visual, non-coding tutorial remit. Don't let common jargon crowd out
    # demos and creator workflows.
    origin=(item.get("source") or "").lower()
    if origin.startswith("dev "):penalty+=7
    elif origin in ("github","stack overflow"):penalty+=5
    if "ai_image" in tags or "ai_video" in tags:
        relevance+=3
    if item.get("likes_verified") and item.get("likes") is not None:
        try:
            if int(item["likes"])>=100:relevance+=2
        except (ValueError,TypeError):pass
    # This is NOT a claim about public engagement or virality.
    total=freshness+creator+relevance-penalty
    return total,tags,age,noiselist

def main():
    rss=read("public-rss-candidates.json")
    social=read("topic-candidates.json")
    public=read("public-platforms.json")
    pool=[]
    for item in rss.get("items",[]):
        pool.append({"source":item.get("source"),"source_type":item.get("source_type"),
                     "url":item.get("url"),"title":item.get("title") or "",
                     "excerpt":item.get("excerpt") or "","published_utc":item.get("published_utc"),
                     "verified_scope":"RSS headline + excerpt only",
                     "comments_verified":False,"likes_verified":False})
    for post in social.get("candidates",[]):
        pool.append({"source":post.get("author"),"source_type":"creator",
                     "url":post.get("url"),"title":(post.get("text_excerpt") or "")[:110],
                     "excerpt":post.get("text_excerpt") or "",
                     "published_utc":post.get("created_at"),
                     "verified_scope":"Retrieved public X post excerpt",
                     "comments_verified":bool(post.get("comments_returned")),
                     "comments_returned":post.get("comments_returned",0),
                     "likes_verified":post.get("likes") is not None,
                     "likes":post.get("likes")})
    for entry in public.get("results",[]):
        if entry.get("status")!="verified":continue
        payload=entry.get("sample")
        if isinstance(payload,dict):
            iterable=payload.get("posts") or payload.get("issues") or payload.get("questions") or []
        elif isinstance(payload,list):iterable=payload
        else:iterable=[]
        for raw in iterable:
            if not isinstance(raw,dict):continue
            url=raw.get("url")
            if not url and isinstance(raw.get("uri"),str):
                uri=raw["uri"]
                if uri.startswith("at://") and "/app.bsky.feed.post/" in uri:
                    key=uri.rsplit("/",1)[-1]
                    handle=raw.get("author")
                    if isinstance(handle,str) and key:
                        url=f"https://bsky.app/profile/{handle}/post/{key}"
                else:url=uri
            pool.append({"source":entry.get("platform"),"source_type":"community",
                         "url":url or "", "title":raw.get("title") or raw.get("text") or "",
                         "excerpt":raw.get("text") or "",
                         "published_utc":raw.get("created_at") or raw.get("published"),
                         "verified_scope":"Actual returned public API record",
                         "comments_verified":False,"likes_verified":False})
    seen=set()
    ranked=[]
    for item in pool:
        u=canonical(item["url"])
        if not u or u in seen:continue
        seen.add(u)
        total,tags,age,noise=score(item)
        if not tags:continue
        item["url"]=u
        item["rank_score"]=total
        item["theme_tags"]=tags
        item["age_days"]=round(age,1) if age is not None else None
        item["negative_signals"]=noise
        item["evidence_status"]="needs_original_full_text_verification"
        item["editorial_claims_verified"]=False
        item["social_virality_verified"]=False
        ranked.append(item)
    ranked.sort(key=lambda x:x["rank_score"],reverse=True)
    report={"checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "scope":"Evidence-labeled pre-editorial shortlist",
            "total_raw_candidates":len(pool),"unique_relevant_candidates":len(ranked),
            "source_observation":{"rss_verified_feeds":rss.get("verified_feeds"),
                                  "x_verified_creators":sum(a.get("status")=="verified" for a in social.get("watchlist",[])),
                                  "public_platforms_verified":[r.get("platform") for r in public.get("results",[]) if r.get("status")=="verified"]},
            "shortlist":ranked[:40],
            "missing_steps":["Fetch and verify original full tutorial or prompt for finalists.",
                             "Cross-check author's date, demonstration, license and tool availability.",
                             "Check domestic topic saturation using actual accessible sources.",
                             "Only label virality when contemporaneous engagement is directly observed."]}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"editorial-shortlist.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Evidence-labeled AI editorial shortlist","",
           f"Checked UTC: {report['checked_at_utc']}",
           f"Raw: {len(pool)}; unique topical candidates: {len(ranked)}.",
           "**IMPORTANT:** ranking is not a promise of virality. Original full text needs verification.",""]
    for i,item in enumerate(ranked[:30],1):
        lines.extend([f"### {i}. {item['title'][:145]}",
                      f"Source: {item['source']} | score: {item['rank_score']} | tags: {', '.join(item['theme_tags'])}",
                      f"URL: {item['url']}",
                      f"Actually verified: {item['verified_scope']}; complete tutorial NOT verified.",""])
    (OUT/"editorial-shortlist.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"status":"shortlist_complete","raw_candidates":len(pool),
                      "unique_relevant":len(ranked),"top":len(ranked[:40])},ensure_ascii=False))
if __name__=="__main__":main()
