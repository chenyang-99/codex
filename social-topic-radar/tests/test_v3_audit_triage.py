"""Cover audit truthfulness and editorial shortlist separation from publication."""
import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def mod(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

a=mod("gap_audit_v3_tests","channel_gap_audit_v3.py")
t=mod("value_triage_v3_tests","reader_value_triage_v3.py")

class GapHealthTests(unittest.TestCase):
    def test_missing_artifacts_are_not_false_zero_posts(self):
        with tempfile.TemporaryDirectory() as p:
            doc=[{"source":"hackernews_hot","status":"retrieved","items":12},
                 {"source":"reddit_week_top","status":"partial","items":4}]
            (Path(p)/"external-discovery.json").write_text(
                json.dumps({"provider_status":doc,"items":[]}))
            files,states=a.collect_health(Path(p))
            self.assertTrue(any(x["artifact_status"]=="missing_or_invalid" for x in files))
            result=a.assess({"sources":[{"id":"hackernews"},{"id":"reddit"}]}, files, states)
            self.assertEqual(2,result["observed_probe_count"])
            self.assertEqual(1,result["successful_probe_count"])
            self.assertGreaterEqual(len(result["missing_or_invalid_collector_artifacts"]),1)

    def test_x_search_failures_never_count_as_success(self):
        health=[
            {"provider":"x_query:AI","status":"unavailable","items":0},
            {"provider":"x_query:tools","status":"error","items":0},
            {"provider":"x_curator:ianlacerda","status":"retrieved","items":30},
        ]
        report=a.assess({"sources":[{"id":"x"}]}, [], health)
        self.assertEqual(2,report["x_keyword_queries"])
        self.assertEqual(0,report["x_keyword_queries_success"])
        self.assertEqual(1,report["x_curators_success"])

    def test_source_catalog_is_not_reported_as_live_probes(self):
        report=a.assess({"sources":[{"id":"x"},{"id":"bilibili"}]}, [], [])
        self.assertEqual(2,report["registered_channels"])
        self.assertEqual(0,report["observed_probe_count"])

class ReaderValueTriageTests(unittest.TestCase):
    def test_collection_and_demo_are_prioritized_but_never_published(self):
        x={"source_url":"https://x.com/a/status/1", "source_family":"x",
           "title":"7 AI video tools GitHub projects", "media":[{"type":"video"}],
           "metric_scope":"snapshot","metrics_checked_at":"2026-10-21T01:00:00Z",
           "metrics":{"views":10500,"bookmarks":400}}
        row={"entity_key":"post:x1","source_posts":[x],
             "project_url":"","independent_source_families":["x"]}
        res=t.review([row])
        self.assertEqual(1,len(res))
        self.assertFalse(res[0]["publication_approved"])
        self.assertIn("resource_collection",res[0]["lanes"])
        self.assertTrue(res[0]["signals"])

    def test_missing_platform_metrics_do_not_create_viral_badge(self):
        x={"source_url":"https://x.com/a/status/1","source_family":"x",
           "title":"AI new model","metric_scope":"unverified_or_undated",
           "metrics":{"views":1_000_000,"bookmarks":10_000}}
        row={"entity_key":"post:x1","source_posts":[x],
             "project_url":"","independent_source_families":["x"]}
        self.assertEqual([],t.engagement_evidence(row))

    def test_all_candidates_remain_in_queue(self):
        rows=[{"entity_key":f"post:{i}", "source_posts":[{"title":"unknown"}],
               "project_url":"","independent_source_families":[]} for i in range(40)]
        result=t.review(rows)
        self.assertEqual(40,len(result))
        self.assertTrue(all(not x["publication_approved"] for x in result))

if __name__=="__main__": unittest.main()
