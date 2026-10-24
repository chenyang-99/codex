"""OpenTopic Radar Cloudflare adapter; same source registry and Evidence schema as CLI."""
from workers import WorkerEntrypoint, Response, fetch
from models import Evidence, canonicalize, now_utc
from source_config import SOURCES
PAUSED_SOURCE_IDS=frozenset(("linuxdo_top","reddit_localllama_hot","tiktok_explore","behance_ai","artstation_ai","linkedin_public","theresanaiforthat","artificial_analysis","kaggle_models","reddit_search","linuxdo_latest"))
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
import json
import xml.etree.ElementTree as ET


from html.parser import HTMLParser
from urllib.parse import urljoin
from html import unescape
import re
class LinkIndex(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links=[]
        self.href=None
        self.fragments=[]
        self.skip=0
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag in ("script","style","svg","noscript"):self.skip+=1
        if tag=="a" and self.skip==0:
            self.href=d.get("href","")
            self.fragments=[]
    def handle_data(self,data):
        if self.href is not None and not self.skip:self.fragments.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:
            title=" ".join("".join(self.fragments).split())
            if title:self.links.append((self.href,title))
            self.href=None
        if tag in ("script","style","svg","noscript") and self.skip:self.skip-=1
def safe_html_links(src,html,limit):
    parser=LinkIndex()
    parser.feed(html[:480000])
    root_host=src["allowed_hosts"][0]
    prefixes=tuple(src.get("path_prefixes",[]))
    seen=set()
    out=[]
    for ref,title in parser.links:
        title=unescape(title).strip()
        if len(title)<8 or len(title)>260 or title.lower() in ("read more","learn more","see all","view all","sign in","subscribe","get started"):continue
        if ref.startswith(("#","javascript:","mailto:")):continue
        url=urljoin(src["url"],ref)
        p=urlparse(url)
        if p.scheme!="https" or p.hostname!=root_host:continue
        if prefixes and not any(p.path.startswith(x) for x in prefixes):continue
        if p.path in ("","/") or url in seen:continue
        seen.add(url)
        out.append(evidence(src,url,title,{"anchor_url":url,"title":title,"list_page":src["url"]},kind="site_discovery",mode="D",state="partial"))
        if len(out)>=limit:break
    if not out:raise ValueError("No qualified public article links in HTML; JS/login/layout may be required")
    return out

class PrimaryPageExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.description="";self.date=None;self.paragraphs=[];self.p=[];self.in_p=False;self.skip=0
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag in ("script","style","noscript","svg"):self.skip+=1
        if tag=="meta":
            key=(d.get("property") or d.get("name") or "").lower()
            val=unescape(d.get("content") or "").strip()
            if key in ("og:description","description","twitter:description") and len(val)>len(self.description):self.description=val[:1800]
            if key in ("article:published_time","date","datepublished") and not self.date:self.date=val[:64]
        if tag=="p" and self.skip==0:self.in_p=True;self.p=[]
    def handle_data(self,data):
        if self.in_p and self.skip==0:self.p.append(data)
    def handle_endtag(self,tag):
        if tag=="p" and self.in_p:
            t=" ".join("".join(self.p).split())
            if len(t)>=55 and t not in self.paragraphs:self.paragraphs.append(t[:1500])
            self.in_p=False;self.p=[]
        if tag in ("script","style","noscript","svg") and self.skip:self.skip-=1
async def enrich_public_article(src,found):
    url=found[0]["canonical_url"]
    p=urlparse(url)
    if p.scheme!="https" or p.hostname not in src["allowed_hosts"] or p.path in ("","/"):return found
    try:
        markup=await official_get(url,p.hostname)
        parser=PrimaryPageExtractor();parser.feed(markup[:480000])
        paras=parser.paragraphs[:6]
        desc=" ".join(parser.description.split())
        text=" ".join(paras)
        combined=(desc+" "+text).strip() if len(text)>=120 else desc
        if len(combined)<140 or any(bad in combined.casefold()[:400] for bad in ("enable javascript","access denied","captcha","verify you are human")):return found
        ev,raw=found
        ev=dict(ev);ev["body_excerpt"]=combined[:1800]
        ev["content_type"]="public_primary_page_excerpt";ev["evidence_status"]="partial"
        ev["published_at"]=parser.date or ev.get("published_at")
        ev["metrics"]=dict(ev.get("metrics") or {},primary_page_read=True,article_paragraph_count=len(paras))
        raw=json.dumps({"primary_url":url,"page_excerpt":combined[:1800],"description":desc[:400],"published_time":parser.date},ensure_ascii=False)
        ev["raw_ref"]="sha256:"+sha256(raw.encode()).hexdigest()
        return ev,raw
    except Exception:return found

from urllib.parse import quote
class TelegramPostParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.posts=[]
        self.current=None
        self.depth=0
        self.body_depth=0
        self.parts=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        classes=(" "+d.get("class","")+" ")
        if self.current is None:
            if tag=="div" and " tgme_widget_message " in classes and d.get("data-post"):
                self.current=str(d["data-post"])
                self.depth=1
                self.parts=[]
                self.body_depth=0
            return
        if tag=="div":
            self.depth+=1
            if " tgme_widget_message_text " in classes:self.body_depth=self.depth
    def handle_data(self,data):
        if self.current is not None and self.body_depth:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag!="div" or self.current is None:return
        if self.depth==self.body_depth:self.body_depth=0
        self.depth-=1
        if self.depth<=0:
            body=" ".join(" ".join(self.parts).split())
            if body:self.posts.append((self.current,body))
            self.current=None
            self.depth=0
            self.body_depth=0

class EmbedPlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
        self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style"):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style") and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)

def verify_direct_oembed_source(src,target_url):
    if src["source_id"] not in ("x_explore","threads_search","tiktok_explore","instagram_explore"):
        raise ValueError("No oEmbed verification on this source")
    if not target_url or len(target_url)>2048:raise ValueError("Missing/too long direct URL")
    p=urlparse(target_url)
    if p.scheme!="https" or p.port not in (None,443) or p.username or p.password:
        raise ValueError("Direct post URL must be HTTPS")
    host=(p.hostname or "").lower()
    rules={
      "x_explore":(("x.com","www.x.com","twitter.com","www.twitter.com"),r"/[A-Za-z0-9_]{1,20}/status/[0-9]+/?$","https://publish.x.com/oembed"),
      "threads_search":(("threads.com","www.threads.com","threads.net","www.threads.net"),r"/(?:@[A-Za-z0-9_.]+/post/|t/)[A-Za-z0-9_-]+/?$","https://graph.threads.com/oembed"),
      "tiktok_explore":(("tiktok.com","www.tiktok.com"),r"/@[A-Za-z0-9_.]+/video/[0-9]+/?$","https://www.tiktok.com/oembed"),
      "instagram_explore":(("instagram.com","www.instagram.com"),r"/(?:p|reel|tv)/[A-Za-z0-9_-]+/?$","https://graph.facebook.com/v26.0/instagram_oembed")
    }
    allowed,pattern,api=rules[src["source_id"]]
    if host not in allowed or not re.fullmatch(pattern,p.path):raise ValueError("Unexpected public URL pattern")
    canonical="https://"+host+p.path
    api_target="https://x.com"+p.path if src["source_id"]=="x_explore" else canonical
    return canonical,api+"?url="+quote(api_target,safe=""),urlparse(api).hostname

async def gather_oembed(src,target_url):
    canonical,endpoint,host=verify_direct_oembed_source(src,target_url)
    data=json.loads(await official_get(endpoint,host))
    if not isinstance(data,dict) or not isinstance(data.get("html"),str) or len(data["html"])<20:raise ValueError("No public embed content")
    parser=EmbedPlainText()
    parser.feed(data["html"][:24000])
    excerpt=" ".join(" ".join(parser.parts).split())[:1400]
    title=" ".join(str(data.get("title") or excerpt[:180] or "Public post").split())[:280]
    provider=str(data.get("provider_name") or "")
    expected={"x_explore":("Twitter","X"),"threads_search":("Threads",),"tiktok_explore":("TikTok",),"instagram_explore":("Instagram",)}
    if provider and provider not in expected[src["source_id"]]:raise ValueError("Unexpected embed provider")
    if src["source_id"] in ("threads_search","instagram_explore"):
        original=("https://www.threads.com"+urlparse(canonical).path) if src["source_id"]=="threads_search" else canonical
        p=urlparse(original)
        html=await official_get(original,p.hostname)
        page=PrimaryPageExtractor();page.feed(html[:1800000])
        real=" ".join(page.description.split())
        if len(real)<65 or real.casefold() in ("view on threads","view this post on instagram"):
            raise ValueError("Official oEmbed works but no real original post text available")
        preview_only=src["source_id"]=="instagram_explore"
        raw={"direct_post_url":canonical,"embed_provider":provider,"text_from_original_page":real[:1500],"original_public_page":original,"verification_api":endpoint.split("?")[0],"media_content_reviewed":False,"risk":"visual claim not verified; research_only" if preview_only else "original page meta text only"}
        return [evidence(src,canonical,real[:180],raw,excerpt=real[:1500],kind="public_post_original_page_excerpt",mode="D",state="research_only" if preview_only else "partial",metrics={"source_page_read":True,"video_visuals_reviewed":False})]
    raw={"target_url":canonical,"embed_provider":provider,"title":title,"body_excerpt":excerpt,"verification_api":endpoint.split("?")[0]}
    return [evidence(src,canonical,title,raw,author=str(data.get("author_name") or ""),excerpt=excerpt,kind="public_post_embed",mode="D",state="official_metadata_only")]


# FxEmbed is an opt-in third-party research provider, not an X-origin feed.
def fx_post_url(post):
    url=post.get("url") if isinstance(post,dict) else None
    if not isinstance(url,str):return None
    p=urlparse(url)
    if p.scheme!="https" or p.hostname not in ("x.com","twitter.com","www.x.com","www.twitter.com"):
        return None
    if not re.fullmatch(r"/[A-Za-z0-9_]{1,20}/status/[0-9]{2,20}/?",p.path):
        return None
    return "https://x.com"+p.path.rstrip("/")


