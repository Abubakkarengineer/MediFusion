import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import SPEECH_UPLOADS_DIR
from app.core.logging_config import get_logger
from app.core.symptom_lexicon import extract_symptoms
from app.db import get_db
from app.models.patient import Patient
from app.models.speech_note import SpeechNote
from app.schemas.speech import SpeechNoteOut
from app.services.speech_service import transcribe_audio

router = APIRouter(prefix="/patients", tags=["speech"])
logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}


def _to_out(note: SpeechNote) -> SpeechNoteOut:
    symptoms = [s for s in note.extracted_symptoms.split(",") if s]
    return SpeechNoteOut(
        id=note.id,
        patient_id=note.patient_id,
        audio_filename=note.audio_filename,
        detected_language=note.detected_language,
        transcript=note.transcript,
        symptoms=symptoms,
        created_at=note.created_at,
    )


@router.post("/{patient_id}/speech", response_model=SpeechNoteOut, status_code=201)
async def upload_speech(patient_id: int, audio: UploadFile = File(...), db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    suffix = Path(audio.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format '{suffix}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    saved_name = f"{uuid.uuid4().hex}{suffix}"
    saved_path = SPEECH_UPLOADS_DIR / saved_name
    contents = await audio.read()
    saved_path.write_bytes(contents)

    try:
        transcript, language = transcribe_audio(str(saved_path))
    except Exception as exc:
        logger.exception("Whisper transcription failed for patient %s", patient_id)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc

    symptoms = extract_symptoms(transcript)

    note = SpeechNote(
        patient_id=patient_id,
        audio_filename=audio.filename or saved_name,
        detected_language=language,
        transcript=transcript,
        extracted_symptoms=",".join(symptoms),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    logger.info("Speech note %s saved for patient %s (lang=%s)", note.id, patient_id, language)
    return _to_out(note)


@router.get("/{patient_id}/speech", response_model=list[SpeechNoteOut])
def list_speech(patient_id: int, db: Session = Depends(get_db)):
    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    notes = db.scalars(
        select(SpeechNote)
        .where(SpeechNote.patient_id == patient_id)
        .order_by(SpeechNote.created_at.desc())
    ).all()
    return [_to_out(n) for n in notes]
