from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
import secrets
import string

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.api.deps import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminUserResponse(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    email: str | None = None
    dify_private_dataset_id: str | None = None
    is_active: bool = True
    is_admin: bool = False
    must_change_password: bool = False

    class Config:
        from_attributes = True


class UpdateUserStatusRequest(BaseModel):
    is_active: bool


class ResetPasswordResponse(BaseModel):
    temp_password: str


def _generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    symbols = "!@#$%^&*"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(max(8, length - 2))) + "".join(
            secrets.choice(symbols) for _ in range(2)
        )
        if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd) and any(c.isdigit() for c in pwd):
            return pwd


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    query = db.query(User)
    if keyword:
        query = query.filter(
            or_(
                User.username.ilike(f"%{keyword}%"),
                User.display_name.ilike(f"%{keyword}%"),
                User.email.ilike(f"%{keyword}%"),
            )
        )
    return query.order_by(User.id.asc()).offset(skip).limit(limit).all()


@router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
def update_user_status(
    user_id: int,
    payload: UpdateUserStatusRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.username == "admin" and payload.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot disable admin")
    user.is_active = payload.is_active
    if payload.is_active is False:
        user.token_version = int(user.token_version or 0) + 1
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reset-password", response_model=ResetPasswordResponse)
def reset_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="Cannot reset admin password here")

    temp_password = _generate_temp_password()
    user.hashed_password = get_password_hash(temp_password)
    user.must_change_password = True
    user.token_version = int(user.token_version or 0) + 1
    db.add(user)
    db.commit()
    return ResetPasswordResponse(temp_password=temp_password)
