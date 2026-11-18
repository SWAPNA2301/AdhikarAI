# Retrieval evaluation — DRAFT

All 40 queries and gold labels in [queries.json](queries.json) are **DRAFT** for human review, especially vague and multi-scheme queries. The JSON retains the requested three-field format. Labels describe relevance to the ten-record corpus, not entitlement or the availability of schemes elsewhere.

From the repository root, with the project environment activated:

```powershell
python -m pip install -e . -r requirements-dev.txt
python eval/run_eval.py
python -m unittest discover -s tests -p test_retrieval_eval.py -v
```

The runner builds/reuses a separate scheme-only index under `data/chroma/eval` and writes [results.md](results.md). It uses the production all-MiniLM-L6-v2 encoder, including its token-window pooling. The first run may download the model; inference is local and needs no Groq key. Optional PDF chunks are excluded because the labels identify schemes. No production code or search settings are changed.

The keyword adapter mirrors the inline loop in [app.py](../src/adhikar_ai/app.py), including all-word substring matching and dataset order. Semantic retrieval calls the existing search function and honors `SEMANTIC_MAX_DISTANCE` (default 0.82). Results record the effective cutoff, model, recipe, timestamp, and input hashes.

Recall@1/3/5 is macro-averaged across queries with gold labels, including partial recall for multi-label queries. MRR uses the full returned ranking after the cutoff, with zero for a missing relevant result. Empty-gold queries are excluded from these metrics and scored separately using no-match accuracy. Every query has per-cutoff misses in the report. These draft labels are not an independent benchmark; review them before using the numbers in a portfolio.

CLI overrides: `--queries`, `--schemes`, `--output`, and `--index-dir`. Full-ranking evaluation currently supports up to 20 schemes, matching the existing search API's limit. Fixture tests use a deterministic encoder and temporary storage; their numbers are not model results.
