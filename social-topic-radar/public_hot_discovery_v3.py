#!/usr/bin/env python3
"""Read-only multi-platform *public hot-list* discovery; no social login.

Separate site-native popularity signals (HN points, Reddit votes, GitHub
cumulative stars, V2EX hot-list placement) from X likes/bookmarks/views.
Every provider records success, empty or error; errors are never zero posts.
Other platforms require an approved adapter, public feed, or on-demand review.
"""
from __future__ import annotations

import concurrent.futures
import datetime as dt
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
USER_AGENT = "PublicTopicDiscovery/3.0 (read-only; contact via repository)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json, application/atom+xml;q=0.9"}
MAX_BYTES = 2_000_000


def get(url: str, timeout: int = 9):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as result:
        return result.read(MAX_BYTES)


def get_json(url: str):
    return json.loads(get(url).decode("utf-8"))


def checked_at():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def unix_time(value):
    if not isinstance(value, (int, float)) or value < 0:
        return None
    return dt.datetime.fromtimestamp(value, tz=dt.timezone.utc).isoformat()


def status(name, state, count=0, detail=""):
    return {"source": name, "status": state, "items": count,
            "detail": str(detail)[:250], "checked_at": checked_at()}


def collect_hn():
    """HN official public API. Up to 12 top + 12 Show HN story details."""
    ids = []
    try:
        for feed in ("topstories", "showstories"):
            rows = get_json(f"https://hacker-news.firebaseio.com/v0/{feed}.json")
            if not isinstance(rows, list):
                raise ValueError("HN list is not JSON array")
            ids.extend(rows[:12])
        ids = list(dict.fromkeys(x for x in ids if isinstance(x, int)))[:24]
        def fetch_story(identifier):
            obj = get_json(f"https://hacker-news.firebaseio.com/v0/item/{identifier}.json")
            if not isinstance(obj, dict) or obj.get("dead") or obj.get("deleted"):
                return None
            if obj.get("type") != "story" or not obj.get("title"):
                return None
            return {
                "source": "hackernews", "platform": "hackernews",
                "url": f"https://news.ycombinator.com/item?id={identifier}",
                "title": str(obj["title"])[:400],
                "author": obj.get("by"),
                "published_utc": unix_time(obj.get("time")),
                "external_links": [obj["url"]] if str(obj.get("url", "")).startswith("https://") else [],
                "platform_native_metrics": {"points": obj.get("score"), "comments": obj.get("descendants")},
                "metrics_checked_at": checked_at(),
                "read_scope": "official HN top/show feed metadata, not full tutorial",
            }
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            records = [x for x in pool.map(fetch_story, ids) if x]
        return status("hackernews_hot", "retrieved" if records else "empty", len(records)), records
    except Exception as e:
        return status("hackernews_hot", "error", detail=type(e).__name__ + ": " + str(e)), []


def collect_v2ex():
    """Official guest-accessible V2EX /api/topics/hot.json; subject to limits."""
    try:
        obj = get_json("https://www.v2ex.com/api/topics/hot.json")
        if not isinstance(obj, list):
            raise ValueError("unexpected V2EX structure")
        records = []
        for rank, item in enumerate(obj[:20], 1):
            if not isinstance(item, dict) or not item.get("url"):
                continue
            records.append({
                "source": "v2ex", "platform": "v2ex", "url": item["url"],
                "title": str(item.get("title") or "")[:400],
                "author": (item.get("member") or {}).get("username"),
                "published_utc": unix_time(item.get("created")),
                "platform_native_metrics": {"replies": item.get("replies"), "hot_rank": rank},
                "metrics_checked_at": checked_at(),
                "read_scope": "public V2EX hot topics, not proven AI-interest audience",
            })
        return status("v2ex_hot", "retrieved" if records else "empty", len(records)), records
    except Exception as e:
        return status("v2ex_hot", "error", detail=type(e).__name__ + ": " + str(e)), []


