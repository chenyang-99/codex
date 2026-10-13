#!/usr/bin/env python3
"""Strict end-to-end Douyin access acceptance report.

A GitHub Actions 'success' is only proof that the probe ran. This report
deliberately does not convert creator-feed filtering, search-engine links,
or inline reply previews into site-wide search/full nested pagination.

The two missing capabilities remain false until an independently audited
provider, permission and real returned rows are present. No request is made.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/"output"

def read(name):
    try:
        x=json.loads((OUT/name).read_text(encoding="utf-8"))
        return x if isinstance(x,dict) else {}
    except (OSError,ValueError):return {}

def integer(x):
    try:return max(0,int(x))
    except (ValueError,TypeError):return 0

def main():
    creator=read("douyin-creator-discovery.json")
    schema=read("douyin-native-search-capability.json")
    first=integer(creator.get("actual_comment_texts"))
    previews=integer(creator.get("actual_reply_preview_texts"))
    feeds=integer(creator.get("verified_author_feeds"))
    videos=integer(creator.get("actual_relevant_video_count"))
    # The currently installed demo source has no native full-site keyword API.
    # Adding URL candidates, actor seeds, raw comment previews or page 2 does
    # not change these two properties.
    full_search=False
    full_reply_threads=False
    status={
       "checked_utc":datetime.now(timezone.utc).isoformat(),
       "platform":"douyin",
       "state":"partial_real_data_verified" if feeds and videos else "no_recent_public_data_verified",
       "independently_proven_sample":{
           "verified_creator_feeds":feeds,
           "verified_related_videos":videos,
           "actual_first_level_comment_texts":first,
           "actual_inline_second_level_reply_previews":previews,
           "scope":"At most 3 seed creators; normalized creator posts, not a platform census",
       },
       "hard_requirements":{
          "any_keyword_platform_wide_search":{
             "passed":full_search,"reason":"Current free demo has no implemented Douyin native keyword search route. Public index/creator filtering is not platform-wide."
          },
          "full_second_level_reply_pagination":{
             "passed":full_reply_threads,"reason":"Dedicated reply endpoint returned UPSTREAM_RISK_CONTROL. Inline reply_comment previews are real but incomplete."
          },
          "unattended_free_without_personal_douyin_login":{
              "passed":bool(feeds and videos),"reason":"Bounded free shared demo run only; not guaranteed service availability."
          },
       },
       "complete":full_search and full_reply_threads and bool(feeds and videos),
       "upstream_search_contract":schema.get("search_route_status","unknown"),
       "halted_known_blocked_surface":"Do not call dedicated demo comments/replies again without a newly authorized source.",
       "separate_provider_requirements":"Both absent capabilities require a genuinely permitted search/reply data source; never bypass CAPTCHA, login or anti-bot.",
       "failed_workflow_is_not_a_platform_failure":True,
       "successful_workflow_is_not_end_to_end_success":True
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"douyin-acceptance.json").write_text(
         json.dumps(status,ensure_ascii=False,indent=2),encoding="utf-8")
    md=[
        "# Douyin end-to-end capability audit",
        "",f"UTC: {status['checked_utc']}",
        f"Data status: {status['state']}; COMPLETE: **{status['complete']}**",
        "",
        f"Verified public author feeds: {feeds}, AI videos: {videos},",
        f"first-level comment texts: {first}, inline second-level previews: {previews}.",
        "",
        "## Hard requirements",
    ]
    for name,check in status["hard_requirements"].items():
        md.extend([f"- **{name}: {'PASS' if check['passed'] else 'NOT MET'}** — {check['reason']}"])
    md.extend(["","Do not imply that a green Actions run equals end-to-end access.",
               "No browser identity, social credentials, private platform data,",
               "upstream blocked reply request, or paid API was used by this audit."])
    (OUT/"douyin-acceptance.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print(json.dumps({"status":"douyin_end_to_end_acceptance",
         "complete":status["complete"],"creator_feeds":feeds,"videos":videos,
         "first_level":first,"inline_second_level_previews":previews,
         "native_full_site_search":full_search,
         "full_second_level_pagination":full_reply_threads},ensure_ascii=False))
if __name__=="__main__": main()
