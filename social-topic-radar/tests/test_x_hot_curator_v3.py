"""Offline X curator and keyword discovery tests; no X requests or logins."""
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("x_hot_curator_v3", HERE / "x_hot_curator_v3.py")
xmod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(xmod)


class XCuratorTests(unittest.TestCase):
    def test_curator_quote_preserves_original_url(self):
        quote = {"url": "https://x.com/maker/status/111",
                 "author": {"handle": "maker"}, "text": "New AI tool",
                 "likes": 15, "bookmarks": 30}
        tweets = [{"url": "https://x.com/ianlacerda/status/222",
                   "author": {"handle": "ianlacerda"}, "text": ".",
                   "quoted": quote}]
        rows, people = xmod.curator_rows(tweets, "ianlacerda")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://x.com/maker/status/111")
        self.assertEqual(rows[0]["curator_quote_url"], "https://x.com/ianlacerda/status/222")
        self.assertTrue(rows[0]["quote_relationship_verified"])
        self.assertEqual(people, {"maker"})

    def test_no_automatic_quote_claim_for_curator_own_post(self):
        rows, people = xmod.curator_rows(
            [{"url": "https://x.com/ianlacerda/status/23",
              "author": {"handle": "ianlacerda"},
              "text": "I like this workflow"}], "ianlacerda")
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["quote_relationship_verified"])
        self.assertEqual(people, set())

    def test_source_unavailable_is_logged_not_empty(self):
        def fail(kind, value):
            raise RuntimeError("third_party_x_access_denied")
        posts, health, authors = xmod.collect({"queries": ["AI tools"], "curators": []},
                                             execute=fail)
        self.assertEqual(posts, [])
        self.assertEqual(authors, [])
        self.assertEqual(len(health), 1)
        self.assertEqual(health[0]["status"], "unavailable")
        self.assertIn("denied", health[0]["error"])

    def test_public_tool_links_preserve_original(self):
        t = {"url": "https://x.com/maker/status/4",
             "author": {"handle": "maker"},
             "text": "Project here https://github.com/example/project",
             "bookmarks": 10, "views": 1000}
        p = xmod.to_candidate(t, "x_keyword_search")
        self.assertEqual(p["project_url"], "https://github.com/example/project")
        self.assertEqual(p["metrics"]["bookmarks"], 10)
        self.assertEqual(p["curator_quote_url"], "")
        self.assertFalse(p["quote_relationship_verified"])


if __name__ == "__main__":
    unittest.main()
