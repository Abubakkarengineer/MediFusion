import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VitalCreate(BaseModel):
    heart_rate: float | None = Field(default=None, ge=0, le=300)
    systolic_bp: float | None = Field(default=None, ge=0, le=300)
    diastolic_bp: float | None = Field(default=None, ge=0, le=250)
    spo2: float | None = Field(default=None, ge=0, le=100)
    respiratory_rate: float | None = Field(default=None, ge=0, le=100)
    temperature: float | None = Field(default=None, ge=25, le=45)
    source: Literal["manual", "simulated"] = "manual"


class VitalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    heart_rate: float | None
    systolic_bp: float | None
    diastolic_bp: float | None
    spo2: float | None
    respiratory_rate: float | None
    temperature: float | None
    source: str
    recorded_at: datetime.datetime
