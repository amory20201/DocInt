"""Input layer: accepts PDF or image files and normalises them."""
from __future__ import annotations
import io, mimetypes, os, subprocess, tempfile
from dataclasses import dataclass, field

MAX_PAGES = 5
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
MAX_BYTES = 20 * 1024 * 1024


class UnsupportedFile(ValueError):
    pass


@dataclass
class Document:
    name: str
    raw: bytes
    mime: str
    is_pdf: bool
    images: list = field(default_factory=list)      # list[PIL.Image] (page renders / the image itself)
    text_layer: str = ""                            # embedded text of PDFs (empty for scans / images)
    pages: int = 1


def load(path: str) -> Document:
    from PIL import Image
    ext = os.path.splitext(path)[1].lower()
    if not os.path.isfile(path):
        raise UnsupportedFile(f"File not found: {path}")
    with open(path, "rb") as fh:
        raw = fh.read()
    if len(raw) > MAX_BYTES:
        raise UnsupportedFile("File is larger than 20 MB.")
    name = os.path.basename(path)

    if ext == ".pdf" or raw[:5] == b"%PDF-":
        import pdfplumber
        text, pages = [], 0
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            pages = len(pdf.pages)
            for p in pdf.pages[:MAX_PAGES]:
                text.append(p.extract_text() or "")
        doc = Document(name, raw, "application/pdf", True, text_layer="\n".join(text).strip(), pages=pages)
        doc.images = _render_pdf(path)
        return doc

    if ext in IMAGE_EXT:
        img = Image.open(io.BytesIO(raw))
        img.load()
        return Document(name, raw, mimetypes.guess_type(path)[0] or "image/png", False,
                        images=[img.convert("RGB")])

    raise UnsupportedFile(f"Unsupported file type '{ext}'. Use PDF, JPG, PNG, WEBP, BMP or TIFF.")


def _render_pdf(path: str):
    """Render pages to images (needed for OCR of scanned PDFs and for display)."""
    from PIL import Image
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-r", "150", "-l", str(MAX_PAGES), "-png", path, os.path.join(d, "p")],
                       check=True, capture_output=True)
        return [Image.open(os.path.join(d, f)).convert("RGB") for f in sorted(os.listdir(d))]
