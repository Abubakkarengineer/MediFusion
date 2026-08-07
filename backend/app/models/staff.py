from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20))  # "Doctor" | "Nurse"
    department: Mapped[str] = mapped_column(String(60))
    is_on_duty: Mapped[bool] = mapped_column(Boolean, default=True)

    patients_as_doctor = relationship(
        "Patient",
        foreign_keys="Patient.assigned_doctor_id",
        back_populates="assigned_doctor",
    )
    patients_as_nurse = relationship(
        "Patient",
        foreign_keys="Patient.assigned_nurse_id",
        back_populates="assigned_nurse",
    )
