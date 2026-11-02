from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.security import DUMMY_HASH, hash_password, verify_password
from app.models.user import User


class UsernameTakenError(ValueError):
    pass


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.exec(select(User).where(User.username == username)).first()


def create_user(db: Session, username: str, password: str,
                role: str = "user") -> User:
    user = User(username=username, hashed_password=hash_password(password),
                role=role)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise UsernameTakenError(username) from exc
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db, username)
    valid = verify_password(password,
                            user.hashed_password if user else DUMMY_HASH)
    return user if user is not None and valid else None