def collect_github():
    """Recent popular repos, not the official GitHub Trending leaderboard."""
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)).date().isoformat()
    terms = [f"ai created:>{since} stars:>=20",
             f"agent created:>{since} stars:>=20",
             f"image generation created:>{since} stars:>=20"]
    out, errors, seen = [], [], set()
    for q in terms:
        params = urllib.parse.urlencode({"q": q, "sort": "stars", "order": "desc", "per_page": 15})
        try:
            obj = get_json("https://api.github.com/search/repositories?" + params)
            if not isinstance(obj, dict) or not isinstance(obj.get("items"), list):
                raise ValueError("unexpected GitHub search results")
            for item in obj["items"]:
                url = item.get("html_url")
                if not isinstance(url, str) or url in seen:
                    continue
                seen.add(url)
                out.append({
                    "source": "github_search_recent", "platform": "github",
                    "url": url, "project_url": url,
                    "title": f"{item.get('full_name', '')}: {item.get('description') or ''}"[:400],
                    "published_utc": item.get("created_at"),
                    "platform_native_metrics": {"cumulative_stars": item.get("stargazers_count"),
                                                "cumulative_forks": item.get("forks_count")},
                    "metrics_checked_at": checked_at(),
                    "read_scope": "GitHub public newly-created repository search; not star growth",
                })
        except Exception as e:
            errors.append(type(e).__name__ + ": " + str(e)[:130])
    state = "partial" if errors and out else "error" if errors else "retrieved" if out else "empty"
    return status("github_recent_popular", state, len(out), "; ".join(errors)), out


def collect_reddit_rss():
    """Guest-only RSS experiment; 403/rate limits are reported, not bypassed."""
    out, errors = [], []
    for community in ("LocalLLaMA", "ChatGPT"):
        try:
            data = get(f"https://www.reddit.com/r/{community}/top/.rss?t=week")
            root = ET.fromstring(data)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns)[:12]:
                title = entry.findtext("atom:title", default="", namespaces=ns)
                link = entry.find("atom:link", ns)
                url = link.attrib.get("href", "") if link is not None else ""
                if not url.startswith("https://"):
                    continue
                out.append({
                    "source": "reddit", "platform": "reddit", "url": url,
                    "title": title[:400], "published_utc":
                        entry.findtext("atom:published", default="", namespaces=ns),
                    "read_scope": "public subreddit top-week RSS; no votes or comments verified",
                })
        except Exception as e:
            errors.append(f"r/{community}: {type(e).__name__}: {str(e)[:90]}")
    state = "partial" if errors and out else "error" if errors else "retrieved" if out else "empty"
    return status("reddit_week_top", state, len(out), "; ".join(errors)), out


def collect_bilibili():
    """Uncredentialed experimental public chart; deny/rate limit = unavailable."""
    try:
        obj = get_json("https://api.bilibili.com/x/web-interface/popular?pn=1&ps=20")
        data = obj.get("data") if isinstance(obj, dict) else None
        if obj.get("code") != 0 or not isinstance(data, dict) or not isinstance(data.get("list"), list):
            raise ValueError("Bilibili returned unavailable popular-list data")
        out = []
        for rank, video in enumerate(data["list"][:20], 1):
            bvid = video.get("bvid")
            if not bvid:
                continue
            out.append({
                "source": "bilibili", "platform": "bilibili",
                "url": f"https://www.bilibili.com/video/{bvid}",
                "title": str(video.get("title") or "")[:400],
                "author": (video.get("owner") or {}).get("name"),
                "published_utc": unix_time(video.get("pubdate")),
                "platform_native_metrics": {
                    "hot_rank": rank, "views": (video.get("stat") or {}).get("view"),
                    "favorites": (video.get("stat") or {}).get("favorite")},
                "metrics_checked_at": checked_at(),
                "read_scope": "public Bilibili popular list if accessible; video body not watched",
            })
        return status("bilibili_popular", "retrieved" if out else "empty", len(out)), out
    except Exception as e:
        return status("bilibili_popular", "error", detail=type(e).__name__ + ": " + str(e)), []


COLLECTORS = (collect_hn, collect_v2ex, collect_github, collect_reddit_rss, collect_bilibili)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    statuses, items = [], []
    for collector in COLLECTORS:
        report, records = collector()
        statuses.append(report)
        items.extend(records)
    result = {
        "checked_at_utc": checked_at(), "provider_status": statuses, "items": items,
        "limitations": [
            "No attempt to access private accounts or bypass a platform restriction.",
            "Site-native scores, favorites and stars have incompatible denominators.",
            "Hot-list presence is not proof of relevance to AI audiences.",
            "Official GitHub Trending and other platform-wide charts are NOT fully collected.",
            "Any missing, empty or failed provider needs independent manual or authorized follow-up.",
        ],
    }
    (OUT / "external-discovery.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"providers": statuses, "items": len(items)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
