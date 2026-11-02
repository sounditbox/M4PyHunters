from sqlmodel import Session

from app.core.config import Settings
from app.services.auth import get_user_by_username, create_user


def seed_users(db: Session, settings: Settings) -> None:
    for username, password, role in (
        ("admin", settings.admin_password, "admin"),
        ("user", settings.user_password, "user"),
    ):
        if get_user_by_username(db, username) is None:
            create_user(db, username, password.get_secret_value(), role)
