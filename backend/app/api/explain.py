from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.db import get_db
from app.models.alert import ClinicalAlert
from app.models.patient import Patient
from app.models.risk_prediction import RiskPrediction
from app.schemas.explain import AlertOut, ExplanationOut
from app.services.concern_service import classify_concern
from app.services.explain_service import explain_prediction
from app.services.patient_service import assign_staff

router = APIRouter(prefix="/patients", tags=["explain"])
alerts_router = APIRouter(prefix="/alerts", tags=["explain"])
logger = get_logger(__name__)


@router.post("/{patient_id}/explain", response_model=ExplanationOut)
def explain_patient_risk(patient_id: int, db: Session = Depends(get_db)):
    import json

    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    latest_pred = db.scalars(
        select(RiskPrediction)
        .where(RiskPrediction.patient_id == patient_id)
        .order_by(RiskPrediction.created_at.desc())
    ).first()
    if latest_pred is None:
        raise HTTPException(
            status_code=400,
            detail="No risk prediction on record yet. Run a risk prediction first.",
        )

    features = json.loads(latest_pred.features_json)
    explanation = explain_prediction(features)
    routing = classify_concern(features, patient.priority)

    specialist_name = nurse_name = None
    if routing["department"]:
        doctor, nurse = assign_staff(db, routing["department"])
        specialist_name = doctor.name if doctor else None
        nurse_name = nurse.name if nurse else None

        message = (
            f"{patient.full_name} ({patient.mrn}) flagged as {patient.priority} priority "
            f"({latest_pred.probability*100:.1f}% deterioration probability)"
            + (f" with a possible {routing['concern'].lower()}" if routing["concern"] else "")
            + f". Routed to {routing['department']}"
            + (f", assigned to {specialist_name}" if specialist_name else "")
            + "."
        )
        alert = ClinicalAlert(
            patient_id=patient_id,
            priority=patient.priority,
            concern=routing["concern"],
            department=routing["department"],
            specialist_name=specialist_name,
            nurse_name=nurse_name,
            probability=latest_pred.probability,
            message=message,
        )
        db.add(alert)
        db.commit()
        logger.info("Alert generated for patient %s: %s", patient_id, message)

    return ExplanationOut(
        probability=latest_pred.probability,
        confidence=latest_pred.confidence,
        model_used=latest_pred.model_used,
        feature_importance=explanation["feature_importance"],
        explanation_text=explanation["explanation_text"],
        concern=routing["concern"],
        department=routing["department"],
        assigned_specialist=specialist_name,
        assigned_nurse=nurse_name,
        priority=patient.priority,
    )


@router.get("/{patient_id}/alerts", response_model=list[AlertOut])
def list_alerts(patient_id: int, db: Session = Depends(get_db)):
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    alerts = db.scalars(
        select(ClinicalAlert)
        .where(ClinicalAlert.patient_id == patient_id)
        .order_by(ClinicalAlert.created_at.desc())
    ).all()
    return alerts


@alerts_router.get("", response_model=list[AlertOut])
def list_all_alerts(db: Session = Depends(get_db)):
    alerts = db.scalars(
        select(ClinicalAlert).order_by(ClinicalAlert.created_at.desc()).limit(50)
    ).all()
    return alerts
