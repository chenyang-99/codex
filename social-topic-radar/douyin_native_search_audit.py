#!/usr/bin/env python3
"""Audit an openly published API schema for genuine native keyword-search access.

One GET to documented public OpenAPI (no account, platform cookie, or API key).
This only verifies whether a formal route exists; it does not call platform
search, and does not treat a named search URL or constants as implemented API.
"""
from datetime import datetime,timezone
from pathlib import Path
import json
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

OUT=Path(__file__).resolve().parent/"output"/"douyin-native-search-capability.json"
URL="https://demo.douyin.wtf/openapi.json"
def main():
    result={"checked_utc":datetime.now(timezone.utc).isoformat(),
      "source":URL,"source_type":"official public demo OpenAPI schema",
      "platform":"douyin","search_route_status":"not_verified",
      "native_platform_keyword_search_verified":False,"comments_route_present":False,
      "nested_reply_route_present":False,"platform_account_used":False}
    try:
        req=Request(URL,headers={"Accept":"application/json","User-Agent":"PublicSchemaCapabilityAudit/1.0"})
        with urlopen(req,timeout=18) as response:
            payload=response.read(4_000_000)
            result["http_status"]=response.status
        obj=json.loads(payload)
        paths=obj.get("paths") or {}
        if not isinstance(paths,dict):raise ValueError("Schema missing paths")
        relevant=[p for p in paths if p.startswith("/api/v1/douyin/")]
        search=[p for p in relevant if "/search" in p or p.endswith("/video/search")]
        result["published_keyword_search_routes"]=search
        result["published_douyin_route_count"]=len(relevant)
        result["comments_route_present"]="/api/v1/{platform}/video/comments" in paths or "/api/v1/douyin/video/comments" in paths
        result["nested_reply_route_present"]="/api/v1/{platform}/video/comments/replies" in paths or "/api/v1/douyin/video/comments/replies" in paths
        result["search_route_status"]="published_search_route" if search else "no_native_keyword_search_route"
        result["native_platform_keyword_search_verified"]=False
        result["methodology"]="Route presence cannot verify that a guest can search or obtain posts"
        # paths are templated in this project, so also count /{platform}/ routes
        result["templated_platform_routes"]=[p for p in paths if p.startswith("/api/v1/{platform}/") and "search" in p]
        if result["templated_platform_routes"]:
            result["search_route_status"]="possible_templated_search_route_not_exercised"
    except (HTTPError,URLError,ValueError,TimeoutError,OSError) as e:
        result["error"]=type(e).__name__+":"+str(e)[:130]
    return result
if __name__=="__main__":
    output=main()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"douyin_native_search_contract_audit":output},ensure_ascii=False))
