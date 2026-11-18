# Architecture

[Back to README](../README.md) · [Test instructions](../README.md#test)

## Phase 3A: PDF text extraction

Install or update dependencies with `python -m pip install -e .`, then run from
the project root (requires internet access):

```powershell
python -m adhikar_ai.pdf_processing
```

The [official PDF manifest](pdf_sources.json) lists three government documents.
The command saves original PDFs under `data/raw/pdfs/` and writes
`data/processed/pdf_chunks.json`. These local outputs remain ignored by Git.
Optional arguments: `--manifest`, `--raw-dir`, and `--output`.
Re-running downloads fresh copies and replaces the output; failures are recorded
in the JSON, printed, and cause a nonzero exit code. Downloads are capped at 25 MiB
per document with a 45-second socket timeout.

[PDF processing](../src/adhikar_ai/pdf_processing.py) uses PyMuPDF's text layer,
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
[PDF tests](../tests/test_pdf_processing.py) are offline and cover text cleanup,
chunk coverage, provenance, blank/image-only pages, corrupt/encrypted PDFs,
non-PDF responses and preservation of all ten scheme records.

## Phase 3B: local semantic search

Install updated dependencies with `python -m pip install -e . -r requirements-dev.txt`.
In Streamlit, choose **Semantic**, click **Build / update local index**, then enter
a question or description. Select 1–20 top matches. Existing keyword search is
unchanged. Scheme filters combine with semantic search; PDF chunks have no scheme
taxonomy, so selecting a non-All filter excludes them.

You can also build and query from the project root:

```powershell
python -m adhikar_ai.semantic_search --query "financial support for retirement"
```

The [indexer](../src/adhikar_ai/semantic_search.py) uses
`sentence-transformers/all-MiniLM-L6-v2` on CPU. The first build downloads the free
model; subsequent runs prefer the local cache. No text is sent to an inference API.
The model cache lives in `data/models/` and Chroma persists automatically in
`data/chroma/`; both are ignored by Git. Chroma telemetry is disabled.

All ten scheme records are indexed with their complete evidence payloads.
If `data/processed/pdf_chunks.json` exists, its nonempty chunks are included with
original/resolved URLs, page numbers, extraction warnings, timestamps, hashes,
and offsets. A missing PDF file is allowed and the UI reports the available count.
Run Phase 3A first to obtain PDF chunks, then update the index.

Long records are split into model-sized token windows; normalized window embeddings
are averaged and normalized again, avoiding silent loss of the end of a record.
Retrieval uses cosine distance (lower is closer), not a confidence score or an
eligibility judgment. This small English embedding model may perform poorly on
other languages and can return weak matches for unrelated questions.

Index collections are keyed by source contents, metadata, model name, and encoding
recipe. Changed sources require a new build; incomplete builds cannot be searched.
Rebuilding unchanged sources reuses the stored embeddings. Older source snapshots
remain on disk but are never queried for a different snapshot.

The [semantic tests](../tests/test_semantic_search.py) use real local Chroma with
deterministic test embeddings, so the test suite needs no model download or network.
They cover persistence, ranking, combined filters, stale/incomplete indexes,
idempotent builds, and PDF provenance. App tests cover semantic results and citations.

## Phase 3C: optional grounded Q&A

Set `GROQ_API_KEY` in the project-root `.env` or server process environment.
The process environment takes precedence, including an explicitly empty value.
The local file is read without interpolation or logging its contents. Do not paste credentials into the app,
source files, chat, or the tracked [.env.example](../.env.example), which must remain blank.
The ignored `.env` is read using the declared `python-dotenv` dependency.
Without the key, Q&A is disabled and semantic search still works.

Choose **Q&A**, enter a question in the search box, and click **Answer from sources**.
Build the local index in Semantic or Q&A mode first if needed. Existing filters and
top-match limits apply. Only the explicit answer button calls Groq; normal search
and reruns do not make an LLM request. Your question and a bounded set of retrieved
evidence are sent to Groq. Provider account quotas/pricing apply.

The [RAG module](../src/adhikar_ai/rag.py) calls Groq's
[chat-completions API](https://console.groq.com/docs/api-reference) using
`llama-3.3-70b-versatile`, JSON mode, and a 30-second timeout.
For this conservative first version, the LLM selects evidence IDs instead of
generating free-form claims. Local validation rejects unknown IDs, additional
claim fields, invalid JSON/types, and incomplete responses. The app displays only
the exact selected stored passages, field-level citations, source dates, and
uncertainty notes. PDF answers include page numbers; suspect extraction text is
excluded from Q&A but remains visible in semantic results.

Missing evidence, an unsupported response, or model-reported gaps produce an
explicit insufficient-information message. Supported passages may accompany a
partial answer. This prevents new model-written claims from reaching the UI;
it does not prove that sources are current or that the model selected every
relevant passage. Personal eligibility decisions are outside scope.

The API key is used only in the authorization header. Provider error bodies and
exceptions are not displayed or logged, and responses are not persisted. Authentication,
network, or provider failures show a generic message while retrieval remains usable.
The [mocked RAG tests](../tests/test_rag.py) and [UI tests](../tests/test_app.py) cover
supported answers, invalid claims/citations, insufficient evidence, absent keys,
provider failures, secret-safe errors, and explicit submission. Run the full suite
with `python -m unittest discover -s tests -v`; tests make no Groq requests.

## Find schemes from personal documents

Semantic retrieval discards results with cosine distance above **0.82** and shows
**No sufficiently relevant schemes found** when none remain. Empty queries prompt
for input; obvious keyboard noise is rejected before loading the model. The cutoff
applies to semantic search, Q&A retrieval, document matching and profiles, preserving
filters and source citations. Configure `SEMANTIC_MAX_DISTANCE` in the server's
environment (finite number from 0 to 2); lower values are stricter. For example,
in PowerShell use `$env:SEMANTIC_MAX_DISTANCE = "0.80"` before starting Streamlit.
Python callers can override it with `search(..., max_distance=0.80)`.
This setting is read from the process environment, not the Groq `.env` file.
See [measurements and limitations](semantic-calibration.md) and rerun
`python tests/calibrate_semantic.py` when the corpus or embedding model changes.

Choose **My documents**. Upload one text-based PDF or UTF-8 TXT file (up to 5 MB,
20 PDF pages, and 20,000 extracted characters), review/edit the extracted text, and
click **Find potential schemes**. You can also type a short description without
uploading anything. Scanned/image-only, encrypted, malformed, or oversized files
produce a helpful message; OCR is not included.

Matching uses the existing local semantic index and returns up to five scheme
records. Build the index in Semantic mode first. Choosing another state excludes
West Bengal schemes; West Bengal includes national schemes. These are similarity
suggestions, not eligibility determinations: review the published conditions and
exclusions. The dataset covers only ten schemes.

Each result includes **Apply / official instructions** links from that record's
cited application sources, alongside the application process and evidence details.
These may be guidance pages rather than online forms; some schemes require visiting
a bank or office. URLs are never guessed and applications are not submitted by the app.

Personal files and extracted text stay in the local Streamlit process/session memory;
they are not written to disk, added to Chroma, or sent to Groq. Use **Clear documents
and details** to clear the upload and text from the UI session. This is not a guarantee
of secure memory erasure. Remove identity numbers and unnecessary personal data before
uploading. If deployed remotely, the Streamlit server receives the uploaded file.

## Voice input and individual/family profiles

Open **Voice input** beside search, document details, or a profile member. Allow
microphone access, record up to two minutes (5 MB), then click **Transcribe into text**.
This explicit action sends only the recording to Groq's
[Whisper transcription service](https://console.groq.com/docs/speech-to-text), using
`whisper-large-v3-turbo` and the configured API key. Provider quotas apply.
Review/correct the transcript before searching, matching, or saving. Transcription
replaces the associated text field. Recordings are not written to disk by the app.
Without a key, manual typing and local matching remain available. A microphone
requires browser permission and localhost or HTTPS. Scheme matching still uses
the English-oriented local embedding model; non-English accuracy may be limited.

In **Profiles**, choose **Individual** or **Family**. Enter an optional nickname,
age, occupation/student status, and support needs. A family profile holds up to
ten members and a shared state; suggestions are generated separately for each member,
with citations and official application instructions. The app does not infer that
one person's eligibility or circumstances apply to the whole family.

**Save profile for this session** retains each profile type independently while
you navigate. **Find schemes for this profile** uses the currently displayed edits.
Profiles are session-only, not accounts or permanent storage; a new session may
lose them. **Delete all saved profiles** clears both types and their entry fields.
Do not provide identity numbers or unnecessary sensitive information. Matching
remains a shortlist of possible schemes, not an eligibility assessment.
