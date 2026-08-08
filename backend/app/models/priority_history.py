import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PriorityHistory(Base):
    __tablename__ = "priority_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))

    previous_priority: Mapped[str] = mapped_column(String(20))
    new_priority: Mapped[str] = mapped_column(String(20))
    probability: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(200))

    changed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    patient = relationship("Patient")
