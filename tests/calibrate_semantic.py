"""Opt-in real-model relevance check: python tests/calibrate_semantic.py.

Uses the existing local index; does not rebuild it or call an LLM.
Kept outside unittest discovery to avoid model downloads in the offline suite.
"""
from adhikar_ai import semantic_search as semantic

CASES = [
    ("financial support for retirement", True),
    ("help with school education", True),
    ("income support for farmers", True),
    ("accident insurance", True),
    ("life insurance", True),
    ("marriage assistance for women", True),
    ("pension for unorganised workers", True),
    ("Atal Pension Yojana", True),
    ("Kanyashree", True),
    ("PM KISAN", True),
    ("how to bake a chocolate cake", False),
    ("football match scores", False),
    ("repair my laptop", False),
    ("weather tomorrow", False),
    ("book a flight to Paris", False),
    ("quantum computing tutorial", False),
    ("asdfghjkl", False),
    ("qwertyuiop", False),
    ("zxqvbnm", False),
    ("banana spaceship dancing", False),
]


def main():
    docs = semantic.load_documents()
    encoder = semantic.get_encoder()
    collection = semantic.get_client().get_collection(
        semantic.collection_name(docs), embedding_function=None,
    )
    results = collection.query(query_embeddings=encoder.encode([q for q, _ in CASES]),
                               n_results=1, include=["distances"])
    for (query, expected), distances in zip(CASES, results["distances"]):
        print(f"{distances[0]:.6f}\t{expected}\t{query}")
        hits = semantic.search(docs, query, encoder=encoder,
                               max_distance=semantic.DEFAULT_MAX_DISTANCE)
        assert bool(hits) == expected, query
    print(f"All {len(CASES)} real-model relevance cases passed.")


if __name__ == "__main__":
    main()