async def discover_tavily_keyless_x(src,keyword,limit):
    from pyodide.ffi import to_js
    if not isinstance(keyword,str) or not 2<=len(keyword)<=90 or any(ord(c)<32 for c in keyword):
        raise ValueError("X keyword must be 2-90 printable characters")
    words=[w.casefold() for w in re.findall(r"[A-Za-z0-9]{2,}",keyword)]
    if not words:raise ValueError("No searchable keyword")
    params={"query":keyword+" site:x.com","search_depth":"basic","max_results":10,
            "include_domains":["x.com","twitter.com"],"include_raw_content":False,"include_answer":False}
    init={"method":"POST","headers":{"content-type":"application/json",
          "X-Tavily-Access-Mode":"keyless","accept":"application/json"},
          "body":json.dumps(params,ensure_ascii=False),"redirect":"manual"}
    response=await fetch("https://api.tavily.com/search",method="POST",headers=init["headers"],body=init["body"],redirect="manual")
    status=int(response.status)
    if status!=200:raise ValueError("Tavily_keyless_HTTP_"+str(status))
    length=response.headers.get("content-length")
    if length and int(length)>MAX_BYTES:raise ValueError("Tavily_response_too_large")
    body=await response.text()
    if len(body.encode("utf-8"))>MAX_BYTES:raise ValueError("Tavily_response_too_large")
    payload=json.loads(body)
    if not isinstance(payload,dict) or not isinstance(payload.get("results"),list):
        raise ValueError("Tavily_invalid_response")
    verified=[];seen=set();attempted=0
    for hit in payload["results"][:10]:
        if not isinstance(hit,dict):continue
        try:
            canonical,_,_=verify_direct_oembed_source(src,str(hit.get("url") or ""))
        except ValueError:continue
        if canonical in seen:continue
        seen.add(canonical)
        attempted+=1
        try:docs=await gather_fx_public(src,1,"D",canonical,"")
        except ValueError:continue
        if not docs:continue
        ev,raw=docs[0]
        hay=(ev.get("title","")+" "+ev.get("body_excerpt","")).casefold()
        if not all(w in hay for w in words):continue
        ev["mode"]="K"
        ev["content_type"]="third_party_x_index_discovered_post"
        ev["evidence_status"]="partial"
        ev["access_limitation"]="Discovered in public web index, not all X or real time. Independently refetched via FxEmbed third party; upstream rights unverified. Search API output not stored."
        ev["metrics"]=dict(ev.get("metrics") or {})
        ev["metrics"]["discovery_method"]="tavily_keyless_web_index"
        ev["metrics"]["query"]=keyword
        verified.append((ev,raw))
        if len(verified)>=limit:break
    return {"items":verified,"index_count":len(payload["results"]),"attempted_posts":attempted}

async def r82_x_ai_monitored_hot(src,limit):
    # Curated AI accounts ONLY; this is neither X Trends nor global X search.
    watch=("OpenAI","AnthropicAI","GoogleDeepMind","NVIDIAAI","MistralAI")
    now=datetime.now(timezone.utc)
    fresh=[];unique=set();upstream_ok=0;upstream_errors=[]
    for handle in watch:
        feed="https://fxtwitter.com/"+handle+"/feed.xml?count=5"
        try:
            feed_src=dict(src);feed_src["url"]=feed
            items=parse_rss_feed(feed_src,await official_get(feed,"fxtwitter.com"),5)
            upstream_ok+=1
        except Exception as exc:
            upstream_errors.append(handle+":"+str(exc)[:50]);continue
        for ev,raw in items[:3]:
            link=ev.get("canonical_url","");parts=urlparse(link).path.split("/")
            if len(parts)<4 or parts[-2]!="status" or not re.fullmatch(r"[0-9]{12,20}",parts[-1]):continue
            if link in unique:continue
            date=r79_parse_date(ev.get("published_at"))
            if not date:continue
            try:age=(now-datetime.fromisoformat(date)).total_seconds()/3600
            except Exception:continue
            if age<0 or age>72:continue
            unique.add(link);fresh.append((ev,parts[-1],age,handle))
    if upstream_ok==0:raise ValueError("X monitored AI RSS feeds all unavailable")
    ranked=[];verified=0
    for ev,status_id,age,feed_handle in fresh[:12]:
        try:
            packet=json.loads(await official_get("https://api.fxtwitter.com/2/status/"+status_id,"api.fxtwitter.com"))
            post=packet.get("status")
            if packet.get("code")!=200 or not isinstance(post,dict):continue
            canonical=fx_post_url(post)
            if not canonical or canonical.split("/")[-1]!=status_id:continue
            msg=post.get("text")
            if not isinstance(msg,str) or len(msg.strip())<35:continue
            source_time=r79_parse_date(post.get("created_at"))
            if not source_time:continue
            author=post.get("author") or {}
            actual_handle=str(author.get("screen_name") or "") if isinstance(author,dict) else ""
            if actual_handle.casefold()!=feed_handle.casefold():continue
            metrics=[]
            for key in ("likes","reposts","quotes","replies"):
                n=post.get(key)
                if not isinstance(n,(int,float)) or isinstance(n,bool) or n<0:break
                metrics.append(int(n))
            if len(metrics)!=4:continue
            verified+=1
            likes,reposts,quotes,replies=metrics
            engagement=likes+2*reposts+2*quotes+replies
            velocity=round(engagement/((age+2)**0.6),3)
            record={"provider":"FxEmbed public third party","feed_account":feed_handle,"observed_post":post,"rank_scope":"five_monitored_ai_accounts_last_72h","metrics_observed_at":now.isoformat(),"not_official_x_trends":True,"independent_media_review":False}
            ev_new,raw_new=evidence(src,canonical,msg[:170],record,author=actual_handle,published_at=source_time,excerpt=msg,kind="monitored_account_high_engagement_post_not_x_trends",mode="H",state="partial",metrics={"fx_likes":likes,"fx_reposts":reposts,"fx_quotes":quotes,"fx_replies":replies,"r82_engagement_count":engagement,"r82_72h_velocity_score":velocity})
            ev_new["access_limitation"]="Scoped to 5 named AI accounts, third-party metrics; NOT X native trends or worldwide search; original X session not verified"
            ranked.append((velocity,engagement,ev_new,raw_new))
        except Exception as exc:
            upstream_errors.append(status_id+":"+str(exc)[:40]);continue
    if not ranked:raise ValueError("No valid dated and metric-verified monitored AI posts in past 72h")
    ranked.sort(key=lambda x:(x[0],x[1]),reverse=True)
    result=[]
    for rank,(_,_,ev,raw) in enumerate(ranked[:limit],1):
        ev["metrics"]["r82_cohort_rank"]=rank
        ev["metrics"]["r82_cohort_accounts"]=len(watch)
        ev["metrics"]["r82_scanned_fresh_posts"]=len(fresh)
        ev["metrics"]["r82_verified_posts"]=verified
        result.append((ev,raw))
    return result

async def r84_twitterapi_io_read(src, limit, mode, query, env):
    # Optional READ ONLY external provider, not X official API. No key in source, URL or logs.
    # No cron; only explicit /collect source=x_explore provider=twitterapi_io.
    if mode not in ("H","K"):
        raise ValueError("twitterapi_io_provider_supports_only_H_and_K")
    key=getattr(env,"TWITTERAPI_IO_KEY",None)
    if not key:raise ValueError("twitterapi_io_secret_not_configured")
    if mode=="H":
        woeid=(query or "1").strip()
        if not re.fullmatch(r"[0-9]{1,10}",woeid):raise ValueError("twitterapi_io_H_requires_numeric_WOEID")
        url="https://api.twitterapi.io/twitter/trends?woeid="+woeid+"&count=30"
    else:
        keyword=" ".join(str(query or "").split())
        if not 2<=len(keyword)<=90 or any(ord(ch)<32 for ch in keyword):
            raise ValueError("twitterapi_io_K_requires_2_to_90_printable_characters")
        url="https://api.twitterapi.io/twitter/tweet/advanced_search?query="+quote(keyword,safe="")+"&queryType=Latest"
    response=await fetch(url,headers={"X-API-Key":str(key),"accept":"application/json"},redirect="manual")
    status=int(response.status)
    if status in (401,403):raise ValueError("twitterapi_io_credential_rejected")
    if status in (402,429):raise ValueError("twitterapi_io_balance_or_rate_limit_HTTP_"+str(status))
    if status!=200:raise ValueError("twitterapi_io_HTTP_"+str(status))
    text=await response.text()
    if len(text)>200000:raise ValueError("twitterapi_io_payload_too_large")
    payload=json.loads(text)
    if not isinstance(payload,dict):raise ValueError("twitterapi_io_response_not_object")
    results=[]
    if mode=="H":
        if payload.get("status")!="success" or not isinstance(payload.get("trends"),list):
            raise ValueError("twitterapi_io_trends_missing_or_provider_error")
        for entry in payload["trends"][:30]:
            trend=entry.get("trend") if isinstance(entry,dict) else None
            if not isinstance(trend,dict):continue
            name=str(trend.get("name") or "").strip()[:180]
            target=trend.get("target") or {}
            term=str(target.get("query") or name) if isinstance(target,dict) else name
            if len(name)<2 or not term:continue
            xlink="https://x.com/search?q="+quote(term,safe="")
            rank=trend.get("rank")
            raw={"provider":"twitterapi.io","source_type":"third_party_regional_trend_snapshot","name":name,"rank":rank,"woeid":woeid,"provider_metadata":payload.get("metadata"),"not_official_x_trends":True}
            ev,body=evidence(src,xlink,name,raw,excerpt="Region "+woeid+" third-party trend snapshot: "+name,mode="H",kind="twitterapi_io_region_trend_topic_not_native",state="research_only",metrics={"r84_region_woeid":woeid,"r84_trend_rank":rank if isinstance(rank,int) else None})
            ev["access_limitation"]="Third-party TwitterAPI.io regional trend proxy; NOT X official trends; topic not necessarily about AI"
            results.append((ev,body))
            if len(results)>=limit:break
    else:
        tweets=payload.get("tweets")
        if not isinstance(tweets,list):raise ValueError("twitterapi_io_search_missing_tweets")
        for t in tweets:
            if not isinstance(t,dict):continue
            ident=str(t.get("id") or "")
            user=t.get("author") or {}
            handle=str(user.get("userName") or "") if isinstance(user,dict) else ""
            if isinstance(user,dict) and user.get("protected") is True:continue
            msg=str(t.get("text") or "").strip()
            if not re.fullmatch(r"[0-9]{10,20}",ident) or not re.fullmatch(r"[A-Za-z0-9_]{1,15}",handle) or not msg:continue
            url="https://x.com/"+handle+"/status/"+ident
            metrics={"likes":t.get("likeCount"),"reposts":t.get("retweetCount"),"quotes":t.get("quoteCount"),"replies":t.get("replyCount"),"views":t.get("viewCount")}
            raw={"provider":"twitterapi.io","tweet_id":ident,"author":handle,"text":msg[:2000],"published_at":t.get("createdAt"),"public_metrics":metrics,"provider_scope":"paid_third_party_advanced_search_first_page"}
            ev,body=evidence(src,url,msg[:180],raw,author=handle,published_at=t.get("createdAt"),excerpt=msg[:2000],mode="K",kind="twitterapi_io_public_search_post",state="partial",metrics={"r84_likes":metrics["likes"],"r84_reposts":metrics["reposts"],"r84_quotes":metrics["quotes"],"r84_replies":metrics["replies"],"r84_views":metrics["views"]})
            ev["access_limitation"]="Third-party TwitterAPI.io query results; not native X-authenticated API, completeness not verified; up to 20 posts may be billed even when 3 stored"
            results.append((ev,body))
            if len(results)>=limit:break
    if not results:raise ValueError("twitterapi_io_no_usable_results")
    return results

