# Eligibility rule audit

Scope: the ten existing records verified on 2026-11-14, not a new verification
of current law. Deterministic checks compare self-reported facts with recorded
new-application criteria. They do not approve benefits, renewals or claims.
All decisions retain the original field evidence and source references.

| Scheme | Supported checks | Deliberately unresolved / excluded |
| --- | --- | --- |
| PMSBY | Individual participating bank/post-office account, entry age 18–70, one account, auto-debit consent, sufficient premium balance | Entry/termination wording conflicts near 70; completed ages 69–70 require provider clarification. Suicide/hospitalisation are claim exclusions, not applicant disqualifiers. |
| PMJJBY | New-entry age 18–50, individual participating account, one account, auto-debit, sufficient premium balance | Age 55 is continuation termination, not new-entry eligibility. 30-day death exclusion concerns claims. |
| APY | Indian citizenship, savings account, entry age 18 through 40th birthday, contributions to 60, no existing APY account; current new applicants must never have paid income tax | At completed age 40, exact birthday confirmation is required. Historical/continuing tax exemptions are not evaluated as new applications. |
| PM-SYM | Age 18–40, unorganised worker, monthly income ≤15,000; EPF, ESIC, income tax and another government pension exclusions | NPS wording differs between sources. Any NPS coverage needs clarification; incomplete exclusions prevent a positive overall determination. |
| PM-KISAN | Published landholding, eKYC and exclusion evidence displayed | Record explicitly says not to decide eligibility from this summary: full exclusion list, professional categories and land-transfer exceptions missing. Always insufficient information. |
| Lakshmir Bhandar | Historical evidence displayed | Do not apply 2023 rules after unresolved 2026 migration. Always insufficient information. |
| Kanyashree | Published unmarried, West Bengal residence, girl applicant, recognised education and own-account conditions | No income cap inferred: FAQ/calendar conflict. K1/K2 birthday cutoffs, disability and special exceptions incomplete; no positive overall determination. |
| Rupashree | Woman, age ≥18 at application, unmarried, first marriage, groom ≥21; WB birth OR five-year residence OR permanent-resident parents; family income ≤150,000/year; active sole NEFT account with IFSC/MICR; no prior assistance | Additional exclusions and possible amendments unknown, so no positive overall determination. Submission window is an application step, not an invented eligibility rejection. |
| Krishak Bandhu | Legacy income and death evidence displayed separately | Current enrolment changes, tenancy exceptions and exact death-age boundaries unknown. No death age applied to income component. Always insufficient information. |
| Swasthya Sathi | Published residency and health-cover restrictions displayed | Transition/opt-out and current statewide rules unknown. Always insufficient information. |

For active checks, a known failure of an unambiguous documented requirement takes
precedence over unknown answers. Otherwise any missing input or unresolved rule
means **insufficient information**. **Meets criteria** means only that every
implemented, documented new-entry check passes in a record with verified
eligibility/exclusions; it is not a complete current entitlement guarantee.
Suspended records never yield a negative or positive decision from historical rules.
Unknown is distinct from No and zero. No identity/account numbers are requested.

The UI shows exact eligibility/exclusion text, notes, verification date and
citations alongside decisions. The audited evidence snapshot is pinned so changed
records require re-audit before rules can run. Sensitive answers and results stay
in Streamlit session memory, with a clear button; they never enter the vector index,
files, logs, URLs or an LLM request.
