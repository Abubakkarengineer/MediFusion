import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ClinicalAlert(Base):
    __tablename__ = "clinical_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))

    priority: Mapped[str] = mapped_column(String(20))
    concern: Mapped[str | None] = mapped_column(String(50), nullable=True)
    department: Mapped[str | None] = mapped_column(String(60), nullable=True)
    specialist_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    nurse_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    probability: Mapped[float] = mapped_column(Float)
    message: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    patient = relationship("Patient")
