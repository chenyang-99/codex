"""Offline tests for off-the-shelf X search and public social-index adapters."""
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

a=load("x_horizon_search_test","horizon_apify_search_v3.py")
b=load("social_index_test","indexed_social_discovery_v3.py")
u=load("unified_offshelf_test","unified_topic_intake.py")
y=load("youtube_official_test","youtube_official_search_v3.py")

class XOffTheShelfTests(unittest.TestCase):
    def test_default_no_paid_calls(self):
        def fail(*args,**kwargs):raise AssertionError("paid network must not run")
        rows,health=a.collect({},call=fail)
        self.assertEqual([],rows)
        self.assertEqual("not_configured",health[0]["status"])
        self.assertEqual("paid_search_not_approved",health[0]["reason"])

    def test_budget_token_enable_three_gates(self):
        base={"X_SEARCH_PAID_APPROVED":"1","X_SEARCH_APIFY_ENABLE":"1",
              "APIFY_TOKEN":"a_secret","X_SEARCH_MAX_RUN_USD":"0.5"}
        self.assertIsNone(a.gate(base))
        for key in ("X_SEARCH_PAID_APPROVED","X_SEARCH_APIFY_ENABLE",
                    "APIFY_TOKEN","X_SEARCH_MAX_RUN_USD"):
            env=dict(base);env.pop(key)
            self.assertIsNotNone(a.gate(env))
        base["X_SEARCH_MAX_RUN_USD"]="10.0"
        self.assertIsNotNone(a.gate(base))

    def test_horizon_actor_contract_with_mock(self):
        paths=[]
        def call(method,path,token,payload=None):
            paths.append((method,path,payload))
            if method=="POST":return {"data":{"id":"R1","defaultDatasetId":"D1"}}
            if "/actor-runs/" in path:return {"data":{"status":"SUCCEEDED"}}
            return [{"id":"2110012345678901234","user":{"screen_name":"artist"},
                     "text":"5 AI tools https://github.com/a/one and https://github.com/b/two",
                     "favorite_count":300,"view_count":14000,
                     "created_at":"2026-10-20T14:00:00Z"}]
        out=a.query("secret","AI tools",0.5,call=call,sleep=lambda _:None)
        self.assertEqual(1,len(out))
        self.assertEqual("",out[0]["project_url"])
        self.assertEqual(2,len(out[0]["external_links"]))
        self.assertTrue(paths[0][1].startswith("/acts/altimis~scweet/runs?"))
        self.assertIn("maxTotalChargeUsd=0.50",paths[0][1])
        self.assertEqual("search",paths[0][2]["source_mode"])
        self.assertEqual("AI tools",paths[0][2]["search_query"])

    def test_x_metrics_and_url_provenance(self):
        out=a.normalize({"id":"tweet-12345","text":"hello",
                         "user":{"screen_name":"worker"},
                         "favorite_count":17,"view_count":1000},"2026-10-21T00:00:00Z")
        self.assertEqual("https://x.com/worker/status/12345",out["url"])
        self.assertEqual(17,out["metrics"]["likes"])
        self.assertNotIn("bookmarks",out["metrics"])

class IndexedLeadsTests(unittest.TestCase):
    def test_google_rss_keeps_index_not_fake_social_metrics(self):
        rss=b"""<rss><channel><item><title>AI visual workflow</title>
        <link>https://news.google.com/rss/articles/ABC</link>
        <pubDate>Wed, 21 Oct 2026 09:00:00 GMT</pubDate></item></channel></rss>"""
        rows=b.parse(rss,"xiaohongshu_index")
        self.assertEqual(1,len(rows))
        self.assertEqual({},rows[0]["metrics"])
        self.assertIn("indirect",rows[0]["retrieved_scope"])
        self.assertIn("2026-10-21",rows[0]["published_utc"])

    def test_search_blocked_is_not_zero_viral_posts(self):
        def fake(_):raise OSError("blocked")
        rows,health=b.collect([("x_tool_index","site:x.com AI")],fetch=fake)
        self.assertEqual([],rows)
        self.assertEqual("unavailable",health[0]["status"])
        self.assertIsNone(health[0]["items"])

    def test_feed_added_to_existing_unified_candidate_pool(self):
        filenames={f[0] for f in u.FILES}
        self.assertIn("x-horizon-apify-v3.json",filenames)
        self.assertIn("indexed-social-leads-v3.json",filenames)

class OfficialYouTubeTests(unittest.TestCase):
    def test_no_api_calls_without_key_or_explicit_enable(self):
        def no_call(*args,**kwargs):raise AssertionError("network requested")
        self.assertEqual("not_configured",y.collect({},api=no_call)[1][0]["status"])
        self.assertEqual("not_configured",y.collect({"YOUTUBE_SEARCH_ENABLED":"1"},api=no_call)[1][0]["status"])

    def test_mocked_search_and_native_views(self):
        called=[]
        def caller(endpoint, params, key):
            called.append((endpoint,params))
            if endpoint=="search":
                return {"items":[{"id":{"videoId":"abc123"},
                       "snippet":{"title":"AI animation tutorial","channelTitle":"Author",
                                  "publishedAt":"2026-10-20T00:00:00Z"}}]}
            return {"items":[{"id":"abc123","statistics":{"viewCount":"25000","likeCount":"250",
                      "commentCount":"51"}}]}
        import datetime as dt
        rows,health=y.collect({"YOUTUBE_SEARCH_ENABLED":"1","YOUTUBE_DATA_API_KEY":"TEST"},api=caller,
             clock=dt.datetime(2026,10,21,tzinfo=dt.timezone.utc))
        self.assertEqual(1,len(rows))
        self.assertEqual(25000,rows[0]["platform_native_metrics"]["views"])
        self.assertEqual(4,len(called))
        self.assertEqual("videos",called[-1][0])
        self.assertTrue(all(s["status"]=="retrieved" for s in health))
        self.assertEqual("https://www.youtube.com/watch?v=abc123",rows[0]["url"])

    def test_video_api_not_an_automatic_trending_claim(self):
        rows,health=y.collect({"YOUTUBE_SEARCH_ENABLED":"0","YOUTUBE_DATA_API_KEY":"TEST"},api=lambda *a:None)
        self.assertEqual([],rows)
        self.assertEqual("disabled_by_default",health[0]["reason"])

if __name__=="__main__":unittest.main()
