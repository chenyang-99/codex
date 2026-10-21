#!/usr/bin/env python3
"""V3 evidence-based discovery-channel coverage audit.

A listed channel is NOT connected merely because its name is in the registry.
An action step completing is NOT evidence that the provider returned data.
This module reads actual collector status and emits operator-actionable gaps.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"

SOURCES = {
    "public-rss-candidates.json": ("source_health", "rss"),
    "external-discovery.json": ("provider_status", "public_hot"),
    "external-discovery-devto-hf.json": ("source_health", "devto_hf"),
    "external-discovery-hot-extra.json": ("source_health", "trending_feeds"),
    "x-hot-curator-v3.json": ("source_health", "x_network"),
    "x-horizon-apify-v3.json": ("source_health", "x_optional_apify"),
    "indexed-social-leads-v3.json": ("source_health", "indexed_social"),
}

def read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

def collect_health(folder, sources=SOURCES):
    seen, statuses = [], []
    for filename,(key,family) in sources.items():
        doc = read(folder / filename)
        if not isinstance(doc, dict):
            seen.append({"file": filename, "family": family, "artifact_status": "missing_or_invalid"})
            continue
        rows = doc.get(key)
        if not isinstance(rows, list):
            seen.append({"file": filename, "family": family, "artifact_status": "health_missing"})
            continue
        seen.append({"file": filename, "family": family, "artifact_status": "observed",
                     "provider_probes": len(rows)})
        for row in rows:
            if not isinstance(row, dict): continue
            state = str(row.get("status") or "unknown")
            statuses.append({
                "provider": str(row.get("source") or row.get("name") or "unknown"),
                "family": family, "status": state,
                "items": row.get("items") if isinstance(row.get("items"), int) else None,
                "checked_at": row.get("checked_at") or doc.get("checked_at_utc") or doc.get("generated_utc"),
                "error": str(row.get("error") or row.get("detail") or "")[:250],
            })
    return seen, statuses

def assess(registry, collected_files, statuses):
    registry = registry.get("sources", []) if isinstance(registry, dict) else []
    known_ids = {str(s["id"]) for s in registry if isinstance(s, dict) and s.get("id")}
    healthy = sum(x["status"] in ("retrieved","verified") for x in statuses)
    degraded = sum(x["status"] in ("partial","unavailable","error","blocked","not_configured") for x in statuses)
    unable = sorted({x["provider"] for x in statuses
                     if x["status"] in ("unavailable","error","blocked")})
    discovered = sum(x["items"] for x in statuses if isinstance(x.get("items"), int)
                     and x["status"] in ("retrieved","partial","verified"))
    x_queries = [s for s in statuses if s["provider"].startswith(("x_query:", "query:"))]
    x_curator = [s for s in statuses if s["provider"].startswith("x_curator:")]
    missing_files = [x["file"] for x in collected_files if x["artifact_status"] != "observed"]
    return {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "registered_channels": len(known_ids),
        "observed_probe_count": len(statuses), "successful_probe_count": healthy,
        "partial_or_failed_probe_count": degraded,
        "sum_observed_provider_items_with_overlap": discovered,
        "failed_providers": unable, "missing_or_invalid_collector_artifacts": missing_files,
        "x_keyword_queries": len(x_queries),
        "x_keyword_queries_success": sum(x["status"] == "retrieved" and (x.get("items") or 0)>0 for x in x_queries),
        "x_curators_checked": len(x_curator),
        "x_curators_success": sum(x["status"] == "retrieved" for x in x_curator),
        "operator_priorities": [
            "Verify unavailable public feeds and add compliant alternate feeds/first-party access where possible.",
            "Resolve X public keyword-search coverage or report it unavailable; quote-network success is not X-wide search.",
            "Maintain independent video / image / tutorial discovery for XHS, Douyin, TikTok, YouTube, Instagram, Pinterest, Behance and Bilibili with explicit access scopes.",
            "Prioritize original media and actionable tutorials, not all-platform headline/score volume.",
            "Treat channel registration, CI success, and candidate count as three different facts.",
            "After 7-day shadow trial, select modules based on independently useful topics, editor acceptance and access cost.",
        ],
        "limitations": [
            "Probe samples overlap, come from different platforms and do not equal qualified AI topics.",
            "No method guarantees complete public, paywalled, private or algorithmic-feed coverage.",
            "No published content, paid API access, or rights claims are implied.",
        ],
    }

def main():
    registry = read(ROOT / "source_coverage_v3.json") or {}
    files, statuses = collect_health(OUT)
    report = assess(registry, files, statuses)
    report["collectors"] = files
    report["probes"] = statuses
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT / "channel-gap-audit-v3.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines = ["# V3 选题发现渠道证据审计", "",
             "采样/审计时间 UTC: "+report["checked_at_utc"],
             "注册渠道："+str(report["registered_channels"])+"（登记 ≠ 实时采集）",
             "本次真实提供健康状态的探针："+str(report["observed_probe_count"]),
             "报告成功探针："+str(report["successful_probe_count"]),
             "部分成功或失败探针："+str(report["partial_or_failed_probe_count"]),
             "X 关键词有效命中："+str(report["x_keyword_queries_success"])+"/"+str(report["x_keyword_queries"]),
             "X 策展者检索成功："+str(report["x_curators_success"])+"/"+str(report["x_curators_checked"]), "",
             "## 实际可用性与失败记录", ""]
    for p in statuses:
        lines.append(f"- {p['family']}/{p['provider']}: {p['status']} "
                     f"({p['items'] if p['items'] is not None else 'unknown'} items)"
                     + (f"; {p['error']}" if p["error"] else ""))
    if report["missing_or_invalid_collector_artifacts"]:
        lines += ["", "## 未产生可用健康报告的采集器", ""]
        lines += ["- "+x for x in report["missing_or_invalid_collector_artifacts"]]
    lines += ["","## 仍必须解决的盲区",""]
    lines += ["- "+x for x in report["operator_priorities"]]
    (OUT / "channel-gap-audit-v3.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({key:report[key] for key in ("registered_channels", "observed_probe_count",
        "successful_probe_count","partial_or_failed_probe_count",
        "x_keyword_queries_success","x_keyword_queries","x_curators_success",
        "missing_or_invalid_collector_artifacts")},ensure_ascii=False))

if __name__ == "__main__": main()
