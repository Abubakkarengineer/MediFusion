import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.db import get_db
from app.models.patient import Patient
from app.models.risk_prediction import RiskPrediction
from app.models.vital import VitalObservation
from app.schemas.risk import RiskPredictionOut
from app.services.risk_service import get_metrics, predict_risk

router = APIRouter(prefix="/patients", tags=["risk"])
ml_router = APIRouter(prefix="/ml", tags=["risk"])
logger = get_logger(__name__)


def _to_out(pred: RiskPrediction) -> RiskPredictionOut:
    return RiskPredictionOut(
        id=pred.id,
        patient_id=pred.patient_id,
        probability=pred.probability,
        confidence=pred.confidence,
        model_used=pred.model_used,
        features=json.loads(pred.features_json),
        created_at=pred.created_at,
    )


@ml_router.get("/metrics")
def model_metrics():
    return get_metrics()


@router.post("/{patient_id}/risk/predict", response_model=RiskPredictionOut, status_code=201)
def run_risk_prediction(patient_id: int, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    latest_vital = db.scalars(
        select(VitalObservation)
        .where(VitalObservation.patient_id == patient_id)
        .order_by(VitalObservation.recorded_at.desc())
    ).first()
    if latest_vital is None:
        raise HTTPException(status_code=400, detail="No vitals recorded for this patient yet")

    feature_values = {
        "age": patient.age,
        "heart_rate": latest_vital.heart_rate,
        "systolic_bp": latest_vital.systolic_bp,
        "diastolic_bp": latest_vital.diastolic_bp,
        "spo2": latest_vital.spo2,
        "respiratory_rate": latest_vital.respiratory_rate,
        "temperature": latest_vital.temperature,
    }
    if any(v is None for v in feature_values.values()):
        raise HTTPException(status_code=400, detail="Latest vital reading is incomplete")

    result = predict_risk(feature_values)

    pred = RiskPrediction(
        patient_id=patient_id,
        probability=result["probability"],
        confidence=result["confidence"],
        model_used=result["model_used"],
        features_json=json.dumps(result["features"]),
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    logger.info(
        "Risk prediction %s for patient %s: p=%.3f (%s)",
        pred.id, patient_id, pred.probability, pred.model_used,
    )
    return _to_out(pred)


@router.get("/{patient_id}/risk", response_model=list[RiskPredictionOut])
def list_risk_predictions(patient_id: int, db: Session = Depends(get_db)):
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    preds = db.scalars(
        select(RiskPrediction)
        .where(RiskPrediction.patient_id == patient_id)
        .order_by(RiskPrediction.created_at.desc())
    ).all()
    return [_to_out(p) for p in preds]
