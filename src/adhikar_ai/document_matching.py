"""Read personal uploads in memory only; never save or index their contents."""

from pathlib import Path

import pymupdf

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 20
MAX_CHARS = 20000


class UploadError(ValueError):
    """A safe, user-facing upload validation message."""


def extract_upload(name, content):
    """Return local text or a safe error without filenames or document contents."""
    if not content or len(content) > MAX_BYTES:
        raise ValueError("Upload a nonempty file no larger than 5 MB.")
    suffix = Path(name).suffix.lower()
    if suffix == ".txt":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeError:
            raise ValueError("Text files must use UTF-8 encoding.") from None
    elif suffix == ".pdf":
        try:
            with pymupdf.open(stream=content, filetype="pdf") as document:
                if document.needs_pass:
                    raise UploadError("Password-protected PDFs are not supported.")
                if len(document) > MAX_PAGES:
                    raise UploadError("Upload a PDF with no more than 20 pages.")
                parts = []
                for page in document:
                    part = page.get_text()
                    if not part.strip():
                        raise UploadError("A PDF page has no readable text. Use a text-based PDF or enter your details below.")
                    parts.append(part)
                    if sum(map(len, parts)) > MAX_CHARS:
                        raise UploadError("Document is too long. Use a shorter document or enter a summary.")
                text = "\n".join(parts)
        except UploadError:
            raise
        except Exception:
            raise ValueError("This PDF could not be read. Use a valid text-based PDF.") from None
    else:
        raise ValueError("Only PDF and TXT files are supported.")
    text = text.strip()
    if not text:
        raise ValueError("No readable text was found. Enter your details below.")
    if len(text) > MAX_CHARS:
        raise ValueError("Document is too long. Use a shorter document or enter a summary.")
    return text


def application_links(scheme):
    """Use only the dataset's cited application guidance, never guessed form URLs."""
    ids = scheme["application_process"]["source_ids"]
    sources = {source["source_id"]: source for source in scheme["sources"]}
    return [{"title": sources[sid]["title"], "url": sources[sid]["url"]} for sid in ids]

