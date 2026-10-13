#!/usr/bin/env python3
"""Bounded guest-visible website check for XHS and Douyin.

Opens ordinary public search pages in a fresh isolated Chromium session;
does not log in, generate API signatures, solve challenges, scroll endlessly,
call private APIs, import cookies, or attempt platform evasion.
HTTP 200 or an HTML shell are not evidence of visible works/comments.
"""
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import quote, urlsplit
import json
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

OUTPUT=Path(__file__).resolve().parent/"output"
KEYWORD="AI生图"
CONFIG=[
    ("xiaohongshu","https://www.xiaohongshu.com/search_result?keyword="+quote(KEYWORD)),
    ("douyin","https://www.douyin.com/search/"+quote(KEYWORD)),
]
LOGIN_SIGNALS=("请先登录","扫码登录","登录后","验证码","安全验证","访问异常","滑动验证")
DOMAIN={"xiaohongshu":"xiaohongshu.com","douyin":"douyin.com"}

def host_valid(h,platform):
    domain=DOMAIN[platform]
    return h==domain or h.endswith("."+domain)

def relevant_work(href,platform):
    parts=urlsplit(href)
    if not host_valid((parts.hostname or "").lower(),platform):
        return False
    if platform=="xiaohongshu":
        return bool(re.search(r"/(explore|discovery/item)/[0-9a-fA-F]{18,30}",parts.path))
    return bool(re.search(r"/(video|note)/[0-9]{15,22}",parts.path))

def safe(v,n=200):
    return re.sub(r"[\x00-\x1f\x7f-\x9f]"," ",str(v or "")).strip()[:n]

def inspect(context,platform,url):
    r={"platform":platform,"keyword":KEYWORD,"url":url,"status":"not_verified",
       "visible_post_links":0,"actual_comments":0,"actual_replies":0,
       "guest_session":"ephemeral_chromium_only","personal_login":False}
    p=context.new_page()
    try:
        response=p.goto(url,wait_until="domcontentloaded",timeout=24000)
        p.wait_for_timeout(4800)
        r["http_status"]=response.status if response else None
        r["landed_url"]=safe(p.url,380)
        r["page_title"]=safe(p.title(),140)
        # Only read rendered, user-visible links. No hidden state / app bootstrap APIs.
        body=safe(p.locator("body").inner_text(timeout=8000),2000)
        has_login=any(x in body for x in LOGIN_SIGNALS)
        r["login_or_challenge_visible"]=has_login
        r["guest_visible_body_excerpt"]=body[:450]
        r["guest_visible_body_chars"]=len(body)
        rendered=p.locator("a[href]").evaluate_all("""els =>
          els.filter(a => a.getClientRects().length && getComputedStyle(a).visibility !== 'hidden')
             .slice(0, 250).map(a => ({url:a.href,title:(a.innerText || a.title || '').trim().slice(0,130)}))""")
        seen=set()
        links=[]
        for item in rendered:
            href=item.get("url","")
            if not relevant_work(href,platform) or href in seen:continue
            seen.add(href)
            links.append({"url":safe(href,450),"visible_link_text":safe(item.get("title"),130)})
        r["total_visible_anchors"]=len(rendered)
        r["visible_post_links"]=len(links)
        r["sample"]=links[:5]
        if response and response.status in (401,403,412,429):
            r["status"]="access_restricted"
        elif has_login:
            r["status"]="login_or_challenge" if not links else "partial_visible_links_with_login"
        elif links:
            r["status"]="verified_visible_search_links"
        else:
            r["status"]="html_without_visible_posts"
        # No reply fetching unless an actual individual post is available.
        # This intentionally does not call unofficial signed comment APIs.
        if links and not has_login:
            detail=context.new_page()
            try:
                result=detail.goto(links[0]["url"],wait_until="domcontentloaded",timeout=18000)
                detail.wait_for_timeout(3200)
                page_text=safe(detail.locator("body").inner_text(timeout=6000),1600)
                r["detail_page_status"]=result.status if result else None
                r["detail_url_matches"]=bool(relevant_work(detail.url,platform))
                r["detail_login_or_challenge"]=any(s in page_text for s in LOGIN_SIGNALS)
                # We deliberately do not count generic "评论" labels as retrieved comments.
                r["comment_status"]="not_verified_from_visible_page"
            except Exception as e:
                r["comment_status"]="detail_not_verified"
                r["detail_error"]=type(e).__name__
            finally:
                detail.close()
        else:
            r["comment_status"]="not_retrieved"
    except (PlaywrightTimeout,Exception) as e:
        r["status"]="error"
        r["error"]=type(e).__name__+": "+safe(e,120)
    finally:
        p.close()
    return r

def main():
    rows=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True,args=["--no-sandbox"])
        try:
            for platform,url in CONFIG:
                ctx=browser.new_context(locale="zh-CN",timezone_id="Asia/Shanghai")
                try:rows.append(inspect(ctx,platform,url))
                finally:ctx.close()
        finally:browser.close()
    result={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"method":"public browser rendered UI, ephemeral guest only",
            "results":rows,
            "critical":"No invisible API payload or actual comment text was retrieved; do not represent successful browser launch as scraper success."}
    OUTPUT.mkdir(exist_ok=True,parents=True)
    (OUTPUT/"guest-visible-browser.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"guest_browser_probe_complete":[{"platform":x["platform"],"status":x["status"],
        "visible_post_links":x["visible_post_links"],"actual_comments":x["actual_comments"],
        "http_status":x.get("http_status"),"title":x.get("page_title"),
        "visible_body":x.get("guest_visible_body_excerpt"),
        "visible_anchors":x.get("total_visible_anchors"),
        "login_or_challenge":x.get("login_or_challenge_visible")} for x in rows]},ensure_ascii=False))
if __name__=="__main__":main()
