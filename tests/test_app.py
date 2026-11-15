"""Exercise scheme discovery and evidence rendering in the real Streamlit app."""

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import adhikar_ai
from adhikar_ai import rag, semantic_search


class AppSmokeTest(unittest.TestCase):
    def open_app(self):
        app_path = Path(adhikar_ai.__file__).parent / "app.py"
        return AppTest.from_file(str(app_path)).run(timeout=15)

    def test_intro_and_all_schemes(self) -> None:
        app = self.open_app()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(
            app.title[0].value, "AdhikarAI — Government Scheme Discovery"
        )
        self.assertIn("documented criteria only", app.info[0].value)
        self.assertFalse(app.text_input[0].disabled)
        self.assertEqual(len(app.expander), 10)
        self.assertIn("Showing 10 of 10 schemes", [c.value for c in app.caption])

    def test_search_name_id_and_benefit(self):
        app = self.open_app()
        for query, expected in (
            ("  kAnYaShReE  ", "Kanyashree Prakalpa"),
            ("IN-PMSBY", "Pradhan Mantri Suraksha Bima Yojana"),
            ("accidental disability", "Pradhan Mantri Suraksha Bima Yojana"),
        ):
            with self.subTest(query=query):
                app.text_input(key="query").set_value(query).run()
                self.assertEqual(len(app.exception), 0)
                self.assertEqual([e.label for e in app.expander], [expected])
        app.text_input(key="query").set_value("   ").run()
        self.assertEqual(len(app.expander), 10)

    def test_filters_combine_with_search_and_reset(self):
        app = self.open_app()
        app.selectbox(key="government_level").select("central").run()
        self.assertEqual(len(app.expander), 5)
        app.selectbox(key="category").select("pension").run()
        self.assertEqual(len(app.expander), 2)
        app.text_input(key="query").set_value("atal").run()
        self.assertEqual([e.label for e in app.expander], ["Atal Pension Yojana"])
        app.selectbox(key="state").select("West Bengal").run()
        self.assertEqual(len(app.expander), 0)
        self.assertTrue(any("No schemes match" in info.value for info in app.info))
        app.text_input(key="query").set_value("")
        app.selectbox(key="government_level").select("all")
        app.selectbox(key="category").select("all").run()
        self.assertEqual(len(app.expander), 5)
        app.selectbox(key="state").select("all_india").run()
        self.assertEqual(len(app.expander), 5)
        app.selectbox(key="state").select("all").run()
        self.assertEqual(len(app.expander), 10)

    def test_all_records_retain_evidence_and_uncertainty(self):
        data_path = Path(__file__).resolve().parents[1] / "data/processed/schemes.json"
        records = json.loads(data_path.read_text(encoding="utf-8"))["schemes"]
        app = self.open_app()
        for record, expander in zip(records, app.expander):
            self.assertEqual(expander.label, record["scheme_name"])
            text = "\n".join(item.value for item in expander.markdown)
            self.assertIn(record["source_passage"], [item.value for item in expander.text])
            self.assertIn(record["verification_date"], "\n".join(c.value for c in expander.caption))
            for field in ("benefits", "eligibility_conditions", "exclusions",
                          "required_documents", "application_process"):
                fact = record[field]
                self.assertIn(fact["note"], text)
                self.assertIn(f"— {fact['status']}**", text)
                for item in fact["items"]:
                    self.assertIn(item, text)
                sources = {s["source_id"]: s for s in record["sources"]}
                if fact["source_ids"]:
                    links = "; ".join(
                        f"[{sources[sid]['title']}]({sources[sid]['url']})"
                        for sid in fact["source_ids"]
                    )
                    self.assertIn("Sources: " + links, text)
            for source in record["sources"]:
                self.assertIn(f"[{source['title']}]({source['url']})", text)
                self.assertIn(source["sections"], text)
            for note in record["verification_notes"]:
                self.assertIn(note, text)

    def test_missing_dataset_shows_error(self):
        with patch("pathlib.Path.read_text", side_effect=FileNotFoundError):
            app = self.open_app()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("could not be loaded", app.error[0].value)

    def test_semantic_no_relevant_matches(self):
        app = self.open_app()
        app.radio(key="search_mode").set_value("Semantic").run()
        with patch.object(semantic_search, "search", return_value=[]):
            app.text_input(key="query").set_value("bake a cake").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.expander), 0)
        self.assertTrue(any(i.value == "No sufficiently relevant schemes found" for i in app.info))
        with patch.object(semantic_search, "search", return_value=[]), patch.object(rag, "answer") as answer:
            app.radio(key="search_mode").set_value("Q&A").run()
            self.assertFalse(any(b.key == "answer" for b in app.button))
            answer.assert_not_called()

    def test_eligibility_form_is_deterministic_cited_and_clearable(self):
        with patch.object(rag, "answer") as llm, patch.object(semantic_search, "search") as search:
            app = self.open_app()
            app.radio(key="search_mode").set_value("Eligibility").run()
            app.selectbox(key="elig_scheme").set_value("IN-PMJJBY").run()
            def submit():
                next(b for b in app.button if b.label == "Check criteria").click().run()
            submit()
            self.assertIn("insufficient information", [x.value for x in app.subheader])
            app.text_input(key="elig_IN-PMJJBY_age").set_value("30")
            for key in ("individual_account", "one_account", "auto_debit", "premium_balance"):
                app.selectbox(key="elig_IN-PMJJBY_" + key).set_value("Yes")
            submit()
            self.assertIn("meets criteria", [x.value for x in app.subheader])
            self.assertIn("https://financialservices.gov.in/pmjjby", "\n".join(x.value for x in app.markdown))
            app.text_input(key="elig_IN-PMJJBY_age").set_value("17")
            submit()
            self.assertIn("does not meet criteria", [x.value for x in app.subheader])
            app.button(key="clear_eligibility").click().run()
            self.assertFalse(any("does not meet criteria" == x.value for x in app.subheader))
            self.assertEqual(app.text_input[0].value, "")
            self.assertEqual(len(app.exception), 0)
            llm.assert_not_called()
            search.assert_not_called()

    def test_semantic_mode_citations_and_missing_index(self):
        doc = semantic_search.load_documents()[0]
        match = {"id": doc["id"], "text": doc["text"], "metadata": doc["metadata"], "distance": 0.2}
        app = self.open_app()
        app.radio(key="search_mode").set_value("Semantic").run()
        self.assertTrue(any("Enter a question" in item.value for item in app.info))
        with patch.object(semantic_search, "search", return_value=[match]) as search:
            app.text_input(key="query").set_value("accident cover").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.expander), 1)
        self.assertIn(doc["metadata"]["url"], "\n".join(m.value for m in app.markdown))
        self.assertEqual(search.call_args.args[1], "accident cover")
        with patch.object(semantic_search, "search", side_effect=semantic_search.IndexNotReady("Build the local index")):
            app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Build the local index" in item.value for item in app.info))

    def test_document_matching_is_local_with_application_links(self):
        doc = semantic_search.load_documents()[0]
        match = {**doc, "distance": 0.2}
        app = self.open_app()
        app.radio(key="search_mode").set_value("My documents").run()
        app.text_area[0].set_value("Farmer seeking accident insurance")
        app.selectbox(key="profile_state").select("Another state")
        with patch.object(semantic_search, "search", return_value=[match]) as search, patch.object(
            rag, "answer"
        ) as answer, patch.object(semantic_search, "build_index") as build:
            app.button(key="match_documents").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(search.call_args.args[1], "Farmer seeking accident insurance")
            self.assertEqual(search.call_args.args[3], {"kind": "scheme", "state": "all_india"})
            self.assertTrue(any("Potential matches only" in w.value for w in app.warning))
            self.assertGreater(len(app.get("link_button")), 0)
            answer.assert_not_called()
            build.assert_not_called()
        app.button(key="clear_documents").click().run()
        self.assertEqual(app.text_area[0].value, "")
        self.assertEqual(len(app.expander), 0)

    def test_individual_and_family_profiles_save_switch_match_and_delete(self):
        app = self.open_app()
        app.radio(key="search_mode").set_value("Profiles").run()
        app.text_input(key="person_0_name").set_value("Person A")
        app.text_input(key="person_0_occupation").set_value("Farmer")
        app.button(key="save_profile").click().run()
        app.radio(key="profile_kind").set_value("Family").run()
        app.text_input(key="household_0_name").set_value("Adult")
        app.text_input(key="household_0_occupation").set_value("Farmer")
        app.text_input(key="household_1_name").set_value("Child")
        app.text_input(key="household_1_occupation").set_value("Student")
        app.button(key="save_profile").click().run()
        doc = semantic_search.load_documents()[0]
        with patch.object(semantic_search, "search", return_value=[{**doc, "distance": 0.2}]) as search:
            app.button(key="match_profile").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(search.call_count, 2)
            self.assertIn("Farmer", search.call_args_list[0].args[1])
            self.assertNotIn("Student", search.call_args_list[0].args[1])
            self.assertIn("Student", search.call_args_list[1].args[1])
        app.radio(key="profile_kind").set_value("Individual").run()
        self.assertEqual(app.text_input(key="person_0_name").value, "Person A")
        app.button(key="delete_profiles").click().run()
        self.assertEqual(app.text_input(key="person_0_name").value, "")
        self.assertEqual(len(app.exception), 0)

    def test_document_matching_empty_input_does_not_search(self):
        app = self.open_app()
        app.radio(key="search_mode").set_value("My documents").run()
        with patch.object(semantic_search, "search") as search:
            app.button(key="match_documents").click().run()
            search.assert_not_called()
        self.assertTrue(any("enter your details first" in i.value for i in app.info))

    def test_qa_without_key_retains_semantic_results(self):
        doc = semantic_search.load_documents()[0]
        match = {**doc, "distance": 0.2}
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}), patch.object(
            semantic_search, "search", return_value=[match]
        ), patch.object(rag, "answer") as answer:
            app = self.open_app()
            app.radio(key="search_mode").set_value("Q&A")
            app.text_input(key="query").set_value("benefits").run()
            self.assertTrue(app.button(key="answer").disabled)
            self.assertEqual(len(app.expander), 1)
            self.assertEqual(len(app.exception), 0)
            answer.assert_not_called()

    def test_qa_explicit_submit_and_citations(self):
        doc = semantic_search.load_documents()[0]
        match = {**doc, "distance": 0.2}
        passage = rag.evidence_passages([match])[0]
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-secret-not-real"}), patch.object(
            semantic_search, "search", return_value=[match]
        ), patch.object(rag, "answer", return_value={
            "status": "answered", "message": "Relevant retrieved evidence:", "passages": [passage]
        }) as answer:
            app = self.open_app()
            app.radio(key="search_mode").set_value("Q&A")
            app.text_input(key="query").set_value("benefits").run()
            answer.assert_not_called()
            app.button(key="answer").click().run()
            answer.assert_called_once_with("benefits", [match])
            self.assertEqual(len(app.exception), 0)
            self.assertIn(passage["text"], [t.value for t in app.text])
            self.assertIn(passage["sources"][0]["url"], "\n".join(m.value for m in app.markdown))
            self.assertNotIn("test-secret-not-real", str(app))

    def test_semantic_pdf_citation_and_quality_warning(self):
        chunk = {
            "chunk_id": "sample:p3:c1", "start_char": 0, "end_char": 12,
            "source": {"publisher": "Government"},
        }
        meta = {
            "kind": "pdf", "title": "Scheme PDF", "url": "https://example.gov.in/a.pdf",
            "resolved_url": "https://example.gov.in/a.pdf", "page_number": 3,
            "retrieved_at": "2026-11-14", "page_status": "suspect_text_requires_review",
            "document_sha256": "abc", "evidence_json": json.dumps(chunk),
        }
        match = {"id": "pdf:sample", "text": "PDF evidence", "metadata": meta, "distance": 0.3}
        app = self.open_app()
        app.radio(key="search_mode").set_value("Semantic")
        app.text_input(key="query").set_value("benefits")
        with patch.object(semantic_search, "search", return_value=[match]):
            app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("page 3", app.expander[0].label)
        self.assertIn("[Official PDF](https://example.gov.in/a.pdf)", "\n".join(m.value for m in app.markdown))
        self.assertTrue(any("requires review" in item.value for item in app.warning))


if __name__ == "__main__":
    unittest.main()
