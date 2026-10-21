#!/usr/bin/env python3
"""Regression tests for the non-network V3 multi-platform intake."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("unified_topic_intake", HERE / "unified_topic_intake.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
NOW = datetime(2026, 10, 21, tzinfo=timezone.utc)


class V3IntakeTest(unittest.TestCase):
    def test_normalize_x_tracking_and_git_repo(self):
        self.assertEqual(
            module.canonical("https://twitter.com/abc/status/123?s=46"),
            "https://x.com/abc/status/123",
        )
        self.assertEqual(
            module.canonical("https://github.com/THYSRAEL/HORIZON/blob/main/README.md"),
            "https://github.com/thysrael/horizon",
        )

    def test_preserves_missing_metrics_and_does_not_invent_virality(self):
        x = module.normalize(
            {"url": "https://x.com/u/status/1", "text": "New tool",
             "likes": 250, "published_utc": "2026-10-20T00:00:00Z"},
            "x", NOW,
        )
        self.assertEqual(x["metrics"]["likes"], 250)
        self.assertIsNone(x["metrics_checked_at"])
        self.assertEqual(x["metric_scope"], "unverified_or_undated")
        self.assertEqual(x["editorial_status"], "research_candidate_only")

    def test_merges_distinct_posts_with_same_verified_project_link(self):
        source = [
            ("x", {"url": "https://x.com/u/status/1", "project_url":
                   "https://github.com/Thysrael/Horizon", "source": "x"}),
            ("aicg", {"url": "https://bsky.app/profile/u/post/abc",
                      "source_workflow_urls": ["https://github.com/thysrael/horizon"],
                      "source": "bluesky"}),
        ]
        groups = module.assemble(source, NOW)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["source_count"], 2)
        self.assertEqual(len(groups[0]["source_types"]), 2)
        self.assertFalse(groups[0]["ready_to_publish"])

    def test_same_name_without_original_link_does_not_merge(self):
        posts = [
            ("x", {"url": "https://x.com/u/status/1", "title": "same tool"}),
            ("x", {"url": "https://x.com/v/status/2", "title": "same tool"}),
        ]
        self.assertEqual(len(module.assemble(posts, NOW)), 2)

    def test_explicit_quote_relationship_only(self):
        item = module.normalize(
            {"url": "https://x.com/ianlacerda/status/99",
             "quoted_post_url": "https://x.com/w/status/10",
             "quote_relationship_verified": True,
             "curator": "https://x.com/ianlacerda"},
            "manual_seed", NOW)
        self.assertTrue(item["quote_relationship_verified"])
        self.assertEqual(item["quoted_post_url"], "https://x.com/w/status/10")

    def test_seed_has_no_fake_quote_claims(self):
        data = json.loads((HERE / "seed_x_curator_v3.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["items"]), 24)
        self.assertEqual(sum(x["quote_relationship_verified"] is True
                             for x in data["items"]), 4)
        self.assertEqual(sum(x["quote_relationship_verified"] is False
                             for x in data["items"]), 20)

    def test_cli_emits_truthful_missing_source_health(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs = root / "input"
            output = root / "out"
            inputs.mkdir()
            (inputs / "public-rss-candidates.json").write_text(json.dumps({
                "items": [{"url": "https://example.com/new",
                           "title": "AI new workflow",
                           "published_utc": "2026-10-20T04:00:00Z"}]
            }), encoding="utf-8")
            subprocess.run(
                [sys.executable, str(HERE / "unified_topic_intake.py"),
                 "--input-dir", str(inputs), "--output-dir", str(output),
                 "--seed", str(root / "missing-seed.json")],
                check=True, capture_output=True, text=True,
            )
            report = json.loads((output / "platform-coverage-v3.json").read_text())
            results = json.loads((output / "unified-topic-candidates-v3.json").read_text())
            self.assertGreaterEqual(report["sources_configured"], 30)
            self.assertFalse(report["cross_day_history_loaded"])
            self.assertEqual(len(results["items"]), 1)
            self.assertFalse(results["items"][0]["ready_to_publish"])


if __name__ == "__main__":
    unittest.main()
