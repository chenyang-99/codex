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

    def test_new_draft_requires_research_and_value_delivery(self):
        item = sample()
        item["edit_scope"] = "new_draft"
        item["original"] = ""
        item["protected_phrases"] = []
        reasons = gate.validate(item)["blocking_reasons"]
        self.assertIn("research_dossier_missing", reasons)
        self.assertIn("value_delivery_missing", reasons)

    def test_new_draft_complete_research_preflight(self):
        item = sample()
        item["edit_scope"] = "new_draft"
        item["original"] = ""
        item["protected_phrases"] = []
        item["research"] = {
            "question": "这一主题解决什么问题",
            "summary": "根据公开技术资料作出的概念区分和判断",
            "limitations": "没有完成个人独立实测",
            "sources": [{"locator": "https://example.org/primary",
                         "supports": "一项具体技术定义"}]
        }
        item["value_delivery"] = {
            "hook": "标题交代阅读收益",
            "primary_payoff_type": "insight",
            "primary_payoff": "读者理解三种方法的根本区别",
            "shareability": "有清楚分享理由，传播仅为编辑预测",
            "readability": "关键术语以人话解释"
        }
        self.assertEqual(gate.validate(item)["status"], "requires_editorial_review")

    def test_new_draft_rejects_empty_sources_and_readability(self):
        item = sample()
        item["edit_scope"] = "new_draft"
        item["research"] = {"question": "问题", "summary": "提炼", "limitations": "限制", "sources": []}
        item["value_delivery"] = {"hook": "开头", "saveable": "清单",
                                   "learning": "方法", "shareability": "理由"}
        reasons = gate.validate(item)["blocking_reasons"]
        self.assertIn("research_sources_missing", reasons)
        self.assertIn("value_readability_missing", reasons)

    def test_emotion_only_payoff_does_not_require_learning_or_save(self):
        item = sample()
        item["edit_scope"] = "new_draft"
        item["original"] = ""
        item["research"] = {
            "question": "如何描述AI学习焦虑", "summary": "公开作者观点和真实情绪表达",
            "limitations": "属于观点而非普适统计结论",
            "sources": [{"locator": "本轮用户文字", "supports": "用户观点"}]
        }
        item["value_delivery"] = {
            "hook": "直面AI学习焦虑", "shareability": "同感读者可能向朋友分享（编辑预测）",
            "primary_payoff_type": "emotion", "primary_payoff": "读者得到情绪理解",
            "readability": "自然短句"
        }
        self.assertEqual(gate.validate(item)["status"], "requires_editorial_review")

    def test_save_only_payoff_does_not_require_learning(self):
        item = sample()
        item["edit_scope"] = "new_draft"
        item["original"] = ""
        item["research"] = {
            "question": "哪些工具适合留存", "summary": "官方页面已列出功能和条件",
            "limitations": "尚未个人实测",
            "sources": [{"locator": "https://example.org/official", "supports": "工具用途与限制"}]
        }
        item["value_delivery"] = {
            "hook": "明确哪种工具值得保留", "shareability": "同领域用户转发（编辑预测）",
            "primary_payoff_type": "save", "primary_payoff": "带适用说明的工具直达入口",
            "readability": "简洁且准确"
        }
        self.assertEqual(gate.validate(item)["status"], "requires_editorial_review")

    def test_primary_payoff_required_but_secondary_optional(self):
        item = sample()
        item["edit_scope"] = "new_draft"
        item["research"] = {
            "question": "讨论内容", "summary": "对照", "limitations": "情况有限",
            "sources": [{"locator": "本轮用户文字", "supports": "个人观点"}]
        }
        item["value_delivery"] = {
            "hook": "看点", "shareability": "传播机制", "readability": "自然"
        }
        self.assertIn("value_primary_payoff_type_missing", gate.validate(item)["blocking_reasons"])
        self.assertIn("value_primary_payoff_missing", gate.validate(item)["blocking_reasons"])

    def test_invalid_payoff_type_blocked(self):
        item = sample()
        item["edit_scope"] = "new_draft"
        item["research"] = {
            "question": "问题", "summary": "归纳", "limitations": "限制",
            "sources": [{"locator": "本轮观点", "supports": "观点"}]
        }
        item["value_delivery"] = {
            "hook": "开头", "shareability": "机制", "readability": "清晰",
            "primary_payoff_type": "fake_virality", "primary_payoff": "真实读者回报"
        }
        self.assertIn("value_primary_payoff_type_invalid", gate.validate(item)["blocking_reasons"])

    def test_substantive_rewrite_requires_research(self):
        item = sample()
        item["edit_scope"] = "substantive_rewrite"
        self.assertIn("research_dossier_missing", gate.validate(item)["blocking_reasons"])

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
