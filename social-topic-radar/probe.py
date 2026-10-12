#!/usr/bin/env python3
"""Anonymous, read-only social platform capability smoke test. Python stdlib."""
from __future__ import annotations
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

OUT = Path(__file__).resolve().parent / "output"
X_SCRIPT = Path(__file__).resolve().parent / "x_upstream.py"
X_TWEET = "https://x.com/thsottiaux/status/2107913674593644711"
XHS_NOTE = "https://www.xiaohongshu.com/discovery/item/69ec4330000000001a02de7d"
DOUYIN_POST = "https://v.douyin.com/72RGMuz7Xpo/"
MAX_BYTES = 550_000

def safe_str(v, length=260):
    if v is None:
        return ""
    value = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", html.unescape(str(v)))
    return re.sub(r"\s+", " ", value).strip()[:length]

def clean_url(url):
    try:
        s = urlsplit(url)
        return urlunsplit((s.scheme, s.netloc, s.path, "", ""))
    except Exception:
        return safe_str(url, 120)

class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.in_title = False
        self.title = ""
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key in {"og:title", "og:description", "description", "twitter:title", "twitter:description", "og:type"}:
                self.meta[key] = safe_str(a.get("content"), 400)
    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
    def handle_data(self, data):
        if self.in_title:
            self.title += data[:300]

def website_probe(platform, url, keyword):
    base = dict(platform=platform, source=clean_url(url), content_status="error",
                comments_status="not_supported", comments_returned=0,
                note="Anonymous HTML probe only; does not attempt complete search or comments.")
    try:
        request = Request(url, headers={"User-Agent":"Mozilla/5.0 (compatible; ReadOnlyPublicMetadataProbe/1.0)",
                                        "Accept":"text/html,application/xhtml+xml"})
        with urlopen(request, timeout=20) as response:
            status = response.status
            final_url = response.geturl()
            raw = response.read(MAX_BYTES)
            encoding = response.headers.get_content_charset() or "utf-8"
        page = raw.decode(encoding, errors="replace")
        parser = Meta()
        parser.feed(page)
        title = safe_str(parser.meta.get("og:title") or parser.meta.get("twitter:title") or parser.title)
        desc = safe_str(parser.meta.get("og:description") or parser.meta.get("description"))
        final_host = (urlsplit(final_url).hostname or "").lower()
        content_indicators = bool(title and title not in {"小红书", "抖音", "Douyin"})
        if platform == "xiaohongshu":
            valid = final_host.endswith("xiaohongshu.com") and "discovery/item/" in urlsplit(final_url).path
            is_generic = title.lower() in ("小红书 - 你的生活兴趣社区", "小红书") or "登录" in title
        else:
            valid = final_host.endswith(("douyin.com", "iesdouyin.com"))
            is_generic = title.lower() in ("抖音", "抖音 - 记录美好生活") or "登录" in title
        verified = bool(status == 200 and valid and content_indicators and not is_generic and desc)
        missing = urlsplit(final_url).path.rstrip("/") == "/404" or "你访问的页面不见了" in title
        base.update(http_status=status, final_url=clean_url(final_url),
                    content_status=("not_found" if missing else "verified" if verified else "partial"),
                    title=title, description_excerpt=desc,
                    note=("Public note/video URL redirected to a 404 page; no content retrieved." if missing
                          else "Public post metadata parsed; full body, media, and comments unverified." if verified
                          else "Page response exists, but this does not verify post-level content."))
        if "captcha" in page[:15000].lower() or "验证码" in page[:15000]:
            base["content_status"] = "blocked"
            base["note"] = "Captcha/security challenge detected; no bypass attempted."
        return base
    except HTTPError as e:
        base.update(content_status="blocked" if e.code in (401,403,429) else "error",
                    http_status=e.code, note=f"HTTP {e.code}, public page not verified.")
    except (URLError, TimeoutError, ValueError, OSError) as e:
        base.update(note=f"{type(e).__name__}: {safe_str(e,120)}")
    except Exception as e:
        base.update(note=f"Parser/network exception: {type(e).__name__}: {safe_str(e,120)}")
    return base

