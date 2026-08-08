import io
import os
import shutil
from pathlib import Path

from app.core.logging_config import get_logger

logger = get_logger(__name__)

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}

# On Linux (Docker/production) 'apt-get install tesseract-ocr' puts the
# binary on PATH automatically. On Windows local dev it commonly isn't,
# even right after installing it, so allow an explicit override.
_TESSERACT_CMD = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract")


def _ocr_image_bytes(image_bytes: bytes) -> str:
    import pytesseract
    from PIL import Image

    if _TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD

    image = Image.open(io.BytesIO(image_bytes))
    try:
        return pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR engine not found. Install it and ensure it's on "
            "PATH, or set the TESSERACT_CMD environment variable to its "
            "full executable path."
        ) from exc


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in IMAGE_EXTENSIONS:
        return _ocr_image_bytes(path.read_bytes())

    if suffix in PDF_EXTENSIONS:
        import fitz  # PyMuPDF

        text_parts = []
        doc = fitz.open(str(path))
        try:
            for page in doc:
                pixmap = page.get_pixmap(dpi=200)
                image_bytes = pixmap.tobytes("png")
                text_parts.append(_ocr_image_bytes(image_bytes))
        finally:
            doc.close()
        return "\n".join(text_parts)

    raise ValueError(f"Unsupported file type: {suffix}")
