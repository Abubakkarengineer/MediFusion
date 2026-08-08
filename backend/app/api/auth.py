from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, get_current_user, verify_password
from app.core.logging_config import get_logger
from app.db import get_db
from app.models.user import User
from app.schemas.auth import CurrentUser, LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.login_id == payload.login_id))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid ID or password")

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
        "display_name": user.display_name,
        "login_id": user.login_id,
        "staff_id": user.staff_id,
    })
    logger.info("Login: %s (%s)", user.login_id, user.role)
    return LoginResponse(
        token=token, role=user.role, display_name=user.display_name, login_id=user.login_id
    )


@router.get("/me", response_model=CurrentUser)
def me(current_user: dict = Depends(get_current_user)):
    return CurrentUser(
        role=current_user["role"],
        display_name=current_user["display_name"],
        login_id=current_user["login_id"],
    )
