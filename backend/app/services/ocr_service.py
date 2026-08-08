import io
from pathlib import Path

from app.core.logging_config import get_logger

logger = get_logger(__name__)

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}


def _ocr_image_bytes(image_bytes: bytes) -> str:
    import pytesseract
    from PIL import Image

    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image)


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
