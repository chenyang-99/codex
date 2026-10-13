#!/usr/bin/env python3
"""Hourly Google/Gemini 4 public announcement evidence monitor.

Reads public X timelines through the pinned upstream used by this repository.
Missing/blocked feeds are reported as unknown, NEVER as no announcements.
Also checks Google-owned public RSS feeds for complementary coverage.
"""
import datetime as dt
import email.utils
import json
import re
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
UPSTREAM = HERE / "x_upstream.py"
HANDLES = [
    "Google", "NewsFromGoogle", "GoogleAI", "GoogleDeepMind",
    "GeminiApp", "GoogleAIStudio", "GoogleCloud", "GoogleDevelopers",
    "GoogleResearch", "GoogleLabs", "GoogleWorkspace", "MadeByGoogle",
    "Android", "googlechrome",
]
FEEDS = {
    "Google AI Blog": "https://blog.google/technology/ai/rss/",
    "Google DeepMind": "https://deepmind.google/discover/blog/rss.xml",
    "Google Research": "https://research.google/blog/rss/",
}
PHRASE = re.compile(r"(?i)\b(?:gemini[\s.\-]*4(?:\b|[.\-]\d+)|gemini\s+four\b|gemini\s+argon\b|gemini\s+4\s+argon\b)")

def scrape_handle(handle):
    if not UPSTREAM.exists():
        return {"status": "unavailable", "reason": "pinned_x_upstream_missing"}, []
    try:
        proc = subprocess.run(
            [sys.executable, str(UPSTREAM), "tweets", handle, "--limit", "15", "--since", "3d"],
            text=True, capture_output=True, timeout=38, check=False
        )
        data = json.loads(proc.stdout or "{}")
        if proc.returncode or not isinstance(data, dict) or data.get("error"):
            return {"status": "unavailable", "reason": str(data.get("error", "nonzero_exit"))[:160]}, []
        tweets = [
            {
                "source": "X", "handle": handle, "author": (t.get("author") or {}).get("handle"),
                "id": str(t.get("id")), "url": t.get("url"),
                "created_at": t.get("created_at"), "text": str(t.get("text") or "")[:2000],
            }
            for t in data.get("tweets", []) if isinstance(t, dict) and t.get("id") and t.get("text")
        ]
        return {"status": "verified", "returned": len(tweets), "has_more": bool(data.get("more"))}, tweets
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {"status": "unavailable", "reason": type(exc).__name__}, []

def scrape_feed(name, url):
    try:
        request = urllib.request.Request(url, headers={
            "User-Agent": "Google-Gemini4-Official-News-Monitor/1.0",
            "Accept": "application/rss+xml,application/atom+xml,application/xml",
        })
        with urllib.request.urlopen(request, timeout=17) as res:
            raw = res.read(1_500_000)
        root = ET.fromstring(raw)
        items = root.findall("./channel/item")
        if not items:
            items = root.findall("{http://www.w3.org/2005/Atom}entry")
        rows = []
        for item in items[:45]:
            title = item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or ""
            desc = item.findtext("description") or item.findtext("{http://www.w3.org/2005/Atom}summary") or ""
            link = item.findtext("link") or ""
            if not link:
                element = item.find("{http://www.w3.org/2005/Atom}link")
                if element is not None:
                    link = element.attrib.get("href", "")
            published = item.findtext("pubDate") or item.findtext("{http://www.w3.org/2005/Atom}published") or item.findtext("{http://www.w3.org/2005/Atom}updated")
            rows.append({"source": name, "title": title[:300], "text": (title + " " + re.sub(r"<[^>]*>", " ", desc))[:1600], "url": link, "created_at": published})
        return {"status": "verified", "returned": len(rows)}, rows
    except Exception as exc:
        return {"status": "unavailable", "reason": type(exc).__name__ + ": " + str(exc)[:110]}, []

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    statuses = {}
    matches = []
    seen = set()
    scan_counts = {"x_posts": 0, "feed_entries": 0}
    for handle in HANDLES:
        status, posts = scrape_handle(handle)
        statuses["X:@" + handle] = status
        scan_counts["x_posts"] += len(posts)
        for post in posts:
            if PHRASE.search(post["text"]) and post.get("url") not in seen:
                matches.append(post)
                seen.add(post["url"])
        time.sleep(.25)
    for name, url in FEEDS.items():
        status, items = scrape_feed(name, url)
        statuses["RSS:" + name] = status
        scan_counts["feed_entries"] += len(items)
        for item in items:
            if PHRASE.search(item["text"]) and item.get("url") not in seen:
                matches.append(item)
                seen.add(item["url"])
    doc = {
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "topic": "Google official Gemini 4 announcements and availability",
        "method": "Pinned anonymous public X-account timeline + official Google RSS",
        "authoritative_baseline": {
            "published": "2026-09-30",
            "model": "Gemini 4 Argon",
            "url": "https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/",
            "note": "Already announced; do not re-alert this news as a new announcement"
        },
        "accounts": HANDLES, "feed_sources": FEEDS,
        "statuses": statuses, "scan_counts": scan_counts,
        "matches": sorted(matches, key=lambda p: str(p.get("created_at") or ""), reverse=True),
        "limitations": [
            "X public timeline gateway is third-party and may fail or omit posts",
            "This is not complete coverage of every Google subsidiary, language or personal staff account",
            "Not a push notification channel; alerting and per-check deduplication are separate",
            "RSS syndication and search indexing can lag official publication"
        ]
    }
    target = OUT / "google-gemini4-watch.json"
    target.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    md = ["# Google Gemini 4 official watch", "",
          "UTC check: " + doc["checked_at_utc"], "",
          f"Scanned {scan_counts['x_posts']} X posts; {scan_counts['feed_entries']} RSS entries.", "",
          "## Per-source coverage"]
    for k, s in statuses.items():
        md.append(f"- {k}: {s['status']}; count={s.get('returned', 'unknown')}; {s.get('reason', '')}")
    md.extend(["", "## Text-matched public evidence (NOT automatically new announcements)", ""])
    for m in doc["matches"]:
        md.extend([f"- {m.get('created_at', '?')} | {m.get('source')} | {m.get('url')}",
                   "  " + m.get("text", "")[:340].replace("\n", " ")])
    md.extend(["", "Verify dates and actual newness before sending alerts. Baseline already announced 2026-09-30."])
    (OUT / "google-gemini4-watch.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"checked_at_utc": doc["checked_at_utc"], "verified_sources":
        sum(s["status"] == "verified" for s in statuses.values()),
        "total_sources": len(statuses), "matching_entries": len(matches),
        "counts": scan_counts}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
