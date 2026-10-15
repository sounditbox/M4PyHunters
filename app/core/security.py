from pwdlib import PasswordHash

from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import Settings

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hash.verify(password, stored_hash)


def create_access_token(username: str, settings: Settings) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes,
        ),
    }
    return jwt.encode(
        payload, settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )


def decode_access_token(token: str, settings: Settings) -> str:
    payload = jwt.decode(
        token, settings.secret_key.get_secret_value(),
        algorithms=["HS256"],
        options={"require": ["sub", "exp"]},
    )
    return payload["sub"]
