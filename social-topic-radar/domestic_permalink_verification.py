#!/usr/bin/env python3
"""Verify indexed public social URLs. No login, cookie, signed API, or bypass.

Strict evidence model: an HTTP 200 or HTML shell does not mean a post was
retrieved. An unrelated redirect is failed verification, never original post.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from html.parser import HTMLParser
from html import unescape
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from urllib.error import HTTPError,URLError
import datetime as dt,json,re

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"

def text(s,n=200):
    return re.sub(r"\s+"," ",unescape(str(s or ""))).strip()[:n]

class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta={}
    def handle_starttag(self,tag,attrs):
        if tag!="meta":return
        a=dict(attrs)
        key=a.get("property") or a.get("name")
        if key and key.lower() in {"og:title","og:description","twitter:title","description"}:
            self.meta[key.lower()]=text(a.get("content"),420)

def probe(seed):
    url=seed["url"]; p=seed["platform"]
    record={**seed,"status":"not_verified","comments_status":"not_retrieved"}
    try:
        with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; PublicMetadataRead/1.0)",
                                          "Accept":"text/html,application/xhtml+xml"}),timeout=13) as r:
            status=r.status;final=r.geturl();blob=r.read(600_000)
        record["http_status"]=status
        record["final_url"]=final[:450]
        ref=urlsplit(url);dst=urlsplit(final)
        expected_id=ref.path.rstrip("/").split("/")[-1]
        host=dst.hostname or ""
        correct_domain=host==("www."+p+".com") if p=="douyin" else host.endswith("xiaohongshu.com")
        same_post=expected_id in dst.path and correct_domain
        if not same_post:
            record.update(status="not_verified_redirect",reason="Final URL is not the original indexed post URL")
            return record
        m=Meta();m.feed(blob.decode("utf-8",errors="replace"))
        title=m.meta.get("og:title") or m.meta.get("twitter:title") or ""
        desc=m.meta.get("og:description") or m.meta.get("description") or ""
        record["title_excerpt"]=title[:180]
        record["description_excerpt"]=desc[:250]
        good=bool(title and desc and "登录" not in title and "抖音" != title and "小红书" != title)
        record["status"]="verified_public_post_metadata" if good else "post_url_open_but_unverified_content"
        record["reason"]="Public post-specific metadata" if good else "No verifiable post-specific metadata returned"
    except HTTPError as e:
        record.update(status="restricted_or_unavailable",http_status=e.code,reason="HTTP "+str(e.code))
    except (URLError,TimeoutError,OSError,ValueError) as e:
        record.update(status="not_verified",reason=type(e).__name__+": "+text(e,90))
    return record

def main():
    seeds=json.loads((ROOT/"domestic-index-seeds.json").read_text(encoding="utf-8"))["seeds"]
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures={ex.submit(probe,s):i for i,s in enumerate(seeds)}
        rows=[None]*len(seeds)
        for f in as_completed(futures):rows[futures[f]]=f.result()
    verified=sum(x["status"]=="verified_public_post_metadata" for x in rows)
    report={"checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "total_seed_links":len(rows),"verified_public_post_metadata":verified,"results":rows,
            "limitations":["Indexed search snippets are not proof of live post content.",
                           "No real comments were retrieved and no claim of platform coverage is made.",
                           "All tests made one read-only anonymous HTTP request per URL."]}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"domestic-permalink-verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    md=["# 公开搜索作品直达链接有效性验证","",
        f"尝试链接：{len(rows)}，验证作品专属元数据：{verified}。","",
        "| 平台 | 索引标题 | 真实验证结果 |","|---|---|---|"]
    for x in rows:
        md.append(f"| {x['platform']} | {x['title_hint']} | {x['status']} |")
    md.extend(["","搜索结果能够定位 URL 并不等于视频、笔记或评论已读取。"
                   "未取得评论时不得写成 0 人评论。"])
    (OUT/"domestic-permalink-verification.md").write_text("\n".join(md),encoding="utf-8")
    print(json.dumps({"status":"domestic_permalinks_checked","attempts":len(rows),
                      "verified_public_post_metadata":verified,
                      "outcomes":{s:sum(x["status"]==s for x in rows) for s in sorted(set(x["status"] for x in rows))}},ensure_ascii=False))
if __name__=="__main__":main()
