"""Offline V2 taxonomy/source catalog regression tests; no network or mocked popularity."""
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
tax = importlib.import_module("topic_taxonomy")
catalog = importlib.import_module("topic_catalog")

class TaxonomyV2Test(unittest.TestCase):
    def test_dimensions(self):
        self.assertEqual(len(tax.AI_DOMAINS), 15)
        self.assertEqual(len(tax.CONTENT_TYPES), 5)
        self.assertEqual(len(tax.SOURCE_ROLES), 6)

    def test_tutorial_and_aicg_are_orthogonal(self):
        a = tax.classify_text("AI视频专业镜头教程：Runway 运镜 Prompt")
        self.assertEqual(a["content_type"], "tutorial")
        self.assertIn("aicg_video", a["domains"])
        self.assertIn("ai_education", a["domains"])
        self.assertEqual(a["classification_status"], "keyword_hints_require_editor_review")

    def test_agent_tools(self):
        a = tax.classify_text("6个开源工具，帮你搭建 Agent 工作流")
        self.assertEqual(a["content_type"], "tool_resource")
        self.assertIn("agents_automation", a["domains"])

    def test_news_without_invented_virality(self):
        a = tax.classify_text("新大模型发布，更新多模态能力")
        self.assertEqual(a["content_type"], "news_update")
        self.assertIn("foundation_models", a["domains"])
        self.assertNotIn("verified_viral", str(a))
        self.assertNotIn("score", str(a))

    def test_no_fabricated_domain(self):
        a = tax.classify_text("这是一条没有明确主题的文字")
        self.assertEqual(a["content_type"], "unclassified")
        self.assertEqual(a["domains"], [])

    def test_curated_catalog_coverage(self):
        entries = catalog.load_catalog()
        self.assertGreaterEqual(len(entries), 40)
        self.assertEqual({d for s in entries for d in s["domains"]}, set(tax.AI_DOMAINS))
        for s in entries:
            self.assertEqual(s["collection"], "on_demand")
            self.assertEqual(s["access_status"], "not_checked")
            self.assertTrue(s["url"].startswith("https://"))

    def test_on_demand_filters(self):
        result = catalog.find_sources(domain="agents_automation")
        self.assertTrue(any(s["name"] == "Skills.sh" for s in result))
        self.assertFalse(any(s["name"] == "Runway Academy" for s in result))
        with self.assertRaises(ValueError):
            catalog.find_sources(domain="invalid-domain")

    def test_zero_observed_is_not_zero_news(self):
        with tempfile.TemporaryDirectory() as d:
            report = catalog.coverage(Path(d) / "missing.json")
        self.assertFalse(report["rss_report_available"])
        self.assertEqual(report["rss_discovered_items"], 0)
        self.assertTrue(any("Zero title matches" in x for x in report["warnings"]))

    def test_observed_rss_classification(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "public-rss-candidates.json"
            f.write_text(json.dumps({
                "checked_at_utc": "2026-10-19T00:00:00+00:00",
                "verified_feeds": 1,
                "items": [{
                    "title": "Runway AI视频专业镜头教程",
                    "url": "https://example.com/test",
                    "source": "Example", "published_utc": "2026-10-19T00:00:00Z"
                }]
            }), encoding="utf-8")
            report = catalog.coverage(f)
        domains = {x["id"]: x["observed_rss_title_matches"] for x in report["domains"]}
        self.assertEqual(domains["aicg_video"], 1)
        self.assertEqual(report["rss_discovered_items"], 1)

if __name__ == "__main__":
    unittest.main()
