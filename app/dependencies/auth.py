from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError

from app.core.security import decode_access_token
from app.dependencies.db import UsersDep
from app.dependencies.settings import SettingsDep
from app.schemas.auth import UserRead

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=401, detail="Неверные учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
        token: TokenDep, users: UsersDep, settings: SettingsDep,
) -> UserRead:
    try:
        username = decode_access_token(token, settings)
    except (InvalidTokenError, ValueError, TypeError):
        raise invalid_credentials() from None
    user = users.get(username)
    if user is None:
        raise invalid_credentials()
    if user.disabled:
        raise HTTPException(status_code=403, detail="Пользователь заблокирован")
    return UserRead(**user.model_dump())


CurrentUserDep = Annotated[UserRead, Depends(get_current_user)]


def require_admin(user: CurrentUserDep) -> UserRead:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return user


AdminUserDep = Annotated[UserRead, Depends(require_admin)]