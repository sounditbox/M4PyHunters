from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token
from app.dependencies.auth import invalid_credentials, CurrentUserDep
from app.dependencies.db import UsersDep
from app.dependencies.settings import SettingsDep
from app.schemas.auth import Token, UserRead
from app.services.auth import authenticate_user

router = APIRouter(prefix="/auth", tags=["Auth"])
LoginForm = Annotated[OAuth2PasswordRequestForm, Depends()]


@router.post("/token", response_model=Token)
def login(form: LoginForm, users: UsersDep, settings: SettingsDep) -> Token:
    user = authenticate_user(users, form.username, form.password)
    if user is None:
        raise invalid_credentials()
    if user.disabled:
        raise HTTPException(status_code=403, detail="Пользователь заблокирован")
    return Token(access_token=create_access_token(user.username, settings))


@router.get("/me", response_model=UserRead)
def read_current_user(user: CurrentUserDep) -> UserRead:
    return user
