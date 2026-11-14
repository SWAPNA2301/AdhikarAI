# AdhikarAI

Government scheme discovery, starting with a minimal Phase 1 Streamlit app.
Search is disabled; no eligibility assessments or simulated results are included.
A curated dataset of ten schemes (five Central and five West Bengal) is available for development
but is not loaded into the application. No API keys are required.

## Install

Use Python 3.11 or newer. Run these commands from the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

On macOS/Linux, activate with `source .venv/bin/activate` instead.
The editable installation installs the package and its essential dependencies
from [requirements.txt](requirements.txt). Tests use Python's built-in `unittest`.
[.env.example](.env.example) documents that no configuration is needed yet;
copying it to `.env` is optional.

## Run

```powershell
python -m streamlit run src/adhikar_ai/app.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501).

## Test

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

The smoke test renders the real Streamlit page and verifies its title,
placeholder message, and disabled search controls. Dataset tests validate the
JSON Schema, provenance references, dates, IDs, unknowns, and malformed records.

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
rules. No RAG, embeddings, LLM integration or eligibility engine is implemented.

Phase 2B adds Lakshmir Bhandar, Kanyashree, Rupashree, Krishak Bandhu and
Swasthya Sathi using the unchanged schema. Exact excerpts and retrieval limitations
are recorded alongside each source. Some terms remain historical, partial or unknown,
including Lakshmir Bhandar's current entitlement following migration notices.
Regression tests preserve the original five records and validate the 5+5 composition.

## Phase 3A: PDF text extraction

Install or update dependencies with `python -m pip install -e .`, then run from
the project root (requires internet access):

```powershell
python -m adhikar_ai.pdf_processing
```

The [official PDF manifest](docs/pdf_sources.json) lists three government documents.
The command saves original PDFs under `data/raw/pdfs/` and writes
`data/processed/pdf_chunks.json`. These local outputs remain ignored by Git.
Optional arguments: `--manifest`, `--raw-dir`, and `--output`.
Re-running downloads fresh copies and replaces the output; failures are recorded
in the JSON, printed, and cause a nonzero exit code. Downloads are capped at 25 MiB
per document with a 45-second socket timeout.

[PDF processing](src/adhikar_ai/pdf_processing.py) uses PyMuPDF's text layer,
normalizes Unicode and whitespace, and splits each page into at most 1,200-character
chunks with 150-character overlap. Chunk boundaries prefer whitespace; a long word
may be split. Every chunk preserves the original and resolved URL, title, publisher,
retrieval timestamp, document SHA-256, one-based page number, page quality status,
and offsets in the cleaned page text. The output also includes PDF metadata,
extractor version, per-document errors and per-page quality flags.

Empty text layers are flagged for review as potentially scanned or blank. Very short
text and replacement characters are flagged as suspect. These checks are heuristics:
garbled legacy fonts, missing text in images and layout errors may escape detection.
No OCR, translation or invented content is added. Flagged nonempty text remains
available with its warning. Text extraction is not policy verification; historical
documents do not establish current eligibility. The ten scheme records are unchanged.

Run all tests with the command in the Test section. The
[PDF tests](tests/test_pdf_processing.py) are offline and cover text cleanup,
chunk coverage, provenance, blank/image-only pages, corrupt/encrypted PDFs,
non-PDF responses and preservation of all ten scheme records.
