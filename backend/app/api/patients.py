import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.db import get_db
from app.models.patient import Patient
from app.models.vital import VitalObservation
from app.schemas.patient import PatientCreate, PatientListItem, PatientOut, PatientUpdate
from app.schemas.vital import VitalCreate, VitalOut
from app.services.patient_service import assign_staff, generate_mrn

router = APIRouter(prefix="/patients", tags=["patients"])
logger = get_logger(__name__)


def _get_patient_or_404(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("", response_model=PatientOut, status_code=201)
def register_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    doctor, nurse = assign_staff(db, payload.department)

    patient = Patient(
        mrn=generate_mrn(db),
        full_name=payload.full_name,
        age=payload.age,
        gender=payload.gender,
        contact_number=payload.contact_number,
        chief_complaint=payload.chief_complaint,
        department=payload.department,
        assigned_doctor_id=doctor.id if doctor else None,
        assigned_nurse_id=nurse.id if nurse else None,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    logger.info("Registered patient %s (%s)", patient.mrn, patient.full_name)
    return patient


@router.get("", response_model=list[PatientListItem])
def list_patients(status: str | None = None, db: Session = Depends(get_db)):
    query = select(Patient).order_by(Patient.created_at.asc())
    if status:
        query = query.where(Patient.status == status)
    return db.scalars(query).all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return _get_patient_or_404(db, patient_id)


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)):
    patient = _get_patient_or_404(db, patient_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    logger.info("Updated patient %s: %s", patient.mrn, list(updates.keys()))
    return patient


@router.post("/{patient_id}/vitals", response_model=VitalOut, status_code=201)
def add_vital(patient_id: int, payload: VitalCreate, db: Session = Depends(get_db)):
    from app.services.priority_service import refresh_patient_priority

    _get_patient_or_404(db, patient_id)
    vital = VitalObservation(patient_id=patient_id, **payload.model_dump())
    db.add(vital)
    db.commit()
    db.refresh(vital)
    refresh_patient_priority(db, patient_id)
    return vital


@router.post("/{patient_id}/vitals/simulate", response_model=list[VitalOut], status_code=201)
def simulate_vitals(patient_id: int, scenario: str, db: Session = Depends(get_db)):
    from app.services.vitals_simulation import SCENARIOS, generate_scenario

    _get_patient_or_404(db, patient_id)
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"scenario must be one of {SCENARIOS}")

    from app.services.priority_service import refresh_patient_priority
    from app.services.vitals_simulation import INTERVAL_MINUTES, STEPS

    # Anchor the simulated timeline's *first* (oldest) reading strictly
    # after this patient's existing latest reading (real or simulated), so
    # back-to-back simulation runs never produce overlapping backdated
    # timestamps -- otherwise "latest vital" lookups can resolve to a stale
    # reading from a prior run for most of the new batch.
    latest_existing = db.scalars(
        select(VitalObservation)
        .where(VitalObservation.patient_id == patient_id)
        .order_by(VitalObservation.recorded_at.desc())
    ).first()
    batch_span = datetime.timedelta(minutes=(STEPS - 1) * INTERVAL_MINUTES)
    now = datetime.datetime.utcnow()
    if latest_existing:
        earliest_allowed_start = latest_existing.recorded_at + datetime.timedelta(minutes=INTERVAL_MINUTES)
        now = max(now, earliest_allowed_start + batch_span)

    readings = generate_scenario(scenario, end_time=now)  # chronological order, oldest first
    saved = []
    for reading in readings:
        vital = VitalObservation(patient_id=patient_id, source="simulated", **reading)
        db.add(vital)
        db.commit()
        db.refresh(vital)
        saved.append(vital)
        # refresh after each step (not just the final one) so the full
        # priority trajectory (e.g. LOW -> MODERATE -> HIGH -> CRITICAL)
        # is captured in priority_history, not just a single end-state jump.
        refresh_patient_priority(db, patient_id)

    logger.info("Simulated %d vitals (%s) for patient %s", len(saved), scenario, patient_id)
    return saved


@router.get("/{patient_id}/vitals", response_model=list[VitalOut])
def list_vitals(patient_id: int, db: Session = Depends(get_db)):
    _get_patient_or_404(db, patient_id)
    return db.scalars(
        select(VitalObservation)
        .where(VitalObservation.patient_id == patient_id)
        .order_by(VitalObservation.recorded_at.asc())
    ).all()
