from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.patient import Patient
from app.models.staff import Staff
from app.schemas.staff import StaffOut
from app.services.patient_service import ACTIVE_STATUSES

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("", response_model=list[StaffOut])
def list_staff(db: Session = Depends(get_db)):
    staff_members = db.scalars(select(Staff).order_by(Staff.department, Staff.role)).all()

    results = []
    for staff in staff_members:
        fk_column = (
            Patient.assigned_doctor_id if staff.role == "Doctor" else Patient.assigned_nurse_id
        )
        active_count = db.scalar(
            select(func.count())
            .select_from(Patient)
            .where(fk_column == staff.id, Patient.status.in_(ACTIVE_STATUSES))
        )
        results.append(
            StaffOut(
                id=staff.id,
                name=staff.name,
                role=staff.role,
                department=staff.department,
                is_on_duty=staff.is_on_duty,
                active_patient_count=active_count or 0,
            )
        )
    return results
