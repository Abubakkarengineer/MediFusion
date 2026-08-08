import datetime

from pydantic import BaseModel, ConfigDict


class RiskPredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    patient_id: int
    probability: float
    confidence: float
    model_used: str
    features: dict[str, float]
    created_at: datetime.datetime
