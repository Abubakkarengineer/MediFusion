import datetime

from pydantic import BaseModel, ConfigDict


class FeatureContribution(BaseModel):
    feature: str
    label: str
    value: float
    contribution: float


class ExplanationOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    probability: float
    confidence: float
    model_used: str
    feature_importance: list[FeatureContribution]
    explanation_text: str
    causation_disclaimer: str = (
        "This explanation describes model behavior for this single prediction, "
        "not proof of medical causation. Overlapping patterns and unrelated "
        "causes can produce similar vitals -- clinical correlation required."
    )
    concern: str | None
    department: str | None
    assigned_specialist: str | None
    assigned_nurse: str | None
    priority: str


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    patient_id: int
    priority: str
    concern: str | None
    department: str | None
    specialist_name: str | None
    nurse_name: str | None
    probability: float
    message: str
    created_at: datetime.datetime
