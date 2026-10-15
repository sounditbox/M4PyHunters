from starlette.requests import Request

from app.core.config import get_settings
from app.core.security import hash_password
from app.schemas.auth import UserInDB

settings = get_settings()

fake_users = {
    "admin": UserInDB(
        id=1, username="admin", role="admin",
        hashed_password=hash_password(
            settings.admin_password.get_secret_value()),
    ),
    "user": UserInDB(
        id=2, username="user", role="user",
        hashed_password=hash_password(
            settings.user_password.get_secret_value()),
    ),
}


def get_users(request: Request) -> dict[str, UserInDB]:
    return request.app.state.users


