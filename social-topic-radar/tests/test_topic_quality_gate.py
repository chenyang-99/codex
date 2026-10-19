"""Synthetic editorial gate tests. Not real-world engagement evidence."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("topic_gate",HERE/"topic_quality_gate.py")
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def record():
    return {
        "topic_id":"a","problem_key":"ai-budget","title":"预算如何算",
        "audience":"新用户","trigger":"考虑开会员","job":"控制预算",
        "outcome":"避免冲动付款","value_type":"决策","angle":"纳入重试成本",
        "promise":"有依据的开支判断","proof_plan":"查官方价并实测",
        "competitor_gap":"竞品忽略重试","difference_rationale":"补成本缺口",
        "source_limitations":"少数用户样本","requires_test":True,"test_gap":"尚未亲测",
        "content_values":{
            "attraction":"两种看似一样便宜的AI服务实际费用对比",
            "spread_mechanism":"透明账单与反常识体验会引起讨论",
            "payoff_type":"decision",
            "payoff_description":"学会如何辨别成本并决定是否值得付费",
            "spread_class":"fresh_potential",
            "spread_source_url":"https://example.com/post/1",
            "original_published_at":"2026-10-19",
            "freshness_reason":"假设近期出现实际开支对照，尚需来源核验"
        },
        "content_scores":{"attraction":23,"spread":26,"payoff":26,"credibility":12},
        "signals":[
            {"kind":"user_post","url":"https://example.com/post/1",
             "quote":"成本怎么算","read_scope":"actual_public_post"},
            {"kind":"user_comment","url":"https://example.org/post/2",
             "quote":"会员够用吗","read_scope":"actual_public_comment"}
        ]
    }

class GateTest(unittest.TestCase):
    def test_two_post_contexts(self):
        x=gate.review_one(record(),set(),set(),set())
        self.assertEqual((x["status"],x["independent_post_contexts"]),("editorial_candidate",2))
        self.assertEqual(x["content_value_score"],87)
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
        for s in x["signals"]: s["read_scope"]="search_snippet_only"
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"blocked")
    def test_no_invented_legacy_score(self):
        x=record();x["ratings"]={"demand":5}
        self.assertIsNone(gate.review_one(x,set(),set(),set())["human_supplied_score"])
    def test_single_official_original_can_be_candidate(self):
        x=record()
        x["signals"]=[{"kind":"official_release","url":"https://example.net/release",
                       "claim":"新功能上线","read_scope":"actual_official_release"}]
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"editorial_candidate")
    def test_missing_content_values_blocks(self):
        x=record();x.pop("content_values")
        r=gate.review_one(x,set(),set(),set())
        self.assertEqual(r["status"],"blocked")
        self.assertIn("missing_content_values",r["blocking_reasons"])
    def test_unscored_values_stay_exploration(self):
        x=record();x.pop("content_scores")
        r=gate.review_one(x,set(),set(),set())
        self.assertEqual(r["status"],"exploratory_only")
        self.assertIsNone(r["content_value_score"])
    def test_no_save_no_tutorial_insight_can_pass(self):
        x=record()
        x["content_values"]["payoff_type"]="insight"
        x["content_values"]["payoff_description"]="理解一个有依据的行业反直觉判断"
        self.assertNotIn("save_asset",x["content_values"])
        self.assertNotIn("learning_outcome",x["content_values"])
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"editorial_candidate")
    def test_emotional_story_without_prompt_can_pass(self):
        x=record()
        x["value_type"]="情绪"
        x["content_values"]["payoff_type"]="emotion"
        x["content_values"]["payoff_description"]="获得有深度的情感共鸣和分享动机"
        x["signals"]=[{"kind":"original_case","url":"https://example.org/story",
                        "observed_result":"原创者故事与公开原始视频","read_scope":"actually_viewed_original"}]
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"editorial_candidate")
    def test_information_only_payoff_can_pass_without_save_or_tutorial(self):
        x=record()
        x["value_type"]="信息"
        x["content_values"]["payoff_type"]="information"
        x["content_values"]["payoff_description"]="读者及时知道一项已核对的发布变化以及适用人群"
        x["signals"]=[{"kind":"official_release","url":"https://example.org/news",
                       "claim":"官方说明新变化","read_scope":"actual_official_release"}]
        self.assertNotIn("save_asset",x["content_values"])
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"editorial_candidate")

    def test_utility_payoff_and_learning_value_type_accepted(self):
        x=record()
        x["value_type"]="学习"
        x["content_values"]["payoff_type"]="utility"
        x["content_values"]["payoff_description"]="能完成一个低成本实际任务"
        x["signals"]=[{"kind":"original_case","url":"https://example.org/guide",
                       "observed_result":"原作者公开的具体步骤","read_scope":"actually_read_original"}]
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"editorial_candidate")

    def test_social_expression_payoff_can_pass_without_save(self):
        x=record()
        x["value_type"]="社交表达"
        x["content_values"]["payoff_type"]="social_expression"
        x["content_values"]["payoff_description"]="读者获得可核对的观点与公共讨论角度"
        x["signals"]=[{"kind":"original_case","url":"https://example.org/opinion",
                       "observed_result":"作者公开原始观点","read_scope":"actually_read_original"}]
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"editorial_candidate")

    def test_low_attraction_blocks(self):
        x=record();x["content_scores"]["attraction"]=10
        r=gate.review_one(x,set(),set(),set())
        self.assertEqual(r["status"],"blocked")
        self.assertIn("content_score_below_minimum_attraction",r["blocking_reasons"])
    def test_low_spread_blocks(self):
        x=record();x["content_scores"]["spread"]=8
        r=gate.review_one(x,set(),set(),set())
        self.assertEqual(r["status"],"blocked")
        self.assertIn("content_score_below_minimum_spread",r["blocking_reasons"])
    def test_fake_viral_claim_blocks(self):
        x=record();x["content_values"]["spread_class"]="verified_viral"
        r=gate.review_one(x,set(),set(),set())
        self.assertEqual(r["status"],"blocked")
        self.assertIn("missing_verified_platform_metric",r["blocking_reasons"])
    def test_invalid_payoff_blocks(self):
        x=record();x["content_values"]["payoff_type"]="magical"
        r=gate.review_one(x,set(),set(),set())
        self.assertIn("missing_or_invalid_payoff_type",r["blocking_reasons"])
    def test_legacy_v11_format_cannot_auto_pass(self):
        x=record()
        x.pop("content_scores")
        x["four_value_scores"]={"attraction":25,"save":30,"learning":25,"spread":20}
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"exploratory_only")
    def test_one_first_party_original_case(self):
        x=record()
        x["signals"]=[{"kind":"original_case","url":"https://example.org/author/work",
                       "observed_result":"作者公开原始资料","read_scope":"actually_read_original"}]
        self.assertEqual(gate.review_one(x,set(),set(),set())["status"],"editorial_candidate")
    def test_history_and_batch_duplicates(self):
        with TemporaryDirectory() as d:
            p=Path(d);x=record()
            (p/"in.json").write_text(json.dumps({"known_problem_keys":["old"],
                "topics":[x,{**x,"topic_id":"b"},{**x,"topic_id":"c","problem_key":"old"}]}))
            a=gate.review_file(p/"in.json",p)
            self.assertEqual(a["counts"]["blocked"],2)
            self.assertEqual(a["counts"]["editorial_candidate"],1)
    def test_radar_never_approves(self):
        with TemporaryDirectory() as d:
            p=Path(d)
            (p/"editorial-shortlist.json").write_text(json.dumps({"shortlist":[
                {"url":"https://example.com/news","title":"New AI model",
                 "verified_scope":"RSS headline + excerpt only"}]}))
            y={"url":"https://www.douyin.com/video/1","post_url":"https://www.douyin.com/video/1",
               "text_excerpt":"请问怎么用？","platform":"douyin","classification_basis":"actual_comment"}
            (p/"domestic-painpoints.json").write_text(json.dumps({"observed_themes":[
                {"theme":"新手","actual_reply_examples":[y,y]}]}))
            a=gate.audit_radar(p)
            self.assertEqual((a["qualified_publishable_topics"],a["comment_examples_visible"],
                               a["distinct_comment_post_contexts"]),(0,1,1))

if __name__=="__main__":unittest.main()
