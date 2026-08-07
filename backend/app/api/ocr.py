import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import OCR_UPLOADS_DIR
from app.core.logging_config import get_logger
from app.core.ocr_lexicon import extract_lab_values, extract_medicines, extract_patient_info
from app.db import get_db
from app.models.ocr_document import OCRDocument
from app.models.patient import Patient
from app.schemas.ocr import OCRDocumentOut
from app.services.ocr_service import extract_text

router = APIRouter(prefix="/patients", tags=["ocr"])
logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp", ".pdf"}
ALLOWED_DOCUMENT_TYPES = {"Prescription", "Lab Report"}


def _to_out(doc: OCRDocument) -> OCRDocumentOut:
    return OCRDocumentOut(
        id=doc.id,
        patient_id=doc.patient_id,
        document_type=doc.document_type,
        filename=doc.filename,
        raw_text=doc.raw_text,
        medicines=json.loads(doc.medicines_json),
        lab_values=json.loads(doc.lab_values_json),
        patient_info=json.loads(doc.patient_info_json),
        created_at=doc.created_at,
    )


@router.post("/{patient_id}/ocr", response_model=OCRDocumentOut, status_code=201)
async def upload_ocr_document(
    patient_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"document_type must be one of {sorted(ALLOWED_DOCUMENT_TYPES)}",
        )

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{suffix}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    saved_name = f"{uuid.uuid4().hex}{suffix}"
    saved_path = OCR_UPLOADS_DIR / saved_name
    contents = await file.read()
    saved_path.write_bytes(contents)

    try:
        raw_text = extract_text(str(saved_path))
    except Exception as exc:
        logger.exception("OCR extraction failed for patient %s", patient_id)
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {exc}") from exc

    medicines = extract_medicines(raw_text) if document_type == "Prescription" else []
    lab_values = extract_lab_values(raw_text) if document_type == "Lab Report" else []
    patient_info = extract_patient_info(raw_text)

    doc = OCRDocument(
        patient_id=patient_id,
        document_type=document_type,
        filename=file.filename or saved_name,
        raw_text=raw_text,
        medicines_json=json.dumps(medicines),
        lab_values_json=json.dumps(lab_values),
        patient_info_json=json.dumps(patient_info),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    logger.info(
        "OCR document %s (%s) saved for patient %s: %d medicines, %d lab values",
        doc.id, document_type, patient_id, len(medicines), len(lab_values),
    )
    return _to_out(doc)


@router.get("/{patient_id}/ocr", response_model=list[OCRDocumentOut])
def list_ocr_documents(patient_id: int, db: Session = Depends(get_db)):
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    docs = db.scalars(
        select(OCRDocument)
        .where(OCRDocument.patient_id == patient_id)
        .order_by(OCRDocument.created_at.desc())
    ).all()
    return [_to_out(d) for d in docs]
