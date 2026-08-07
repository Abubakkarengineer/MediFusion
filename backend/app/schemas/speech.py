import datetime

from pydantic import BaseModel, ConfigDict


class SpeechNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    audio_filename: str
    detected_language: str | None
    transcript: str
    symptoms: list[str]
    created_at: datetime.datetime
