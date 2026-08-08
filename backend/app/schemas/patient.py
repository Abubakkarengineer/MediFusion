import datetime
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Gender = Literal["Male", "Female", "Other"]
Department = Literal[
    "General Medicine", "Emergency", "Cardiology", "Pulmonology", "ICU"
]
PatientStatus = Literal["Waiting", "In Consultation", "Admitted", "Discharged"]

# Letters (incl. accented), spaces, hyphens, apostrophes, periods -- no
# digits or other characters, so placeholder/junk entries like "asdf123"
# or "N/A" can't be registered as a patient's name.
NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ɏ][A-Za-zÀ-ɏ .'-]{1,119}$")
MOBILE_PATTERN = re.compile(r"^\d{10}$")


def _validate_name(value: str) -> str:
    cleaned = value.strip()
    if not NAME_PATTERN.match(cleaned):
        raise ValueError(
            "Enter a real name using letters only (spaces, hyphens and "
            "apostrophes allowed) -- no digits or symbols."
        )
    if cleaned.replace(" ", "").replace("-", "").replace("'", "").replace(".", "") == "":
        raise ValueError("Name cannot be blank.")
    return cleaned


def _validate_mobile(value: str) -> str:
    cleaned = value.strip()
    if not MOBILE_PATTERN.match(cleaned):
        raise ValueError("Enter a valid 10-digit mobile number (digits only, no spaces or symbols).")
    return cleaned


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    age: int = Field(ge=0, le=130)
    gender: Gender
    contact_number: str = Field(max_length=10)
    chief_complaint: str | None = Field(default=None, max_length=500)
    department: Department = "General Medicine"

    _validate_full_name = field_validator("full_name")(_validate_name)
    _validate_contact_number = field_validator("contact_number")(_validate_mobile)


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    age: int | None = Field(default=None, ge=0, le=130)
    gender: Gender | None = None
    contact_number: str | None = Field(default=None, max_length=10)
    chief_complaint: str | None = Field(default=None, max_length=500)
    department: Department | None = None
    status: PatientStatus | None = None

    @field_validator("full_name")
    @classmethod
    def _validate_full_name(cls, v):
        return _validate_name(v) if v is not None else v

    @field_validator("contact_number")
    @classmethod
    def _validate_contact_number(cls, v):
        return _validate_mobile(v) if v is not None else v


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
