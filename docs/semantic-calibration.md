# Semantic relevance calibration

Measured locally on 2026-11-16 with the 10-scheme corpus, no PDF chunks,
`sentence-transformers/all-MiniLM-L6-v2`, and `mean-token-windows-cosine-v1`.
Distances below are the nearest unfiltered Chroma cosine distance, not a
probability or an eligibility score.

| Query | Relevant topic? | Nearest distance |
| --- | --- | ---: |
| financial support for retirement | Yes | 0.590985 |
| help with school education | Yes | 0.790168 |
| income support for farmers | Yes | 0.616131 |
| accident insurance | Yes | 0.721369 |
| life insurance | Yes | 0.647574 |
| marriage assistance for women | Yes | 0.551185 |
| pension for unorganised workers | Yes | 0.562491 |
| Atal Pension Yojana | Yes | 0.339085 |
| Kanyashree | Yes | 0.760497 |
| PM KISAN | Yes | 0.653522 |
| how to bake a chocolate cake | No | 0.881729 |
| football match scores | No | 0.971932 |
| repair my laptop | No | 0.907463 |
| weather tomorrow | No | 0.916563 |
| book a flight to Paris | No | 0.991998 |
| quantum computing tutorial | No | 0.891366 |
| asdfghjkl | No | 0.859230 |
| qwertyuiop | No | 0.927745 |
| zxqvbnm | No | 0.904937 |
| banana spaceship dancing | No | 1.028666 |

The midpoint between the largest positive distance (0.790168) and smallest
negative (0.859230) is 0.824699. Rounded down to **0.82**, the default admits at
least one result for all ten positive queries and rejects all ten negative
queries on this calibration set. Every returned result must individually meet
the cutoff, including after filtering; searches never backfill with weaker hits.

This is a small English calibration set, not a held-out accuracy estimate or
proof that every accepted passage is relevant. Recalibrate for new schemes,
PDF chunks, languages, models or encoding recipes. Long personal documents can
also have different distance distributions. Empty/non-letter inputs, repeated
characters and obvious keyboard-row strings are rejected before model loading;
other nonsense relies on the distance check. Acronyms and Unicode letters are
not rejected by an English dictionary.

Reproduce after building the local index:

```powershell
python tests/calibrate_semantic.py
```

This opt-in check uses the real model and checks actual search admission against
the labels; the regular unit suite uses deterministic embeddings and mocked UI
results for offline, repeatable boundary, filtering and citation tests.
