"""Personal document extraction and cited application guidance checks."""

import json
import unittest

import pymupdf

from adhikar_ai import document_matching as matching, semantic_search


class DocumentMatchingTests(unittest.TestCase):
    def test_text_and_pdf_extraction(self):
        self.assertEqual(matching.extract_upload("profile.txt", b"  Farmer in West Bengal  "), "Farmer in West Bengal")
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text((72, 72), "Farmer in West Bengal")
            content = pdf.tobytes()
        self.assertIn("Farmer in West Bengal", matching.extract_upload("profile.pdf", content))

    def test_invalid_empty_scanned_encrypted_and_large_files(self):
        for name, data in [
            ("image.png", b"image"), ("empty.txt", b""), ("blank.txt", b" "),
            ("large.txt", b"x" * (matching.MAX_BYTES + 1)),
            ("long.txt", b"x" * (matching.MAX_CHARS + 1)),
            ("invalid.txt", b"\xff"), ("bad.pdf", b"not a pdf"),
        ]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                matching.extract_upload(name, data)
        with pymupdf.open() as pdf:
            pdf.new_page()
            with self.assertRaisesRegex(ValueError, "no readable text"):
                matching.extract_upload("scan.pdf", pdf.tobytes())
            encrypted = pdf.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256,
                                    owner_pw="owner", user_pw="user")
            with self.assertRaisesRegex(ValueError, "Password-protected"):
                matching.extract_upload("locked.pdf", encrypted)
            for _ in range(20):
                pdf.new_page()
            with self.assertRaisesRegex(ValueError, "20 pages"):
                matching.extract_upload("long.pdf", pdf.tobytes())

    def test_application_links_are_exact_cited_sources(self):
        for document in semantic_search.load_documents():
            if document["metadata"]["kind"] != "scheme":
                continue
            scheme = json.loads(document["metadata"]["evidence_json"])
            expected = [source["url"] for source in scheme["sources"]
                        if source["source_id"] in scheme["application_process"]["source_ids"]]
            self.assertCountEqual([link["url"] for link in matching.application_links(scheme)], expected)


if __name__ == "__main__":
    unittest.main()

