"""Retrospective 20-topic regression using existing project notes, not live metrics."""
import importlib.util
import json
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("topic_gate_historical",HERE/"topic_quality_gate.py")
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
DATA=Path(__file__).resolve().parent/"data"/"historical_20_20261020.json"
DOC=json.loads(DATA.read_text(encoding="utf-8"))
RECORDS=DOC["records"]
EVIDENCE_READY={"H01","H02","H04","H05","H06","H08"}

class Historical20RegressionTest(unittest.TestCase):
    def test_twenty_real_prior_topics_with_unique_ids(self):
        self.assertEqual(len(RECORDS),20)
        self.assertEqual(len({r["topic_id"] for r in RECORDS}),20)
        self.assertEqual(len({r["title"] for r in RECORDS}),20)

    def test_all_nine_values_scanned_without_mandating_all_nine(self):
        for record in RECORDS:
            with self.subTest(id=record["topic_id"]):
                self.assertEqual(set(record["value_scan"]),set(gate.VALUE_LABELS))
                self.assertEqual(list(record["value_scan"].values()).count("primary"),1)

    def test_value_proof_gate_identifies_known_evidence_gaps(self):
        ready=[]
        blocked=[]
        for record in RECORDS:
            errors=gate.audit_nine_values(record)
            (blocked if errors else ready).append(record["topic_id"])
            if record["value_proof"]["evidence_status"]=="pending":
                self.assertIn("unverified_value_evidence",errors)
        self.assertEqual(set(ready),EVIDENCE_READY)
        self.assertEqual(len(blocked),14)

    def test_source_link_is_part_of_value_evidence(self):
        for record in RECORDS:
            with self.subTest(id=record["topic_id"]):
                source=gate.canon(record["value_proof"].get("source_url"))
                verified={gate.canon(e["url"]) for e in record["signals"]}
                if record["topic_id"] in EVIDENCE_READY:
                    self.assertIn(source,verified)

    def test_source_material_not_equal_to_editorial_approval(self):
        for record in RECORDS:
            with self.subTest(id=record["topic_id"]):
                result=gate.review_one(record,set(),set(),set())
                self.assertEqual(result["status"],"blocked")
                self.assertFalse(result["human_editorial_approval"])
                self.assertIn("missing_social_pitch",result["blocking_reasons"])
                # The historical dataset deliberately does not invent four-way scores.
                self.assertIsNone(result["content_value_score"])

    def test_user_feedback_is_not_used_to_assess_source_truth(self):
        for record in RECORDS:
            self.assertIn("historical_label",record)
            cleaned=dict(record)
            cleaned.pop("historical_label")
            self.assertEqual(gate.audit_nine_values(cleaned),
                             gate.audit_nine_values(record))

if __name__=="__main__":
    unittest.main()
