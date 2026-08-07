import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SpeechNote(Base):
    __tablename__ = "speech_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))

    audio_filename: Mapped[str] = mapped_column(String(255))
    detected_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    transcript: Mapped[str] = mapped_column(Text)
    extracted_symptoms: Mapped[str] = mapped_column(Text, default="")  # comma-separated

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    patient = relationship("Patient")
