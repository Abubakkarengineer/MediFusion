import os
from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[3]
# Overridable so a deployment can point this at a mounted persistent disk
# (e.g. Render Disks) -- otherwise the SQLite DB and uploads are wiped on
# every redeploy since the rest of the filesystem is ephemeral.
DATA_DIR = Path(os.environ.get("MEDIFUSION_DATA_DIR", str(BASE_DIR / "data")))
UPLOADS_DIR = DATA_DIR / "uploads"
SPEECH_UPLOADS_DIR = UPLOADS_DIR / "speech"
OCR_UPLOADS_DIR = UPLOADS_DIR / "ocr"
IMAGE_UPLOADS_DIR = UPLOADS_DIR / "images"


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
IMAGE_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