async def gather_fx_public(src,limit,mode,target_url,query):
    if mode not in ("D","K","F","H"):
        raise ValueError("Invalid FxTwitter mode")
    base="https://api.fxtwitter.com"
    if mode=="H":return await r82_x_ai_monitored_hot(src,limit)
    if mode=="D":
        canonical,_,_=verify_direct_oembed_source(src,target_url)
        ident=urlparse(canonical).path.split("/")[-1]
        if not re.fullmatch(r"[0-9]{2,20}",ident):raise ValueError("Invalid X status ID")
        endpoint=base+"/2/status/"+ident
    elif mode=="K":
        if not isinstance(query,str) or not 2<=len(query)<=90 or any(ord(c)<32 for c in query):
            raise ValueError("X keyword query required, 2-90 characters")
        endpoint=base+"/2/search?q="+quote(query,safe="")+"&feed=latest&count="+str(limit)
    elif mode=="F":
        handle=str(query).lstrip("@")
        if not re.fullmatch(r"[A-Za-z0-9_]{1,15}",handle):
            raise ValueError("Known public X handle required")
        feed="https://fxtwitter.com/"+handle+"/feed.xml?count="+str(max(3,limit))
        copy=dict(src);copy["url"]=feed
        items=parse_rss_feed(copy,await official_get(feed,"fxtwitter.com"),limit)
        for ev,raw in items:
            ev["mode"]="F";ev["evidence_status"]="partial";ev["content_type"]="third_party_x_rss_post"
            ev["access_limitation"]="FxTwitter RSS is third-party, upstream X session not verified"
        return items
    else:
        endpoint=base+"/2/trends?type=trending&count=20"
    try:
        payload=json.loads(await official_get(endpoint,"api.fxtwitter.com"))
    except ValueError as exc:
        if mode!="K" or str(exc)!="HTTP 404":raise
        try:
            webindex=await discover_tavily_keyless_x(src,limit,query)
            if webindex["items"]:return webindex["items"]
        except (ValueError,TypeError):pass
        found=[];working=0
        for handle in ("OpenAI","AnthropicAI","NVIDIAAI"):
            feed="https://fxtwitter.com/"+handle+"/feed.xml?count=15"
            try:
                clone=dict(src);clone["url"]=feed
                items=parse_rss_feed(clone,await official_get(feed,"fxtwitter.com"),15)
                working+=1
            except ValueError:continue
            for ev,raw in items:
                if query.casefold() not in (ev["title"]+" "+ev["body_excerpt"]).casefold():continue
                ev["mode"]="K";ev["evidence_status"]="partial";ev["content_type"]="third_party_x_rss_post"
                ev["access_limitation"]="Keyword matching ONLY 3 watched author RSS feeds, not global X search; FxEmbed upstream unknown"
                found.append((ev,raw))
                if len(found)>=limit:return found
        if not working:raise ValueError("All watched X RSS unavailable")
        return found
    if not isinstance(payload,dict) or payload.get("code")!=200:
        raise ValueError("FxTwitter non-success application status")
    if mode=="H":
        topics=payload.get("trends")
        if not isinstance(topics,list):raise ValueError("Unexpected FxTwitter trends")
        result=[]
        for topic in topics[:limit]:
            if not isinstance(topic,dict):continue
            name=str(topic.get("name") or "").strip()
            if not 2<=len(name)<=150:continue
            link="https://x.com/search?q="+quote(name,safe="")
            record={"provider":"FxEmbed third party","kind":"trend_topic","item":topic,"api_resource":"/2/trends","original_x_verified":False}
            ev,raw=evidence(src,link,name,record,excerpt=str(topic.get("context") or ""),kind="third_party_trend_hint",mode="H",state="partial",metrics={"fx_rank":topic.get("rank")})
            ev["access_limitation"]="FxEmbed proxy trend; not an X post, not verified X Explore"
            result.append((ev,raw))
        return result
    posts=[payload.get("status")] if mode=="D" else payload.get("results")
    if not isinstance(posts,list):raise ValueError("Unexpected FxTwitter results")
    results=[]
    for post in posts[:limit]:
        if not isinstance(post,dict) or post.get("type") not in ("status",None):continue
        post_url=fx_post_url(post)
        msg=post.get("text")
        if not post_url or not isinstance(msg,str) or not msg.strip():continue
        if mode=="D" and post_url.split("/")[-1]!=ident:raise ValueError("FxTwitter post ID mismatch")
        author=post.get("author") or {}
        handle=str(author.get("screen_name") or "") if isinstance(author,dict) else ""
        rec={"provider":"FxEmbed third party","mode":mode,"post":post,"upstream_x_auth_unknown":True}
        metrics={"fx_likes":post.get("likes"),"fx_reposts":post.get("reposts"),"fx_quotes":post.get("quotes"),"fx_replies":post.get("replies")}
        ev,raw=evidence(src,post_url,msg[:180],rec,author=handle,published_at=post.get("created_at"),excerpt=msg,kind="third_party_x_post",mode=mode,state="partial",metrics=metrics)
        ev["access_limitation"]="Third-party FxEmbed content; direct X reading and upstream session not verified"
        results.append((ev,raw))
    return results


async def gather_aa_free(src,limit,env,dataset):
    """Official authenticated v2 Free API only; no website scraping."""
    routes={
      "language":"/api/v2/language/models/free?page=1",
      "image":"/api/v2/media/text-to-image/models/free",
      "video":"/api/v2/media/text-to-video/models/free"
    }
    if dataset not in routes:raise ValueError("Allowed datasets: language, image, video")
    secret=getattr(env,"AA_API_KEY",None)
    if not secret:raise ValueError("credential_required: AA_API_KEY is not configured")
    url="https://artificialanalysis.ai"+routes[dataset]
    p=urlparse(url)
    if p.scheme!="https" or p.hostname!="artificialanalysis.ai":raise ValueError("Invalid official API endpoint")
    response=await fetch(url,headers={"accept":"application/json","x-api-key":str(secret),"user-agent":"OpenTopicRadar/0.1 official-free-api"},redirect="manual")
    status=int(response.status)
    if status in (401,403,429):raise ValueError("official_API_HTTP_"+str(status))
    if status!=200:raise ValueError("official_API_HTTP_"+str(status))
    if response.headers.get("content-length") and int(response.headers.get("content-length"))>MAX_BYTES:
        raise ValueError("AA API response size limit exceeded")
    body=await response.text()
    if len(body.encode("utf-8"))>MAX_BYTES:raise ValueError("AA API response size limit exceeded")
    payload=json.loads(body)
    if not isinstance(payload,dict) or not isinstance(payload.get("data"),list):
        raise ValueError("Invalid AA free API response")
    data=payload["data"]
    summary=[]
    for item in data[:limit]:
        if not isinstance(item,dict) or not item.get("name"):continue
        record={"name":str(item["name"])[:160],"id":item.get("id"),"slug":item.get("slug"),"creator":(item.get("model_creator") or {}).get("name") if isinstance(item.get("model_creator"),dict) else None}
        if dataset=="language":
            evs=item.get("evaluations") or {}
            if isinstance(evs,dict):record["indexes"]={k:v for k,v in evs.items() if k in ("artificial_analysis_intelligence_index","artificial_analysis_coding_index","artificial_analysis_agentic_index") and isinstance(v,(int,float,str,dict))}
            record["performance"]=item.get("performance")
            record["pricing"]=item.get("pricing")
        else:
            record["elo"]=item.get("elo")
            record["ci_95"]=item.get("ci_95")
        summary.append(record)
    if not summary:raise ValueError("No valid records in official API snapshot")
    title="Artificial Analysis Free "+dataset+" benchmark sample"
    excerpt="; ".join(x["name"] for x in summary)[:1900]
    snapshot={"provider":"Artificial Analysis official API v2 Free","endpoint":routes[dataset],"dataset":dataset,"attribution":"https://artificialanalysis.ai/","tier":payload.get("tier"),"index_version":payload.get("intelligence_index_version"),"sample":summary,"sample_only":True}
    ev,raw=evidence(src,url,title,snapshot,excerpt=excerpt,kind="official_benchmark_sample",mode="K",state="partial",metrics={"sample_size":len(summary)})
    ev["access_limitation"]="Requires server-side AA_API_KEY; not a full leaderboard export or a hot/trending ranking"
    return [(ev,raw)]


def parse_rss_feed(src,xml,limit):
    if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():raise ValueError("Unsafe XML declaration")
    root=ET.fromstring(xml)
    tag=lambda e:e.tag.rsplit("}",1)[-1]
    children=lambda e,n:[v for v in e if tag(v)==n]
    child=lambda e,n:next(iter(children(e,n)),None)
    field=lambda e,n:" ".join("".join(child(e,n).itertext()).split()) if child(e,n) is not None else ""
    if tag(root)=="rss":
        channel=child(root,"channel")
        if channel is None:raise ValueError("Missing RSS channel")
        entries=children(channel,"item");rss=True
    elif tag(root)=="feed":entries=children(root,"entry");rss=False
    else:raise ValueError("Invalid RSS/Atom root")
    results=[]
    for item in entries[:limit]:
        title=field(item,"title")
        if rss:
            url=field(item,"link");published=field(item,"pubDate");author=field(item,"author");summary=field(item,"description")
        else:
            link=next((v for v in children(item,"link") if v.attrib.get("rel","alternate")=="alternate"),None)
            url=link.attrib.get("href","") if link is not None else ""
            published=field(item,"published") or field(item,"updated");author="";summary=field(item,"summary")
        if not summary:summary=field(item,"encoded") or field(item,"content")
        if "<" in summary and ">" in summary:
            txt=EmbedPlainText();txt.feed(summary[:100000]);summary=" ".join(" ".join(txt.parts).split())
        summary=" ".join(unescape(summary).split())[:1900]
        if title and url and urlparse(url).scheme:
            results.append(evidence(src,url,title,{"title":title,"url":url,"published":published,"excerpt":summary[:1000],"feed":src["url"]},author=author,published_at=published or None,excerpt=summary,kind="feed_entry",mode="F",state="partial"))
    return results



