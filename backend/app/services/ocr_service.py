from functools import lru_cache
from pathlib import Path

from app.core.logging_config import get_logger

logger = get_logger(__name__)

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}


@lru_cache(maxsize=1)
def get_reader():
    import easyocr

    logger.info("Loading EasyOCR reader (en)...")
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    logger.info("EasyOCR reader loaded.")
    return reader


def _ocr_image_bytes(image_bytes: bytes) -> str:
    reader = get_reader()
    results = reader.readtext(image_bytes, detail=0, paragraph=True)
    return "\n".join(results)


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
