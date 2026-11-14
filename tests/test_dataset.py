"""Offline structural and provenance checks; these do not reverify live policy."""

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/schemes.schema.json").read_text(encoding="utf-8"))
DATA = json.loads((ROOT / "data/processed/schemes.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
FACT_FIELDS = (
    "eligibility_conditions", "exclusions", "benefits",
    "required_documents", "application_process",
)


def validate_dataset(data: dict) -> None:
    """Check schema plus cross-record and provenance invariants."""
    VALIDATOR.validate(data)
    ids = [record["scheme_id"] for record in data["schemes"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate scheme ID")
    for record in data["schemes"]:
        verified = date.fromisoformat(record["verification_date"])
        if verified > date.today():
            raise ValueError("Verification date is in the future")
        effective = record["effective_date"]
        if effective != "unknown" and date.fromisoformat(effective) > verified:
            raise ValueError("Effective date is after verification")
        sources = record["sources"]
        source_ids = [source["source_id"] for source in sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Duplicate source ID")
        if record["official_source_url"] not in {s["url"] for s in sources}:
            raise ValueError("Primary source is missing from sources")
        for source in sources:
            parsed = urlsplit(source["url"])
            host = parsed.hostname or ""
            if parsed.scheme != "https" or not (
                host.endswith(".gov.in") or host.endswith(".nic.in")
                or host == "pfrda.org.in" or host == "www.pfrda.org.in"
            ):
                raise ValueError("Source must be an approved official host")
            if date.fromisoformat(source["accessed_on"]) != verified:
                raise ValueError("Source access and verification dates differ")
        for field in FACT_FIELDS:
            if not set(record[field]["source_ids"]).issubset(source_ids):
                raise ValueError("Unresolved source reference")
        if record["government_level"] == "state" and record["state"] == "all_india":
            raise ValueError("State scheme must name its state")


class DatasetTest(unittest.TestCase):
    def test_schema_and_ten_seed_records(self) -> None:
        Draft202012Validator.check_schema(SCHEMA)
        validate_dataset(DATA)
        self.assertEqual(len(DATA["schemes"]), 10)

    def test_rejects_invalid_records(self) -> None:
        mutations = {
            "missing name": lambda r: r.pop("scheme_name"),
            "invalid date": lambda r: r.update(verification_date="2026-02-30"),
            "unknown with invented detail": lambda r: r.update(
                benefits={"status": "unknown", "items": ["invented"], "source_ids": [], "note": "unknown"}
            ),
            "unsupported claim": lambda r: r["benefits"].update(source_ids=["missing"]),
            "unofficial source": lambda r: r["sources"][0].update(url="https://example.com"),
            "empty verified claim": lambda r: r["benefits"].update(items=[]),
            "unknown property": lambda r: r.update(eligibility_result=True),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                data = deepcopy(DATA)
                mutate(data["schemes"][0])
                with self.assertRaises((ValidationError, ValueError)):
                    validate_dataset(data)

    def test_rejects_duplicate_ids(self) -> None:
        data = deepcopy(DATA)
        data["schemes"].append(deepcopy(data["schemes"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate scheme ID"):
            validate_dataset(data)


if __name__ == "__main__":
    unittest.main()