# R16: offline contract and parser fixtures, no outbound requests.
SUPPORTED_KINDS={
  "hn_topstories","github_search","rss","hf_repo_list","reddit_listing",
  "bsky_trends","x_hybrid_fx","oembed_direct","html_index","civitai_models",
  "devto_articles","gitlab_projects","bsky_search","arena_hf_rows","aa_v2_free_api",
  "telegram_public_posts","markdown_changelog","hf_daily_papers","github_trending_public","youtube_public_search_html",
  "public_token_rankings","official_startup_benefits",
}
def classify_source(s, env):
    kind=s.get("kind","")
    stage=s.get("deployment_stage","")
    gate="needs_live_probe"
    if stage=="registered_only":gate="site_permission_required"
    elif kind=="aa_v2_free_api" and not getattr(env,"AA_API_KEY",None):gate="credential_required"
    elif kind=="oembed_direct":gate="public_post_url_required"
    elif kind=="x_hybrid_fx":gate="public_post_url_or_explicit_third_party"
    issues=[]
    p=urlparse(s.get("url",""))
    hosts=s.get("allowed_hosts") or []
    if p.scheme!="https" or not p.hostname or p.port not in (None,443) or p.username or p.password:
        issues.append("unsafe_source_url")
    if p.hostname not in hosts or len(hosts)!=1:issues.append("source_host_allowlist_mismatch")
    if kind not in SUPPORTED_KINDS and stage!="registered_only":issues.append("missing_dispatch")
    if not isinstance(s.get("modes"),list):issues.append("invalid_modes")
    if stage not in ("registered_only","adapter_configured"):issues.append("invalid_stage")
    if kind=="rss" and "F" not in s.get("modes",[]):issues.append("rss_mode_mismatch")
    if kind=="aa_v2_free_api" and p.path!="/api/v2/language/models/free":issues.append("aa_endpoint_mismatch")
    if kind=="oembed_direct" and s.get("source_id") not in ("threads_search","tiktok_explore","instagram_explore"):issues.append("unknown_oembed")
    return {"source_id":s["source_id"],"kind":kind,"stage":stage,"gate":gate,
        "contract":"pass" if not issues else "fail","issues":issues,
        "semantic_scope":("official_news_only" if s["source_id"]=="pinterest_ai" else
                          "third_party_opt_in" if kind=="x_hybrid_fx" else
                          "public_index_only" if kind=="html_index" else
                          "official_free_api_sample" if kind=="aa_v2_free_api" else
                          "direct_post_only" if kind=="oembed_direct" else "source_limited")}

def selftest_report(env):
    checks=[classify_source(x,env) for x in SOURCES]
    ids=[x["source_id"] for x in checks]
    if len(set(ids))!=len(ids):
        for x in checks:
            x["issues"].append("duplicate_source_id")
            x["contract"]="fail"
    fixtures={"html_links":"fail","rss_rss":"fail","rss_atom":"fail"}
    dummy={"source_id":"test_public","platform":"test","url":"https://example.org/","allowed_hosts":["example.org"]}
    try:
        a=safe_html_links(dummy,'<a href="/news/test">Original AI research launch details</a>',1)
        if len(a)==1:fixtures["html_links"]="pass"
    except Exception:pass
    sample_url="https://example.org/posts/ai-news"
    try:
        x=parse_rss_feed(dummy,"<rss version='2.0'><channel><item><title>Original AI paper overview</title><link>"+sample_url+"</link><pubDate>Fri, 23 Oct 2026 00:00:00 GMT</pubDate></item></channel></rss>",1)
        if len(x)==1:fixtures["rss_rss"]="pass"
    except Exception:pass
    try:
        x=parse_rss_feed(dummy,'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Original AI paper overview</title><link href="'+sample_url+'"/><updated>2026-10-23T00:00:00Z</updated></entry></feed>',1)
        if len(x)==1:fixtures["rss_atom"]="pass"
    except Exception:pass
    pass_count=sum(x["contract"]=="pass" for x in checks)
    return {"scope":"offline_contract_and_local_parser_fixtures_only","real_upstream_requests":0,
        "registered":len(checks),"configured":sum(x["stage"]=="adapter_configured" for x in checks),
        "contract_pass":pass_count,"contract_fail":len(checks)-pass_count,
        "fixture_checks":fixtures,"sources":checks,
        "interpretation":"A passing contract is NOT a real source HTTP or ingestion success."}

BY_ID={s["source_id"]:s for s in SOURCES}
MAX_BYTES=2097152
def respond(payload,status=200):
    return Response.json(payload,status=status,headers={"cache-control":"no-store","x-content-type-options":"nosniff"})
def rows_data(o):
    if hasattr(o,"to_py"):o=o.to_py()
    if hasattr(o,"results"):return rows_data(o.results)
    if isinstance(o,dict):return rows_data(o.get("results",[]))
    if isinstance(o,list):return [x.to_py() if hasattr(x,"to_py") else x for x in o]
    return o
async def rows(db,sql,args=()):
    st=db.prepare(sql)
    if args:st=st.bind(*args)
    return rows_data(await st.all())
async def official_get(url,host):
    """Only public HTTPS sources; bounded same-host redirects, no credential forwarding."""
    p=urlparse(url)
    if p.scheme!="https" or p.hostname!=host or p.port not in (None,443) or p.username or p.password:
        raise ValueError("URL not in official host allowlist")
    current=url
    for step in range(4):
        r=await fetch(current,headers={"accept":"application/json,application/rss+xml,application/atom+xml,application/xml,text/xml,text/html,text/markdown","user-agent":"OpenTopicRadar/0.1 public-metadata-only"},redirect="manual")
        status=int(r.status)
        if status in (301,302,303,307,308):
            loc=r.headers.get("location")
            if not loc:raise ValueError("Redirect missing location")
            dest=urljoin(current,loc)
            u=urlparse(dest)
            if u.scheme!="https" or u.hostname!=host or u.port not in (None,443) or u.username or u.password:
                raise ValueError("blocked cross-host redirect HTTP "+str(status))
            current=dest
            continue
        if status in (401,403,429,451):raise ValueError("blocked HTTP "+str(status))
        if status not in (200,206):raise ValueError("HTTP "+str(status))
        length=r.headers.get("content-length")
        limit=4194304
        if length and int(length)>limit:raise ValueError("Body too large")
        body=await r.text()
        if len(body.encode("utf-8"))>limit:raise ValueError("Body too large")
        return body
    raise ValueError("Too many redirects")
def r79_parse_date(value):
    value=str(value or "").strip()[:96]
    if not value:return None
    try:dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError:
        try:dt=parsedate_to_datetime(value)
        except (TypeError,ValueError,IndexError):
            try:dt=datetime.strptime(value,"%a %b %d %H:%M:%S %z %Y")
            except ValueError:return None
    if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")

def evidence(src,url,title,raw,author="",published_at=None,excerpt="",metrics=None,kind="article",mode="K",state="official_metadata_only"):
    url=canonicalize(str(url))
    raw=raw if isinstance(raw,str) else json.dumps(raw,ensure_ascii=False,sort_keys=True)
    ev=Evidence(source_id=src["source_id"],platform=src["platform"],source_url=url,canonical_url=url,author=str(author),published_at=published_at,collected_at=now_utc(),language=None,content_type=kind,title=str(title)[:500],body_excerpt=str(excerpt)[:2000],raw_ref="sha256:"+sha256(raw.encode()).hexdigest(),metrics=metrics or {},mode=mode,evidence_status=state,job_id="cloudflare-manual")
    return ev.as_dict(),raw
async def r72_direct_public_html(src,link):
    if not link or len(link)>2048:raise ValueError("Specific public URL required for D")
    p=urlparse(link)
    if p.scheme!="https" or p.hostname not in src["allowed_hosts"] or p.port not in (None,443) or p.username or p.password or p.path in ("","/"):raise ValueError("Direct URL must be on official allowed host")
    html=await official_get(link,p.hostname)
    page=PrimaryPageExtractor();page.feed(html[:480000])
    desc=" ".join((page.description+" "+" ".join(page.paragraphs[:6])).split())[:1800]
    if len(desc)<120:raise ValueError("Original primary page excerpt too short")
    title=p.path.rsplit("/",1)[-1].replace("-"," ") or link
    return [evidence(src,link,title,{"official_page":link,"original_excerpt":desc},published_at=page.date,excerpt=desc,kind="primary_public_page_excerpt",mode="D",state="partial")]

