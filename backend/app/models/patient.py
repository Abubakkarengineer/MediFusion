import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

DEFAULT_DEPARTMENT = "General Medicine"
DEFAULT_STATUS = "Waiting"
DEFAULT_PRIORITY = "LOW"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mrn: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    full_name: Mapped[str] = mapped_column(String(120))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(20))
    contact_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    chief_complaint: Mapped[str | None] = mapped_column(String(500), nullable=True)

    department: Mapped[str] = mapped_column(String(60), default=DEFAULT_DEPARTMENT)
    status: Mapped[str] = mapped_column(String(30), default=DEFAULT_STATUS)
    priority: Mapped[str] = mapped_column(String(20), default=DEFAULT_PRIORITY)

    assigned_doctor_id: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id"), nullable=True
    )
    assigned_nurse_id: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id"), nullable=True
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    assigned_doctor = relationship(
        "Staff", foreign_keys=[assigned_doctor_id], back_populates="patients_as_doctor"
    )
    assigned_nurse = relationship(
        "Staff", foreign_keys=[assigned_nurse_id], back_populates="patients_as_nurse"
    )
    vitals = relationship(
        "VitalObservation", back_populates="patient", order_by="VitalObservation.recorded_at"
    )
