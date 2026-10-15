from app.core.security import DUMMY_HASH, verify_password
from app.schemas.auth import UserInDB


def authenticate_user(
        users: dict[str, UserInDB], username: str, password: str,
) -> UserInDB | None:
    user = users.get(username)
    stored_hash = user.hashed_password if user else DUMMY_HASH
    valid = verify_password(password, stored_hash)
    if user is None or not valid:
        return None
    return user
