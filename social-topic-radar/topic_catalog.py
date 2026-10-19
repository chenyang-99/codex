#!/usr/bin/env python3
"""V2 source discovery index and observed coverage audit.

No scraping or paid API. The static catalog is NOT claimed to be monitored.
Output separates catalog presence from actually retrieved RSS evidence.
"""
import argparse
import datetime as dt
import json
from collections import Counter
from pathlib import Path
from topic_taxonomy import AI_DOMAINS, CONTENT_TYPES, SOURCE_ROLES, classify_text

HERE = Path(__file__).resolve().parent
DEFAULT_REPORT = HERE / "output" / "public-rss-candidates.json"

def load_json(path):
    try:
        with Path(path).open(encoding="utf-8") as f:
            value = json.load(f)
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}

def load_catalog():
    return load_json(HERE / "source_catalog_v2.json").get("sources", [])

def find_sources(domain=None, role=None, limit=30):
    if domain and domain not in AI_DOMAINS:
        raise ValueError("Unknown domain: " + domain)
    if role and role not in SOURCE_ROLES:
        raise ValueError("Unknown source role: " + role)
    result = [x for x in load_catalog()
              if (not domain or domain in x.get("domains", []))
              and (not role or role in x.get("roles", []))]
    return result[:limit]

def coverage(rss_path=DEFAULT_REPORT):
    catalog = load_catalog()
    rss_cfg = load_json(HERE / "sources.json").get("feeds", [])
    rss = load_json(rss_path)
    observed = []
    for item in rss.get("items", []):
        if not isinstance(item, dict):
            continue
        labels = classify_text(item.get("title"), item.get("excerpt"))
        observed.append({"url": item.get("url"), "title": item.get("title"),
                         "source": item.get("source"),
                         "published_utc": item.get("published_utc"),
                         "domains": labels["domains"],
                         "content_type": labels["content_type"]})
    catalog_counts = Counter(domain for src in catalog
                             for domain in src.get("domains", []) if domain in AI_DOMAINS)
    observed_counts = Counter(domain for x in observed for domain in x["domains"])
    content_counts = Counter(x["content_type"] for x in observed)
    health = rss.get("source_health", [])
    return {
        "taxonomy_version": "2.0",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "configured_legacy_rss_feeds": len(rss_cfg),
        "catalog_on_demand_sources": len(catalog),
        "rss_checked_at_utc": rss.get("checked_at_utc"),
        "rss_report_available": bool(rss),
        "rss_verified_feeds": rss.get("verified_feeds"),
        "rss_discovered_items": len(observed),
        "source_health": health,
        "domains": [
            {"id": k, "name": name,
             "catalog_on_demand_entries": catalog_counts[k],
             "observed_rss_title_matches": observed_counts[k]}
            for k, name in AI_DOMAINS.items()
        ],
        "content_types": [
            {"id": k, "name": name, "observed_rss_title_matches": content_counts[k]}
            for k, name in CONTENT_TYPES.items()
        ],
        "observed_unclassified_items": content_counts["unclassified"],
        "roles": [{"id": k, "name": v} for k, v in SOURCE_ROLES.items()],
        "warnings": [
            "All source_catalog_v2.json links are on-demand leads, NOT automatically crawled.",
            "RSS configured does not mean RSS verified or that a field is fully monitored.",
            "Observed domain/content tags are heuristic headline-based hints, not independent verification.",
            "Zero title matches is not proof that no news or demand exists in a domain.",
            "A topic must pass the existing evidence gate and human scoring before editorial recommendation.",
        ]
    }

def main():
    parser = argparse.ArgumentParser(description="V2 AI topic taxonomy and source coverage")
    sub = parser.add_subparsers(dest="command", required=True)
    find = sub.add_parser("sources")
    find.add_argument("--domain", choices=list(AI_DOMAINS))
    find.add_argument("--role", choices=list(SOURCE_ROLES))
    find.add_argument("--limit", type=int, default=30)
    classify = sub.add_parser("classify")
    classify.add_argument("--title", required=True)
    classify.add_argument("--description", default="")
    audit = sub.add_parser("coverage")
    audit.add_argument("--rss-report", default=str(DEFAULT_REPORT))
    audit.add_argument("--output-dir", default=str(HERE / "output"))
    args = parser.parse_args()
    if args.command == "sources":
        data = {"matching_sources": find_sources(args.domain, args.role, max(0, args.limit)),
                "note": "Catalog entries are research leads; not confirmed reachable or automatically collected."}
    elif args.command == "classify":
        data = classify_text(args.title, args.description)
    else:
        data = coverage(args.rss_report)
        path = Path(args.output_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "topic-source-coverage-v2.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        rows = ["# AI 选题信源覆盖 · V2（已配置 ≠ 已访问）",
                "", "仅以 RSS 实际读取的标题/摘要衡量可观察覆盖；未逐个访问 V2 on-demand 目录。",
                "", "| AI领域 | 静态目录来源 | 实际RSS标题匹配 |",
                "|---|---:|---:|"]
        for d in data["domains"]:
            rows.append("| {} | {} | {} |".format(
                d["name"], d["catalog_on_demand_entries"], d["observed_rss_title_matches"]))
        rows.extend(["", "## 限制", *(("- " + s) for s in data["warnings"])])
        (path / "topic-source-coverage-v2.md").write_text(
            "\n".join(rows) + "\n", encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
