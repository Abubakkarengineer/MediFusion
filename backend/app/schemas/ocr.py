import datetime

from pydantic import BaseModel, ConfigDict


class Medicine(BaseModel):
    name: str
    dosage: str | None
    frequency: str | None


class LabValue(BaseModel):
    test_name: str
    value: float
    unit: str
    flag: str


class OCRDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    document_type: str
    filename: str
    raw_text: str
    medicines: list[Medicine]
    lab_values: list[LabValue]
    patient_info: dict[str, str]
    created_at: datetime.datetime
