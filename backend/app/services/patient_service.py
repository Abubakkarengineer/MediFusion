from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import DEPARTMENTS, PATIENT_STATUSES
from app.models.patient import Patient
from app.models.staff import Staff

DEMO_STAFF = [
    ("Dr. Ananya Rao", "Doctor", "General Medicine"),
    ("Nurse Priya Menon", "Nurse", "General Medicine"),
    ("Dr. Karthik Iyer", "Doctor", "Emergency"),
    ("Nurse Sneha Pillai", "Nurse", "Emergency"),
    ("Dr. Meera Nair", "Doctor", "Cardiology"),
    ("Nurse Divya Suresh", "Nurse", "Cardiology"),
    ("Dr. Rohan Verma", "Doctor", "Pulmonology"),
    ("Nurse Anjali Kumar", "Nurse", "Pulmonology"),
    ("Dr. Sanjay Gupta", "Doctor", "ICU"),
    ("Nurse Fathima Rasheed", "Nurse", "ICU"),
]

ACTIVE_STATUSES = [s for s in PATIENT_STATUSES if s != "Discharged"]


def seed_demo_staff(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Staff)):
        return
    for name, role, department in DEMO_STAFF:
        db.add(Staff(name=name, role=role, department=department, is_on_duty=True))
    db.commit()


def generate_mrn(db: Session) -> str:
    count = db.scalar(select(func.count()).select_from(Patient)) or 0
    return f"MFA-{count + 1:06d}"


def _least_loaded_staff(db: Session, department: str, role: str) -> Staff | None:
    fk_column = Patient.assigned_doctor_id if role == "Doctor" else Patient.assigned_nurse_id

    load_subquery = (
        select(fk_column, func.count(Patient.id).label("load"))
        .where(Patient.status.in_(ACTIVE_STATUSES))
        .group_by(fk_column)
        .subquery()
    )

    candidates = db.execute(
        select(Staff, func.coalesce(load_subquery.c.load, 0).label("load"))
        .outerjoin(load_subquery, Staff.id == load_subquery.c[fk_column.key])
        .where(Staff.department == department, Staff.role == role, Staff.is_on_duty.is_(True))
        .order_by("load")
    ).first()

    if candidates:
        return candidates[0]

    # Fallback: no on-duty staff in the requested department, use General Medicine.
    if department != "General Medicine":
        return _least_loaded_staff(db, "General Medicine", role)
    return None


def assign_staff(db: Session, department: str) -> tuple[Staff | None, Staff | None]:
    department = department if department in DEPARTMENTS else "General Medicine"
    doctor = _least_loaded_staff(db, department, "Doctor")
    nurse = _least_loaded_staff(db, department, "Nurse")
    return doctor, nurse
