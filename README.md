# AdhikarAI

AdhikarAI helps people discover relevant government schemes and understand documented application criteria through source-cited information.

## How it works

- **Local semantic retrieval:** searches curated, source-cited scheme records and available PDF chunks using sentence-transformer embeddings and ChromaDB.
- **Evidence-only Q&A:** the LLM only selects evidence IDs, which are validated locally; it never writes free-form claims for the user.
- **Rule-based eligibility:** deterministic checks evaluate documented criteria with no LLM and preserve unknowns rather than assuming eligibility.
- **Session-only personal data:** uploaded documents, profile details, and eligibility answers stay in session memory rather than being saved or indexed. Optional voice transcription sends audio to Groq; Q&A sends the submitted question and retrieved evidence.

## Limitations

- Coverage is limited to **ten schemes**: five Central and five West Bengal.
- The embedding model is English-oriented; matching in other languages may be limited.
- No OCR: scanned or image-only documents are not supported for personal-document matching.
- **Four schemes always return insufficient information:** PM-KISAN, Lakshmir Bhandar, Krishak Bandhu, and Swasthya Sathi, because their recorded criteria are incomplete or unresolved. See the [eligibility audit](docs/eligibility-audit.md).

## Results

Evaluation results will be added here.

## Quick start

### Install

Use Python 3.11 or newer. Run these commands from the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

On macOS/Linux, activate with `source .venv/bin/activate` instead.
The editable installation installs the package and its essential dependencies
from [requirements.txt](requirements.txt). Tests use Python's built-in `unittest`.
[.env.example](.env.example) documents optional Groq configuration for Q&A and voice;
copying it to `.env` is optional.

### Run

```powershell
python -m streamlit run src/adhikar_ai/app.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501).

### Test

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

The app tests render the real Streamlit page and verify search, combined filters,
empty results, dataset errors, and preservation of citations and uncertainty. Dataset tests validate the
JSON Schema, provenance references, dates, IDs, unknowns, and malformed records.

## Further reading

See [Architecture](docs/architecture.md) for PDF extraction, semantic retrieval, grounded Q&A, document uploads, voice input, and profiles.

## Scheme discovery

Government scheme discovery with a Streamlit app backed by ten curated schemes
(five Central and five West Bengal). Search by name, ID, benefits, or keywords and
combine government-level, coverage, and category filters. Search is case-insensitive;
all entered words must occur in a record. Empty search shows all records matching
the filters. Coverage selects the recorded scope; All India includes West Bengal.
Each result preserves evidence statuses, uncertainty notes, field-level source links,
official excerpts, and source access/verification dates. No API keys are required.
Semantic mode also retrieves related schemes and available PDF chunks locally.
Optional Phase 3C Q&A uses Groq to select cited evidence. Keyword and semantic search
remain local and require no API key. Eligibility mode deterministically checks
documented new-application criteria; it does not approve entitlement.

## Documented eligibility checks

Choose **Eligibility**, select a scheme, enter only the relevant facts, then click
**Check criteria**. Missing answers default to Unknown. Results are **meets criteria**,
**does not meet criteria**, or **insufficient information**, with per-condition source
links, exact recorded evidence and uncertainty notes. This uses no LLM or semantic
similarity. Age means completed years at application; APY additionally asks whether
an age-40 application is on the 40th birthday. Renewals, continuation and claims
return insufficient information because only new-application rules were audited.

The [ten-scheme audit](docs/eligibility-audit.md) identifies what can safely be
checked. PM-KISAN and the unresolved historical/transition records always return
insufficient information. Partial records cannot receive a positive determination;
an explicit, unambiguous failed requirement can still explain a negative result
for active checks. Unknown exclusions, income conflicts or birthday boundaries are
never filled in with assumptions. Meets criteria only describes the audited
checks, not a guarantee that every current official condition has been met.

Answers and results remain in session memory and are not written to files, indexed,
logged or sent to Groq. **Clear eligibility answers** removes this form's session
answers and displayed result. No names, identity/account numbers or exact birth dates
are requested. A remote Streamlit server would receive form values in memory.
The public evidence fingerprint in `eligibility_audit.json` stops checks when source
records change; re-audit rules and tests before updating it. Run all tests with
`python -m unittest discover -s tests -v`.

## Structure

```text
data/
  raw/                  Original local datasets (ignored by Git)
  processed/            Prepared local datasets (ignored by Git)
notebooks/              Exploratory notebooks
src/adhikar_ai/
  __init__.py           Python package
  app.py                Streamlit application entry point
tests/
  test_app.py            Basic application smoke test
.env.example            Configuration documentation; no secrets
.gitignore              Local data, secrets, and cache exclusions
pyproject.toml          Package and installation configuration
requirements.txt        Streamlit and PyMuPDF dependencies
```

Keep local datasets under `data/`; directory placeholders and the curated public
[schemes.json](data/processed/schemes.json) seed are tracked; other data is ignored.

## Scheme dataset

[JSON Schema](schemas/schemes.schema.json) defines the versioned record contract.
[Official sources and verification notes](docs/scheme_sources.md) document the
ten schemes, evidence, source conflicts and unknown fields. Verification date:
2026-11-14. Records are descriptive and may be partial, not executable eligibility
rules. Phase 3B adds local embeddings and retrieval; Phase 3C adds optional grounded
Q&A. A rule-based eligibility engine checks audited new-application criteria; see
[documented eligibility checks](#documented-eligibility-checks).

Phase 2B adds Lakshmir Bhandar, Kanyashree, Rupashree, Krishak Bandhu and
Swasthya Sathi using the unchanged schema. Exact excerpts and retrieval limitations
are recorded alongside each source. Some terms remain historical, partial or unknown,
including Lakshmir Bhandar's current entitlement following migration notices.
Regression tests preserve the original five records and validate the 5+5 composition.
