#!/usr/bin/env python3
"""V3 shadow intake: unify *observed* discovery records without fabricating virality.

No network calls, login, posting, Sheet mutation, or dependency installation.
The input files are produced by existing collectors or are explicitly supplied
manual seeds. A source catalog entry alone is not a scraped post.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode

HERE = Path(__file__).resolve().parent
REGISTRY = HERE / "source_coverage_v3.json"
SOCIAL_HOSTS = {
    "x.com", "twitter.com", "www.reddit.com", "reddit.com", "youtube.com",
    "www.youtube.com", "bilibili.com", "www.bilibili.com", "douyin.com",
    "www.douyin.com", "xiaohongshu.com", "www.xiaohongshu.com", "bsky.app",
}
FILES = (
    ("public-rss-candidates.json", "items", "rss"),
    ("topic-candidates.json", "candidates", "x"),
    ("aicg-fresh-candidates.json", "items_newest_72h", "aicg"),
    ("aicg-fresh-candidates.json", "items_undated_or_time_unverified", "aicg"),
    ("aicg-original-site-items.json", "items", "aicg"),
    ("external-discovery.json", "items", "external"),
    ("external-discovery-devto-hf.json", "items", "devto_hf"),
    ("external-discovery-hot-extra.json", "items", "trending_rss"),
    ("x-hot-curator-v3.json", "items", "x_hot_curator"),
)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def canonical(value):
    """Preserve identity query keys; drop tracking so stories do not collide."""
    if not isinstance(value, str): return ""
    try:
        p = urlsplit(value.strip())
        if p.scheme not in ("http", "https") or not p.hostname: return ""
        host = p.hostname.lower().removeprefix("www.")
        if host in ("twitter.com", "mobile.twitter.com"): host = "x.com"
        path = re.sub(r"/+$", "", p.path) or "/"
        # README is the repository landing document, not a discussion post.
        # Keep distinct issue/pull/release links intact for editorial history.
        if host == "github.com":
            parts = [x for x in path.split("/") if x]
            if len(parts) == 2 or (len(parts) >= 5 and
                   parts[2] == "blob" and parts[-1].lower().startswith("readme.")):
                path = "/" + "/".join([parts[0].lower(), parts[1].lower()])
        q = parse_qs(p.query, keep_blank_values=False)
        keep = {}
        if host == "news.ycombinator.com" and path == "/item" and q.get("id"):
            keep["id"] = q["id"][0]
        if host in ("youtube.com", "m.youtube.com") and path == "/watch" and q.get("v"):
            host = "youtube.com"
            keep["v"] = q["v"][0]
        return urlunsplit(("https", host, path, urlencode(keep), ""))
    except ValueError: return ""


def project_identity(value):
    """Only infer an identity for an explicitly known project page."""
    url = canonical(value)
    if not url: return ""
    p = urlsplit(url)
    parts = [x for x in p.path.split("/") if x]
    if p.hostname == "github.com":
        return f"https://github.com/{parts[0].lower()}/{parts[1].lower()}" if len(parts) >= 2 else ""
    if p.hostname == "huggingface.co":
        if len(parts) >= 3 and parts[0] in ("spaces", "datasets"):
            return f"https://huggingface.co/{parts[0]}/{parts[1]}/{parts[2]}"
        if len(parts) >= 2 and parts[0] not in ("blog", "papers", "api", "docs"):
            return f"https://huggingface.co/{parts[0]}/{parts[1]}"
    return url


def source_family(source_url, source_type, intake):
    host = urlsplit(source_url).hostname or ""
    if host == "x.com": return "x"
    if host == "news.ycombinator.com": return "hackernews"
    if host == "github.com": return "github"
    if host == "huggingface.co": return "huggingface"
    if host == "bilibili.com": return "bilibili"
    if "reddit.com" in host: return "reddit"
    if "producthunt.com" in host: return "producthunt"
    return host or str(source_type)


def entity_key(url, project_url):
    proj = project_identity(project_url)
    return "project:" + proj if proj else "post:" + canonical(url)


def valid_iso(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        value = value.replace("Z", "+00:00")
        date = dt.datetime.fromisoformat(value)
        if date.tzinfo is None:
            return None
        return date.astimezone(dt.timezone.utc)
    except ValueError:
        return None


def iso_age_days(value, now):
    when = valid_iso(value)
    if not when:
        return None
    return round((now - when).total_seconds() / 86400, 2)


def safe_metric(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and value >= 0:
        return value
    return None


def normalize(item, origin, now):
    if not isinstance(item, dict):
        return None
    url = canonical(item.get("url") or item.get("source_url") or item.get("post_url"))
    if not url:
        return None
    source_type = str(item.get("source") or item.get("platform") or origin)[:100]
    author = str(item.get("author") or item.get("original_author") or "")[:90]
    title = str(item.get("title") or item.get("title_or_excerpt")
                or item.get("text_excerpt") or item.get("text") or "")[:600]
    project_url = project_identity(item.get("project_url"))
    links = item.get("source_workflow_urls") or item.get("external_links") or []
    if not isinstance(links, list):
        links = []
    # If a post lists many different projects, it is a COLLECTION, not
    # a post about the first repo on the list.
    if not project_url:
        projects = []
        for link in links:
            normalized = canonical(link)
            if urlsplit(normalized).hostname in ("github.com", "huggingface.co"):
                identity = project_identity(link)
                if identity and identity not in projects:
                    projects.append(identity)
        if len(projects) == 1:
            project_url = projects[0]
    if not project_url:
        p = urlsplit(url)
        parts = [x for x in p.path.split("/") if x]
        if p.hostname == "github.com" and len(parts) == 2:
            project_url = project_identity(url)
        elif p.hostname == "huggingface.co" and len(parts) >= 3 and parts[0] in ("spaces", "datasets"):
            project_url = project_identity(url)
    metrics_in = item.get("engagement_reported") or item.get("metrics") or {}
    if not isinstance(metrics_in, dict):
        metrics_in = {}
    metrics = {}
    for metric in ("views", "likes", "bookmarks", "reposts", "replies", "comments", "points", "reactions", "trending_score"):
        number = safe_metric(metrics_in.get(metric, item.get(metric)))
        if number is not None:
            metrics[metric] = number
    observed_at = item.get("metrics_checked_at") or item.get("checked_at")
    published_at = item.get("published_utc") or item.get("created_at") or item.get("original_published_at")
    age = iso_age_days(published_at, now)
    native = item.get("platform_native_metrics") if isinstance(item.get("platform_native_metrics"), dict) else {}
    return {
        "source_url": url, "source_type": source_type, "intake": origin,
        "source_family": source_family(url, source_type, origin),
        "author": author, "title": title, "project_url": project_url,
        "entity_key": entity_key(url, project_url),
        "published_utc": published_at, "age_days": age,
        "metrics": metrics,
        "platform_native_metrics": native,
        "media_metadata": (item.get("media") or item.get("media_metadata") or [])[:6]
            if isinstance(item.get("media") or item.get("media_metadata") or [], list) else [],
        "external_links": links[:12],
        "metrics_checked_at": observed_at,
        "metric_scope": "snapshot" if (metrics or native) and observed_at else "unverified_or_undated",
        "source_metric_platform": item.get("source_metric_platform") or source_type,
        "curator": item.get("curator") or "",
        "quote_relationship_verified": item.get("quote_relationship_verified") is True,
        "quoted_post_url": item.get("quoted_post_url") or item.get("curator_quote_url") or "",
        "read_scope": item.get("retrieved_scope") or item.get("verified_scope")
                      or item.get("evidence_level") or item.get("read_scope") or "discovery_lead_only",
        "editorial_status": "research_candidate_only",
    }


def iter_input(folder, seed):
    files = []
    for filename, field, origin in FILES:
        path = folder / filename
        data = load(path)
        files.append({"file": filename, "field": field, "found": data is not None})
        if not isinstance(data, dict):
            continue
        for item in data.get(field, []) if isinstance(data.get(field), list) else []:
            yield origin, item
    public = load(folder / "public-platforms.json")
    files.append({"file": "public-platforms.json", "found": public is not None})
    if isinstance(public, dict):
        for record in public.get("results", []):
            if not isinstance(record, dict) or record.get("status") != "verified":
                continue
            sample = record.get("sample")
            children = (sample.get("posts") or sample.get("issues")
                        or sample.get("questions") or []) if isinstance(sample, dict) else sample
            if isinstance(children, list):
                for item in children:
                    if isinstance(item, dict):
                        row = dict(item)
                        row.setdefault("platform", record.get("platform", "public"))
                        yield "public", row
    if seed:
        obj = load(seed)
        files.append({"file": str(seed), "found": obj is not None})
        if isinstance(obj, dict):
            for item in obj.get("items", []):
                yield "manual_seed", item


def assemble(rows, now):
    groups = defaultdict(list)
    for origin, item in rows:
        row = normalize(item, origin, now)
        if not row:
            continue
        groups[row["entity_key"]].append(row)
    output = []
    for key, entries in groups.items():
        posts = {(p["source_url"], p["source_type"]): p for p in entries}
        unique = list(posts.values())
        newest = min((p["age_days"] for p in unique
                      if p["age_days"] is not None and p["age_days"] >= 0), default=None)
        independent_sources = sorted(set(p["source_family"] for p in unique))
        recency = 3 if newest is not None and newest <= 3 else 2 if newest is not None and newest <= 7 else 1 if newest is not None and newest <= 30 else 0
        score = recency + min(3, len(independent_sources)-1) + int(key.startswith("project:"))
        output.append({
            "entity_key": key, "project_url": unique[0]["project_url"],
            "source_count": len(unique), "source_types": sorted(set(p["source_type"] for p in unique)),
            "independent_source_families": independent_sources,
            "heuristic_priority": score,
            "priority_explanation": "recency + independent source labels + explicit project identity; NOT comparable platform virality",
            "source_posts": unique, "ready_to_publish": False,
            "requires": ["verify original content", "check platform-native metrics and timing",
                         "check reader value and rights", "run existing editorial gate"],
        })
    return sorted(output, key=lambda p: (-p["heuristic_priority"], -p["source_count"], p["entity_key"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=HERE / "output")
    parser.add_argument("--output-dir", type=Path, default=HERE / "output")
    parser.add_argument("--seed", type=Path, default=HERE / "seed_x_curator_v3.json")
    parser.add_argument("--history", type=Path, default=None)
    parser.add_argument("--state-output", type=Path, default=None)
    args = parser.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    discovered = list(iter_input(args.input_dir, args.seed))
    items = assemble(discovered, now)
    history = load(args.history) if args.history else None
    old_keys = (set(history.get("entity_keys", [])) if isinstance(history, dict) else set())
    for row in items:
        row["already_seen"] = row["entity_key"] in old_keys if history is not None else None
    registry = load(REGISTRY) or {"sources": []}
    report = {
        "generated_utc": now.isoformat(),
        "sources_configured": len(registry.get("sources", [])),
        "coverage": registry.get("sources", []),
        "raw_records": len(discovered), "distinct_entities": len(items),
        "platform_capability_is_not_verified_by_registry": True,
        "cross_day_history_loaded": history is not None,
        "observed_platform_health": (load(args.input_dir / "external-discovery.json") or {}).get("provider_status", [])
        + (load(args.input_dir / "external-discovery-devto-hf.json") or {}).get("source_health", [])
        + (load(args.input_dir / "external-discovery-hot-extra.json") or {}).get("source_health", [])
        + (load(args.input_dir / "x-hot-curator-v3.json") or {}).get("source_health", []),
        "limitations": [
            "All channels are discovery options, not claims of exhaustive access.",
            "Third-party counts, if present, are timed snapshots; unknown metrics remain unknown.",
            "No cross-platform absolute popularity ranking; metrics cannot be pooled across platforms.",
            "Manual seed attribution is user-reported unless quote_relationship_verified=true.",
            "Without --history there is only per-run deduplication; GitHub artifacts expire.",
            "Social source posts grouped without a project URL require later entity resolution.",
            "No candidate is automatically publication-approved.",
        ],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "unified-topic-candidates-v3.json").write_text(
        json.dumps({"generated_utc": now.isoformat(), "items": items},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "platform-coverage-v3.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.state_output:
        # Runner state is ephemeral: caller must store this snapshot explicitly.
        all_keys = sorted(old_keys | {p["entity_key"] for p in items})
        args.state_output.parent.mkdir(parents=True, exist_ok=True)
        args.state_output.write_text(json.dumps({
            "schema_version": 1, "updated_at_utc": now.isoformat(),
            "entity_keys": all_keys,
            "limitations": "Keys-only novelty ledger; not a publishing history or guaranteed permanent store",
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_records": len(discovered),
                      "distinct_entities": len(items),
                      "source_channels_in_registry": len(registry.get("sources", [])),
                      "cross_day_history_loaded": history is not None},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
