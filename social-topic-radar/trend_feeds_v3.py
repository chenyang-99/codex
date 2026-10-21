#!/usr/bin/env python3
"""Supplementary public hot-content feeds: Product Hunt, Lobsters, GitHub Trending.

RSS/JSON is read-only. "Trending" labels reflect each provider, never a claim
about X/Douyin popularity. A dead feed is recorded as an unavailable source.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
UA = "SocialTopicRadar/3.1 (public read-only trend discovery)"
ATOM = "{http://www.w3.org/2005/Atom}"
MAX_BYTES = 1_700_000
FEEDS = {
    "producthunt_launch_rss": {
        "url": "https://www.producthunt.com/feed",
        "type": "xml",
        "platform": "producthunt",
        "scope": "official RSS launches, NOT independently verified top-ranking votes",
    },
    "lobsters_hot_rss": {
        "url": "https://lobste.rs/hottest.rss",
        "type": "xml",
        "platform": "lobsters",
        "scope": "official public programming community hottest-feed snapshot",
    },
    "github_trending_mirror": {
        "url": "https://cdn.jsdelivr.net/gh/Hyraze/trending-collection@main/api/daily/all.json",
        "type": "json",
        "platform": "github_trending_mirror",
        "scope": "third-party daily GitHub Trending mirror; freshness and provenance require checks",
    },
}

def retrieve(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json, application/xml, application/atom+xml, application/rss+xml"})
    with urlopen(req, timeout=12) as response:
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("content_exceeds_max_bytes")
        return data

def unpack_xml(raw):
    root = ET.fromstring(raw)
    if root.tag.endswith("rss"):
        container = root.find("channel")
        items = container.findall("item") if container is not None else []
        for item in items[:30]:
            yield {
                "title": item.findtext("title") or "",
                "url": item.findtext("link") or "",
                "published_utc": item.findtext("pubDate") or None,
            }
    elif root.tag.endswith("feed"):
        for item in root.findall(ATOM + "entry")[:30]:
            link = next((node.attrib.get("href", "") for node in item.findall(ATOM + "link")
                        if node.attrib.get("rel", "alternate") == "alternate"), "")
            yield {
                "title": item.findtext(ATOM + "title") or "",
                "url": link,
                "published_utc": item.findtext(ATOM + "published") or item.findtext(ATOM + "updated"),
            }
    else:
        raise ValueError("unexpected_rss_or_atom_root")

def unpack_trending_json(raw):
    obj = json.loads(raw)
    rows = obj.get("items", []) if isinstance(obj, dict) else []
    if not isinstance(rows, list):
        raise ValueError("unexpected_trending_json")
    for item in rows[:35]:
        if not isinstance(item, dict):
            continue
        yield {
            "title": (item.get("title") or "") + " — " + str(item.get("description") or "")[:250],
            "url": item.get("url") or "",
            "project_url": item.get("url") or "",
            "published_utc": None,  # publication of RSS archive != project creation date
        }

def normalized_date(value):
    if not isinstance(value, str) or not value: return None
    try:
        return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc).isoformat()
    except ValueError:
        try:
            return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
        except (TypeError,ValueError,OverflowError):
            return None

def fetch_one(source, cfg, read=retrieve):
    raw = read(cfg["url"])
    candidates = (unpack_xml(raw) if cfg["type"] == "xml" else unpack_trending_json(raw))
    rows, seen = [], set()
    now = datetime.now(timezone.utc).isoformat()
    for item in candidates:
        url = str(item.get("url") or "").strip()
        if not url.startswith("https://") or url in seen or not item.get("title"):
            continue
        seen.add(url)
        rows.append({
            "url": url, "source": source, "platform": cfg["platform"],
            "title": re.sub(r"\s+", " ", str(item["title"])).strip()[:650],
            "project_url": item.get("project_url") if str(item.get("project_url") or "").startswith("https://") else "",
            "published_utc": normalized_date(item.get("published_utc")),
            "collected_utc": now,
            "metrics": {},
            "read_scope": cfg["scope"], "editorial_status": "research_candidate_only",
        })
    return rows

def collect(feeds=FEEDS, read=retrieve):
    records, health = [], []
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks = {pool.submit(fetch_one, name, cfg, read): name for name, cfg in feeds.items()}
        for future in as_completed(tasks):
            name = tasks[future]
            try:
                rows = future.result()
                records.extend(rows)
                health.append({"source": name, "status": "retrieved" if rows else "empty",
                               "items": len(rows), "checked_at": datetime.now(timezone.utc).isoformat()})
            except (OSError, ValueError, ET.ParseError, HTTPError, URLError, TimeoutError) as exc:
                health.append({"source": name, "status": "unavailable", "items": 0,
                               "error": f"{type(exc).__name__}: {str(exc)[:145]}",
                               "checked_at": datetime.now(timezone.utc).isoformat()})
    return records, sorted(health, key=lambda x: x["source"])

def main():
    records, health = collect()
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "items": records, "source_health": health,
        "limitations": [
            "A published RSS entry is a discovery lead, not a social media hit.",
            "Product Hunt RSS may list launches rather than vote-sorted top products.",
            "Github Trending JSON is a third-party mirror; track archive freshness separately.",
            "Public sources can be blocked by rate limits; zero is not a substitute for failure.",
        ],
    }
    (OUT / "external-discovery-hot-extra.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources": health, "records": len(records)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
