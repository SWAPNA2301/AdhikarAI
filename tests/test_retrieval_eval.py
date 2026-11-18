"""Offline harness integration with real Chroma and a tiny deterministic fixture."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("retrieval_eval", ROOT / "eval/run_eval.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class FixtureEncoder:
    def encode(self, texts):
        return [[float("pension" in text.lower()), float("school" in text.lower()),
                 float("weather" in text.lower())] for text in texts]


class RetrievalEvaluationTests(unittest.TestCase):
    def test_tiny_fixture_writes_report_with_real_search(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            root = Path(directory)
            schemes = []
            for sid, name in (("A", "pension"), ("B", "school")):
                scheme = dict(scheme_id=sid, scheme_name=name, category=name,
                              state="all_india", government_level="central",
                              official_source_url="https://example.gov.in", verification_date="2026-11-14",
                              verification_notes=[])
                scheme.update({field: {"status": "verified", "items": [name], "note": ""}
                               for field in evaluation.semantic.FACT_FIELDS})
                schemes.append(scheme)
            queries = [{"query": query, "gold_scheme_ids": gold, "language": "en"}
                       for query, gold in (("PENSION", ["A"]), ("school", ["B"]), ("weather", []))]
            (root / "schemes.json").write_text(json.dumps({"schemes": schemes}), encoding="utf-8")
            (root / "queries.json").write_text(json.dumps(queries), encoding="utf-8")
            with patch.dict("os.environ", {"SEMANTIC_MAX_DISTANCE": "0.82"}):
                results = evaluation.run(root / "queries.json", root / "schemes.json",
                                         root / "results.md", root / "index", FixtureEncoder())
            for rows in results.values():
                self.assertEqual([row["ranked"] for row in rows], [["A"], ["B"], []])
                self.assertTrue(all(value == 1 for value in evaluation.metrics(rows).values()))
            report = (root / "results.md").read_text(encoding="utf-8")
            self.assertIn("DRAFT", report)
            self.assertIn("TEST FIXTURE", report)
            self.assertIn("Misses@5", report)
            self.assertIn("correct abstention", report)

    def test_metrics_partial_recall_rank_and_empty_gold(self):
        rows = [{"gold_scheme_ids": ["A", "B"], "ranked": ["X", "A", "B"]},
                {"gold_scheme_ids": ["C"], "ranked": []},
                {"gold_scheme_ids": [], "ranked": ["X"]}]
        self.assertEqual(evaluation.metrics(rows), {
            "recall@1": 0, "recall@3": 0.5, "recall@5": 0.5,
            "MRR": 0.25, "No-match accuracy": 0})
        self.assertIsNone(evaluation.metrics(rows[-1:])["MRR"])
        with self.assertRaises(ValueError):
            evaluation.validate_queries([{"query": "help", "gold_scheme_ids": ["unknown"],
                                          "language": "en"}], {"A"})

    def test_draft_queries_reference_real_ids(self):
        schemes = json.loads((ROOT / "data/processed/schemes.json").read_text(encoding="utf-8"))["schemes"]
        queries = json.loads((ROOT / "eval/queries.json").read_text(encoding="utf-8"))
        evaluation.validate_queries(queries, {scheme["scheme_id"] for scheme in schemes})
        self.assertEqual(len(queries), 40)
        self.assertTrue(any(not row["gold_scheme_ids"] for row in queries))


if __name__ == "__main__":
    unittest.main()
