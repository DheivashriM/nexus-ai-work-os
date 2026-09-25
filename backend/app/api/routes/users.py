from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_authenticated_user, get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.email_settings import EmailSettingsRead, EmailSettingsUpdate
from app.services.email_connection_service import EmailConnectionService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[UserRead])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _: User = Depends(get_authenticated_user)):
    service = UserService(db)
    return service.get_all_users(skip=skip, limit=limit)

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me/settings", response_model=UserRead)
def update_me_settings(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates the authenticated user's general settings."""
    service = UserService(db)
    return service.update_user(current_user.id, user_in)


@router.get("/me/email-settings", response_model=EmailSettingsRead)
def get_my_email_settings(current_user: User = Depends(get_current_user)):
    return EmailConnectionService.read_settings(current_user)


@router.put("/me/email-settings", response_model=EmailSettingsRead)
def update_my_email_settings(
    settings_in: EmailSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return EmailConnectionService.save_settings(db, current_user, settings_in)


@router.post("/me/email-settings/test", response_model=EmailSettingsRead)
def test_my_email_settings(current_user: User = Depends(get_current_user)):
    try:
        EmailConnectionService.test_connection(current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return EmailConnectionService.read_settings(current_user)

@router.get("/{user_id}", response_model=UserRead)
def get_user_by_id(user_id: str, db: Session = Depends(get_db), _: User = Depends(get_authenticated_user)):
    service = UserService(db)
    return service.get_user_by_id(user_id)

@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Administrator access required")
    service = UserService(db)
    return service.create_user(user_in)

@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: str, user_in: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_authenticated_user)):
    if current_user.role != "ADMIN" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Administrator access required")
    if current_user.id != user_id:
        user_in.role = None
        user_in.status = None
    service = UserService(db)
    return service.update_user(user_id, user_in)

