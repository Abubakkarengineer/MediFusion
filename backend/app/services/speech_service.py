import os
from functools import lru_cache

from app.core.logging_config import get_logger

logger = get_logger(__name__)

WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")
WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")


@lru_cache(maxsize=1)
def get_model():
    from faster_whisper import WhisperModel

    logger.info("Loading Whisper model '%s' (compute_type=%s)...", WHISPER_MODEL_SIZE, WHISPER_COMPUTE_TYPE)
    model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type=WHISPER_COMPUTE_TYPE)
    logger.info("Whisper model loaded.")
    return model


def transcribe_audio(file_path: str) -> tuple[str, str | None]:
    model = get_model()
    segments, info = model.transcribe(file_path, beam_size=1)
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    language = getattr(info, "language", None)
    return transcript, language
