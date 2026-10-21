#!/usr/bin/env python3
"""Experimental X search + curator quote graph using the existing pinned reader.

The pinned X reader is installed by the current CI workflow. This collector
never logs into X, buys API access, bypasses private-account restrictions or
claims that source availability is guaranteed. Failed sources remain labeled.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
READER = HERE / "x_upstream.py"
CONFIG = HERE / "x_discovery_queries_v3.json"
URL = re.compile(r"https?://[^\s<>\"'，。；]+")
MAX_TEXT = 3500
MAX_SECONDS = 28
MAX_EXTRA_AUTHORS = 8


def sanitize_url(u):
    return str(u or "").rstrip(".,;:!?)）】")


def external_links(txt):
    return list(dict.fromkeys(sanitize_url(m.group(0)) for m in URL.finditer(txt or "")))[:10]


def public_project(links):
    for u in links:
        if u.startswith(("https://github.com/", "https://huggingface.co/spaces/",
                         "https://huggingface.co/", "https://www.producthunt.com/posts/")):
            return u
    return ""


def run(args):
    if not READER.is_file():
        raise RuntimeError("pinned_x_reader_not_installed")
    proc = subprocess.run([sys.executable, str(READER), *args],
                          capture_output=True, text=True, timeout=MAX_SECONDS)
    if proc.returncode:
        raise RuntimeError("x_reader_unavailable: " + (proc.stderr or proc.stdout)[-260:])
    try:
        obj = json.loads(proc.stdout)
    except ValueError as exc:
        raise RuntimeError("invalid_x_reader_output") from exc
    if not isinstance(obj, dict) or obj.get("error"):
        raise RuntimeError("x_reader_error: " + str(obj.get("error")))
    return obj


def to_candidate(tweet, origin, curator="", curator_quote_url=""):
    if not isinstance(tweet, dict):
        return None
    url = tweet.get("url")
    if not isinstance(url, str) or not url.startswith("https://x.com/"):
        return None
    author = tweet.get("author") or {}
    text = str(tweet.get("text") or "")
    article = tweet.get("article") or {}
    if isinstance(article, dict):
        text += "\n" + str(article.get("text") or article.get("preview") or "")
    links = external_links(text)
    metrics = {k: tweet[k] for k in ("views", "likes", "reposts", "bookmarks", "replies")
               if type(tweet.get(k)) in (int, float) and tweet[k] >= 0}
    return {
        "source": origin, "url": url, "title": text[:MAX_TEXT],
        "author": author.get("handle") if isinstance(author, dict) else "",
        "published_utc": tweet.get("created_at"),
        "external_links": links, "project_url": public_project(links),
        "metrics": metrics,
        "metrics_checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "curator": curator,
        "curator_quote_url": curator_quote_url,
        "quote_relationship_verified": bool(curator_quote_url),
        "retrieved_scope": "public_x_reader_search_or_quote_excerpt",
        "editorial_status": "research_candidate_only",
    }


def curator_rows(tweets, handle):
    out, discovered = [], set()
    for t in tweets[:45]:
        if not isinstance(t, dict):
            continue
        q = t.get("quoted")
        if isinstance(q, dict) and q.get("url"):
            original = to_candidate(q, "x_curator_quote", handle, t.get("url", ""))
            if original:
                out.append(original)
                if original["author"] and original["author"].lower() != handle.lower():
                    discovered.add(original["author"])
        # Curator-owned substantive posts are leads too, but not quoted works.
        if str(t.get("text") or "").strip() not in ("", "."):
            own = to_candidate(t, "x_curator_original", handle)
            if own:
                out.append(own)
    return out, discovered


def fetch_task(kind, value):
    if kind == "query":
        obj = run(["search", value, "--limit", "30", "--since", "7d", "--top"])
        return [p for t in obj.get("tweets", []) if (p := to_candidate(t, "x_keyword_search"))], {
            "source": "x_query:" + value, "status": "retrieved",
            "items": len(obj.get("tweets", [])), "more": bool(obj.get("more"))
        }, set()
    if kind == "curator":
        obj = run(["tweets", value, "--limit", "45", "--since", "7d", "--reposts"])
        rows, people = curator_rows(obj.get("tweets", []), value)
        return rows, {"source": "x_curator:" + value, "status": "retrieved",
                      "items": len(rows), "new_authors": len(people)}, people
    if kind == "author":
        obj = run(["tweets", value, "--limit", "10", "--since", "7d"])
        posts = [p for t in obj.get("tweets", [])
                 if (p := to_candidate(t, "x_discovered_author"))]
        return posts, {"source": "x_author:" + value, "status": "retrieved",
                       "items": len(posts)}, set()
    raise ValueError("unknown_task")


def collect(cfg, execute=fetch_task):
    rows, health, discovered = [], [], set()
    work = [("query", x) for x in cfg.get("queries", [])[:6]]
    work += [("curator", x) for x in cfg.get("curators", [])[:5]]
    with ThreadPoolExecutor(max_workers=3) as ex:
        jobs = {ex.submit(execute, kind, v): (kind, v) for kind, v in work}
        for future in as_completed(jobs):
            kind, val = jobs[future]
            try:
                posts, status, people = future.result()
                rows.extend(posts)
                health.append(status)
                discovered.update(people)
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
                health.append({"source": kind + ":" + val, "status": "unavailable",
                               "items": 0, "error": str(exc)[:260]})
    curator_set = set(cfg.get("curators", []))
    for person in sorted(discovered - curator_set)[:MAX_EXTRA_AUTHORS]:
        try:
            posts, status, _ = execute("author", person)
            rows.extend(posts)
            health.append(status)
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            health.append({"source": "x_author:" + person, "status": "unavailable",
                           "items": 0, "error": str(exc)[:260]})
    # One post can appear in search and author scan. Preserve distinct entry
    # provenance within collection, but don't multiply same signal twice.
    seen = set()
    dedup = []
    for item in rows:
        key = (item.get("url"), item.get("source"), item.get("curator_quote_url"))
        if key not in seen:
            seen.add(key)
            dedup.append(item)
    return dedup, sorted(health, key=lambda p: p["source"]), sorted(discovered)


def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    items, health, authors = collect(cfg)
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "items": items, "source_health": health, "discovered_authors": authors,
        "limitations": [
            "Source API is third-party read-only, not official X API or comprehensive access.",
            "Search is bounded and hot ranking is the provider's, not objective virality.",
            "Quote relationship is verified only when original is nested in a retrieved quote.",
            "Any metric is a per-post third-party snapshot; never an outcome forecast.",
            "Full article, actual project utility and multimedia rights require manual verification.",
            "Public collector failures do not imply absence of posts.",
        ],
    }
    (OUT / "x-hot-curator-v3.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"posts": len(items), "sources": health,
                      "new_authors": len(authors)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
