from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.api.deps import get_current_user, get_current_active_user

router = APIRouter(prefix="/api/users", tags=["users"])


class UserMeResponse(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    email: str | None = None
    dify_private_dataset_id: str | None = None
    is_admin: bool = False
    is_active: bool = True
    must_change_password: bool = False

    class Config:
        from_attributes = True


class UpdateMeRequest(BaseModel):
    display_name: str | None = None
    email: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.get("/me", response_model=UserMeResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.put("/me", response_model=UserMeResponse)
def update_me(
    payload: UpdateMeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    if payload.email is not None:
        current_user.email = payload.email
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password too short")

    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.must_change_password = False
    current_user.token_version = int(current_user.token_version or 0) + 1
    db.add(current_user)
    db.commit()
    return {"status": "ok"}