async def gather(src,limit,target_url=None,fx_mode="D",fx_query="",fx_provider="",env=None):
    host=src["allowed_hosts"][0]
    kind=src["kind"]
    if kind=="hn_topstories" and fx_mode=="D":
        link=str(target_url or "")
        if not link.startswith("https://news.ycombinator.com/item?id=") or not link.split("id=",1)[-1].isdigit():raise ValueError("HN D requires official story URL with numeric id")
        ident=int(link.split("id=",1)[-1]);item=json.loads(await official_get("https://hacker-news.firebaseio.com/v0/item/"+str(ident)+".json",host))
        if item.get("id")!=ident or not item.get("title"):raise ValueError("HN item missing")
        dt=datetime.fromtimestamp(int(item["time"]),timezone.utc).isoformat() if item.get("time") else None
        return [evidence(src,link,item["title"],item,author=item.get("by",""),published_at=dt,excerpt=item.get("text") or "",mode="D",kind="hn_direct_item",state="official_metadata_only")]
    if src["source_id"]=="youtube_search" and fx_mode=="D":
        link=str(target_url or "");p=urlparse(link);query=parse_qs(p.query);video=query.get("v",[""])[0]
        if p.scheme!="https" or p.hostname not in ("youtube.com","www.youtube.com") or p.path!="/watch" or not re.fullmatch(r"[A-Za-z0-9_-]{11}",video):raise ValueError("YouTube D requires official watch URL")
        canonical="https://www.youtube.com/watch?v="+video
        info=json.loads(await official_get("https://www.youtube.com/oembed?url="+quote(canonical,safe="")+"&format=json",host))
        title=info.get("title");author=info.get("author_name")
        if not title or not author:raise ValueError("YouTube official metadata absent")
        return [evidence(src,canonical,title,info,author=author,kind="video_metadata_visuals_not_verified",mode="D",state="official_metadata_only")]
    if src["source_id"] in ("github_trending","producthunt_search","skills_sh") and fx_mode=="D":
        if src["source_id"]=="github_trending":
            p=urlparse(str(target_url or ""))
            if p.hostname!="github.com" or not re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?",p.path):raise ValueError("GitHub D requires exact owner/repo URL")
        return await r72_direct_public_html(src,target_url)
    if kind=="aa_v2_free_api":return await gather_aa_free(src,limit,env,fx_query or "language")
    if kind=="x_hybrid_fx":
        if fx_provider=="twitterapi_io":return await r84_twitterapi_io_read(src,limit,fx_mode,fx_query,env)
        if fx_provider=="fx":return await gather_fx_public(src,limit,fx_mode,target_url,fx_query)
        if fx_provider in ("","official"):return await gather_oembed(src,target_url)
        raise ValueError("Unknown X provider")
    if kind=="oembed_direct":
        try:return await gather_oembed(src,target_url)
        except ValueError as embed_error:
            if src["source_id"]!="instagram_explore" or "blocked HTTP 429" not in str(embed_error):raise
            canonical,_,_=verify_direct_oembed_source(src,target_url)
            p=urlparse(canonical)
            html=await official_get(canonical,p.hostname)
            page=PrimaryPageExtractor();page.feed(html[:1000000])
            description=" ".join(page.description.split())
            if len(description)<65 or description.casefold().strip() in ("view this post on instagram","login"):
                raise ValueError("Instagram official embed limited and original page has no usable public metadata")
            raw={"original_public_url":canonical,"original_page_meta":description[:1600],"oembed_rate_limited":True,"media_content_reviewed":False}
            return [evidence(src,canonical,description[:180],raw,excerpt=description[:1600],published_at=page.date,kind="instagram_official_public_metadata_only",mode="D",state="research_only",metrics={"original_page_meta_read":True,"video_visuals_reviewed":False})]
    if kind=="hn_topstories":
        ids=json.loads(await official_get(src["url"],host))
        if not isinstance(ids,list) or any(not isinstance(x,int) or x<=0 for x in ids[:limit]):raise ValueError("Unexpected HN ID list")
        results=[]
        for rank,ident in enumerate(ids[:limit],1):
            raw=await official_get("https://hacker-news.firebaseio.com/v0/item/"+str(ident)+".json",host)
            item=json.loads(raw)
            if item.get("id")!=ident:raise ValueError("HN response mismatch")
            if not item.get("title") or item.get("dead") or item.get("deleted"):continue
            dt=datetime.fromtimestamp(int(item["time"]),timezone.utc).isoformat() if item.get("time") else None
            results.append(evidence(src,item.get("url") or "https://news.ycombinator.com/item?id="+str(ident),item["title"],raw,author=item.get("by",""),published_at=dt,excerpt=item.get("text",""),metrics={"hn_points":item.get("score"),"hn_comments":item.get("descendants"),"hn_front_page_rank":rank},mode="H"))
        return results
    if kind=="github_search":
        req=src["url"]
        if fx_query.strip():
            q=" ".join(fx_query.split())
            if not 2<=len(q)<=90 or any(ord(c)<32 for c in q):raise ValueError("Invalid GitHub query")
            req="https://api.github.com/search/repositories?q="+quote(q+" in:name,description,readme",safe="")+"&sort=created&order=desc&per_page=10"
        payload=json.loads(await official_get(req,host))
        if not isinstance(payload.get("items"),list):raise ValueError("Unexpected GitHub search JSON")
        results=[]
        for item in payload["items"][:limit]:
            if not item.get("html_url") or not item.get("full_name"):continue
            results.append(evidence(src,item["html_url"],item["full_name"],item,author=(item.get("owner") or {}).get("login",""),published_at=item.get("created_at"),excerpt=item.get("description") or "",kind="repository",metrics={"github_stars":item.get("stargazers_count"),"github_updated_at":item.get("updated_at")}))
        return results
    if kind=="hf_repo_list":
        req=src["url"]
        if fx_mode=="F" and "sort=trendingScore" in req:req=req.replace("sort=trendingScore","sort=createdAt&direction=-1")
        payload=json.loads(await official_get(req,host))
        if not isinstance(payload,list):raise ValueError("Unexpected Hugging Face JSON")
        result=[]
        for item in payload[:limit]:
            rid=item.get("id") or item.get("modelId")
            if not isinstance(rid,str) or "/" not in rid:continue
            repo_type=src.get("repo_type","model")
            page="https://huggingface.co/"+("spaces/" if repo_type=="space" else "")+rid
            dt=item.get("createdAt") or item.get("lastModified")
            result.append(evidence(src,page,rid,item,author=rid.split("/")[0],published_at=dt,excerpt=" ".join((item.get("tags") or [])[:12]) if isinstance(item.get("tags"),list) else "",kind=repo_type,mode=fx_mode,metrics={"hf_downloads":item.get("downloads"),"hf_likes":item.get("likes"),"hf_trending_score":item.get("trendingScore")}))
        return result
    if kind=="reddit_listing":
        payload=json.loads(await official_get(src["url"],host))
        data=payload.get("data") or {}
        if not isinstance(data.get("children"),list):raise ValueError("Unexpected Reddit listing")
        result=[]
        for wrapper in data["children"][:limit]:
            item=wrapper.get("data") or {}
            path=item.get("permalink","")
            if not path.startswith("/") or not item.get("title"):continue
            dt=datetime.fromtimestamp(float(item["created_utc"]),timezone.utc).isoformat() if item.get("created_utc") else None
            result.append(evidence(src,"https://www.reddit.com"+path,item["title"],item,author=item.get("author",""),published_at=dt,excerpt=item.get("selftext","") or "",mode="H",kind="discussion",metrics={"reddit_score":item.get("score"),"reddit_comments":item.get("num_comments")},state="official_metadata_only"))
        return result
    if kind=="bsky_trends":
        payload=json.loads(await official_get(src["url"],host))
        topics=payload.get("trends")
        if not isinstance(topics,list):raise ValueError("Unexpected official Bluesky trends JSON")
        results=[]
        for item in topics:
            display=str(item.get("displayName") or "").strip()
            link=str(item.get("link") or "")
            if not 5<=len(display)<=210 or not link.startswith("/profile/") or "/feed/" not in link:continue
            count=item.get("postCount")
            info={"name":display,"official_topic_id":item.get("topic"),"postCount":count,"source_url":src["url"],"AI_relevance":"NOT_EVALUATED","editorial_scope":"raw_network_trends_only"}
            results.append(evidence(src,"https://bsky.app"+link,display,info,excerpt=display+" — official Bluesky raw topic metadata; AI relevance not assessed",kind="official_trending_topic_unfiltered",mode="H",state="research_only",metrics={"postCount":count,"ai_relevance":"not_assessed"}))
            if len(results)>=limit:break
        if not results:raise ValueError("No usable official Bluesky trend records")
        return results
    if kind=="devto_articles":
        req=src["url"]
        if fx_mode=="K" and fx_query.strip():
            tag=fx_query.strip().lower()
            if not re.fullmatch(r"[a-z0-9_-]{2,30}",tag):raise ValueError("DEV keyword supports official tags only")
            req="https://dev.to/api/articles?tag="+quote(tag,safe="")+"&per_page=8"
        data=json.loads(await official_get(req,host))
        if not isinstance(data,list):raise ValueError("Unexpected DEV articles JSON")
        results=[]
        for item in data[:limit]:
            url=item.get("url")
            title=item.get("title")
            if not url or not title:continue
            results.append(evidence(src,url,title,item,author=(item.get("user") or {}).get("username",""),published_at=item.get("published_at"),excerpt=item.get("description") or "",kind="article",mode=fx_mode,metrics={"reactions":item.get("public_reactions_count"),"comments":item.get("comments_count")}))
        if not results:raise ValueError("No article entries")
        return results
    if kind=="gitlab_projects":
        req=src["url"]
        if fx_mode=="F":req="https://gitlab.com/api/v4/projects?search=ai&per_page=8&order_by=created_at&sort=desc"
        if fx_mode=="K" and fx_query.strip():
            q=" ".join(fx_query.split())
            if not 2<=len(q)<=90 or any(ord(c)<32 for c in q):raise ValueError("Invalid GitLab query")
            req="https://gitlab.com/api/v4/projects?search="+quote(q,safe="")+"&per_page=8&order_by=created_at&sort=desc"
        data=json.loads(await official_get(req,host))
        if not isinstance(data,list):raise ValueError("Unexpected GitLab project JSON")
        results=[]
        for item in data[:limit]:
            url=item.get("web_url")
            title=item.get("path_with_namespace") or item.get("name")
            if not url or not title:continue
            results.append(evidence(src,url,title,item,author=(item.get("namespace") or {}).get("name",""),published_at=item.get("created_at"),excerpt=item.get("description") or "",kind="repository",mode=fx_mode,metrics={"stars":item.get("star_count"),"updated_at":item.get("last_activity_at")}))
        if not results:raise ValueError("No public projects")
        return results
    if kind=="bsky_search":
        q=" ".join((fx_query or "AI agent").split())
        if not 2<=len(q)<=90 or any(ord(c)<32 for c in q):raise ValueError("Invalid Bluesky query")
        req="https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?q="+quote(q,safe="")+"&limit=8&sort="+("latest" if fx_mode=="F" else "top")
        data=json.loads(await official_get(req,host))
        posts=data.get("posts")
        if not isinstance(posts,list):raise ValueError("Unexpected Bluesky search JSON")
        results=[]
        for item in posts[:limit]:
            record=item.get("record") or {}
            author=item.get("author") or {}
            uri=item.get("uri") or ""
            handle=author.get("handle") or ""
            tid=uri.rsplit("/",1)[-1]
            msg=record.get("text") or ""
            if not handle or not tid or not msg:continue
            page="https://bsky.app/profile/"+handle+"/post/"+tid
            results.append(evidence(src,page,msg[:250],item,author=handle,published_at=record.get("createdAt"),excerpt=msg,kind="post",mode=fx_mode,metrics={"likes":item.get("likeCount"),"reposts":item.get("repostCount")}))
        if not results:raise ValueError("No matching public Bluesky posts")
        return results
    if kind=="civitai_models":
        req="https://civitai.com/api/v1/models?limit=8&sort="+("Newest" if fx_mode=="F" else "Most%20Downloaded&period=Week")
        data=json.loads(await official_get(req,host))
        entries=data.get("items")
        if not isinstance(entries,list):raise ValueError("Unexpected Civitai models JSON")
        results=[]
        for item in entries[:limit]:
            name=item.get("name")
            mid=item.get("id")
            if not name or not isinstance(mid,int):continue
            results.append(evidence(src,"https://civitai.com/models/"+str(mid),name,item,author=(item.get("creator") or {}).get("username",""),published_at=item.get("createdAt"),excerpt=item.get("description") or "",kind="model",mode=fx_mode,metrics={"downloads":(item.get("stats") or {}).get("downloadCount"),"likes":(item.get("stats") or {}).get("favoriteCount")}))
        if not results:raise ValueError("No model entries")
        return results
    if kind=="arena_hf_rows":
        payload=json.loads(await official_get(src["url"],host))
        entries=payload.get("rows")
        if not isinstance(entries,list):raise ValueError("Unexpected Arena dataset response")
        results=[]
        for wrapper in entries[:limit]:
            item=wrapper.get("row") or {}
            idx=wrapper.get("row_idx")
            name=item.get("model_name")
            rank=item.get("rank")
            published=item.get("leaderboard_publish_date")
            if not isinstance(idx,int) or not isinstance(name,str) or not isinstance(rank,int) or not isinstance(published,str):continue
            single_url=src["url"].split("&offset=")[0]+"&offset="+str(idx)+"&length=1"
            results.append(evidence(src,single_url,"Arena Agent #"+str(rank)+" "+name,{"dataset":"lmarena-ai/leaderboard-dataset","row":item,"original_url":src["url"]},author=str(item.get("organization") or ""),published_at=published,kind="leaderboard_snapshot",mode="F",state="official_metadata_only",metrics={"arena_rank":rank,"arena_agent_score":item.get("score"),"snapshot_date":published,"category":item.get("category")}))
        if not results:raise ValueError("No Arena Agent leaderboard records")
        return results
    if kind=="hf_daily_papers":
        payload=json.loads(await official_get(src["url"],host))
        if not isinstance(payload,list):raise ValueError("Unexpected Hugging Face daily papers JSON")
        results=[]
        for item in payload[:max(8,limit)]:
            if not isinstance(item,dict):continue
            paper=item.get("paper") or item
            if not isinstance(paper,dict):continue
            pid=str(paper.get("id") or paper.get("arxivId") or "")
            title=paper.get("title") or item.get("title") or ""
            if not re.fullmatch(r"[0-9]{4}\.[0-9]{4,5}",pid) or not isinstance(title,str) or not title:continue
            summary=paper.get("summary") or paper.get("ai_summary") or ""
            pub=paper.get("publishedAt") or item.get("publishedAt") or paper.get("published")
            results.append(evidence(src,"https://huggingface.co/papers/"+pid,title,item,published_at=pub,excerpt=str(summary)[:900],kind="paper",mode="D",state="official_metadata_only"))
            if len(results)>=limit:break
        if not results:raise ValueError("No qualified public papers from HF official API")
        return results
    if kind=="telegram_public_posts":
        html=await official_get(src["url"],host)
        parser=TelegramPostParser()
        parser.feed(html[:500000])
        out=[]
        for post_id,body in parser.posts:
            if not re.fullmatch(r"[A-Za-z0-9_]{4,64}/[0-9]{1,20}",post_id):continue
            title=" ".join(body.split())[:200]
            if len(title)<20:continue
            url="https://t.me/"+post_id
            out.append(evidence(src,url,title,{"public_post_url":url,"text":body[:1600]},author=post_id.split("/")[0],excerpt=body[:1400],kind="public_channel_post",mode="D",state="partial"))
            if len(out)>=limit:break
        if not out:raise ValueError("No public Telegram post body found in official channel HTML")
        return out
    if kind=="markdown_changelog":
        markdown=await official_get(src["url"],host)
        matches=list(re.finditer(r"(?m)^#{2,4}\s+(.{6,180})$",markdown))
        if not matches:raise ValueError("No changelog headings in official markdown")
        first=matches[0]
        title="OpenAI API changelog: "+first.group(1).strip()
        excerpt=markdown[first.start():min(len(markdown),first.end()+1300)].strip()
        return [evidence(src,"https://developers.openai.com/api/docs/changelog",title,{"document_url":src["url"],"source_excerpt":excerpt},excerpt=excerpt[:1200],kind="changelog_snapshot",mode="D",state="partial")]
    if kind=="github_trending_public":
        html=await official_get(src["url"],host)
        blocks=html.split('<article class="Box-row">')[1:]
        out=[]
        for rank,full in enumerate(blocks,1):
            seg=full.split("</article>",1)[0]
            h2=seg.split("<h2",1)[-1].split("</h2>",1)[0]
            match=re.search(r'href="/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)"',h2)
            if not match:continue
            owner,repo=match.group(1),match.group(2)
            if owner in ("features","login","topics","collections","marketplace"):continue
            url="https://github.com/"+owner+"/"+repo
            p=PrimaryPageExtractor();p.feed(seg[:22000])
            description=" ".join((p.paragraphs or [])[:2])[:450]
            out.append(evidence(src,url,owner+"/"+repo,{"trending_rank":rank,"source_url":src["url"],"description":description},author=owner,excerpt=description,kind="repository",mode="H",state="official_metadata_only",metrics={"source_trending_rank":rank}))
            if len(out)>=limit:break
        if not out:raise ValueError("No authentic GitHub Trending repo cards")
        return out
    if kind=="youtube_public_search_html":
        req=src["url"]
        if fx_query.strip():
            q=" ".join(fx_query.split())
            if not 2<=len(q)<=90:raise ValueError("YouTube query length invalid")
            req="https://www.youtube.com/results?search_query="+quote(q,safe="")
        html=await official_get(req,host)
        marker="var ytInitialData = "
        k=html.find(marker)
        if k<0:raise ValueError("No public YouTube search JSON embedded")
        data,_end=json.JSONDecoder().raw_decode(html[k+len(marker):])
        seen=set();videos=[]
        def walk(n):
            if isinstance(n,dict):
                if isinstance(n.get("videoRenderer"),dict):videos.append(n["videoRenderer"])
                for v in n.values():walk(v)
            elif isinstance(n,list):
                for v in n:walk(v)
        walk(data)
        out=[]
        for v in videos:
            vid=str(v.get("videoId") or "")
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}",vid) or vid in seen:continue
            titleinfo=v.get("title") or {}
            title=" ".join(z.get("text","") for z in titleinfo.get("runs",[]) if isinstance(z,dict)) or titleinfo.get("simpleText") or ""
            if not 8<=len(title)<=400:continue
            description=" ".join(z.get("text","") for z in (v.get("descriptionSnippet") or {}).get("runs",[]) if isinstance(z,dict))[:900]
            owner=" ".join(z.get("text","") for z in (v.get("ownerText") or {}).get("runs",[]) if isinstance(z,dict))[:90]
            rel=(v.get("publishedTimeText") or {}).get("simpleText") or ""
            link="https://www.youtube.com/watch?v="+vid
            out.append(evidence(src,link,title,{"videoId":vid,"title":title,"description":description,"displayed_age":rel,"owner":owner},author=owner,excerpt=description,kind="video_public_search_metadata",mode="K",state="official_metadata_only",metrics={"displayed_age":rel}))
            seen.add(vid)
            if len(out)>=limit:break
        if not out:raise ValueError("No qualified videoRenderer objects in public YouTube search")
        return out
    if kind=="public_token_rankings":
        html=await official_get(src["url"],host)
        marker="Model rankings by tokens processed"
        start=html.find(marker)
        if start<0:raise ValueError("Official usage ranking table unavailable")
        block=html[start:start+12000].split("</tbody>",1)[0]
        if "or-table__body" not in block:raise ValueError("No official table body")
        rows=re.findall(r'<tr[^>]*class="or-table__row"[^>]*>(.*?)</tr>',block,re.S)
        out=[]
        for segment in rows:
            fields=re.findall(r'<(?:td|th)[^>]*class="or-table__cell[^"]*"[^>]*>(.*?)</(?:td|th)>',segment,re.S)
            if len(fields)!=5:continue
            vals=[unescape(re.sub(r"<[^>]*>","",f)).strip() for f in fields]
            if not vals[0].isdigit() or not vals[1] or not vals[3]:continue
            rank=int(vals[0])
            if rank<1 or rank>100:continue
            model,author,tokens,change=vals[1:5]
            if not re.search(r"\d+(?:\.\d+)?[TBM]",tokens):continue
            matches=re.search(r'"name":"'+re.escape(model)+r'","item":"(https://openrouter\.ai/[^"]+)"',html)
            link=matches.group(1) if matches else src["url"]+"?rank="+str(rank)
            payload={"model":model,"author":author,"rank":rank,"tokens_processed":tokens,"change":change,"leaderboard":src["url"],"metric":"tokens_processed_not_model_quality"}
            out.append(evidence(src,link,model+" — tokens usage rank #"+str(rank),payload,author=author,excerpt=model+" by "+author+": "+tokens+", change "+change,kind="official_token_usage_rank",mode="H",state="official_metadata_only",metrics={"rank":rank,"tokens":tokens,"change":change}))
            if len(out)>=limit:break
        if not out:raise ValueError("No qualified official token usage ranking rows")
        return out
    if kind=="official_startup_benefits":
        html=await official_get(src["url"],host)
        p=PrimaryPageExtractor()
        p.feed(html[:3900000])
        desc=" ".join(p.description.split())
        prose=" ".join(p.paragraphs[:18])
        combined=(desc+" "+prose).strip()[:1950]
        if len(combined)<240 or not all(x in combined.casefold() for x in ("startup","cloud")):
            raise ValueError("Google program page did not return usable official benefits text")
        if any(z in combined[:450].casefold() for z in ("captcha","access denied","verify you are human")):raise ValueError("Access challenge not article text")
        raw={"url":src["url"],"description":desc,"excerpt":combined,"snapshot":"static_program_benefits_not_new_ai_news"}
        return [evidence(src,src["url"],"Google for Startups Cloud Program: eligibility and benefits",raw,excerpt=combined,kind="official_program_benefits_snapshot",mode="D",state="partial",metrics={"static_program_page":True})]
    if kind=="html_index":
        actual=dict(src)
        if src["source_id"]=="producthunt_search" and fx_mode=="K":
            q=" ".join((fx_query or "ai").split())
            if not 2<=len(q)<=90:raise ValueError("Product Hunt query length invalid")
            actual["url"]="https://www.producthunt.com/search?q="+quote(q,safe="")
        scan_limit=min(60,max(limit*15,limit)) if src["source_id"]=="skills_sh" and fx_mode=="H" else limit
        original=safe_html_links(actual,await official_get(actual["url"],host),scan_limit)
        if src["source_id"]=="skills_sh" and fx_mode=="H":
            original=[p for p in original if len([x for x in urlparse(p[0]["canonical_url"]).path.split("/") if x])==3][:limit]
            if not original:raise ValueError("No ranked skill detail links on official trending page")
        enriched=[]
        for found in original:
            ev,raw=await enrich_public_article(actual,found)
            if src["source_id"] in ("producthunt_search","skills_sh"):ev["mode"]=fx_mode
            enriched.append((ev,raw))
        return enriched
    if kind=="rss":
        xml=await official_get(src["url"],host)
        items=parse_rss_feed(src,xml,limit)
        for i in range(min(2,len(items))):
            item=items[i]
            if urlparse(item[0]["canonical_url"]).hostname not in src["allowed_hosts"]:continue
            improved=await enrich_public_article(src,item)
            if improved[0].get("content_type")=="public_primary_page_excerpt":
                improved[0]["mode"]="F"
                items[i]=improved
        return items
    raise ValueError("Unsupported source adapter")
