"""Synthetic cases only; these tests are mechanics, not AI writing-quality scores."""
import importlib.util
import tempfile
import json
import subprocess
import sys
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "scripts" / "editorial_preflight.py"
spec = importlib.util.spec_from_file_location("editorial_preflight", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EditorialPreflightTests(unittest.TestCase):
    def test_normal_story_is_not_forced_to_cite_tools(self):
        x = module.analyze({"draft": "我那天盯着邮件看了很久，最后还是关掉了电脑。", "genre": "story"})
        self.assertEqual(x["hints"], [])
        self.assertFalse(x["approved"])

    def test_blank_draft(self):
        self.assertIn("empty_draft", [x["code"] for x in module.analyze({"draft": "  "})["hints"]])

    def test_repetition_warns_and_does_not_edit(self):
        txt = "这个段落包含了足够具体的内容，反复出现可能是复制错误。\n\n这个段落包含了足够具体的内容，反复出现可能是复制错误。"
        res = module.analyze({"draft": txt})
        self.assertIn("duplicate_paragraph", [x["code"] for x in res["hints"]])
        self.assertNotIn("draft", res)

    def test_missing_required_and_protected(self):
        res = module.analyze({"draft": "只有功能名称", "required_facts": ["原始链接", "版本"], "protected_phrases": ["豆姐"]})
        self.assertEqual(len([x for x in res["hints"] if x["code"] == "required_facts_missing"]), 1)
        self.assertIn("protected_phrase_changed", [x["code"] for x in res["hints"]])

    def test_factual_guarantee_and_first_person(self):
        res = module.analyze({"draft": "我亲测它保证涨粉，完全免费且无限制。", "genre": "tool", "test_status": "unknown"})
        codes = [x["code"] for x in res["hints"]]
        self.assertIn("first_person_test_unverified", codes)
        self.assertIn("absolute_claim_check", codes)
        self.assertIn("source_gap", codes)

    def test_verified_first_person_with_source_not_falsely_flagged(self):
        res = module.analyze({"draft": "我亲测新建了三个立方体。", "genre": "tool", "test_status": "user_verified", "sources": ["official readme"]})
        codes = [x["code"] for x in res["hints"]]
        self.assertNotIn("first_person_test_unverified", codes)
        self.assertNotIn("source_gap", codes)

    def test_editorial_figurative_phrase_remains_nonblocking(self):
        res = module.analyze({"draft": "真正重要的是，我们终于看见了那条河。", "genre": "essay"})
        self.assertIn("generic_promo_phrase", [x["code"] for x in res["hints"]])
        self.assertEqual(res["status"], "editorial_hints_only")
        self.assertIsNone(res["virality_prediction"])

    def test_scope_warning(self):
        res = module.analyze({"draft": "改完的正文", "original": "原正文", "edit_scope": "title_only"})
        self.assertIn("edit_scope_changed_body", [x["code"] for x in res["hints"]])

    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "in.json"
            src.write_text(json.dumps({"draft": "具体说明", "genre": "story"}), encoding="utf-8")
            r = subprocess.run([sys.executable, str(PATH), "--input", str(src)], check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(r.stdout)["status"], "editorial_hints_only")


if __name__ == "__main__":
    unittest.main()
