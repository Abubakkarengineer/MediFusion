import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import IMAGE_UPLOADS_DIR
from app.core.logging_config import get_logger
from app.db import get_db
from app.models.medical_image import MedicalImage
from app.models.patient import Patient
from app.schemas.image import MedicalImageOut
from app.services.image_service import ImagingUnavailableError, classify_image

router = APIRouter(prefix="/patients", tags=["imaging"])
logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
ALLOWED_MODALITIES = {"X-ray", "CT", "MRI"}


def _to_out(img: MedicalImage) -> MedicalImageOut:
    return MedicalImageOut(
        id=img.id,
        patient_id=img.patient_id,
        modality=img.modality,
        filename=img.filename,
        top_label=img.top_label,
        top_confidence=img.top_confidence,
        predictions=json.loads(img.predictions_json),
        created_at=img.created_at,
    )


@router.post("/{patient_id}/images", response_model=MedicalImageOut, status_code=201)
async def upload_medical_image(
    patient_id: int,
    modality: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    if modality not in ALLOWED_MODALITIES:
        raise HTTPException(status_code=400, detail=f"modality must be one of {sorted(ALLOWED_MODALITIES)}")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{suffix}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    saved_name = f"{uuid.uuid4().hex}{suffix}"
    saved_path = IMAGE_UPLOADS_DIR / saved_name
    contents = await file.read()
    saved_path.write_bytes(contents)

    try:
        predictions = classify_image(str(saved_path))
    except ImagingUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Image classification failed for patient %s", patient_id)
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {exc}") from exc

    top = max(predictions, key=lambda p: p["confidence"]) if predictions else {"label": "Unknown", "confidence": 0.0}

    img = MedicalImage(
        patient_id=patient_id,
        modality=modality,
        filename=file.filename or saved_name,
        top_label=top["label"],
        top_confidence=top["confidence"],
        predictions_json=json.dumps(predictions),
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    logger.info(
        "Medical image %s (%s) saved for patient %s: top=%s (%.2f)",
        img.id, modality, patient_id, top["label"], top["confidence"],
    )
    return _to_out(img)


@router.get("/{patient_id}/images", response_model=list[MedicalImageOut])
def list_medical_images(patient_id: int, db: Session = Depends(get_db)):
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    images = db.scalars(
        select(MedicalImage)
        .where(MedicalImage.patient_id == patient_id)
        .order_by(MedicalImage.created_at.desc())
    ).all()
    return [_to_out(i) for i in images]
