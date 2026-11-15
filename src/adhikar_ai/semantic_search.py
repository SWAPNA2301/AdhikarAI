"""Local sentence-transformer embeddings and a persistent Chroma index."""

import argparse
from functools import lru_cache
import hashlib
import json
import math
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMES_PATH = ROOT / "data/processed/schemes.json"
PDF_PATH = ROOT / "data/processed/pdf_chunks.json"
INDEX_PATH = ROOT / "data/chroma"
MODEL_PATH = ROOT / "data/models"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# Calibrated against this corpus/model; see docs/semantic-calibration.md.
DEFAULT_MAX_DISTANCE = 0.82
# Include the encoding recipe in the identity so incompatible indexes are not reused.
INDEX_VERSION = "mean-token-windows-cosine-v1"
FACT_FIELDS = ("benefits", "eligibility_conditions", "exclusions",
               "required_documents", "application_process")


def load_documents(schemes_path=SCHEMES_PATH, pdf_path=PDF_PATH):
    """Keep complete evidence payloads; missing optional PDF output is valid."""
    schemes = json.loads(Path(schemes_path).read_text(encoding="utf-8"))["schemes"]
    documents = []
    for scheme in schemes:
        lines = [scheme["scheme_name"], scheme["scheme_id"],
                 scheme["category"].replace("_", " "), scheme["state"]]
        for field in FACT_FIELDS:
            fact = scheme[field]
            lines.append(f"{field.replace('_', ' ')} ({fact['status']}): "
                         + " ".join(fact["items"]) + " " + fact["note"])
        lines.extend(scheme["verification_notes"])
        documents.append({
            "id": "scheme:" + scheme["scheme_id"], "text": "\n".join(lines),
            "metadata": {
                "kind": "scheme", "scheme_id": scheme["scheme_id"],
                "title": scheme["scheme_name"], "url": scheme["official_source_url"],
                "government_level": scheme["government_level"],
                "state": scheme["state"], "category": scheme["category"],
                "verification_date": scheme["verification_date"],
                "evidence_json": json.dumps(scheme, ensure_ascii=False),
            },
        })
    if Path(pdf_path).exists():
        chunks = json.loads(Path(pdf_path).read_text(encoding="utf-8"))["chunks"]
        for chunk in chunks:
            if not chunk["text"].strip():
                continue
            source = chunk["source"]
            documents.append({
                "id": "pdf:" + chunk["chunk_id"], "text": chunk["text"],
                "metadata": {
                    "kind": "pdf", "title": source["title"], "url": source["url"],
                    "resolved_url": source.get("resolved_url", source["url"]),
                    "page_number": chunk["page_number"],
                    "page_status": chunk["page_status"],
                    "document_sha256": chunk["document_sha256"],
                    "retrieved_at": source["retrieved_at"],
                    "evidence_json": json.dumps(chunk, ensure_ascii=False),
                },
            })
    if len({doc["id"] for doc in documents}) != len(documents):
        raise ValueError("Duplicate source IDs in semantic corpus")
    return documents


class LocalEncoder:
    """Pool token windows so long schemes/PDF chunks are not silently truncated."""

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        # Prefer the cached model: repeated searches work without network access.
        try:
            self.model = SentenceTransformer(
                MODEL_NAME, cache_folder=str(MODEL_PATH), device="cpu",
                local_files_only=True,
            )
        except OSError:
            self.model = SentenceTransformer(
                MODEL_NAME, cache_folder=str(MODEL_PATH), device="cpu",
            )

    def encode(self, texts):
        import numpy as np
        tokenizer = self.model.tokenizer
        size = self.model.max_seq_length - tokenizer.num_special_tokens_to_add(pair=False)
        windows, counts = [], []
        for text in texts:
            tokens = tokenizer.encode(text, add_special_tokens=False, truncation=False)
            parts = [tokenizer.decode(tokens[i:i + size]) for i in range(0, len(tokens), size)]
            parts = parts or [""]
            windows.extend(parts)
            counts.append(len(parts))
        vectors = self.model.encode(windows, normalize_embeddings=True, show_progress_bar=False)
        output, offset = [], 0
        for count in counts:
            vector = np.mean(vectors[offset:offset + count], axis=0)
            vector /= max(float(np.linalg.norm(vector)), 1e-12)
            output.append(vector.tolist())
            offset += count
        return output


