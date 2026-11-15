"""Audited, deterministic new-application checks. No network, model or profile storage."""
import hashlib
import json
import math
from pathlib import Path

MEETS = "meets criteria"
FAILS = "does not meet criteria"
UNKNOWN = "insufficient information"
AUDIT_FIELDS = ("eligibility_conditions", "exclusions", "benefits", "verification_notes",
                "sources", "verification_date")
AUDIT = json.loads(Path(__file__).with_name("eligibility_audit.json").read_text(encoding="utf-8"))
SUSPENDED = {
    "IN-PM-KISAN": "The record explicitly prohibits decisions from this incomplete exclusion summary.",
    "IN-WB-LAKSHMIR-BHANDAR": "Historical rules cannot establish eligibility after the unresolved migration.",
    "IN-WB-KRISHAK-BANDHU": "Current income enrolment rules and death-component boundaries are unresolved.",
    "IN-WB-SWASTHYA-SATHI": "Current statewide transition and opt-out conditions are unresolved.",
}

# Field kind, label. No identifying numbers or exact date of birth are collected.
FIELDS = {
    "age": ("number", "Completed age at application (years)"),
    "individual_account": ("bool", "Individual account at a participating bank/post office?"),
    "one_account": ("bool", "Enrolling through only one account for this scheme?"),
    "auto_debit": ("bool", "Consent to premium auto-debit?"),
    "premium_balance": ("bool", "Sufficient balance for the applicable scheme premium?"),
    "citizen": ("bool", "Indian citizen?"),
    "savings_account": ("bool", "Savings bank/post-office account?"),
    "birthday_40": ("bool", "If completed age is 40: applying on the 40th birthday itself?"),
    "contributions": ("bool", "Will make prescribed contributions until age 60?"),
    "ever_taxpayer": ("bool", "Are you or have you ever been an income-tax payer?"),
    "existing_apy": ("bool", "Already have an APY account?"),
    "unorganised": ("bool", "Unorganised worker?"),
    "monthly_income": ("number", "Monthly income (INR)"),
    "epf": ("bool", "Covered by EPF?"),
    "esic": ("bool", "Covered by ESIC?"),
    "nps": ("bool", "Covered by any NPS arrangement?"),
    "taxpayer": ("bool", "Income-tax payer?"),
    "government_pension": ("bool", "Receiving another government pension?"),
    "female": ("bool", "Woman/girl applicant as described in the source?"),
    "unmarried": ("bool", "Unmarried at application?"),
    "wb_resident": ("bool", "Resident of West Bengal?"),
    "education": ("bool", "Attending recognised education?"),
    "own_account": ("bool", "Own bank account?"),
    "first_marriage": ("bool", "Proposing first marriage?"),
    "groom_age": ("number", "Groom's completed age (years)"),
    "wb_born": ("bool", "Born in West Bengal?"),
    "wb_five_years": ("bool", "Resident in West Bengal for at least five years?"),
    "wb_parents": ("bool", "Parents permanent residents of West Bengal?"),
    "annual_family_income": ("number", "Annual family income (INR)"),
    "rupashree_bank": ("bool", "Active sole-holder bank account supporting NEFT, with IFSC and MICR?"),
    "prior_rupashree": ("bool", "Already received Rupashree assistance?"),
}
SCHEME_FIELDS = {
    "IN-PMSBY": ["age", "individual_account", "one_account", "auto_debit", "premium_balance"],
    "IN-PMJJBY": ["age", "individual_account", "one_account", "auto_debit", "premium_balance"],
    "IN-APY": ["age", "birthday_40", "citizen", "savings_account", "contributions", "ever_taxpayer", "existing_apy"],
    "IN-PM-SYM": ["age", "unorganised", "monthly_income", "epf", "esic", "nps", "taxpayer", "government_pension"],
    "IN-WB-KANYASHREE": ["female", "unmarried", "wb_resident", "education", "own_account"],
    "IN-WB-RUPASHREE": ["age", "female", "unmarried", "first_marriage", "groom_age", "wb_born",
                         "wb_five_years", "wb_parents", "annual_family_income", "rupashree_bank", "prior_rupashree"],
}


