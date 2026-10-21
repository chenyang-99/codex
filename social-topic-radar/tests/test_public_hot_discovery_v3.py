"""No-network tests for the public hot-feed collector."""
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_hot_discovery_v3", ROOT / "public_hot_discovery_v3.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class HotFeedTests(unittest.TestCase):
    @mock.patch.object(module, "get_json")
    def test_v2ex_hot_returns_provenance_not_ai_proof(self, get_json):
        get_json.return_value = [{"id": 12, "title": "New tool", "url": "https://v2ex.com/t/12",
                                  "created": 1792483200, "replies": 12,
                                  "member": {"username": "alice"}}]
        report, items = module.collect_v2ex()
        self.assertEqual(report["status"], "retrieved")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["platform_native_metrics"]["hot_rank"], 1)
        self.assertNotIn("likes", items[0])
        self.assertEqual(items[0]["read_scope"],
                         "public V2EX hot topics, not proven AI-interest audience")

    @mock.patch.object(module, "get_json", side_effect=OSError("403 forbidden"))
    def test_blocked_source_is_error_not_zero(self, get_json):
        report, posts = module.collect_v2ex()
        self.assertEqual(report["status"], "error")
        self.assertEqual(posts, [])
        self.assertIn("OSError", report["detail"])

    @mock.patch.object(module, "get_json")
    def test_github_stars_not_social_likes(self, get_json):
        get_json.return_value = {"items": [{
            "html_url": "https://github.com/a/b", "full_name": "a/b",
            "description": "AI tool", "created_at": "2026-10-20T00:00:00Z",
            "stargazers_count": 99, "forks_count": 10
        }]}
        report, posts = module.collect_github()
        self.assertEqual(report["status"], "retrieved")
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["platform_native_metrics"]["cumulative_stars"], 99)
        self.assertNotIn("metrics", posts[0])

    @mock.patch.object(module, "get_json")
    def test_hn_top_and_show_merge_duplicate_ids(self, get_json):
        def data(url):
            if "topstories" in url:
                return [42]
            if "showstories" in url:
                return [42, 43]
            ident = int(url.split("/item/")[1].split(".")[0])
            return {"id": ident, "type": "story", "title": "AI video demonstration",
                    "score": 19, "descendants": 3, "time": 1792483200}
        get_json.side_effect = data
        report, posts = module.collect_hn()
        self.assertEqual(report["status"], "retrieved")
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]["platform_native_metrics"]["points"], 19)

    @mock.patch.object(module, "get_json")
    def test_bilibili_chart_keeps_favorites_separate(self, get_json):
        get_json.return_value = {"code": 0, "data": {"list": [{
            "bvid": "BV123", "title": "AI animation", "pubdate": 1792483200,
            "stat": {"view": 200, "favorite": 50}, "owner": {"name": "up"}
        }]}}
        report, posts = module.collect_bilibili()
        self.assertEqual(report["status"], "retrieved")
        self.assertEqual(posts[0]["platform_native_metrics"]["favorites"], 50)
        self.assertNotIn("likes", posts[0])


if __name__ == "__main__":
    unittest.main()
