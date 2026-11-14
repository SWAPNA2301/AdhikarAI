"""Download official PDFs and extract page-local text; no OCR or inference."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import pymupdf


def clean_text(text):
    """Normalize Unicode and whitespace without translating or repairing words."""
    text = unicodedata.normalize("NFC", text)
    text = "".join(c for c in text if c in "\n\t" or unicodedata.category(c) != "Cc")
    lines = [re.sub(r"[^\S\n]+", " ", line).strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def split_text(text, max_chars=1200, overlap=150):
    """Yield exact substrings and offsets in cleaned text; never cross a page."""
    if max_chars <= 0 or not 0 <= overlap < max_chars:
        raise ValueError("Require max_chars > 0 and 0 <= overlap < max_chars")
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = max(text.rfind("\n", start, end), text.rfind(" ", start, end))
            if boundary > start + max(overlap, max_chars // 2):
                end = boundary + 1
        yield start, end, text[start:end]
        if end == len(text):
            break
        start = end - overlap


def extract_pdf(path, source, max_chars=1200, overlap=150):
    """Return a document report and chunks, retaining explicit extraction failures."""
    list(split_text("", max_chars, overlap))  # Validate even for empty PDFs.
    report = {"source": dict(source), "status": "error", "pages": [], "errors": []}
    chunks = []
    try:
        payload = Path(path).read_bytes()
        report["sha256"] = hashlib.sha256(payload).hexdigest()
        with pymupdf.open(stream=payload, filetype="pdf") as document:
            if document.needs_pass:
                raise ValueError("Encrypted PDF requires a password")
            report["page_count"] = len(document)
            report["pdf_metadata"] = document.metadata
            for page_number, page in enumerate(document, 1):
                page_report = {"page_number": page_number}
                try:
                    text = clean_text(page.get_text("text", sort=True))
                    # Heuristic warning only: an empty page may be blank, scanned,
                    # or have unsupported text. No OCR content is manufactured.
                    if not text:
                        status = "no_extractable_text_review_for_scan_or_blank"
                    elif "\ufffd" in text or sum(c.isalnum() for c in text) < 20:
                        status = "suspect_text_requires_review"
                    else:
                        status = "extracted"
                    page_report.update(status=status, cleaned_characters=len(text))
                    for index, (start, end, part) in enumerate(split_text(text, max_chars, overlap), 1):
                        chunks.append({
                            "chunk_id": f"{source['document_id']}:p{page_number}:c{index}",
                            "source": dict(source), "document_sha256": report["sha256"],
                            "page_number": page_number, "chunk_index": index,
                            "start_char": start, "end_char": end,
                            "page_status": status, "text": part,
                        })
                except Exception as exc:
                    page_report.update(status="unreadable", error=str(exc))
                    report["errors"].append(f"Page {page_number}: {exc}")
                report["pages"].append(page_report)
            report["status"] = "extracted" if report["pages"] and all(
                p["status"] == "extracted" for p in report["pages"]
            ) else "requires_review"
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    report["chunk_count"] = len(chunks)
    return report, chunks


def official_url(url):
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return parsed.scheme == "https" and host.endswith((".gov.in", ".nic.in"))


def download_pdf(url, destination):
    """Bound downloads and reject non-government redirects and non-PDF responses."""
    if not official_url(url):
        raise ValueError("Expected an HTTPS government URL")
    with urlopen(Request(url, headers={"User-Agent": "AdhikarAI/0.1 PDF research"}), timeout=45) as response:
        if not official_url(response.url):
            raise ValueError("Download redirected outside supported government domains")
        payload = response.read(25 * 1024 * 1024 + 1)
        if len(payload) > 25 * 1024 * 1024:
            raise ValueError("PDF exceeds 25 MiB limit")
        if not payload.lstrip().startswith(b"%PDF-"):
            raise ValueError("Response is not a PDF")
        final_url = response.url
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    Path(destination).write_bytes(payload)
    return final_url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("docs/pdf_sources.json"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/pdfs"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/pdf_chunks.json"))
    args = parser.parse_args()
    sources = json.loads(args.manifest.read_text(encoding="utf-8"))
    ids = [s["document_id"] for s in sources]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r"[a-z0-9-]+", i) for i in ids):
        parser.error("Source IDs must be unique lowercase filename-safe identifiers")
    result = {"schema_version": "1.0.0", "generated_at": datetime.now(timezone.utc).isoformat(),
              "extractor": {"name": "PyMuPDF", "version": pymupdf.VersionBind},
              "chunking": {"max_chars": 1200, "overlap": 150, "offset_basis": "cleaned page text"},
              "documents": [], "chunks": []}
    for original in sources:
        source = dict(original)
        source["retrieved_at"] = datetime.now(timezone.utc).isoformat()
        path = args.raw_dir / f"{source['document_id']}.pdf"
        try:
            source["resolved_url"] = download_pdf(source["url"], path)
            report, chunks = extract_pdf(path, source)
        except Exception as exc:
            source.pop("retrieved_at", None)
            report = {"source": source, "status": "download_error", "pages": [],
                      "chunk_count": 0, "errors": [f"{type(exc).__name__}: {exc}"]}
            chunks = []
        result["documents"].append(report)
        result["chunks"].extend(chunks)
        print(f"{source['document_id']}: {report['status']}, {len(chunks)} chunks; {report['errors']}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(result['chunks'])} chunks to {args.output}")
    return int(any(d["status"] in ("error", "download_error") or d["errors"] for d in result["documents"]))


if __name__ == "__main__":
    raise SystemExit(main())