def fingerprint(scheme):
    return hashlib.sha256(json.dumps({k: scheme.get(k) for k in AUDIT_FIELDS},
                                    sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def evaluate(scheme, profile, new_application=True):
    """Fail closed for changed sources, historical rules, malformed or missing inputs."""
    checks = []

    def add(label, value, field="eligibility_conditions"):
        fact = scheme[field]
        ids = fact["source_ids"]
        sources = [s for s in scheme["sources"] if s["source_id"] in ids]
        checks.append({"criterion": label, "outcome": MEETS if value is True else FAILS if value is False else UNKNOWN,
                       "evidence": list(fact["items"]), "note": fact["note"], "sources": sources})

    def yes(key, required=True, field="eligibility_conditions"):
        value = profile.get(key)
        add(FIELDS[key][1] + (" Required: Yes." if required else " Required: No."),
            value == required if type(value) is bool else None, field)

    def number(key):
        value = profile.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            return None
        if key in ("age", "groom_age") and (value > 120 or value != int(value)):
            return None
        return value

    def band(key, low, high):
        value = number(key)
        add(f"{FIELDS[key][1]}: {low} to {high}, inclusive.",
            low <= value <= high if value is not None else None)

    sid = scheme["scheme_id"]
    if AUDIT.get(sid) != fingerprint(scheme):
        add("Source evidence changed or has not been audited; re-audit required.", None)
    elif new_application is not True:
        add("Only new applications are checked; renewals, continuation and claims require separate rules.", None)
    elif sid in SUSPENDED:
        add(SUSPENDED[sid], None)
        add(scheme["exclusions"]["note"], None, "exclusions")
    else:
        if sid in ("IN-PMSBY", "IN-PMJJBY"):
            age = number("age")
            if sid == "IN-PMSBY" and age is not None and 69 <= age <= 70:
                add("Entry age and termination near age 70 conflict; bank clarification required.", None, "exclusions")
            else:
                band("age", 18, 70 if sid == "IN-PMSBY" else 50)
            for key in ("individual_account", "one_account", "auto_debit"):
                yes(key)
            yes("premium_balance", field="exclusions")
        elif sid == "IN-APY":
            age = number("age")
            if age == 40:
                yes("birthday_40")
            else:
                band("age", 18, 40)
            for key in ("citizen", "savings_account", "contributions"):
                yes(key)
            for key in ("ever_taxpayer", "existing_apy"):
                yes(key, False, "exclusions")
        elif sid == "IN-PM-SYM":
            band("age", 18, 40)
            yes("unorganised")
            band("monthly_income", 0, 15000)
            for key in ("epf", "esic", "taxpayer", "government_pension"):
                yes(key, False, "exclusions")
            add("NPS coverage: none; other NPS arrangements have unresolved treatment.",
                True if profile.get("nps") is False else None, "exclusions")
        elif sid == "IN-WB-KANYASHREE":
            for key in SCHEME_FIELDS[sid]:
                yes(key)
        elif sid == "IN-WB-RUPASHREE":
            for key in ("female", "unmarried", "first_marriage", "rupashree_bank"):
                yes(key)
            for key, minimum in (("age", 18), ("groom_age", 21)):
                value = number(key)
                add(f"{FIELDS[key][1]}: at least {minimum}.", value >= minimum if value is not None else None)
            values = [profile.get(key) for key in ("wb_born", "wb_five_years", "wb_parents")]
            add("Born in WB OR resident for five years OR parents permanent residents.",
                True if any(v is True for v in values) else False if all(v is False for v in values) else None)
            band("annual_family_income", 0, 150000)
            yes("prior_rupashree", False, "exclusions")
        for field in ("eligibility_conditions", "exclusions"):
            if scheme[field]["status"] != "verified":
                add("Unresolved source limitation: " + scheme[field]["note"], None, field)
    outcome = FAILS if any(c["outcome"] == FAILS for c in checks) else (
        MEETS if checks and all(c["outcome"] == MEETS for c in checks) else UNKNOWN)
    return {"outcome": outcome, "checks": checks, "verification_date": scheme["verification_date"]}
