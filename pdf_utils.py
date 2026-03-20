import re
from pathlib import Path
from typing import Optional


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber (preferred) with PyPDF2 fallback."""
    text = ""

    # Try pdfplumber first — better layout preservation
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
            text = "\n\n".join(pages)
        if text.strip():
            return clean_text(text)
    except ImportError:
        pass
    except Exception as e:
        print(f"pdfplumber failed: {e}, trying PyPDF2...")

    # Fallback to PyPDF2
    try:
        import PyPDF2
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pages = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
            text = "\n\n".join(pages)
        if text.strip():
            return clean_text(text)
    except ImportError:
        raise ImportError("Please install pdfplumber: pip install pdfplumber")
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")

    return text


def clean_text(text: str) -> str:
    """Clean extracted PDF text — remove artifacts, fix spacing."""
    # Remove null bytes and weird control chars
    text = text.replace("\x00", "").replace("\r", "\n")
    # Collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Fix hyphenation across lines (e.g., "meth-\nodology" → "methodology")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Remove page numbers (standalone numbers on a line)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    # Strip excessive spaces
    text = re.sub(r" {3,}", " ", text)
    return text.strip()


def fetch_pdf_from_url(url: str, save_path: str = "/tmp/paper.pdf") -> str:
    """Download a PDF from URL and extract its text."""
    import requests

    headers = {"User-Agent": "Mozilla/5.0 (research-paper-analyzer/1.0)"}

    # Handle arXiv URLs — convert abs/ to pdf/
    if "arxiv.org/abs/" in url:
        url = url.replace("/abs/", "/pdf/")
        if not url.endswith(".pdf"):
            url += ".pdf"

    response = requests.get(url, headers=headers, timeout=30, stream=True)
    response.raise_for_status()

    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return extract_text_from_pdf(save_path)


def truncate_for_context(text: str, max_chars: int = 12000) -> str:
    """
    Smart truncation: keep beginning (abstract/intro) and end (references/conclusion).
    Most important content is at the edges of academic papers.
    """
    if len(text) <= max_chars:
        return text

    half = max_chars // 2
    head = text[:half]
    tail = text[-half:]
    return head + "\n\n[...middle section truncated for context window...]\n\n" + tail
