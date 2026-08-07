import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class OCRDocument(Base):
    __tablename__ = "ocr_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))

    document_type: Mapped[str] = mapped_column(String(30))  # "Prescription" | "Lab Report"
    filename: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)
    medicines_json: Mapped[str] = mapped_column(Text, default="[]")
    lab_values_json: Mapped[str] = mapped_column(Text, default="[]")
    patient_info_json: Mapped[str] = mapped_column(Text, default="{}")

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    patient = relationship("Patient")
