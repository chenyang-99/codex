"""Synthetic release checks. No user drafts or credentials in repository fixtures."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TARGET = Path(__file__).resolve().parent.parent / "scripts" / "delivery_release_gate.py"
spec = importlib.util.spec_from_file_location("copy_release_gate", TARGET)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def fixture():
    body = ("这款开源工具帮助AI网站开发者检查布局和文字层级。"
            "先说明产品受众，再检查页面设计问题。"
            "项目与安装方法见 https://example.org/tool")
    checks = {name: {
        "status": "pass",
        "evidence": "编辑复核了这条具体文案的相关部分；以下锚点确实存在。",
        "anchor": "产品受众" if name in gate.CONTENT_ANCHORED else "",
    } for name in gate.GATES}
    return {
        "draft": body,
        "platform": "x",
        "format": "short_text",
        "genre": "tool",
        "edit_scope": "new_draft",
        "sources": [{"locator": "https://example.org/tool", "supports": "工具定位与基本安装说明"}],
        "acceptance": checks,
        "reviewer": {
            "editorial_reviewed": True,
            "facts_and_rights_checked": True,
            "final_publish_previewed": True,
        }
    }

class DeliveryReleaseTests(unittest.TestCase):
    def codes(self, pkt):
        return gate.validate(pkt)["blocking_reasons"]

    def test_complete_short_text_eligible_but_no_machine_approval(self):
        x = gate.validate(fixture())
        self.assertEqual(x["status"], "eligible_for_delivery")
        self.assertFalse(x["machine_approval"])
        self.assertFalse(x["user_approved"])
        self.assertFalse(x["published"])

    def test_missing_one_gate_blocks(self):
        p = fixture()
        del p["acceptance"]["original_angle"]
        self.assertIn("original_angle_not_signed_off", self.codes(p))

    def test_empty_evidence_blocks(self):
        p = fixture()
        p["acceptance"]["primary_payoff"]["evidence"] = "好"
        self.assertIn("primary_payoff_evidence_insufficient", self.codes(p))

    def test_fake_anchor_blocks(self):
        p = fixture()
        p["acceptance"]["natural_voice"]["anchor"] = "此处根本不存在的句子"
        self.assertIn("natural_voice_missing_real_draft_anchor", self.codes(p))

    def test_missing_editorial_attestation_blocks(self):
        p = fixture()
        p["reviewer"]["final_publish_previewed"] = False
        self.assertIn("reviewer_attestation_incomplete", self.codes(p))

    def test_x_chinese_weight_counts_double(self):
        self.assertEqual(gate.x_weighted_length("你"*140), 280)
        self.assertEqual(gate.x_weighted_length("你"*141), 282)

    def test_x_link_length_is_23_even_when_long(self):
        self.assertEqual(gate.x_weighted_length("链接：https://example.org/" + "a"*300), 6+23)

    def test_x_oversize_like_impeccable_v2_is_blocked(self):
        p = fixture()
        p["draft"] = "AI网站为什么总有模板感？" + "我们用具体设计准则检查页面。"*35
        self.assertIn("x_post_1_over_280_conservative_weight", self.codes(p))

    def test_x_long_post_unknown_entitlement_blocks(self):
        p = fixture()
        p["format"] = "long_post"
        self.assertIn("x_long_post_entitlement_not_confirmed", self.codes(p))
        p["account_long_posts_confirmed"] = True
        self.assertEqual(gate.validate(p)["status"], "eligible_for_delivery")

    def test_x_article_unknown_entitlement_blocks(self):
        p = fixture()
        p["format"] = "article"
        self.assertIn("x_article_entitlement_not_confirmed", self.codes(p))

    def test_thread_requires_part_separation(self):
        p = fixture()
        p["format"] = "thread"
        self.assertIn("thread_requires_complete_posts", self.codes(p))
        p["draft"] = ""
        p["posts"] = ["产品受众，第一页说明产品问题。", "第二页给可用的安装入口 https://example.org/tool"]
        self.assertEqual(gate.validate(p)["status"], "eligible_for_delivery")

    def test_missing_media_rights_blocks_when_required(self):
        p = fixture()
        p["media_required"] = True
        self.assertIn("required_media_unavailable", self.codes(p))
        p["media_assets"] = [{"ready": True, "rights_cleared": False}]
        self.assertIn("required_media_1_not_ready_or_rights_uncleared", self.codes(p))

    def test_disclosure_not_in_copy_blocks(self):
        p = fixture()
        p["disclosure_required"] = True
        p["disclosure_text"] = "广告合作"
        self.assertIn("mandatory_disclosure_not_in_publish_text", self.codes(p))

    def test_source_specificity_blocks(self):
        p = fixture()
        p["sources"] = [{"locator": "https://example.org"}]
        self.assertIn("no_claim_specific_external_sources", self.codes(p))

    def test_placeholder_blocks(self):
        p = fixture()
        p["draft"] += "\n[待补截图]"
        self.assertIn("unresolved_publish_placeholder", self.codes(p))

    def test_review_only_is_not_release(self):
        p = fixture()
        p["edit_scope"] = "review_only"
        self.assertIn("review_only_is_not_release", self.codes(p))

    def test_title_only_preserves_body(self):
        p = fixture()
        p["edit_scope"] = "title_only"
        p["original"] = "另一版本正文"
        self.assertIn("title_only_modified_body", self.codes(p))

    def test_other_platform_nonviral_poetry_not_forced_to_have_sources(self):
        p = fixture()
        p["platform"] = "xiaohongshu"
        p["format"] = "text"
        p["genre"] = "emotion"
        p.pop("sources")
        self.assertEqual(gate.validate(p)["status"], "eligible_for_delivery")

    def test_bad_protected_phrases_does_not_crash(self):
        p = fixture()
        p["protected_phrases"] = None
        self.assertIn("invalid_protected_phrases", self.codes(p))

    def test_xiaohongshu_visual_package_needs_media(self):
        p = fixture()
        p["platform"] = "xiaohongshu"
        p["format"] = "carousel"
        self.assertIn("visual_format_requires_real_media", self.codes(p))

    def test_douyin_script_cannot_pass_as_finished_video(self):
        p = fixture()
        p["platform"] = "douyin"
        p["format"] = "video_script"
        p["video_deliverable_requested"] = True
        self.assertIn("video_script_is_not_finished_video", self.codes(p))

    def test_cli_exit_status_is_hard_gate(self):
        p = fixture()
        p.pop("reviewer")
        with tempfile.TemporaryDirectory() as d:
            f = Path(d)/"packet.json"
            f.write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([sys.executable, str(TARGET), "--input", str(f)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertEqual(json.loads(r.stdout)["status"], "blocked")

if __name__ == "__main__":
    unittest.main()
