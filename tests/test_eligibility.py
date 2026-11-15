"""Audited eligibility boundaries and fail-closed decisions; no model or network."""
import copy
import json
from pathlib import Path
import unittest

from adhikar_ai import eligibility as e


class EligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(e.__file__).resolve().parents[2] / "data/processed/schemes.json"
        cls.schemes = {s["scheme_id"]: s for s in json.loads(path.read_text(encoding="utf-8"))["schemes"]}

    def result(self, sid, profile, **kwargs):
        return e.evaluate(self.schemes[sid], profile, **kwargs)

    def insurance(self, age=30):
        return dict(age=age, individual_account=True, one_account=True, auto_debit=True, premium_balance=True)

    def apy(self, age=30):
        return dict(age=age, citizen=True, savings_account=True, contributions=True,
                    ever_taxpayer=False, existing_apy=False)

    def test_ten_schemes_audited_unknown_by_default_with_citations(self):
        self.assertEqual(set(self.schemes), set(e.AUDIT))
        for sid, scheme in self.schemes.items():
            with self.subTest(sid=sid):
                self.assertEqual(e.fingerprint(scheme), e.AUDIT[sid])
                result = self.result(sid, {})
                self.assertEqual(result["outcome"], e.UNKNOWN)
                self.assertTrue(result["checks"])
                for check in result["checks"]:
                    self.assertTrue(check["sources"])
                    for source in check["sources"]:
                        self.assertIn(source, scheme["sources"])
                    for text in check["evidence"]:
                        self.assertIn(text, scheme["eligibility_conditions"]["items"] + scheme["exclusions"]["items"])

    def test_insurance_age_boundaries_and_claims_not_entry_rules(self):
        for sid, cases in {
            "IN-PMSBY": [(17, e.FAILS), (18, e.MEETS), (68, e.MEETS), (69, e.UNKNOWN), (70, e.UNKNOWN), (71, e.FAILS)],
            "IN-PMJJBY": [(17, e.FAILS), (18, e.MEETS), (50, e.MEETS), (51, e.FAILS), (55, e.FAILS)],
        }.items():
            for age, expected in cases:
                with self.subTest(sid=sid, age=age):
                    self.assertEqual(self.result(sid, self.insurance(age))["outcome"], expected)
        for key in ("individual_account", "one_account", "auto_debit", "premium_balance"):
            self.assertEqual(self.result("IN-PMJJBY", {**self.insurance(), key: False})["outcome"], e.FAILS)

    def test_apy_birthday_and_tax_exclusion_only_for_new_applications(self):
        for age, expected in [(17, e.FAILS), (18, e.MEETS), (39, e.MEETS), (40, e.UNKNOWN), (41, e.FAILS)]:
            self.assertEqual(self.result("IN-APY", self.apy(age))["outcome"], expected)
        self.assertEqual(self.result("IN-APY", {**self.apy(40), "birthday_40": True})["outcome"], e.MEETS)
        self.assertEqual(self.result("IN-APY", {**self.apy(40), "birthday_40": False})["outcome"], e.FAILS)
        for key in ("ever_taxpayer", "existing_apy"):
            p = {**self.apy(), key: True}
            self.assertEqual(self.result("IN-APY", p)["outcome"], e.FAILS)
            self.assertEqual(self.result("IN-APY", p, new_application=False)["outcome"], e.UNKNOWN)

    def test_missing_invalid_and_false_values_are_distinct(self):
        for value in (None, "30", True, -1, float("nan"), float("inf"), 30.5, 200):
            self.assertEqual(self.result("IN-PMJJBY", self.insurance(value))["outcome"], e.UNKNOWN)
        self.assertEqual(self.result("IN-PMJJBY", {**self.insurance(), "auto_debit": "yes"})["outcome"], e.UNKNOWN)
        # A definite failed condition still explains a negative result when other answers are missing.
        self.assertEqual(self.result("IN-PMJJBY", {"age": 17})["outcome"], e.FAILS)

    def test_pmsym_income_and_unresolved_nps(self):
        p = dict(age=40, unorganised=True, monthly_income=15000, epf=False,
                 esic=False, nps=False, taxpayer=False, government_pension=False)
        for income, expected in [(0, e.UNKNOWN), (15000, e.UNKNOWN), (15001, e.FAILS)]:
            self.assertEqual(self.result("IN-PM-SYM", {**p, "monthly_income": income})["outcome"], expected)
        self.assertEqual(self.result("IN-PM-SYM", {**p, "nps": True})["outcome"], e.UNKNOWN)
        for key in ("epf", "esic", "taxpayer", "government_pension"):
            self.assertEqual(self.result("IN-PM-SYM", {**p, key: True})["outcome"], e.FAILS)

    def test_rupashree_or_residency_income_and_age(self):
        p = dict(age=18, female=True, unmarried=True, first_marriage=True, groom_age=21,
                 wb_born=False, wb_five_years=False, wb_parents=True, annual_family_income=150000,
                 rupashree_bank=True, prior_rupashree=False)
        self.assertEqual(self.result("IN-WB-RUPASHREE", p)["outcome"], e.UNKNOWN)
        for key in ("wb_born", "wb_five_years", "wb_parents"):
            r = self.result("IN-WB-RUPASHREE", {**p, "wb_born": None, "wb_five_years": None,
                                               "wb_parents": None, key: True})
            self.assertEqual(next(c for c in r["checks"] if " OR " in c["criterion"])["outcome"], e.MEETS)
        for changes in ({"age": 17}, {"groom_age": 20}, {"annual_family_income": 150001},
                        {"wb_parents": False}, {"prior_rupashree": True}, {"first_marriage": False}):
            self.assertEqual(self.result("IN-WB-RUPASHREE", {**p, **changes})["outcome"], e.FAILS)
        r = self.result("IN-WB-RUPASHREE", {**p, "wb_parents": None})
        self.assertEqual(next(c for c in r["checks"] if " OR " in c["criterion"])["outcome"], e.UNKNOWN)

    def test_kanyashree_never_infers_income_age_or_disability_rules(self):
        p = {key: True for key in e.SCHEME_FIELDS["IN-WB-KANYASHREE"]}
        for income in (0, 120000, 999999):
            self.assertEqual(self.result("IN-WB-KANYASHREE", {**p, "annual_family_income": income})["outcome"], e.UNKNOWN)
        self.assertEqual(self.result("IN-WB-KANYASHREE", {**p, "unmarried": False})["outcome"], e.FAILS)

    def test_suspended_sources_and_evidence_changes_fail_closed(self):
        for sid in e.SUSPENDED:
            self.assertEqual(self.result(sid, {k: False for k in e.FIELDS})["outcome"], e.UNKNOWN)
            self.assertEqual(self.result(sid, {k: True for k in e.FIELDS})["outcome"], e.UNKNOWN)
            self.assertNotIn(sid, e.SCHEME_FIELDS)
        scheme = copy.deepcopy(self.schemes["IN-PMJJBY"])
        scheme["eligibility_conditions"]["items"][0] = "Changed rules"
        self.assertEqual(e.evaluate(scheme, self.insurance())["outcome"], e.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
