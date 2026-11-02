from fastapi import APIRouter, HTTPException

from app.dependencies.auth import AdminUserDep
from app.dependencies.db import SessionDep
from app.schemas.auth import UserRead, UserCreate
from app.services.auth import create_user, UsernameTakenError

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserRead, status_code=201)
def add_user(data: UserCreate, db: SessionDep, _admin: AdminUserDep):
    try:
        user = create_user(db, data.username, data.password.get_secret_value())
    except UsernameTakenError:
        raise HTTPException(status_code=409, detail="Логин уже занят") from None
    return UserRead.model_validate(user, from_attributes=True)
