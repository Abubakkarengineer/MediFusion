import datetime

from pydantic import BaseModel, ConfigDict


class Prediction(BaseModel):
    label: str
    confidence: float


class MedicalImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    modality: str
    filename: str
    top_label: str
    top_confidence: float
    predictions: list[Prediction]
    created_at: datetime.datetime
