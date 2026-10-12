#!/usr/bin/env python3
"""One-page domestic access status report; never conflate CI success with data access."""
from datetime import datetime,timezone
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent/"output"

def read(name):
    try:
        x=json.loads((HERE/name).read_text(encoding="utf-8"))
        return x if isinstance(x,dict) else {}
    except (OSError,ValueError):
        return {}

def main():
    xhs=read("xiaohongshu-public.json")
    dy=read("douyin-public.json")
    index=read("domestic-multisearch.json")
    permalink=read("domestic-permalink-verification.json")
    domestic=read("domestic-discovery.json")
    pain=read("domestic-painpoints.json")
    v2=next((x for x in domestic.get("tests",[]) if x.get("platform")=="v2ex"),{})
    bili=next((x for x in domestic.get("tests",[]) if x.get("platform")=="bilibili"),{})
    tests=[
        {"platform":"Xiaohongshu","surface":"anonymous public feed","status":xhs.get("status","not_tested"),"verified_items":xhs.get("records_returned",0),"actual_comments":0},
        {"platform":"Douyin","surface":"anonymous public hot board ONLY","status":dy.get("status","not_tested"),"verified_items":dy.get("records_returned",0),"actual_comments":0},
        {"platform":"XHS + Douyin","surface":"4 public search indexes, 16 sampled queries","status":"indexed" if index.get("unique_indexed_urls") else "no_direct_links_confirmed","verified_items":len(index.get("unique_indexed_urls",[])),"actual_comments":0},
        {"platform":"XHS + Douyin","surface":"verify indexed permalinks really open as intended","status":"verified" if permalink.get("verified_public_post_metadata") else "no_post_metadata_verified","verified_items":permalink.get("verified_public_post_metadata",0),"actual_comments":0},
        {"platform":"Bilibili","surface":"public search or confirmed historical seeds; public video replies","status":bili.get("status","not_tested"),"verified_items":len(bili.get("posts",[])),"actual_comments":len(bili.get("comments",[]))},
        {"platform":"V2EX","surface":"public topics and replies","status":v2.get("status","not_tested"),"verified_items":len(v2.get("posts",[])),"actual_comments":len(v2.get("comments",[]))}
    ]
    total=int(pain.get("actual_domestic_comment_count",0))
    report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
            "scope":"best-effort access without social-account logins, paid APIs or credentialed scraping",
            "tests":tests,"distinct_domestic_comment_samples":total,
            "comment_platforms":pain.get("comment_platforms",[]),
            "gaps":["Native Xiaohongshu search and comments remain unavailable without authorization.",
                    "Native Douyin video search and comments remain unavailable without authorization.",
                    "Search engine snippets and invalid permalink redirects are not content or comments.",
                    "Bilibili and V2EX comments are not Xiaohongshu/Douyin user comments."],
            "automated_status":"Code execution success does NOT imply data-source success."}
    HERE.mkdir(parents=True,exist_ok=True)
    (HERE/"domestic-status.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Domestic social research: source-by-source reality check","",
          f"Checked UTC: {report['checked_at_utc']}","",
          "| Platform | Access route | State | Actual content items | Actual comment samples |",
          "|---|---|---|---:|---:|"]
    for s in tests:
        lines.append(f"| {s['platform']} | {s['surface']} | {s['status']} | {s['verified_items']} | {s['actual_comments']} |")
    lines +=["",f"**Deduplicated actual Chinese public reply samples:** {total}.",
             "**Do NOT treat zero obtained comments as evidence of zero user comments.**",
             "","## Remaining constraints"]
    for issue in report["gaps"]:lines.append("- "+issue)
    (HERE/"domestic-status.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"status":"domestic_status_complete","summary":[{"platform":s["platform"],"route":s["surface"],"state":s["status"],"items":s["verified_items"],"replies":s["actual_comments"]} for s in tests]},ensure_ascii=False))
if __name__=="__main__":main()
