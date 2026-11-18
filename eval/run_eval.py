"""Evaluate existing retrieval on DRAFT scheme relevance labels; never calls an LLM."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from adhikar_ai import semantic_search as semantic

ROOT = Path(__file__).resolve().parents[1]


def keyword_search(schemes, query):
    """Mirror app.main's inline keyword loop, without filters, in dataset order.

    Kept here to avoid modifying production code; update if that loop changes.
    """
    def label(value):
        return "All India" if value == "all_india" else value.replace("_", " ").title()

    terms = query.casefold().split()
    results = []
    for scheme in schemes:
        searchable = " ".join(
            [scheme["scheme_name"], scheme["scheme_id"], label(scheme["category"]),
             label(scheme["state"]), label(scheme["government_level"])]
            + [text for field in semantic.FACT_FIELDS
               for text in scheme[field]["items"] + [scheme[field]["note"]]]
        ).casefold()
        if all(term in searchable for term in terms):
            results.append(scheme["scheme_id"])
    return results


def validate_queries(queries, scheme_ids):
    if not isinstance(queries, list) or not queries:
        raise ValueError("Queries must be a nonempty JSON list")
    for row in queries:
        if not isinstance(row, dict) or set(row) != {"query", "gold_scheme_ids", "language"}:
            raise ValueError("Each query needs query, gold_scheme_ids, and language")
        if not isinstance(row["query"], str) or not row["query"].strip():
            raise ValueError("Query must be a nonempty string")
        if not isinstance(row["language"], str) or not row["language"].strip():
            raise ValueError("Language must be a nonempty string")
        gold = row["gold_scheme_ids"]
        if (not isinstance(gold, list) or any(not isinstance(x, str) for x in gold)
                or len(set(gold)) != len(gold) or not set(gold) <= scheme_ids):
            raise ValueError("Gold IDs must be unique known scheme IDs")


def metrics(rows):
    positive = [row for row in rows if row["gold_scheme_ids"]]
    negative = [row for row in rows if not row["gold_scheme_ids"]]
    result = {}
    for k in (1, 3, 5):
        result[f"recall@{k}"] = (
            sum(len(set(row["ranked"][:k]) & set(row["gold_scheme_ids"]))
                / len(row["gold_scheme_ids"]) for row in positive) / len(positive)
            if positive else None)
    result["MRR"] = (sum(next((1 / rank for rank, sid in enumerate(row["ranked"], 1)
                                               if sid in row["gold_scheme_ids"]), 0)
                             for row in positive) / len(positive) if positive else None)
    result["No-match accuracy"] = (sum(not row["ranked"] for row in negative)
                                   / len(negative) if negative else None)
    return result


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def render_report(results, provenance):
    lines = ["# Retrieval evaluation — DRAFT", "",
             "Gold labels are DRAFT and require human review. These measure retrieval relevance, not eligibility.",
             "", provenance, "",
             "Recall@k is macro-averaged over queries with nonempty gold lists: retrieved gold IDs / all gold IDs.",
             "MRR uses the first relevant result in the full returned scheme ranking (after the existing cutoff).",
             "Empty-gold queries are excluded from recall and MRR; no-match accuracy measures their empty-result rate.",
             "Keyword ties retain dataset order. Both methods use schemes only, no PDF chunks or taxonomy filters.",
             "", "| Method | Recall@1 | Recall@3 | Recall@5 | MRR | No-match accuracy |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for method, rows in results.items():
        values = ["N/A" if value is None else f"{value:.4f}" for value in metrics(rows).values()]
        lines.append("| " + " | ".join([method] + values) + " |")
    lines += ["", "## Per-query results and misses", "",
              "Missing gold IDs are reported separately at each cutoff. For empty gold, any returned ID is a false positive.",
              "", "| # | Method | Query | Language | Gold | Ranked results (full) | Misses@1 | Misses@3 | Misses@5 | No-match outcome |",
              "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for method, rows in results.items():
        for index, row in enumerate(rows, 1):
            gold, ranked = row["gold_scheme_ids"], row["ranked"]
            missing = [", ".join(sid for sid in gold if sid not in ranked[:k]) or "—" for k in (1, 3, 5)]
            outcome = "—" if gold else ("false positive" if ranked else "correct abstention")
            lines.append("| " + " | ".join(map(cell, [index, method, row["query"], row["language"],
                         ", ".join(gold) or "∅", ", ".join(ranked) or "∅", *missing, outcome])) + " |")
    return "\n".join(lines) + "\n"


def run(queries_path, schemes_path, output_path, index_path, encoder=None):
    queries_path, schemes_path, output_path = map(Path, (queries_path, schemes_path, output_path))
    queries = json.loads(queries_path.read_text(encoding="utf-8"))
    schemes = json.loads(schemes_path.read_text(encoding="utf-8"))["schemes"]
    ids = {scheme["scheme_id"] for scheme in schemes}
    if not schemes or len(ids) != len(schemes) or len(schemes) > 20:
        raise ValueError("Full-ranking evaluation requires 1–20 unique schemes (search API limit)")
    validate_queries(queries, ids)
    # Load the real evidence representation, then exclude optional PDF records.
    documents = [doc for doc in semantic.load_documents(schemes_path)
                 if doc["metadata"]["kind"] == "scheme"]
    limit = semantic.distance_limit()
    semantic.build_index(documents, index_path=index_path, encoder=encoder)
    results = {"Keyword": [], "Semantic": []}
    for row in queries:
        results["Keyword"].append({**row, "ranked": keyword_search(schemes, row["query"])})
        hits = semantic.search(documents, row["query"], top_k=len(schemes),
                               index_path=index_path, encoder=encoder, max_distance=limit)
        results["Semantic"].append({**row, "ranked": [hit["metadata"]["scheme_id"] for hit in hits]})
    provenance = (
        f"Run (UTC): {datetime.now(timezone.utc).isoformat()}. "
        f"Queries: {len(queries)}; schemes: {len(schemes)}. "
        f"Encoder: {'TEST FIXTURE (not model evaluation)' if encoder is not None else semantic.MODEL_NAME}. "
        f"Cosine-distance cutoff: {limit}. Recipe: {semantic.INDEX_VERSION}.\n\n"
        f"Query SHA-256: `{hashlib.sha256(queries_path.read_bytes()).hexdigest()}`. "
        f"Dataset SHA-256: `{hashlib.sha256(schemes_path.read_bytes()).hexdigest()}`.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(results, provenance), encoding="utf-8")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, default=ROOT / "eval/queries.json")
    parser.add_argument("--schemes", type=Path, default=semantic.SCHEMES_PATH)
    parser.add_argument("--output", type=Path, default=ROOT / "eval/results.md")
    parser.add_argument("--index-dir", type=Path, default=ROOT / "data/chroma/eval")
    args = parser.parse_args()
    run(args.queries, args.schemes, args.output, args.index_dir)
    print(f"DRAFT evaluation written to {args.output}")


if __name__ == "__main__":
    main()
