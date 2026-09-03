from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class Chunk:
    text: str
    source: str
    page: int


def extract_pdf(data: bytes, filename: str = "upload.pdf") -> list[Chunk]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF ingestion") from exc
    document = fitz.open(stream=data, filetype="pdf")
    chunks: list[Chunk] = []
    for page_number, page in enumerate(document, 1):
        blocks = page.get_text("blocks")
        header = Path(filename).stem.replace("_", " ")
        for block in blocks:
            text = re.sub(r"\s+", " ", block[4]).strip()
            if not text:
                continue
            lines = text.split(". ")
            for part in lines:
                if part.strip():
                    chunks.append(Chunk(f"[{header} | page {page_number}]\n{part.strip()}", filename, page_number))
    return chunks