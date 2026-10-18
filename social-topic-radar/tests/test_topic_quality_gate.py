"""Synthetic guardrail tests. Not real-world traffic/performance evidence."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("topic_gate", HERE/"topic_quality_gate.py")
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def record():
    return {"topic_id":"a","problem_key":"ai-budget","title":"预算如何算",
      "audience":"新用户","trigger":"考虑开会员","job":"控制预算","outcome":"减少浪费",
      "value_type":"决策","angle":"纳入重试成本","promise":"可核验预算","proof_plan":"查官方价并实测",
      "competitor_gap":"竞品忽略重试","difference_rationale":"补成本缺口",
      "source_limitations":"少数用户样本","requires_test":True,"test_gap":"尚未亲测",
      "four_values":{
         "attraction":"开头对比免费会员两种开销误区",
         "save_asset":"可复制的预算记录表",
         "learning_outcome":"学会逐项核对订阅成本",
         "spread_mechanism":"公开成本对比激发真实讨论",
         "spread_class":"fresh_potential",
         "spread_source_url":"https://example.com/post/1",
         "original_published_at":"2026-10-19",
         "freshness_reason":"近期用户问题，编辑判断有可展示的反差"
      },
      "four_value_scores":{"attraction":22,"save":27,"learning":22,"spread":16},
      "signals":[
        {"kind":"user_post","url":"https://example.com/post/1","quote":"成本怎么算","read_scope":"actual_public_post"},
        {"kind":"user_comment","url":"https://example.org/post/2","quote":"会员够用吗","read_scope":"actual_public_comment"}]}

class GateTest(unittest.TestCase):
    def test_two_post_contexts(self):
        x=gate.review_one(record(),set(),set(),set())
        self.assertEqual((x["status"],x["independent_post_contexts"]),("editorial_candidate",2))
    def test_two_comments_one_post(self):
        x=record()
        x["signals"][1]["url"]="https://example.com/post/1#comment"
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"exploratory_only")
    def test_rejected(self):
        x=gate.review_one(record(),{"ai-budget"},set(),set())
        self.assertIn("explicitly_rejected_topic",x["blocking_reasons"])
        self.assertEqual(x["status"],"blocked")
    def test_snippets_untrusted(self):
        x=record()
        for s in x["signals"]:s["read_scope"]="search_snippet_only"
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"blocked")
    def test_no_invented_score(self):
        x=record();x["ratings"]={"demand":5}
        self.assertIsNone(gate.review_one(x,set(),set(),set())["human_supplied_score"])
    def test_official_single_is_exploration(self):
        x=record()
        x["signals"]=[{"kind":"official_release","url":"https://example.net/release",
            "claim":"新功能上线","read_scope":"actual_official_release"}]
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"editorial_candidate")
    def test_missing_four_values_blocks(self):
        x=record(); x.pop("four_values")
        r=gate.review_one(x,set(),set(),set())
        self.assertEqual(r["status"],"blocked")
        self.assertIn("missing_four_values",r["blocking_reasons"])
    def test_unscored_four_values_are_exploratory(self):
        x=record(); x.pop("four_value_scores")
        r=gate.review_one(x,set(),set(),set())
        self.assertEqual(r["status"],"exploratory_only")
        self.assertIsNone(r["four_value_score"])
    def test_low_save_value_blocks(self):
        x=record();x["four_value_scores"]["save"]=8
        r=gate.review_one(x,set(),set(),set())
        self.assertEqual(r["status"],"blocked")
        self.assertIn("four_value_below_minimum_save",r["blocking_reasons"])
    def test_false_viral_claim_blocks(self):
        x=record();v=x["four_values"]
        v["spread_class"]="verified_viral"
        v.pop("freshness_reason",None)
        r=gate.review_one(x,set(),set(),set())
        self.assertEqual(r["status"],"blocked")
        self.assertIn("missing_verified_platform_metric",r["blocking_reasons"])
    def test_one_first_party_original_case(self):
        x=record()
        x["signals"]=[{"kind":"original_case","url":"https://example.org/author/work",
                       "observed_result":"作者公开的原始工作流","read_scope":"actually_read_original"}]
        r=gate.review_one(x,set(),set(),set())
        self.assertEqual(r["status"],"editorial_candidate")
    def test_history_and_batch_duplicates(self):
        with TemporaryDirectory() as d:
            p=Path(d)
            x=record()
            (p/"in.json").write_text(json.dumps({"known_problem_keys":["old"],
                "topics":[x,{**x,"topic_id":"b"},{**x,"topic_id":"c","problem_key":"old"}]}))
            a=gate.review_file(p/"in.json",p)
            self.assertEqual(a["counts"]["blocked"],2)
            self.assertEqual(a["counts"]["editorial_candidate"],1)
    def test_radar_never_approves(self):
        with TemporaryDirectory() as d:
            p=Path(d)
            (p/"editorial-shortlist.json").write_text(json.dumps({"shortlist":[
               {"url":"https://example.com/news","title":"New AI model","verified_scope":"RSS headline + excerpt only"}]}))
            y={"url":"https://www.douyin.com/video/1","post_url":"https://www.douyin.com/video/1",
               "text_excerpt":"请问怎么用？","platform":"douyin","classification_basis":"actual_comment"}
            (p/"domestic-painpoints.json").write_text(json.dumps({"observed_themes":[
                {"theme":"新手","actual_reply_examples":[y,y]}]}))
            a=gate.audit_radar(p)
            self.assertEqual((a["qualified_publishable_topics"],a["comment_examples_visible"],a["distinct_comment_post_contexts"]),(0,1,1))

if __name__=="__main__":unittest.main()
