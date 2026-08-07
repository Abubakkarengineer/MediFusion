from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.environment,
    }


@router.get("/disclaimer")
def get_disclaimer() -> dict:
    return {"disclaimer": settings.clinical_disclaimer}
