#!/usr/bin/env python3
"""Public multi-platform hot-content leads, with source-by-source failure evidence.

Only documented/public read-only endpoints, no login, private content or
unapproved paid services. Platform scores are NOT comparable with each other.
"""
from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = Path(__file__).resolve().parent
OUT = BASE / "output"
AGENT = "AI-topic-radar/3.0 (public-read-only)"
MAX_BYTES = 2_000_000
TIMEOUT = 9

ENDPOINTS = {
    "hackernews_show": "https://hacker-news.firebaseio.com/v0/showstories.json",
    "hackernews_top": "https://hacker-news.firebaseio.com/v0/topstories.json",
    "devto_top": "https://dev.to/api/articles?top=7&per_page=20",
    "v2ex_hot": "https://www.v2ex.com/api/topics/hot.json",
    "hf_spaces": "https://huggingface.co/api/spaces?sort=trendingScore&direction=-1&limit=20",
}
# Explicit public endpoints, not arbitrary URLs from source-provided text.
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def fetch_json(url):
    req = Request(url, headers={
        "User-Agent": AGENT,
        "Accept": "application/json",
    })
    with urlopen(req, timeout=TIMEOUT) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response_exceeds_limit")
    return json.loads(raw)


def iso_epoch(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat()
    except (ValueError, OSError, OverflowError):
        return None


def value(row, key, default=None):
    return row.get(key, default) if isinstance(row, dict) else default


def metric(value_):
    if isinstance(value_, (int, float)) and not isinstance(value_, bool) and value_ >= 0:
        return value_
    return None


def pack(*, source, title, url, published=None, author="", project_url="",
         engagement=None, scope="public_platform_api"):
    if not isinstance(url, str) or not url.startswith("https://"):
        return None
    return {
        "source": source, "title": str(title or "")[:420],
        "url": url, "published_utc": published, "author": str(author or "")[:90],
        "project_url": project_url if str(project_url).startswith("https://") else "",
        "metrics": {k: n for k, v in (engagement or {}).items()
                    if (n := metric(v)) is not None},
        "retrieved_scope": scope,
        "metrics_checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "editorial_status": "research_candidate_only",
    }


def hnews(key):
    ids = fetch_json(ENDPOINTS[key])
    if not isinstance(ids, list):
        raise ValueError("invalid_hn_story_list")
    # Small bounded sample of ranked IDs. Each item URL has a numeric ID only.
    ids = [n for n in ids if isinstance(n, int) and n > 0][:12]
    rows = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(lambda sid: _safe_hn_item(sid), ids))
    for sid, obj in zip(ids, responses):
        if not isinstance(obj, dict) or obj.get("deleted") or obj.get("dead"):
            continue
        link = f"https://news.ycombinator.com/item?id={sid}"
        external = str(obj.get("url") or "")
        project_url = external if external.startswith("https://github.com/") else ""
        row = pack(source=key, title=obj.get("title"), url=link,
                   published=iso_epoch(obj.get("time")),
                   author=obj.get("by"), project_url=project_url,
                   engagement={"points": obj.get("score"), "comments": obj.get("descendants")})
        if row:
            rows.append(row)
    return rows


def _safe_hn_item(sid):
    try:
        return fetch_json(HN_ITEM.format(sid))
    except (ValueError, HTTPError, URLError, TimeoutError, OSError):
        return None


def devto():
    items = fetch_json(ENDPOINTS["devto_top"])
    if not isinstance(items, list):
        raise ValueError("invalid_devto_list")
    rows = []
    for item in items[:20]:
        row = pack(source="devto_top", title=value(item, "title"),
                   url=value(item, "url"), published=value(item, "published_at"),
                   author=value(value(item, "user", {}), "username"),
                   engagement={"reactions": value(item, "positive_reactions_count"),
                               "comments": value(item, "comments_count")},
                   scope="public_devto_top_articles")
        if row:
            rows.append(row)
    return rows


def v2ex():
    items = fetch_json(ENDPOINTS["v2ex_hot"])
    if not isinstance(items, list):
        raise ValueError("invalid_v2ex_list")
    rows = []
    for item in items[:20]:
        link = str(value(item, "url") or "")
        if link.startswith("http://www.v2ex.com/"):
            link = link.replace("http://", "https://", 1)
        row = pack(source="v2ex_hot", title=value(item, "title"),
                   url=link, published=iso_epoch(value(item, "created")),
                   author=value(value(item, "member", {}), "username"),
                   engagement={"comments": value(item, "replies")},
                   scope="public_v2ex_hot_listing")
        if row:
            rows.append(row)
    return rows


def huggingface():
    items = fetch_json(ENDPOINTS["hf_spaces"])
    if not isinstance(items, list):
        raise ValueError("invalid_hf_spaces_list")
    rows = []
    for item in items[:20]:
        space_id = value(item, "id")
        if not isinstance(space_id, str) or "/" not in space_id:
            continue
        url = "https://huggingface.co/spaces/" + space_id
        row = pack(source="huggingface_spaces_trending",
                   title=value(item, "id"), url=url,
                   published=value(item, "createdAt"),
                   author=space_id.split("/", 1)[0],
                   engagement={"likes": value(item, "likes"),
                               "trending_score": value(item, "trendingScore")},
                   scope="public_huggingface_trending_spaces")
        if row:
            rows.append(row)
    return rows


COLLECTORS = {
    "hackernews_show": lambda: hnews("hackernews_show"),
    "hackernews_top": lambda: hnews("hackernews_top"),
    "devto_top": devto,
    "v2ex_hot": v2ex,
    "hf_spaces": huggingface,
}


def collect(collectors=COLLECTORS):
    records, health = [], []
    # Work is independently bounded; one unavailable platform does not
    # masquerade as an empty trend board or stop other sources.
    with ThreadPoolExecutor(max_workers=5) as executor:
        jobs = {executor.submit(fn): name for name, fn in collectors.items()}
        for future in as_completed(jobs):
            name = jobs[future]
            try:
                items = future.result()
                records.extend(items)
                health.append({"source": name, "status": "retrieved" if items else "empty",
                               "items": len(items)})
            except (ValueError, HTTPError, URLError, TimeoutError, OSError) as exc:
                health.append({"source": name, "status": "unavailable",
                               "items": 0, "error": f"{type(exc).__name__}: {str(exc)[:130]}"})
    return records, sorted(health, key=lambda x: x["source"])


def main():
    records, health = collect()
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "items": records, "source_health": health,
        "limitations": [
            "Hot lists are platform-specific and do not prove AI audience relevance.",
            "Only bounded visible items were sampled; access and coverage may differ by runtime.",
            "Missing data is not a zero engagement count.",
            "GitHub Stars/HN points/DEV reactions are not X/Douyin/Reddit views or virality.",
            "No public-media rights or topic suitability automatically verified.",
        ],
    }
    (OUT / "external-discovery.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "sources": health},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
