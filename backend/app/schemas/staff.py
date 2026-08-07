from pydantic import BaseModel, ConfigDict


class StaffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: str
    department: str
    is_on_duty: bool
    active_patient_count: int = 0
