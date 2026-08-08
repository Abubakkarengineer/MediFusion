import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.core.priority_rules import priority_from_probability
from app.models.patient import Patient
from app.models.priority_history import PriorityHistory
from app.models.risk_prediction import RiskPrediction
from app.models.vital import VitalObservation
from app.services.risk_service import predict_risk

logger = get_logger(__name__)


def refresh_patient_priority(db: Session, patient_id: int) -> dict | None:
    """Recomputes risk from the latest vitals and updates the patient's
    priority if it changed, logging the transition. Called whenever new
    vitals arrive (manual or simulated) or a prediction is explicitly run.
    Returns None if there isn't enough data yet (no vitals recorded).
    """
    patient = db.get(Patient, patient_id)
    if patient is None:
        return None

    latest_vital = db.scalars(
        select(VitalObservation)
        .where(VitalObservation.patient_id == patient_id)
        .order_by(VitalObservation.recorded_at.desc())
    ).first()
    if latest_vital is None:
        return None

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
        return None

    result = predict_risk(feature_values)

    prediction = RiskPrediction(
        patient_id=patient_id,
        probability=result["probability"],
        confidence=result["confidence"],
        model_used=result["model_used"],
        features_json=json.dumps(result["features"]),
    )
    db.add(prediction)

    new_priority = priority_from_probability(result["probability"])
    previous_priority = patient.priority
    transitioned = new_priority != previous_priority

    if transitioned:
        db.add(PriorityHistory(
            patient_id=patient_id,
            previous_priority=previous_priority,
            new_priority=new_priority,
            probability=result["probability"],
            reason=(
                f"Deterioration probability {result['probability']*100:.1f}% "
                f"from latest vitals (model: {result['model_used']})"
            ),
        ))
        patient.priority = new_priority
        logger.info(
            "Patient %s priority transition: %s -> %s (p=%.3f)",
            patient_id, previous_priority, new_priority, result["probability"],
        )

    db.commit()

    return {
        "probability": result["probability"],
        "confidence": result["confidence"],
        "previous_priority": previous_priority,
        "new_priority": new_priority,
        "transitioned": transitioned,
    }
