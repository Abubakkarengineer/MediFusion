from fastapi import APIRouter

from app.core.constants import DEPARTMENTS, GENDERS, PATIENT_STATUSES, PRIORITY_LEVELS

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/options")
def get_options() -> dict:
    return {
        "departments": DEPARTMENTS,
        "genders": GENDERS,
        "statuses": PATIENT_STATUSES,
        "priorities": PRIORITY_LEVELS,
    }
