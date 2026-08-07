import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class MedicalImage(Base):
    __tablename__ = "medical_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))

    modality: Mapped[str] = mapped_column(String(10))  # X-ray | CT | MRI
    filename: Mapped[str] = mapped_column(String(255))
    top_label: Mapped[str] = mapped_column(String(100))
    top_confidence: Mapped[float] = mapped_column()
    predictions_json: Mapped[str] = mapped_column(Text, default="[]")

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    patient = relationship("Patient")
