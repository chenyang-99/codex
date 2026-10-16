#!/usr/bin/env python3
"""Read-only Zotero Web API v3 export for Codex literature workflows.

Only GET endpoints; credentials are read from environment variables.
Python standard library only. Outputs are local and should never be committed.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class ZoteroError(Exception):
    pass


def config():
    user_id = os.environ.get("ZOTERO_USER_ID", "").strip()
    api_key = os.environ.get("ZOTERO_API_KEY", "").strip()
    if not user_id.isdigit() or not api_key:
        raise ZoteroError(
            "Set ZOTERO_USER_ID (numeric) and ZOTERO_API_KEY in the secure "
            "runtime environment; never commit or print the key."
        )
    return user_id, api_key


class Zotero:
    def __init__(self, user_id, api_key):
        self.base = "https://api.zotero.org/users/" + user_id
        self.headers = {
            "Zotero-API-Key": api_key,
            "Zotero-API-Version": "3",
            "Accept": "application/json",
            "User-Agent": "Codex-Zotero-Research-ReadOnly/0.1",
        }

    def get(self, path, params=None, missing_ok=False):
        url = self.base + "/" + path.lstrip("/")
        if params:
            url += "?" + urlencode(params)
        req = Request(url, headers=self.headers, method="GET")
        try:
            with urlopen(req, timeout=35) as resp:
                return json.load(resp)
        except HTTPError as exc:
            if exc.code == 404 and missing_ok:
                return None
            if exc.code in (401, 403):
                raise ZoteroError("Zotero API rejected the read-only key or library permissions.") from exc
            raise ZoteroError("Zotero API request failed with HTTP " + str(exc.code)) from exc
        except (URLError, TimeoutError) as exc:
            raise ZoteroError("Unable to reach Zotero API: " + str(exc.reason if hasattr(exc, "reason") else exc)) from exc

    def list_all(self, path, max_items):
        items, start = [], 0
        while len(items) < max_items:
            count = min(100, max_items - len(items))
            page = self.get(path, {"start": start, "limit": count, "format": "json"})
            if not isinstance(page, list):
                raise ZoteroError("Unexpected Zotero API response for " + path)
            items.extend(page)
            if len(page) < count:
                break
            start += len(page)
        return items


def item_key(raw):
    if not raw or not raw.isalnum() or len(raw) > 30:
        raise ZoteroError("Invalid Zotero collection or item key.")
    return quote(raw, safe="")


def authors(creators):
    output = []
    for c in creators or []:
        name = c.get("name") or " ".join(filter(None, [c.get("firstName"), c.get("lastName")]))
        if name:
            output.append(name)
    return output


def papers(client, collection, limit, fulltext, max_chars):
    path = "collections/" + item_key(collection) + "/items/top"
    source = client.list_all(path, limit)
    result = []
    for paper in source:
        data = paper.get("data", {})
        kind = data.get("itemType", "")
        if kind in ("attachment", "note"):
            continue
        entry = {
            "item_key": paper.get("key"),
            "item_type": kind,
            "title": data.get("title"),
            "abstract": data.get("abstractNote"),
            "authors": authors(data.get("creators")),
            "date": data.get("date"),
            "publication": data.get("publicationTitle"),
            "doi": data.get("DOI"),
            "url": data.get("url"),
            "tags": [t.get("tag") for t in data.get("tags", [])],
            "fulltext_status": "not_requested",
        }
        if fulltext:
            entry["fulltext_status"] = "unavailable"
            entry["attachments"] = []
            children = client.list_all("items/" + item_key(paper["key"]) + "/children", 100)
            for child in children:
                cdata = child.get("data", {})
                if cdata.get("itemType") != "attachment":
                    continue
                child_key = child.get("key")
                text_data = client.get("items/" + item_key(child_key) + "/fulltext", missing_ok=True)
                if not text_data or not text_data.get("content"):
                    continue
                body = text_data["content"]
                entry["attachments"].append({
                    "attachment_key": child_key,
                    "filename": cdata.get("filename"),
                    "content_type": cdata.get("contentType"),
                    "indexed_pages": text_data.get("indexedPages"),
                    "total_pages": text_data.get("totalPages"),
                    "text": body[:max_chars],
                    "truncated": len(body) > max_chars,
                })
            if entry["attachments"]:
                entry["fulltext_status"] = "indexed_text_available"
        result.append(entry)
    return result


def save_json(data, output):
    encoded = json.dumps(data, ensure_ascii=False, indent=2)
    if output == "-":
        print(encoded)
        return
    dest = Path(output).expanduser().resolve()
    repo_root = Path(__file__).resolve().parents[4]
    if dest == repo_root or repo_root in dest.parents:
        raise ZoteroError("Refusing to write Zotero library data into the GitHub repository. Use /tmp or another private directory.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(dest), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(encoded)
            f.write("\n")
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise
    print("Saved Zotero data locally to " + str(dest) + " (not committed to GitHub).")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only Zotero collections and papers")
    sub = parser.add_subparsers(dest="command", required=True)
    collections = sub.add_parser("collections", help="List Zotero collection names and keys")
    collections.add_argument("--limit", type=int, default=1000)
    collections.add_argument("--output", default="-")
    ps = sub.add_parser("papers", help="Export top-level papers in one Zotero collection")
    ps.add_argument("--collection", required=True, help="Zotero collection key (not display name)")
    ps.add_argument("--limit", type=int, default=100)
    ps.add_argument("--fulltext", action="store_true", help="Include available indexed text of child attachments")
    ps.add_argument("--max-chars", type=int, default=200000)
    ps.add_argument("--output", default="-", help="Private file path or '-' for metadata on stdout")
    args = parser.parse_args(argv)
    if args.limit < 1 or args.limit > 10000:
        parser.error("--limit must be between 1 and 10000")
    if args.command == "papers" and args.max_chars < 1:
        parser.error("--max-chars must be positive")
    if args.command == "papers" and args.fulltext and args.output == "-":
        parser.error("--fulltext requires --output to a private file, e.g. /tmp/zotero-papers.json")
    user_id, key = config()
    client = Zotero(user_id, key)
    if args.command == "collections":
        data = [
            {"key": x.get("key"), "name": x.get("data", {}).get("name"), "parent": x.get("data", {}).get("parentCollection")}
            for x in client.list_all("collections", args.limit)
        ]
    else:
        data = papers(client, args.collection, args.limit, args.fulltext, args.max_chars)
    save_json(data, args.output)


if __name__ == "__main__":
    try:
        main()
    except ZoteroError as exc:
        print("Zotero error: " + str(exc), file=sys.stderr)
        sys.exit(1)
