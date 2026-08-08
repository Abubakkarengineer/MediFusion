import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.db import get_db
from app.models.patient import Patient
from app.models.priority_history import PriorityHistory
from app.models.risk_prediction import RiskPrediction
from app.schemas.risk import RiskPredictionOut
from app.services.priority_service import refresh_patient_priority
from app.services.risk_service import get_metrics

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
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    outcome = refresh_patient_priority(db, patient_id)
    if outcome is None:
        raise HTTPException(
            status_code=400, detail="No complete vital reading recorded for this patient yet"
        )

    latest_pred = db.scalars(
        select(RiskPrediction)
        .where(RiskPrediction.patient_id == patient_id)
        .order_by(RiskPrediction.created_at.desc())
    ).first()
    return _to_out(latest_pred)


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


@router.get("/{patient_id}/priority-history")
def list_priority_history(patient_id: int, db: Session = Depends(get_db)):
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    rows = db.scalars(
        select(PriorityHistory)
        .where(PriorityHistory.patient_id == patient_id)
        .order_by(PriorityHistory.changed_at.desc())
    ).all()
    return [
        {
            "id": r.id,
            "previous_priority": r.previous_priority,
            "new_priority": r.new_priority,
            "probability": r.probability,
            "reason": r.reason,
            "changed_at": r.changed_at,
        }
        for r in rows
    ]
