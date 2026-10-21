#!/usr/bin/env python3
"""Regression checks for V3 shadow discovery: no paid APIs or live web required."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import datetime as dt

HERE = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, HERE / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


unified = load("unified_topic_intake_tested", "unified_topic_intake.py")
hot = load("public_hot_channels_tested", "public_hot_channels.py")


class UnifiedIntakeTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 10, 21, tzinfo=dt.timezone.utc)

    def test_registry_tracks_gaps_without_fake_claims(self):
        obj = json.loads((HERE / "source_coverage_v3.json").read_text())
        self.assertGreaterEqual(len(obj["sources"]), 30)
        required = {"x", "reddit", "hackernews", "github", "youtube", "douyin",
                    "xiaohongshu", "bilibili", "tiktok", "instagram", "producthunt",
                    "huggingface", "curator"}
        self.assertTrue(required.issubset({x["id"] for x in obj["sources"]}))
        self.assertTrue(any(x["status"] != "partial" for x in obj["sources"]))

    def test_user_seed_does_not_fake_twenty_verified_quotes(self):
        doc = json.loads((HERE / "seed_x_curator_v3.json").read_text())
        items = doc["items"]
        self.assertGreaterEqual(len(items), 24)
        verified = [i for i in items if i.get("quote_relationship_verified") is True]
        self.assertEqual(4, len(verified))
        self.assertEqual(20, len(items)-len(verified))

    def test_project_dedup_retains_distinct_source_provenance(self):
        one = {
            "url": "https://x.com/a/status/1",
            "project_url": "https://github.com/Org/tool?utm_campaign=foo",
            "title": "AI tool", "metrics": {"likes": 140},
            "metrics_checked_at": "2026-10-21T00:00:00Z",
        }
        two = {
            "url": "https://news.ycombinator.com/item?id=91",
            "project_url": "https://github.com/org/tool",
            "title": "Show HN AI tool",
        }
        rows = unified.assemble([("x", one), ("hn", two)], self.now)
        self.assertEqual(1, len(rows))
        self.assertEqual(2, rows[0]["source_count"])
        self.assertFalse(rows[0]["ready_to_publish"])
        self.assertEqual({"hn", "x"}, {p["intake"] for p in rows[0]["source_posts"]})

    def test_unknown_engagement_never_defaults_to_zero(self):
        o = unified.normalize({"url": "https://x.com/a/status/3",
                  "metrics": {"likes": "viral", "views": -1, "bookmarks": None},
                  "author": "a"}, "x", self.now)
        self.assertEqual({}, o["metrics"])
        self.assertEqual("unverified_or_undated", o["metric_scope"])

    def test_curator_quote_relation_preserved(self):
        x = unified.normalize({"url": "https://x.com/ianlacerda/status/21",
               "curator": "ianlacerda", "quote_relationship_verified": True,
               "quoted_post_url": "https://x.com/CY160909/status/34"}, "manual", self.now)
        self.assertTrue(x["quote_relationship_verified"])
        self.assertEqual("https://x.com/CY160909/status/34", x["quoted_post_url"])

    def test_per_run_dedup_does_not_claim_cross_day_without_history(self):
        data = unified.assemble([("x", {"url": "https://x.com/a/status/2"})], self.now)
        self.assertEqual(1, len(data))
        self.assertNotIn("already_seen", data[0])
        self.assertEqual("https://x.com/a/status/2", unified.canonical("http://twitter.com/a/status/2?s=46"))

    def test_multiple_platform_input_in_single_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "public-rss-candidates.json").write_text(json.dumps({
                "items": [{"url": "https://example.org/release", "title": "Official"}]}))
            (p / "external-discovery.json").write_text(json.dumps({
                "items": [{"url": "https://dev.to/xyz/new-tool", "source": "devto_top"}]}))
            (p / "aicg-fresh-candidates.json").write_text(json.dumps({
                "items_newest_72h": [{"url": "https://x.com/artist/status/4",
                                      "title_or_excerpt": "AICG design"}]}))
            rows = list(unified.iter_input(p, None))
            self.assertEqual(3, len(rows))
            self.assertEqual(3, len(unified.assemble(rows, self.now)))


class PublicHotFeedTests(unittest.TestCase):
    def test_public_pack_ignores_invalid_engagement(self):
        item = hot.pack(source="devto_top", title="something",
                        url="https://dev.to/u/p", engagement={
                        "comments": 12, "views": "not_available", "likes": -1})
        self.assertEqual({"comments": 12}, item["metrics"])
        self.assertEqual("research_candidate_only", item["editorial_status"])

    def test_isolated_platform_failure_does_not_discard_success(self):
        def good():
            return [{"url": "https://news.ycombinator.com/item?id=1"}]
        def bad():
            raise ValueError("mock_blocked")
        records, health = hot.collect({"hn": good, "blocked_platform": bad})
        self.assertEqual(1, len(records))
        self.assertEqual({"retrieved", "unavailable"}, {x["status"] for x in health})
        self.assertTrue(any(x.get("error", "").startswith("ValueError") for x in health))

    def test_hn_show_mock_json_api(self):
        def fake_fetch(url):
            if url.endswith("showstories.json"):
                return [1, 2]
            if url.endswith("/1.json"):
                return {"id": 1, "title": "Show HN: new tool", "by": "maker",
                        "score": 17, "descendants": 3, "time": 1792538400,
                        "url": "https://github.com/Org/tool"}
            return {"id": 2, "deleted": True}
        with patch.object(hot, "fetch_json", side_effect=fake_fetch):
            result = hot.hnews("hackernews_show")
        self.assertEqual(1, len(result))
        self.assertEqual("https://github.com/Org/tool", result[0]["project_url"])
        self.assertEqual(17, result[0]["metrics"]["points"])


if __name__ == "__main__":
    unittest.main()
