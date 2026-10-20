"""Synthetic regressions for nine value types; not real post-performance evidence."""
import unittest
from test_topic_quality_gate import gate, record, retarget


class NineValueEvidenceTest(unittest.TestCase):
    def audit(self, x):
        return gate.review_one(x, set(), set(), set())

    def test_missing_scan_and_proof_blocks_high_score(self):
        x=record()
        x.pop("value_scan")
        x.pop("value_proof")
        r=self.audit(x)
        self.assertEqual(r["status"], "blocked")
        self.assertIn("missing_nine_value_scan", r["blocking_reasons"])
        self.assertIn("missing_value_proof", r["blocking_reasons"])
        self.assertEqual(r["content_value_score"], 87)

    def test_one_primary_with_optional_secondary(self):
        x=record()
        self.assertEqual(self.audit(x)["status"], "editorial_candidate")
        x["value_scan"]["learning"]="secondary"
        self.assertEqual(self.audit(x)["status"], "editorial_candidate")
        x["value_scan"]["learning"]="primary"
        self.assertIn("nine_value_scan_requires_one_primary", self.audit(x)["blocking_reasons"])

    def test_mismatched_primary_and_chinese_label(self):
        x=record()
        x["value_scan"]["decision"]="not_applicable"
        x["value_scan"]["insight"]="primary"
        self.assertIn("primary_value_mismatch", self.audit(x)["blocking_reasons"])
        y=record()
        y["value_type"]="情绪"
        self.assertIn("chinese_value_label_mismatch", self.audit(y)["blocking_reasons"])

    def test_weak_news_without_specific_fact_is_blocked(self):
        x=retarget(record(),"information")
        x["value_proof"]["category_evidence"]["new_fact"]=""
        self.assertIn("missing_value_information_new_fact", self.audit(x)["blocking_reasons"])

    def test_save_post_without_access_conditions_is_blocked(self):
        x=retarget(record(),"save")
        x["value_proof"]["category_evidence"]["access_conditions"]=""
        self.assertIn("missing_value_save_access_conditions", self.audit(x)["blocking_reasons"])

    def test_visual_work_never_viewed_is_blocked(self):
        x=retarget(record(),"entertainment")
        x["value_proof"]["source_access"]="original_read"
        self.assertIn("visual_work_not_viewed", self.audit(x)["blocking_reasons"])

    def test_unlinked_source_and_unverified_claim_are_blocked(self):
        x=record()
        x["value_proof"]["source_url"]="https://example.net/unread"
        self.assertIn("unlinked_value_proof_source", self.audit(x)["blocking_reasons"])
        y=record()
        y["value_proof"]["evidence_status"]="pending"
        self.assertIn("unverified_value_evidence", self.audit(y)["blocking_reasons"])

    def test_all_nine_values_use_separate_category_proofs(self):
        for value in gate.VALUE_LABELS:
            with self.subTest(value=value):
                x=retarget(record(),value)
                r=self.audit(x)
                self.assertEqual(r["status"],"editorial_candidate")
                self.assertEqual(r["primary_value"],value)
                self.assertEqual(r["value_proof_verdict"],"manual_value_review_required")
                self.assertFalse(r["human_editorial_approval"])
                requirement=gate.VALUE_PROOF_FIELDS[value][0]
                x["value_proof"]["category_evidence"][requirement]=""
                self.assertIn("missing_value_"+value+"_"+requirement,
                              self.audit(x)["blocking_reasons"])

    def test_formerly_rejected_topic_stays_blocked(self):
        x=record()
        x["problem_key"]="past-batch-43"
        r=gate.review_one(x,{"past-batch-43"},set(),set())
        self.assertEqual(r["status"],"blocked")
        self.assertIn("explicitly_rejected_topic",r["blocking_reasons"])

    def test_resource_style_positive_sample_requires_actual_material(self):
        x=retarget(record(),"save")
        x["title"]="AI漫画资源原作入口和使用边界（仅作合成回归）"
        self.assertEqual(self.audit(x)["status"],"editorial_candidate")
        x["value_proof"]["observed_material"]=""
        self.assertIn("missing_value_proof_observed_material",
                      self.audit(x)["blocking_reasons"])


if __name__=="__main__":
    unittest.main()
