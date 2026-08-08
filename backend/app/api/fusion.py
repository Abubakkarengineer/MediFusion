import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.medical_image import MedicalImage
from app.models.ocr_document import OCRDocument
from app.models.patient import Patient
from app.models.speech_note import SpeechNote
from app.models.vital import VitalObservation
from app.schemas.patient import PatientOut

router = APIRouter(prefix="/patients", tags=["fusion"])


@router.get("/{patient_id}/profile")
def get_patient_profile(patient_id: int, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    vitals = db.scalars(
        select(VitalObservation)
        .where(VitalObservation.patient_id == patient_id)
        .order_by(VitalObservation.recorded_at.desc())
    ).all()
    speech_notes = db.scalars(
        select(SpeechNote)
        .where(SpeechNote.patient_id == patient_id)
        .order_by(SpeechNote.created_at.desc())
    ).all()
    ocr_documents = db.scalars(
        select(OCRDocument)
        .where(OCRDocument.patient_id == patient_id)
        .order_by(OCRDocument.created_at.desc())
    ).all()
    images = db.scalars(
        select(MedicalImage)
        .where(MedicalImage.patient_id == patient_id)
        .order_by(MedicalImage.created_at.desc())
    ).all()

    seen_symptoms = {}  # lowercase -> display form, dedupes case variants across notes
    for note in speech_notes:
        for s in note.extracted_symptoms.split(","):
            if s and s.lower() not in seen_symptoms:
                seen_symptoms[s.lower()] = s
    all_symptoms = sorted(seen_symptoms.values())

    seen_medicine_names = set()
    seen_lab_names = set()
    all_medicines = []
    all_abnormal_labs = []
    for doc in ocr_documents:
        for med in json.loads(doc.medicines_json):
            if med["name"] not in seen_medicine_names:
                seen_medicine_names.add(med["name"])
                all_medicines.append(med)
        for lab in json.loads(doc.lab_values_json):
            if lab["flag"] != "Normal" and lab["test_name"] not in seen_lab_names:
                seen_lab_names.add(lab["test_name"])
                all_abnormal_labs.append(lab)

    return {
        "patient": PatientOut.model_validate(patient).model_dump(mode="json"),
        "latest_vital": (
            {
                "heart_rate": vitals[0].heart_rate,
                "systolic_bp": vitals[0].systolic_bp,
                "diastolic_bp": vitals[0].diastolic_bp,
                "spo2": vitals[0].spo2,
                "respiratory_rate": vitals[0].respiratory_rate,
                "temperature": vitals[0].temperature,
                "recorded_at": vitals[0].recorded_at.isoformat(),
            }
            if vitals else None
        ),
        "vitals_count": len(vitals),
        "combined_symptoms": all_symptoms,
        "active_medicines": all_medicines,
        "abnormal_lab_values": all_abnormal_labs,
        "speech_notes_count": len(speech_notes),
        "ocr_documents_count": len(ocr_documents),
        "images_count": len(images),
        "latest_image": (
            {
                "modality": images[0].modality,
                "top_label": images[0].top_label,
                "top_confidence": images[0].top_confidence,
                "created_at": images[0].created_at.isoformat(),
            }
            if images else None
        ),
    }