@lru_cache(maxsize=1)
def get_encoder():
    return LocalEncoder()


def collection_name(documents):
    payload = json.dumps([MODEL_NAME, INDEX_VERSION, documents], sort_keys=True, ensure_ascii=False)
    return "adhikar-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:40]


def get_client(index_path=INDEX_PATH):
    import chromadb
    from chromadb.config import Settings
    return chromadb.PersistentClient(
        path=str(index_path), settings=Settings(anonymized_telemetry=False),
    )


class IndexNotReady(RuntimeError):
    """The current source snapshot has not yet been indexed."""


def build_index(documents, index_path=INDEX_PATH, encoder=None):
    """Idempotently build a source snapshot; publish only after every batch succeeds."""
    if not documents:
        raise ValueError("No documents to index")
    client = get_client(index_path)
    collection = client.get_or_create_collection(
        collection_name(documents), embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}},
        metadata={"ready": False, "model": MODEL_NAME},
    )
    if collection.metadata.get("ready") and collection.count() == len(documents):
        return len(documents)
    encoder = encoder or get_encoder()
    for start in range(0, len(documents), 32):
        batch = documents[start:start + 32]
        collection.upsert(
            ids=[doc["id"] for doc in batch],
            documents=[doc["text"] for doc in batch],
            metadatas=[doc["metadata"] for doc in batch],
            embeddings=encoder.encode([doc["text"] for doc in batch]),
        )
    collection.modify(metadata={**collection.metadata, "ready": True})
    return collection.count()


def meaningful_query(query):
    """Reject obvious noise without an English dictionary or excluding scheme acronyms."""
    words = re.findall(r"[^\W\d_]+", query.casefold(), flags=re.UNICODE)
    keyboard_rows = ("qwertyuiop", "asdfghjkl", "zxcvbnm")
    return any(
        len(word) >= 2 and len(set(word)) > 1
        and not (len(word) >= 4 and any(word in row or word in row[::-1]
                                      for row in keyboard_rows))
        for word in words
    )


def distance_limit(value=None):
    """Validate a cosine-distance cutoff; never echo configuration values in errors."""
    try:
        limit = float(value if value is not None else
                      os.environ.get("SEMANTIC_MAX_DISTANCE", DEFAULT_MAX_DISTANCE))
    except (TypeError, ValueError):
        raise ValueError("SEMANTIC_MAX_DISTANCE must be a finite number from 0 to 2") from None
    if not math.isfinite(limit) or not 0 <= limit <= 2:
        raise ValueError("SEMANTIC_MAX_DISTANCE must be a finite number from 0 to 2")
    return limit


def search(documents, query, top_k=5, filters=None, index_path=INDEX_PATH, encoder=None,
           max_distance=None):
    """Return nearest passages with evidence; similarity is not eligibility confidence."""
    if not meaningful_query(query) or not documents:
        return []
    limit = distance_limit(max_distance)
    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")
    from chromadb.errors import NotFoundError
    try:
        collection = get_client(index_path).get_collection(
            collection_name(documents), embedding_function=None,
        )
    except NotFoundError as exc:
        raise IndexNotReady("Build the local index for the current sources first.") from exc
    if not collection.metadata.get("ready") or collection.count() != len(documents):
        raise IndexNotReady("The local index is incomplete. Build it again.")
    clauses = [{field: value} for field, value in (filters or {}).items() if value != "all"]
    where = {"$and": clauses} if len(clauses) > 1 else (clauses[0] if clauses else None)
    result = collection.query(
        query_embeddings=(encoder or get_encoder()).encode([query.strip()]),
        n_results=min(top_k, collection.count()), where=where,
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"id": identifier, "text": text, "metadata": metadata, "distance": distance}
        for identifier, text, metadata, distance in zip(
            result["ids"][0], result["documents"][0],
            result["metadatas"][0], result["distances"][0],
        )
        if math.isfinite(distance) and distance <= limit
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", help="Search after building/updating the local index")
    args = parser.parse_args()
    documents = load_documents()
    print(f"Indexed {build_index(documents)} documents locally.")
    if args.query:
        for match in search(documents, args.query):
            meta = match["metadata"]
            page = f" page {meta['page_number']}" if meta["kind"] == "pdf" else ""
            print(f"{meta['title']}{page} — {meta['url']} (distance {match['distance']:.3f})")


if __name__ == "__main__":
    main()

