"""Synthetic regression cases: no private/user originals are committed."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "ai_copy_preflight", HERE / "scripts" / "copy_quality_gate.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def sample():
    original = ("今天给豆姐安装了工具。按提示扫码授权，然后试了两分钟课程。"
                "后面的整套课程还没测。我的建议是先从第一节试。"
                "当然，如果你的课有老师手把手辅导，那当我没说。")
    return {
        "case_id": "R04-synthetic",
        "edit_scope": "minimal",
        "platform": "xiaohongshu",
        "content_type": "tutorial",
        "audience": "囤网课但没空系统学习的人",
        "central_claim": "可以尝试让AI帮助管理学习",
        "original": original,
        "draft": original.replace("我的建议是", "我建议"),
        "headline_original": "学网课的想法",
        "headline_new": "学网课的想法",
        "protected_phrases": ["豆姐", "两分钟课程", "整套课程还没测",
                              "那当我没说"],
        "required_terms": ["授权", "第一节"],
        "proof_plan": "核对学习材料、长度及回答是否对应原视频",
        "claims": [{"text": "两分钟课程分析",
                    "evidence_status": "user_verified",
                    "presented_as_tested": True},
                   {"text": "完整课程学习",
                    "evidence_status": "proposed",
                    "presented_as_tested": False}],
    }


class CopySkillGateTests(unittest.TestCase):
    def test_small_edit_preserves_author(self):
        result = gate.validate(sample())
        self.assertEqual(result["status"], "requires_editorial_review")
        self.assertEqual(result["preserved"]["protected_count"], 4)

    def test_review_only_cannot_replace_draft(self):
        item = sample()
        item["edit_scope"] = "review_only"
        item["draft"] = item["original"] + "新一句"
        self.assertIn("review_only_must_not_rewrite", gate.validate(item)["blocking_reasons"])

    def test_review_only_unmodified_ok(self):
        item = sample()
        item["edit_scope"] = "review_only"
        item["draft"] = item["original"]
        self.assertEqual(gate.validate(item)["status"], "requires_editorial_review")

    def test_title_only_cannot_change_body(self):
        item = sample()
        item["edit_scope"] = "title_only"
        self.assertIn("title_only_body_changed", gate.validate(item)["blocking_reasons"])

    def test_title_only_exact_body_ok(self):
        item = sample()
        item["edit_scope"] = "title_only"
        item["draft"] = item["original"]
        item["headline_new"] = "换个标题"
        self.assertEqual(gate.validate(item)["status"], "requires_editorial_review")

    def test_minimal_edit_can_not_delete_most_content(self):
        item = sample()
        item["draft"] = "今天装了工具。"
        self.assertIn("minimal_edit_extensively_rewritten", gate.validate(item)["blocking_reasons"])

    def test_preserve_exact_humor_and_reality(self):
        item = sample()
        item["draft"] = item["draft"].replace("那当我没说", "大家一起努力")
        self.assertIn("protected_content_lost", gate.validate(item)["blocking_reasons"])

    def test_missing_required_steps(self):
        item = sample()
        item["draft"] = item["draft"].replace("扫码授权", "扫码")
        self.assertIn("required_content_missing", gate.validate(item)["blocking_reasons"])

    def test_third_party_not_personal_test(self):
        item = sample()
        item["claims"] = [{"text": "第三方视频演示", "evidence_status": "third_party_claim",
                           "presented_as_tested": True, "first_person_experience": True}]
        reasons = gate.validate(item)["blocking_reasons"]
        self.assertIn("claim_0_unverified_experience_claim", reasons)
        self.assertIn("claim_0_source_laundered_as_personal_experience", reasons)

    def test_proposed_play_not_falsely_tested(self):
        item = sample()
        item["claims"][1]["presented_as_tested"] = True
        self.assertIn("claim_1_unverified_experience_claim", gate.validate(item)["blocking_reasons"])

    def test_unknown_data_not_marked_fact(self):
        item = sample()
        item["claims"] = [{"text": "1000次实测", "evidence_status": "unknown",
                           "presented_as_fact": True}]
        self.assertIn("claim_0_unverified_statement_of_fact", gate.validate(item)["blocking_reasons"])

    def test_new_draft_does_not_need_original(self):
        item = sample()
        item["edit_scope"] = "new_draft"
        item["original"] = ""
        item["protected_phrases"] = []
        self.assertEqual(gate.validate(item)["status"], "requires_editorial_review")

    def test_tutorial_missing_proof_plan_warns(self):
        item = sample()
        item["proof_plan"] = ""
        self.assertIn("tutorial_missing_verification_plan", gate.validate(item)["warnings"])

    def test_mechanical_pass_never_published(self):
        result = gate.validate(sample())
        self.assertFalse(result["manually_verified"])
        self.assertFalse(result["published"])

    def test_multiple_cases_counts(self):
        first = sample()
        second = deepcopy(first)
        second["case_id"] = "blocked"
        second["draft"] = "删光了"
        report = gate.audit({"cases": [first, second]})
        self.assertEqual(report["counts"], {"blocked": 1, "requires_editorial_review": 1})

    def test_invalid_record_rejected(self):
        self.assertEqual(gate.validate("not-a-record")["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
