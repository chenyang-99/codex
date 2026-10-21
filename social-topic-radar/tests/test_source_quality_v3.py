"""Regression tests for known V3 candidate loss and mistaken identity problems."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import unittest
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]

def load(modname, filename):
    spec = importlib.util.spec_from_file_location(modname, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

u = load("intake_correctness_v3", "unified_topic_intake.py")
f = load("trend_feeds_correctness_v3", "trend_feeds_v3.py")
NOW = dt.datetime(2026, 10, 21, tzinfo=dt.timezone.utc)

class IdentityRegressionTests(unittest.TestCase):
    def test_hackernews_id_survives_canonical(self):
        a = u.canonical("https://news.ycombinator.com/item?id=123&foo=2")
        b = u.canonical("https://news.ycombinator.com/item?id=456")
        self.assertNotEqual(a, b)
        self.assertEqual(a, "https://news.ycombinator.com/item?id=123")

    def test_youtube_video_query_id_is_not_discarded(self):
        a = u.canonical("https://www.youtube.com/watch?v=abc123&t=11s")
        b = u.canonical("https://www.youtube.com/watch?v=abc234")
        self.assertNotEqual(a, b)
        self.assertEqual(a, "https://youtube.com/watch?v=abc123")

    def test_github_discussions_remain_distinct_posts(self):
        a = u.canonical("https://github.com/company/repo/issues/2")
        b = u.canonical("https://github.com/company/repo/issues/3")
        self.assertNotEqual(a, b)

    def test_github_explicit_project_identity_deduplicates_repo_links(self):
        items = [
            ("reddit", {"url":"https://www.reddit.com/r/ai/comments/1",
                         "project_url":"https://github.com/ORG/Project"}),
            ("x", {"url":"https://x.com/a/status/2",
                   "project_url":"https://github.com/org/project?utm_source=foo"}),
        ]
        result = u.assemble(items, NOW)
        self.assertEqual(len(result), 1)
        self.assertEqual(2, result[0]["source_count"])
        self.assertEqual(["reddit","x"], result[0]["independent_source_families"])

    def test_two_github_repos_in_collection_do_not_collapse(self):
        result = u.normalize({"url":"https://x.com/author/status/10",
             "external_links":["https://github.com/a/repo1","https://github.com/b/repo2"]},
             "x", NOW)
        self.assertEqual("", result["project_url"])
        self.assertEqual("post:https://x.com/author/status/10", result["entity_key"])

    def test_one_github_repo_in_post_is_valid_entity(self):
        result = u.normalize({"url":"https://x.com/author/status/11",
             "external_links":["https://github.com/a/repo1"]}, "x", NOW)
        self.assertEqual("project:https://github.com/a/repo1", result["entity_key"])

    def test_native_metrics_are_retained_but_not_mixed(self):
        result = u.normalize({"url":"https://news.ycombinator.com/item?id=5",
             "platform_native_metrics":{"points":100,"comments":23},
             "metrics_checked_at":"2026-10-21T01:00:00Z"}, "hackernews", NOW)
        self.assertEqual({"points":100,"comments":23}, result["platform_native_metrics"])
        self.assertEqual({}, result["metrics"])
        self.assertEqual("snapshot",result["metric_scope"])

    def test_same_x_post_twice_does_not_count_as_two_independent_platforms(self):
        rows = [
            ("manual_seed",{"url":"https://x.com/a/status/22","source":"x"}),
            ("x_hot_curator",{"url":"https://x.com/a/status/22","source":"x_curator_quote"}),
        ]
        items = u.assemble(rows, NOW)
        self.assertEqual(1,len(items))
        self.assertEqual(["x"],items[0]["independent_source_families"])

    def test_trending_feed_inputs_are_not_lost(self):
        self.assertIn(("external-discovery-hot-extra.json","items","trending_rss"),u.FILES)

class TrendFeedTests(unittest.TestCase):
    def test_rss_read_without_popularity_fabrication(self):
        raw=b'''<rss version="2.0"><channel>
          <item><title>Tool Alpha</title><link>https://www.producthunt.com/products/alpha</link></item>
          <item><title>Tool Beta</title><link>https://www.producthunt.com/products/beta</link></item>
          </channel></rss>'''
        values=f.fetch_one("producthunt_launch_rss",f.FEEDS["producthunt_launch_rss"],read=lambda _:raw)
        self.assertEqual(2,len(values))
        self.assertEqual({},values[0]["metrics"])
        self.assertIn("NOT independently verified", values[0]["read_scope"])

    def test_trending_json_mapping_distinct(self):
        raw=json.dumps({"items":[{"title":"a/tool","url":"https://github.com/a/tool",
         "description":"an AI app"}]}).encode()
        rows=f.fetch_one("github_trending_mirror",f.FEEDS["github_trending_mirror"],read=lambda _:raw)
        self.assertEqual("https://github.com/a/tool",rows[0]["project_url"])
        self.assertIsNone(rows[0]["published_utc"])

    def test_lobsters_hot_json_has_site_native_metrics(self):
        raw=json.dumps([{"title":"AI developer tooling","short_id_url":"https://lobste.rs/s/abc",
            "url":"https://github.com/team/tool","score":37,
            "comment_count":12,"created_at":"2026-10-20T12:00:00-05:00"}]).encode()
        rows=f.fetch_one("lobsters_hot_json",f.FEEDS["lobsters_hot_json"],read=lambda _:raw)
        self.assertEqual(1,len(rows))
        self.assertEqual("https://lobste.rs/s/abc",rows[0]["url"])
        self.assertEqual({"points":37,"comments":12},rows[0]["metrics"])
        self.assertTrue(rows[0]["published_utc"].startswith("2026-10-20"))
        self.assertEqual("https://github.com/team/tool",rows[0]["project_url"])

    def test_youtube_official_atom_rss_404_first_party_recovery(self):
        source=f.FEEDS["youtube_fireship"]
        atom=b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
          <title>New AI video editor</title><link href="https://www.youtube.com/watch?v=xyz123"/>
          <published>2026-10-21T01:00:00Z</published></entry></feed>'''
        calls=[]
        def getter(url):
            calls.append(url)
            if url.endswith("UCsBjURrPoezykLs9EqgamOA") and "/xml/feeds/" not in url:
                raise HTTPError(url,404,"temporary",{},None)
            return atom
        with unittest.mock.patch.object(f.time,"sleep",lambda _:None):
            rows=f.fetch_one("youtube_fireship",source,read=getter)
        self.assertEqual(1,len(rows))
        self.assertEqual("official_alternate_path",rows[0]["retrieval_path"])
        self.assertEqual(2,len(calls))
        self.assertEqual("https://www.youtube.com/watch?v=xyz123",rows[0]["url"])

    def test_youtube_403_is_not_bypassed_or_hidden(self):
        source=f.FEEDS["youtube_fireship"]
        called=[]
        def getter(url):
            called.append(url)
            raise HTTPError(url,403,"not permitted",{},None)
        with self.assertRaises(HTTPError):
            f.fetch_rss_with_official_retry("youtube_fireship",source,read=getter,
                                           sleep=lambda _:None)
        self.assertEqual(1,len(called))

    def test_youtube_all_official_endpoints_failed_reports_unavailable(self):
        source={"youtube_test":f.FEEDS["youtube_fireship"]}
        def getter(url):
            raise HTTPError(url,404,"temp",{},None)
        with unittest.mock.patch.object(f.time,"sleep",lambda _:None):
            rows,health=f.collect(source,getter)
        self.assertEqual([],rows)
        self.assertEqual("unavailable",health[0]["status"])
        self.assertIn("HTTPError",health[0]["error"])

    def test_provider_failure_does_not_hide_success(self):
        tiny={"ok": {"url":"https://lobste.rs/hottest.rss","type":"xml",
                      "platform":"lobsters","scope":"public"},
              "blocked": {"url":"https://www.producthunt.com/feed","type":"xml",
                          "platform":"producthunt","scope":"public"}}
        raw=b'<rss><channel><item><title>AI</title><link>https://example.org/a</link></item></channel></rss>'
        def getter(url):
            if "producthunt.com" in url: raise ValueError("blocked")
            return raw
        rows,health=f.collect(tiny,getter)
        self.assertEqual(1,len(rows))
        self.assertEqual({"retrieved","unavailable"}, {a["status"] for a in health})

if __name__ == "__main__":unittest.main()