async def store(db,items):
    for ev,raw in items:
        source_date=ev.get("published_at")
        normalized=r79_parse_date(source_date)
        flags=dict(ev.get("metrics") or {})
        flags["r79_date_provenance"]="source_claimed" if normalized else "unknown"
        flags["r79_raw_date"]=str(source_date)[:96] if source_date else ""
        flags["r79_content_scope"]="excerpt_or_public_metadata_not_verified_full_article"
        ev["metrics"]=flags
        ev["published_at"]=normalized
        await db.prepare("INSERT OR IGNORE INTO raw_payloads(sha256,bytes,stored_at) VALUES (?,?,?)").bind(ev["raw_ref"],raw,ev["collected_at"]).run()
        await db.prepare("INSERT INTO evidence(source_id,canonical_url,entity_id,collected_at,evidence_json) VALUES (?,?,?,?,?) ON CONFLICT(source_id,canonical_url) DO UPDATE SET entity_id=excluded.entity_id,collected_at=excluded.collected_at,evidence_json=excluded.evidence_json").bind(ev["source_id"],ev["canonical_url"],ev["entity_id"],ev["collected_at"],json.dumps(ev,ensure_ascii=False)).run()
        if normalized:
            await db.prepare("INSERT INTO r79_date_parse(source_id,canonical_url,published_utc,raw_date,parse_method) VALUES(?,?,?,?,?) ON CONFLICT(source_id,canonical_url) DO UPDATE SET published_utc=excluded.published_utc,raw_date=excluded.raw_date,parse_method=excluded.parse_method").bind(ev["source_id"],ev["canonical_url"],normalized,str(source_date)[:96],"source_date_python").run()

