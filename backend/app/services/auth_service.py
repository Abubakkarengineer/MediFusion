from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import hash_password
from app.models.staff import Staff
from app.models.user import User

# Demo credentials -- for hackathon demonstration only, never use fixed
# passwords like this in a real deployment.
ADMIN_PASSWORD = "Admin@123"
DOCTOR_PASSWORD = "Doctor@123"


def seed_demo_users(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(User)):
        return  # already seeded

    db.add(User(
        login_id="ADM-001",
        password_hash=hash_password(ADMIN_PASSWORD),
        role="Admin",
        display_name="System Administrator",
    ))

    doctors = db.scalars(
        select(Staff).where(Staff.role == "Doctor").order_by(Staff.id)
    ).all()
    for i, doctor in enumerate(doctors, start=1):
        db.add(User(
            login_id=f"DOC-{i:03d}",
            password_hash=hash_password(DOCTOR_PASSWORD),
            role="Doctor",
            display_name=doctor.name,
            staff_id=doctor.id,
        ))

    db.commit()
