"""
api/thumbs.py

Geração de thumbnails (pré-visualização) para PDFs e imagens.
- `pdf_page_thumb(pdf_bytes, page_index) -> (data_url, w, h)`
- `image_thumb(image_bytes) -> (data_url, w, h)`
"""

from __future__ import annotations
import base64, io
from typing import Tuple, Any
from PIL import Image
import fitz  # PyMuPDF

PREVIEW_PDF_DPI = 60
PREVIEW_BOX_W   = 200
PREVIEW_BOX_H   = 300

def _b64_jpeg(img: Image.Image, max_w: int, max_h: int, quality=70) -> str:
    im = img.copy()
    im.thumbnail((max_w, max_h))
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

def pdf_page_thumb(pdf_bytes: bytes, page_index: int) -> Tuple[str, int, int]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page: Any = doc.load_page(page_index)              # tipagem frouxa p/ pylance
    pix = page.get_pixmap(dpi=PREVIEW_PDF_DPI, alpha=False)  # type: ignore[attr-defined]
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)  # <-- tupla
    b64 = _b64_jpeg(img, PREVIEW_BOX_W, PREVIEW_BOX_H, quality=60)
    w, h = int(page.rect.width), int(page.rect.height)
    doc.close()
    return b64, w, h

def image_thumb(image_bytes: bytes) -> Tuple[str, int, int]:
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    # (sem mudança aqui)
    b64 = _b64_jpeg(img, PREVIEW_BOX_W, PREVIEW_BOX_H, quality=70)
    return b64, int(w), int(h)