class Default(WorkerEntrypoint):
    async def fetch(self,request):
        try:
            u=urlparse(str(request.url))
            path=u.path;method=str(request.method)
            params=parse_qs(u.query)
            if method=="GET" and path in ("/","/health"):
                a=await rows(self.env.DB,"SELECT COUNT(*) AS count FROM evidence")
                return respond({"service":"open-topic-radar","version":"0.1.0.dev0","runtime":"cloudflare-python","database":"D1","db_ready":True,"stored_evidence":a[0]["count"] if a else None,"sources":sum(1 for x in SOURCES if x.get("deployment_stage")=="adapter_configured"),"registered_sources":len(SOURCES),"registry_only_sources":sum(1 for x in SOURCES if x.get("deployment_stage")=="registered_only"),"scheduler_enabled":False,"editorial_approval":False})



            if method=="GET" and path=="/r64-status":
                a=await rows(self.env.DB,"SELECT COUNT(*) AS n FROM r64_events")
                b=await rows(self.env.DB,"SELECT COUNT(*) AS n FROM r64_discovery_feed")
                c=await rows(self.env.DB,"SELECT COUNT(*) AS n FROM r64_metric_history")
                return respond({"feature":"r64_research_discovery","event_index_count":a[0]["n"] if a else 0,"feed_rows":b[0]["n"] if b else 0,"metric_snapshots":c[0]["n"] if c else 0,"human_editorial_approval":False,"autonomous_x_trends_verified":False})

            if method=="GET" and path=="/r65-system-status":
                a=await rows(self.env.DB,"SELECT (SELECT COUNT(*) FROM evidence) AS worker_evidence,(SELECT COUNT(*) FROM r65_regression_cases) AS fixed_regression_cases,(SELECT COUNT(*) FROM r65_coverage_audit WHERE matching_worker_evidence>0) AS worker_detected_cases,(SELECT COUNT(*) FROM r64_events WHERE editorial_state='benchmark_only') AS benchmark_only_events,(SELECT COUNT(*) FROM r64_discovery_feed) AS candidate_feed_rows")
                r=a[0] if a else {}
                return respond({"feature":"R65_system_diagnostics","worker_evidence":r.get("worker_evidence",0),"fixed_regression_cases":r.get("fixed_regression_cases",0),"worker_detected_cases":r.get("worker_detected_cases",0),"benchmark_only_events_excluded":r.get("benchmark_only_events",0),"candidate_feed_rows":r.get("candidate_feed_rows",0),"rss_requested_cap":12,"other_source_requested_cap":3,"scheduler_enabled":False,"editorial_approval":False,"note":"Manual research benchmark samples are not Worker collector successes. Regression passes only with matching original Worker evidence."})

            expected=getattr(self.env,"ADMIN_KEY",None)
            supplied=request.headers.get("x-radar-admin-key")
            original_admin_ok=bool(expected and supplied and supplied==expected)
            if not original_admin_ok:
                # Temporary independently authorized test credential; original ADMIN_KEY unchanged.
                if not ((method=="POST" and path=="/collect") or (method=="GET" and path in ("/r79-discovery","/r82-x-ai-hot"))):return respond({"error":"unauthorized"},403)
                test_token=request.headers.get("x-radar-r76-test") or ""
                if not 30<=len(test_token)<=200 or not test_token.startswith("r76_"):
                    return respond({"error":"unauthorized"},403)
                token_digest=sha256(test_token.encode("utf-8")).hexdigest()
                claimed=await rows(self.env.DB,
                    "UPDATE r76_test_sessions SET uses_remaining=uses_remaining-1 WHERE token_sha256=? AND CAST(valid_until AS INTEGER)>CAST(strftime('%s','now') AS INTEGER) AND uses_remaining>0 RETURNING allowed_sources",
                    (token_digest,))
                permitted="r79_read" if path=="/r79-discovery" else "r82_read" if path=="/r82-x-ai-hot" else params.get("source",[""])[0]
                if not claimed or permitted not in claimed[0]["allowed_sources"].split(",") or permitted in PAUSED_SOURCE_IDS:
                    return respond({"error":"unauthorized"},403)

            if method=="GET" and path=="/r82-x-ai-hot":
                try:limit=min(15,max(1,int(params.get("limit",["10"])[0])))
                except Exception:return respond({"error":"invalid_limit"},422)
                result=await rows(self.env.DB,"SELECT canonical_url,title,excerpt,author,published_utc,measured_utc,likes,reposts,quotes,replies,weighted_engagement,age_adjusted_score,monitoring_scope,metric_provenance,scope_warning FROM r82_x_scoped_hot_feed ORDER BY age_adjusted_score DESC LIMIT ?",(limit,))
                return respond({"feature":"r82_monitored_ai_accounts_engagement","source_id":"x_explore","mode":"H","provider":"FxEmbed third-party public metrics","official_x_trends":False,"all_x_search":False,"coverage":"five named AI accounts, last 72 hours, observed recent public posts only","rank_basis":"weighted observed likes/reposts/quotes/replies divided by age factor","live_collection_triggered":False,"refresh":"explicitly POST /collect?source=x_explore&mode=H&provider=fx using existing admin authorization","research_only":True,"records":result})
            if method=="GET" and path=="/r79-discovery":
                q=" ".join(params.get("q",[""])[0].split()).casefold()
                if len(q)>90 or any(ord(c)<32 for c in q):return respond({"error":"invalid_query"},422)
                try:lim=min(40,max(1,int(params.get("limit",["20"])[0])))
                except Exception:return respond({"error":"invalid_limit"},422)
                base="SELECT source_id,canonical_url,published_utc,title,substr(excerpt,1,450) AS excerpt_preview,content_quality_class,evidence_status,excerpt_chars,discovery_rank FROM r79_recent_discovery"
                if q:
                    data=await rows(self.env.DB,base+" WHERE lower(title) LIKE ? OR lower(coalesce(excerpt,'')) LIKE ? ORDER BY discovery_rank DESC,published_utc DESC LIMIT ?",("%"+q+"%","%"+q+"%",lim))
                else:
                    data=await rows(self.env.DB,base+" ORDER BY discovery_rank DESC,published_utc DESC LIMIT ?",(lim,))
                stats=await rows(self.env.DB,"SELECT freshness_class,COUNT(*) n FROM r79_quality_inventory GROUP BY freshness_class")
                return respond({"feature":"r79_recent_firsthand_discovery","live_collection_triggered":False,"window":"72h verified source-claimed publication times","query":q,"results":data,"date_class_counts":stats,"editorial_approval":False,"original_article_full_text_verified":False,"x_global_trends_verified":False})
            if method=="GET" and path=="/r64-discovery":
                lane=params.get("lane",[""])[0]
                if lane not in ("","major_updates","social_signals","quality_archive","cross_source_discovery"):
                    return respond({"error":"invalid_lane"},400)
                try: limit=min(40,max(1,int(params.get("limit",["20"])[0])))
                except Exception:return respond({"error":"invalid_limit"},400)
                if lane:
                    content=await rows(self.env.DB,"SELECT event_id,lane,title,primary_url,event_date,provenance_level,discovery_path,editorial_state,limitations,direct_worker_links,worker_sources FROM r64_discovery_feed WHERE lane=? ORDER BY (discovery_path='worker_evidence_unlinked'),event_date DESC LIMIT ?",(lane,limit))
                else:
                    content=await rows(self.env.DB,"SELECT event_id,lane,title,primary_url,event_date,provenance_level,discovery_path,editorial_state,limitations,direct_worker_links,worker_sources FROM r64_discovery_feed ORDER BY (discovery_path='worker_evidence_unlinked'),event_date DESC LIMIT ?",(limit,))
                return respond({"r64_query":True,"results":content,"editorial_approval":False,"hotness_verified":False,"note":"Worker records plus separately sourced and manually verified legacy events; not 100% X coverage or verified virality"})
            if method=="GET" and path=="/selftest":
                return respond(selftest_report(self.env))
            if method=="GET" and path=="/diagnostics":
                hist=await rows(self.env.DB,"SELECT source_id,status,mode,detail,collected_at,item_count,job_id FROM attempts ORDER BY id DESC LIMIT 2000")
                last={}
                last_real={}
                for x in hist:
                    sid=x["source_id"]
                    if sid not in last:last[sid]=x
                    if x.get("job_id")!="cloudflare-probe" and sid not in last_real:last_real[sid]=x
                report=selftest_report(self.env)
                counts=await rows(self.env.DB,"SELECT source_id,COUNT(*) AS records FROM evidence GROUP BY source_id")
                evidence_counts={x["source_id"]:x["records"] for x in counts}
                for item in report["sources"]:
                    sid=item["source_id"]
                    item["evidence_count"]=evidence_counts.get(sid,0)
                    item["last_attempt"]=last.get(sid)
                    item["last_real_attempt"]=last_real.get(sid)
                    item["runtime_verified"]=bool(evidence_counts.get(sid,0) and
                         last_real.get(sid,{}).get("status")=="success")
                report["runtime_verified_sources"]=sum(x["runtime_verified"] for x in report["sources"])
                report["attempt_window"]=len(hist)
                return respond(report)
            if method=="POST" and path=="/probe-batch":
                requested=params.get("sources",[""])[0].split(",")
                if any(s in PAUSED_SOURCE_IDS for s in requested):return respond({"error":"source_paused_by_user"},409)
                if not 1<=len(requested)<=3 or len(set(requested))!=len(requested) or any(x not in BY_ID for x in requested):
                    return respond({"error":"specify_1_to_3_unique_existing_sources"},400)
                result=[]
                for sid in requested:
                    src=BY_ID[sid]
                    state="blocked";detail="";n=0
                    if src.get("deployment_stage")=="registered_only":
                        detail="site_permission_required"
                    elif src["kind"] in ("oembed_direct","x_hybrid_fx"):
                        detail="input_required_for_direct_post_or_opt_in"
                    elif src["kind"]=="aa_v2_free_api" and not getattr(self.env,"AA_API_KEY",None):
                        detail="credential_required"
                    else:
                        try:
                            items=await gather(src,1,env=self.env)
                            n=len(items)
                            state="probe_ok" if n else "empty"
                            detail="Read-only upstream parse; evidence not stored" if n else "No qualified items"
                        except Exception as exc:
                            detail=str(exc)[:160]
                            state="blocked" if ("HTTP 403" in detail or "HTTP 429" in detail or "credential_" in detail or "blocked HTTP" in detail) else "failed"
                    await self.env.DB.prepare("INSERT INTO attempts(job_id,source_id,source_url,mode,status,detail,collected_at,item_count) VALUES (?,?,?,?,?,?,?,?)").bind("cloudflare-probe",sid,src["url"],",".join(src.get("modes",[])),state,detail,now_utc(),n).run()
                    result.append({"source_id":sid,"probe_status":state,"items_parsed":n,"detail":detail})
                return respond({"probe_only":True,"evidence_written":0,"results":result,"editorial_approval":False})
            if method=="GET" and path=="/sources":
                return respond({"sources":[{"source_id":x["source_id"],"platform":x["platform"],"kind":x["kind"],"url":x["url"],"modes":x["modes"],"deployment_stage":x.get("deployment_stage","adapter_configured"),"access_status":x.get("access_status","unknown"),"planned_signal":x.get("planned_signal","unknown"),"r8_id":x.get("r8_id","")} for x in SOURCES]})
            if method=="GET" and path in ("/evidence","/export","/candidates"):
                limit=min(50,max(1,int(params.get("limit",["20"])[0])))
                cap=limit if path=="/evidence" else 250
                content=await rows(self.env.DB,"SELECT evidence_json FROM evidence ORDER BY collected_at DESC LIMIT ?",(cap,))
                data=[json.loads(x["evidence_json"]) for x in content]
                if path=="/evidence":return respond({"evidence":data})
                if path=="/export":return respond({"schema_version":1,"evidence":data,"truncated_at":cap})
                groups={}
                for ev in data:
                    rec=groups.setdefault(ev["entity_id"],{"entity_id":ev["entity_id"],"title":ev["title"],"canonical_url":ev["canonical_url"],"sources":set(),"evidence_statuses":set(),"editorial_state":"research_only","records":0})
                    rec["sources"].add(ev["source_id"])
                    rec["evidence_statuses"].add(ev["evidence_status"])
                    rec["records"]+=1
                candidates=[]
                for rec in groups.values():
                    rec["sources"]=sorted(rec["sources"]);rec["evidence_statuses"]=sorted(rec["evidence_statuses"]);candidates.append(rec)
                return respond({"candidates":candidates[:limit],"editorial_approval":False})

            if method=="POST" and path=="/collect-indexed-x":
                keyword=params.get("q",[""])[0].strip()
                targets=params.get("url",[])
                if not 2<=len(keyword)<=90 or any(ord(c)<32 for c in keyword):
                    return respond({"error":"keyword_2_to_90_required"},400)
                if not 1<=len(targets)<=3 or len(set(targets))!=len(targets):
                    return respond({"error":"one_to_three_unique_indexed_post_urls_required"},400)
                source=BY_ID["x_explore"]
                terms=[x for x in re.findall(r"[a-z0-9]+",keyword.casefold()) if len(x)>=2]
                if not terms:return respond({"error":"empty_search_terms"},400)
                accepted=[];out=[]
                for target in targets:
                    try:
                        canonical,_,_=verify_direct_oembed_source(source,target)
                        data=await gather(source,1,canonical,"D","","fx",self.env)
                        if len(data)!=1:raise ValueError("Index-discovered post not returned")
                        ev,raw=data[0]
                        hay=(ev.get("title","")+" "+ev.get("body_excerpt","")).casefold()
                        if not all(term in hay for term in terms):
                            out.append({"url":canonical,"state":"irrelevant","reason":"post_text_missing_query_terms"})
                            continue
                        ev["mode"]="K"
                        ev["content_type"]="third_party_x_public_index_post"
                        ev["evidence_status"]="partial"
                        ev["access_limitation"]="Discovered via outside public search engine index; not comprehensive or real-time X search; FxEmbed third party upstream authorization unknown"
                        ev["metrics"]=dict(ev.get("metrics") or {})
                        ev["metrics"]["discovery_method"]="public_web_index"
                        ev["metrics"]["index_query"]=keyword[:90]
                        accepted.append((ev,raw))
                        out.append({"url":ev["canonical_url"],"state":"verified","title":ev.get("title","")[:95]})
                    except Exception as ex:
                        out.append({"url":target[:200],"state":"failed","reason":(type(ex).__name__+": "+str(ex))[:140]})
                if accepted:await store(self.env.DB,accepted)
                count=len(accepted)
                await self.env.DB.prepare("INSERT INTO attempts(job_id,source_id,source_url,mode,status,detail,collected_at,item_count) VALUES (?,?,?,?,?,?,?,?)").bind("r20-x-public-index","x_explore",source["url"],"K:index_assisted","success" if count else "empty","Public index verified candidates; NOT full X search",now_utc(),count).run()
                return respond({"source_id":"x_explore","mode":"K","scope":"public_web_index_assisted_only","source_search_inside_worker":False,"stored":count,"results":out,"editorial_approval":False})
            if method=="POST" and path=="/collect":
                key=params.get("source",[""])[0]
                if key in PAUSED_SOURCE_IDS:return respond({"error":"source_paused_by_user","source_id":key},409)
                if key not in BY_ID:return respond({"error":"unknown_source"},400)
                src=BY_ID[key]
                if src.get("deployment_stage")=="registered_only":return respond({"error":"adapter_not_implemented","source_id":key,"deployment_stage":"registered_only"},409)

                if key=="artificial_analysis" and not getattr(self.env,"AA_API_KEY",None):
                    return respond({"error":"credential_required","source_id":key,"status":"blocked","detail":"AA_API_KEY not configured; no request was sent"},409)
                limit=min(12 if src["kind"]=="rss" else 3,max(1,int(params.get("limit",["1"])[0])))
                selected_mode=params.get("mode",[""])[0] or src["modes"][0]
                if selected_mode not in src["modes"]:return respond({"error":"mode_not_configured"},422)
                try:
                    items=await gather(src,limit,params.get("url",[""])[0],selected_mode,params.get("q",[""])[0],params.get("provider",[""])[0],self.env)
                    query=params.get("q",[""])[0].strip().casefold()
                    if selected_mode=="K" and query and key in ("bluesky_search","github_ai","github_agent","gitlab_explore","producthunt_search","youtube_search"):
                        terms=re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]{2,}",query)[:5]
                        if not terms:raise ValueError("No usable query terms")
                        qualified=[]
                        for ev,raw in items:
                            hay=(str(ev.get("title") or "")+" "+str(ev.get("body_excerpt") or "")).casefold()
                            if all(term in hay for term in terms):
                                ev["metrics"]=dict(ev.get("metrics") or {},r79_query_content_match=True)
                                qualified.append((ev,raw))
                        items=qualified
                        if not items:raise ValueError("No content-verified matches for requested keyword terms")
                    if any(ev.get("mode")!=selected_mode for ev,raw in items):raise ValueError("requested_mode_not_proven_by_adapter")
                    if not items:raise ValueError("selected_mode_returned_no_items")
                    await store(self.env.DB,items)
                    status="success" if items else "empty";detail=("TwitterAPI.io third-party regional trends or limited advanced search; NOT X native API; charged per returned item" if items and key=="x_explore" and params.get("provider",[""])[0]=="twitterapi_io" else "Curated five-account X AI engagement signals; FxEmbed third-party metrics; NOT official X Trends" if items and key=="x_explore" and selected_mode=="H" and params.get("provider",[""])[0]=="fx" else "FxEmbed third-party metadata; X original and upstream session unverified" if items and key=="x_explore" and params.get("provider",[""])[0]=="fx" else "Official Artificial Analysis Free API sampled data; requires attribution, no resale or full export" if items and key=="artificial_analysis" else "official anonymous metadata" if items else "No qualified items returned; not a verified source success")
                except Exception as exc:
                    status="blocked" if "blocked HTTP" in str(exc) else "failed";detail=str(exc)[:160];items=[]
                await self.env.DB.prepare("INSERT INTO attempts(job_id,source_id,source_url,mode,status,detail,collected_at,item_count) VALUES (?,?,?,?,?,?,?,?)").bind("cloudflare-manual",key,src["url"],("fx:"+params.get("mode",["D"])[0] if key=="x_explore" and params.get("provider",[""])[0]=="fx" else selected_mode),status,detail,now_utc(),len(items)).run()
                return respond({"source_id":key,"mode":selected_mode,"status":status,"items":len(items),"detail":detail,"editorial_approval":False},200 if status=="success" else 502)
            return respond({"error":"not_found"},404)
        except Exception as exc:
            return respond({"error":"worker_failure","error_type":type(exc).__name__},500)
