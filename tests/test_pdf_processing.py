"""Offline extraction tests using PDFs created in temporary directories."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pymupdf

from adhikar_ai.pdf_processing import clean_text, download_pdf, extract_pdf, official_url, split_text


ROOT = Path(__file__).resolve().parents[1]
SOURCE = {"document_id": "test-source", "title": "Test document", "publisher": "Test publisher",
          "url": "https://example.gov.in/test.pdf", "retrieved_at": "2026-11-14T00:00:00+00:00"}


class PdfProcessingTests(unittest.TestCase):
    def test_cleaning_preserves_unicode_and_paragraphs(self):
        self.assertEqual(clean_text("  Cafe\u0301\t বাংলা \x00\n\n\n Next  line "), "Café বাংলা\n\nNext line")

    def test_chunks_cover_text_with_bounded_overlap(self):
        text = "First sentence. Second sentence.\n" * 100
        chunks = list(split_text(text, 100, 20))
        self.assertEqual(chunks[0][0], 0)
        self.assertEqual(chunks[-1][1], len(text))
        for start, end, part in chunks:
            self.assertEqual(part, text[start:end])
            self.assertLessEqual(len(part), 100)
        for previous, current in zip(chunks, chunks[1:]):
            self.assertEqual(current[0], previous[1] - 20)
            self.assertGreater(current[0], previous[0])
        self.assertEqual(list(split_text("")), [])
        for size, overlap in [(0, 0), (10, 10), (10, -1)]:
            with self.assertRaises(ValueError):
                list(split_text("", size, overlap))

    def test_page_provenance_and_blank_page_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.pdf"
            with pymupdf.open() as pdf:
                pdf.new_page().insert_text((72, 72), "First page has enough readable text for extraction.")
                pdf.new_page().insert_text((72, 72), "Second page has separate government source content.")
                pdf.new_page()
                pdf.save(path)
            report, chunks = extract_pdf(path, SOURCE, 30, 5)
            self.assertEqual(report["status"], "requires_review")
            self.assertEqual(report["page_count"], 3)
            self.assertEqual(report["pages"][2]["status"], "no_extractable_text_review_for_scan_or_blank")
            self.assertEqual({c["page_number"] for c in chunks}, {1, 2})
            self.assertEqual(len({c["chunk_id"] for c in chunks}), len(chunks))
            for chunk in chunks:
                self.assertEqual(chunk["source"], SOURCE)
                self.assertEqual(chunk["document_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(len(chunk["text"]), chunk["end_char"] - chunk["start_char"])
            self.assertEqual(extract_pdf(path, SOURCE, 30, 5), (report, chunks))

    def test_image_only_page_has_no_invented_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image.pdf"
            with pymupdf.open() as pdf:
                page = pdf.new_page()
                pix = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 20, 20))
                pix.clear_with(200)
                page.insert_image(pymupdf.Rect(0, 0, 100, 100), pixmap=pix)
                pdf.save(path)
            report, chunks = extract_pdf(path, SOURCE)
            self.assertEqual(chunks, [])
            self.assertEqual(report["status"], "requires_review")

    def test_corrupt_and_encrypted_documents_report_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.pdf"
            path.write_bytes(b"not a pdf")
            report, chunks = extract_pdf(path, SOURCE)
            self.assertEqual(report["status"], "error")
            self.assertTrue(report["errors"])
            self.assertEqual(chunks, [])
            with pymupdf.open() as pdf:
                pdf.new_page()
                pdf.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="secret", owner_pw="owner")
            report, chunks = extract_pdf(path, SOURCE)
            self.assertIn("password", report["errors"][0])
            self.assertEqual(chunks, [])

    def test_official_urls_and_non_pdf_download_rejected(self):
        self.assertTrue(official_url(SOURCE["url"]))
        for url in ["http://example.gov.in/a.pdf", "https://gov.in.evil.com/a.pdf", "file:///a.pdf"]:
            self.assertFalse(official_url(url))
        with tempfile.TemporaryDirectory() as directory, patch("adhikar_ai.pdf_processing.urlopen") as request:
            response = request.return_value.__enter__.return_value
            response.url = SOURCE["url"]
            response.read.return_value = b"<html>Unavailable</html>"
            path = Path(directory) / "no.pdf"
            with self.assertRaisesRegex(ValueError, "not a PDF"):
                download_pdf(SOURCE["url"], path)
            self.assertFalse(path.exists())

    def test_ten_schemes_unchanged_since_phase_2b(self):
        # Git may check out CRLF on Windows; compare the original LF bytes.
        raw = (ROOT / "data/processed/schemes.json").read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(len(json.loads(raw)["schemes"]), 10)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "5f3842eef3e43c1f7d44fff8b192091ca5af92fbb00b63bf970f6e2f35dc3638")


if __name__ == "__main__":
    unittest.main()
