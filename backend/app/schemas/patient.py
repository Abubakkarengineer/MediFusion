import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Gender = Literal["Male", "Female", "Other"]
Department = Literal[
    "General Medicine", "Emergency", "Cardiology", "Pulmonology", "ICU"
]
PatientStatus = Literal["Waiting", "In Consultation", "Admitted", "Discharged"]


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    age: int = Field(ge=0, le=130)
    gender: Gender
    contact_number: str | None = Field(default=None, max_length=30)
    chief_complaint: str | None = Field(default=None, max_length=500)
    department: Department = "General Medicine"


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    age: int | None = Field(default=None, ge=0, le=130)
    gender: Gender | None = None
    contact_number: str | None = Field(default=None, max_length=30)
    chief_complaint: str | None = Field(default=None, max_length=500)
    department: Department | None = None
    status: PatientStatus | None = None


class StaffSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: str
    department: str


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mrn: str
    full_name: str
    age: int
    gender: str
    contact_number: str | None
    chief_complaint: str | None
    department: str
    status: str
    priority: str
    assigned_doctor: StaffSummary | None
    assigned_nurse: StaffSummary | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class PatientListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mrn: str
    full_name: str
    age: int
    gender: str
    department: str
    status: str
    priority: str
    assigned_doctor: StaffSummary | None
    assigned_nurse: StaffSummary | None
    created_at: datetime.datetime
