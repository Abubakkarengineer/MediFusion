from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import images, meta, ocr, patients, speech, staff, system
from app.core.config import settings
from app.core.logging_config import get_logger, setup_logging
from app.db import SessionLocal, init_db
from app.services.patient_service import seed_demo_staff

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    description=settings.app_tagline,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_demo_staff(db)
    finally:
        db.close()
    logger.info("%s startup complete (env=%s)", settings.app_name, settings.environment)


app.include_router(system.router, prefix="/api")
app.include_router(meta.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(staff.router, prefix="/api")
app.include_router(speech.router, prefix="/api")
app.include_router(ocr.router, prefix="/api")
app.include_router(images.router, prefix="/api")
