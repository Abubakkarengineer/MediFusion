from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api import auth, explain, fusion, images, meta, ocr, patients, risk, speech, staff, system
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.logging_config import get_logger, setup_logging
from app.db import SessionLocal, init_db
from app.services.auth_service import seed_demo_users
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
        seed_demo_users(db)
    finally:
        db.close()
    logger.info("%s startup complete (env=%s)", settings.app_name, settings.environment)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


# Public: health/disclaimer and login itself.
app.include_router(system.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# Everything else requires a valid Admin or Doctor session token.
_auth_dep = [Depends(get_current_user)]
app.include_router(meta.router, prefix="/api", dependencies=_auth_dep)
app.include_router(patients.router, prefix="/api", dependencies=_auth_dep)
app.include_router(staff.router, prefix="/api", dependencies=_auth_dep)
app.include_router(speech.router, prefix="/api", dependencies=_auth_dep)
app.include_router(ocr.router, prefix="/api", dependencies=_auth_dep)
app.include_router(images.router, prefix="/api", dependencies=_auth_dep)
app.include_router(fusion.router, prefix="/api", dependencies=_auth_dep)
app.include_router(risk.router, prefix="/api", dependencies=_auth_dep)
app.include_router(risk.ml_router, prefix="/api", dependencies=_auth_dep)
app.include_router(explain.router, prefix="/api", dependencies=_auth_dep)
app.include_router(explain.alerts_router, prefix="/api", dependencies=_auth_dep)
