from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
SPEECH_UPLOADS_DIR = UPLOADS_DIR / "speech"
OCR_UPLOADS_DIR = UPLOADS_DIR / "ocr"


class Settings(BaseSettings):
    app_name: str = "MediFusion AI"
    app_tagline: str = "Multimodal Clinical Intelligence Platform"
    environment: str = "hackathon-demo"
    database_url: str = f"sqlite:///{(DATA_DIR / 'medifusion.db').as_posix()}"
    cors_origins: list[str] = ["*"]

    # Shown throughout the UI and attached to every AI-generated output.
    clinical_disclaimer: str = (
        "AI-Assisted Clinical Decision Support — outputs are generated from "
        "demonstration/synthetic data to illustrate the workflow. They "
        "assist, but never replace, the judgment of a qualified healthcare "
        "professional. Final clinical decisions always rest with the doctor."
    )


settings = Settings()

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
SPEECH_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OCR_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
