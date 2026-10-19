"""Synthetic safeguards for recurring topic curation; no fake performance claims."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "topic_editorial_preflight.py"
spec=importlib.util.spec_from_file_location("topic_editorial_preflight", SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
BASE={"id":"1","title":"某AI工具本周更新","entity":"product-a","source_url":"https://example.com/release",
      "original_published_at":"2026-10-18","original_read_scope":"original_page",
      "value_delivery":"附完整用法与限制","spread_class":"fresh_potential",
      "spread_basis":"具体读者有保存需求","counterevidence_reviewed":True,
      "editorial_status":"research_candidate"}
HISTORY=[{"row":176,"title":"相同官方更新","entity":"product-a","source_url":"https://example.com/release"}]
class PreflightTests(unittest.TestCase):
 def check(self,obj,history=None):
  return m.audit({"history":history or [],"candidates":[obj]},"2026-10-19")["results"][0]
 def test_same_url_blocks_without_new_fact(self):
  flags=self.check(dict(BASE),HISTORY)["flags"]
  self.assertIn("historical_collision_requires_editor_review",flags)
  self.assertIn("distinct_new_facts_not_documented",flags)
 def test_new_angle_still_requires_manual_review(self):
  item={**BASE,"novelty_delta":"真的新增API","novelty_source_url":"https://example.com/new-api"}
  result=self.check(item,HISTORY)
  self.assertIn("historical_collision_requires_editor_review",result["flags"])
  self.assertNotIn("distinct_new_facts_not_documented",result["flags"])
 def test_old_launch_cannot_be_passed_off_as_new(self):
  o={**BASE,"original_published_at":"2026-10-01"}
  self.assertIn("older_than_72_hours_not_labeled",self.check(o)["flags"])
  o["timeliness_label"]="evergreen_or_ongoing"
  self.assertNotIn("older_than_72_hours_not_labeled",self.check(o)["flags"])
 def test_producthunt_votes_not_social_viral(self):
  o={**BASE,"spread_class":"verified_viral","source_metric_platform":"producthunt",
     "viral_post_url":"https://producthunt.com/products/test","viral_metrics":{"points":100},"metrics_checked_at":"2026-10-19T12:00+08:00"}
  self.assertIn("product_votes_or_stars_are_not_social_virality",self.check(o)["flags"])
 def test_totals_without_components_not_formal(self):
  o={**BASE,"editorial_status":"formal_recommendation","scores":{"total":89}}
  self.assertIn("four_component_scores_missing_or_invalid",self.check(o)["flags"])
 def test_subthreshold_component_rejected(self):
  o={**BASE,"editorial_status":"formal_recommendation","scores":{"attraction":25,"spread":22,"payoff":30,"credibility":15},
     "scores_evidence":"逐项来源说明"}
  self.assertIn("does_not_meet_v12_editorial_thresholds",self.check(o)["flags"])
 def test_counterevidence_is_mandatory_and_no_auto_approval(self):
  o={**BASE,"counterevidence_reviewed":False}
  r=self.check(o)
  self.assertIn("counterevidence_not_reviewed",r["flags"])
  self.assertFalse(r["automatically_approved"])
 def test_good_metadata_is_still_not_approval(self):
  r=self.check(BASE)
  self.assertEqual(r["status"],"requires_manual_review")
  self.assertFalse(r["automatically_approved"])
 def test_within_round_duplicate_is_checked(self):
  o={**BASE,"id":"2","title":"Second name"}
  a=m.audit({"history":[],"candidates":[BASE,o]},"2026-10-19")
  self.assertIn("historical_collision_requires_editor_review",a["results"][1]["flags"])
if __name__=="__main__":unittest.main()
