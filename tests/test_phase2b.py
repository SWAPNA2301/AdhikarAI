"""Phase 2B coverage, preservation and evidence regression checks (offline)."""

from copy import deepcopy
import hashlib
import json
import unittest

from test_dataset import DATA, FACT_FIELDS, validate_dataset


CENTRAL_IDS = {
    "IN-PMSBY", "IN-PMJJBY", "IN-APY", "IN-PM-SYM", "IN-PM-KISAN",
}
WB_IDS = {
    "IN-WB-LAKSHMIR-BHANDAR", "IN-WB-KANYASHREE", "IN-WB-RUPASHREE",
    "IN-WB-KRISHAK-BANDHU", "IN-WB-SWASTHYA-SATHI",
}
# Captured from the five original records before Phase 2B edits. Canonical JSON
# makes this insensitive to file formatting, but sensitive to every field value.
PHASE_2A_SHA256 = "913c98c5d7f90336d32fb278fe13eb36cb22355745598f59016bfcff6728ef0b"


class Phase2BTest(unittest.TestCase):
    def test_original_five_records_preserved(self) -> None:
        original = DATA["schemes"][:5]
        self.assertEqual({r["scheme_id"] for r in original}, CENTRAL_IDS)
        canonical = json.dumps(
            original, sort_keys=True, ensure_ascii=True, separators=(",", ":")
        ).encode()
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), PHASE_2A_SHA256)

    def test_requested_state_schemes_and_schema_version(self) -> None:
        self.assertEqual(DATA["schema_version"], "1.0.0")
        self.assertEqual({r["scheme_id"] for r in DATA["schemes"]}, CENTRAL_IDS | WB_IDS)
        state_records = [r for r in DATA["schemes"] if r["government_level"] == "state"]
        self.assertEqual({r["scheme_id"] for r in state_records}, WB_IDS)
        self.assertTrue(all(r["state"] == "West Bengal" for r in state_records))
        self.assertEqual(sum(r["government_level"] == "central" for r in DATA["schemes"]), 5)

    def test_state_records_have_dated_located_evidence(self) -> None:
        for record in DATA["schemes"][5:]:
            with self.subTest(scheme=record["scheme_id"]):
                self.assertEqual(record["verification_date"], "2026-11-14")
                self.assertTrue(record["source_passage"].strip())
                for source in record["sources"]:
                    self.assertIn("Access:", source["sections"])
                    if source["url"] != record["official_source_url"]:
                        self.assertRegex(source["sections"], r'Exact evidence: "[^"]+"')
                for field in FACT_FIELDS:
                    fact = record[field]
                    if fact["status"] in {"partial", "unknown"}:
                        self.assertIn("unknown", fact["note"].lower())

    def test_unresolved_policy_is_not_labelled_verified(self) -> None:
        records = {r["scheme_id"]: r for r in DATA["schemes"]}
        self.assertEqual(records["IN-WB-LAKSHMIR-BHANDAR"]["benefits"]["status"], "unknown")
        self.assertEqual(records["IN-WB-KANYASHREE"]["eligibility_conditions"]["status"], "partial")
        self.assertEqual(records["IN-WB-KRISHAK-BANDHU"]["required_documents"]["status"], "partial")
        self.assertEqual(records["IN-WB-SWASTHYA-SATHI"]["exclusions"]["status"], "partial")

    def test_state_record_provenance_rejections(self) -> None:
        mutations = {
            "national scope on state scheme": lambda r: r.update(state="all_india"),
            "duplicate evidence ID": lambda r: r["sources"].append(deepcopy(r["sources"][0])),
            "unresolved evidence": lambda r: r["eligibility_conditions"].update(source_ids=["missing"]),
            "source date mismatch": lambda r: r["sources"][0].update(accessed_on="2026-11-13"),
            "deceptive host": lambda r: r["sources"][0].update(url="https://wb.gov.in.example.com/source"),
        }
        for label, mutate in mutations.items():
            with self.subTest(case=label):
                data = deepcopy(DATA)
                mutate(data["schemes"][5])
                with self.assertRaises(ValueError):
                    validate_dataset(data)


if __name__ == "__main__":
    unittest.main()