def run_x(name, args, timeout=48):
    result=dict(platform="x", name=name, content_status="error",
                source="public FxTwitter (via pinned X-Aggregate-Data)",
                comments_status="not_tested", comments_returned=0)
    if not X_SCRIPT.is_file():
        result["note"]="Pinned read-only X script was not installed on this runner."
        return result
    try:
        p=subprocess.run([sys.executable, str(X_SCRIPT), *args], capture_output=True,
                         text=True, timeout=timeout, check=False)
        payload=json.loads(p.stdout or "{}")
        if p.returncode != 0 or not isinstance(payload,dict) or payload.get("error"):
            result["content_status"]="source_unavailable" if p.returncode in (4,5) else "error"
            result["note"]=safe_str(payload.get("error") or p.stderr or f"Exit {p.returncode}",220)
            return result
        if name == "tweet_and_replies":
            post = payload.get("tweet") or {}
            posts = [post] if post.get("id") and post.get("text") else []
            replies = payload.get("replies") if isinstance(payload.get("replies"),list) else []
            result["comments_returned"]=len(replies)
            result["comments_status"]="verified" if replies else "empty_or_unavailable"
            result["replies_info"]=payload.get("replies_info",{})
        else:
            posts = payload.get("tweets") if isinstance(payload.get("tweets"),list) else []
        result["count"]=len(posts)
        result["content_status"]="verified" if posts else "empty_or_unavailable"
        result["sample"]=[{
            "id": safe_str(x.get("id"),30),
            "url": clean_url(x.get("url") or ""),
            "text_excerpt":safe_str(x.get("text"),350),
            "created_at":safe_str(x.get("created_at"),50),
            "likes":x.get("likes"),"replies":x.get("replies")
        } for x in posts[:3] if isinstance(x,dict)]
        result["note"]="Actual returned public rows. Coverage is partial; not the entire platform."
    except (OSError,subprocess.TimeoutExpired,json.JSONDecodeError) as e:
        result["note"]=f"{type(e).__name__}: {safe_str(e,160)}"
    return result

def generate_report():
    results=[
        run_x("keyword_search",["search","AI image prompt","--limit","5"]),
        run_x("creator_timeline",["tweets","karpathy","--limit","3"]),
        run_x("tweet_and_replies",["tweet",X_TWEET,"--replies","5"]),
        website_probe("xiaohongshu",XHS_NOTE,"笔记"),
        website_probe("douyin",DOUYIN_POST,"视频"),
    ]
    doc={"checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
         "mode":"anonymous_read_only", "social_login_used":False, "paid_api_used":False,
         "completeness":"Full-platform capture impossible. This is bounded public-data evidence only.",
         "results":results}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"report.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding="utf-8")
    lines=["# Anonymous social media read-only capability test","",
           f"Checked (UTC): {doc['checked_at_utc']}","","No account login, cookies, paid APIs or bypass.","",
           "| Platform | Probe | Content | Comments | Count |","|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['platform']} | {r.get('name','public_url')} | {r['content_status']} | {r['comments_status']} | {r.get('comments_returned',0)} |")
    lines += ["","## Evidence and limitations",""]
    for r in results:
        lines += [f"### {r['platform']} — {r.get('name','public_url')}",
                  f"Status: **{r['content_status']}**. {r.get('note','')}",
                  f"Comments: **{r['comments_status']}**; actually returned: {r.get('comments_returned',0)}.",
                  f"Source: {r.get('source','')}", ""]
        for s in r.get("sample",[]):
            lines += [f"- {s.get('url','')} — {safe_str(s.get('text_excerpt',''),180)}"]
    lines += ["","The status of a public page is not proof of complete note/video retrieval. "
              "Missing comments must NOT be represented as zero audience comments. "
              "GitHub Actions IP blocking and public gateway rate limits may affect results."]
    (OUT/"report.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"status":"probe_complete","results":[{"platform":r["platform"],"probe":r.get("name","public_url"),
                  "content":r["content_status"],"comments":r["comments_status"],
                  "comments_returned":r.get("comments_returned",0)} for r in results]},ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(generate_report())
