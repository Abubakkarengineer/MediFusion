from functools import lru_cache

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Public demo chest X-ray classifier (pneumonia vs normal). This is the
# scope of what this model can meaningfully assess -- results are only
# indicative for chest X-ray-style images, not a general CT/MRI reader.
MODEL_NAME = "nickmuchi/vit-finetuned-chest-xray-pneumonia"


class ImagingUnavailableError(RuntimeError):
    """Raised when the vision model isn't installed in this deployment."""


@lru_cache(maxsize=1)
def get_pipeline():
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise ImagingUnavailableError(
            "AI-assisted image analysis is disabled on this deployment (the "
            "vision model needs more memory than this hosting tier provides). "
            "Install 'transformers' and run the backend locally to use this "
            "feature."
        ) from exc

    logger.info("Loading image classification model '%s'...", MODEL_NAME)
    pipe = pipeline("image-classification", model=MODEL_NAME)
    logger.info("Image classification model loaded.")
    return pipe


def classify_image(file_path: str) -> list[dict]:
    from PIL import Image

    pipe = get_pipeline()
    image = Image.open(file_path).convert("RGB")
    results = pipe(image)
    return [{"label": r["label"], "confidence": round(float(r["score"]), 4)} for r in results]
