"""Offline retrieval tests: real persistent Chroma, deterministic test embeddings."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from adhikar_ai import semantic_search as semantic


class TestEncoder:
    """Only for deterministic ranking tests; production always uses SentenceTransformer."""

    def encode(self, texts):
        return [[float("pension" in text.lower()), float("school" in text.lower()), 0.1]
                for text in texts]


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.encoder = TestEncoder()

    def sample_documents(self):
        return [
            {"id": "a", "text": "pension for retirement",
             "metadata": {"kind": "scheme", "state": "all_india", "category": "pension"}},
            {"id": "b", "text": "school education",
             "metadata": {"kind": "pdf", "url": "https://example.gov.in/a.pdf",
                          "page_number": 7, "page_status": "suspect_text_requires_review"}},
        ]

    def test_all_ten_schemes_and_pdf_provenance(self):
        chunk = {
            "chunk_id": "test:p7:c1", "text": "school education",
            "source": {"title": "Official document", "url": "https://example.gov.in/a.pdf",
                       "publisher": "Government", "retrieved_at": "2026-11-14",
                       "resolved_url": "https://example.gov.in/b.pdf"},
            "page_number": 7, "page_status": "suspect_text_requires_review",
            "document_sha256": "abc", "start_char": 0, "end_char": 16,
        }
        path = self.path / "chunks.json"
        path.write_text(json.dumps({"chunks": [chunk, {**chunk, "chunk_id": "empty", "text": " "}]}))
        documents = semantic.load_documents(pdf_path=path)
        self.assertEqual(len(documents), 11)
        schemes = json.loads(semantic.SCHEMES_PATH.read_text(encoding="utf-8"))["schemes"]
        for source, doc in zip(schemes, documents):
            self.assertEqual(json.loads(doc["metadata"]["evidence_json"]), source)
            for field in semantic.FACT_FIELDS:
                for item in source[field]["items"]:
                    self.assertIn(item, doc["text"])
        meta = documents[-1]["metadata"]
        self.assertEqual(json.loads(meta["evidence_json"]), chunk)
        self.assertEqual(meta["page_number"], 7)
        self.assertEqual(meta["resolved_url"], chunk["source"]["resolved_url"])
        self.assertEqual(len(semantic.load_documents(pdf_path=self.path / "absent.json")), 10)

    def test_persistence_ranking_filtering_and_idempotence(self):
        documents = self.sample_documents()
        self.assertEqual(semantic.build_index(documents, self.path, self.encoder), 2)
        # A fresh client opens the persisted collection without re-embedding.
        unused = Mock()
        self.assertEqual(semantic.build_index(documents, self.path, unused), 2)
        unused.encode.assert_not_called()
        result = semantic.search(documents, "school", 20, index_path=self.path, encoder=self.encoder,
                                 max_distance=2.0)
        self.assertEqual([hit["id"] for hit in result], ["b", "a"])
        self.assertEqual(result[0]["metadata"]["page_number"], 7)
        self.assertEqual(result[0]["text"], "school education")
        self.assertLess(result[0]["distance"], result[1]["distance"])
        filtered = semantic.search(
            documents, "pension", filters={"state": "all_india", "category": "pension"},
            index_path=self.path, encoder=self.encoder,
        )
        self.assertEqual([hit["id"] for hit in filtered], ["a"])
        self.assertEqual(semantic.search(
            documents, "school", filters={"state": "West Bengal"},
            index_path=self.path, encoder=self.encoder,
        ), [])
        self.assertTrue((self.path / "chroma.sqlite3").exists())

    def test_blank_query_and_stale_index(self):
        documents = self.sample_documents()
        self.assertEqual(semantic.search(documents, " ", index_path=self.path, encoder=Mock()), [])
        with self.assertRaises(semantic.IndexNotReady):
            semantic.search(documents, "school", index_path=self.path, encoder=self.encoder)
        semantic.build_index(documents, self.path, self.encoder)
        documents[0]["metadata"]["state"] = "West Bengal"
        with self.assertRaises(semantic.IndexNotReady):
            semantic.search(documents, "pension", index_path=self.path, encoder=self.encoder)
        semantic.build_index(documents, self.path, self.encoder)
        self.assertEqual(semantic.search(
            documents, "pension", 1, index_path=self.path, encoder=self.encoder,
        )[0]["metadata"]["state"], "West Bengal")
        with self.assertRaises(ValueError):
            semantic.search(documents, "pension", 0, index_path=self.path, encoder=self.encoder)

    def test_empty_and_obvious_noise_skip_index_and_encoder(self):
        with patch.object(semantic, "get_client") as client:
            for query in ("", "  ", "!!!", "123456", "aaaaaa", "asdfghjkl", "qwertyuiop"):
                encoder = Mock()
                self.assertEqual(semantic.search(self.sample_documents(), query, encoder=encoder), [])
                encoder.encode.assert_not_called()
            client.assert_not_called()

    def test_relevance_rejects_unrelated_results_without_relaxing_filters(self):
        documents = self.sample_documents()
        semantic.build_index(documents, self.path, self.encoder)
        with patch.dict(os.environ, {"SEMANTIC_MAX_DISTANCE": "0.8"}):
            hits = semantic.search(documents, "school", index_path=self.path, encoder=self.encoder)
            self.assertEqual([hit["id"] for hit in hits], ["b"])
            self.assertEqual(hits[0]["metadata"], documents[1]["metadata"])
            for query in ("bake a cake", "zxqvbnm"):
                self.assertEqual(semantic.search(documents, query, index_path=self.path,
                                                  encoder=self.encoder), [])
            self.assertEqual(semantic.search(documents, "school", filters={"category": "pension"},
                                              index_path=self.path, encoder=self.encoder), [])
            self.assertEqual(len(semantic.search(documents, "school", index_path=self.path,
                                                  encoder=self.encoder, max_distance=2.0)), 2)

    def test_distance_boundary_and_invalid_configuration(self):
        collection = Mock()
        collection.metadata = {"ready": True}
        collection.count.return_value = 2
        collection.query.return_value = {"ids": [["a", "b"]], "documents": [["a", "b"]],
            "metadatas": [[{"url": "https://example.gov.in"}, {}]], "distances": [[0.8, 0.80001]]}
        with patch.object(semantic, "get_client") as client:
            client.return_value.get_collection.return_value = collection
            hits = semantic.search(self.sample_documents(), "pension", encoder=self.encoder,
                                   max_distance=0.8)
            self.assertEqual([hit["id"] for hit in hits], ["a"])
            for value in ("nan", "inf", "-0.1", "2.1", "invalid"):
                with patch.dict(os.environ, {"SEMANTIC_MAX_DISTANCE": value}):
                    with self.assertRaises(ValueError):
                        semantic.search(self.sample_documents(), "pension", encoder=self.encoder)

    def test_failed_build_can_retry_without_publishing_partial_index(self):
        documents = self.sample_documents()
        broken = Mock()
        broken.encode.side_effect = RuntimeError("model unavailable")
        with self.assertRaisesRegex(RuntimeError, "model unavailable"):
            semantic.build_index(documents, self.path, broken)
        with self.assertRaises(semantic.IndexNotReady):
            semantic.search(documents, "school", index_path=self.path, encoder=self.encoder)
        self.assertEqual(semantic.build_index(documents, self.path, self.encoder), 2)

    def test_model_and_source_changes_change_index_identity(self):
        documents = self.sample_documents()
        original = semantic.collection_name(documents)
        with patch.object(semantic, "MODEL_NAME", "another-model"):
            self.assertNotEqual(original, semantic.collection_name(documents))
        documents.pop()
        self.assertNotEqual(original, semantic.collection_name(documents))

    def test_long_records_encode_every_window_and_normalize(self):
        import numpy as np
        encoder = semantic.LocalEncoder.__new__(semantic.LocalEncoder)
        model = Mock()
        model.max_seq_length = 5
        model.tokenizer.num_special_tokens_to_add.return_value = 2
        model.tokenizer.encode.side_effect = [[1, 2, 3, 4, 5, 6, 7], [8]]
        model.tokenizer.decode.side_effect = lambda tokens: " ".join(map(str, tokens))
        model.encode.return_value = np.array([[1., 0.], [0., 1.], [1., 0.], [0., 1.]])
        encoder.model = model
        vectors = encoder.encode(["long record", "short query"])
        self.assertEqual(model.encode.call_args.args[0], ["1 2 3", "4 5 6", "7", "8"])
        self.assertEqual(len(vectors), 2)
        np.testing.assert_allclose(np.linalg.norm(vectors, axis=1), [1., 1.])
        np.testing.assert_allclose(vectors[0], np.array([2., 1.]) / np.sqrt(5))


if __name__ == "__main__":
    unittest.main()

