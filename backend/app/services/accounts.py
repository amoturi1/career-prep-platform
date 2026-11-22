"""Account rules: registration, sign-in, sign-out (PB-01, PB-02, PB-11)."""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import RevokedToken, Role, User
from app.schemas import RegisterIn
from app.security import create_access_token, hash_password, verify_password


class DuplicateEmailError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InactiveAccountError(Exception):
    pass


def find_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == email.lower()))


def register_student(db: Session, data: RegisterIn) -> User:
    """Self-registration always creates a student. Mentor/admin roles are granted by an admin."""
    if find_by_email(db, data.email):
        raise DuplicateEmailError
    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=Role.student,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> tuple[User, str]:
    user = find_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    if not user.is_active:
        raise InactiveAccountError
    return user, create_access_token(user.id, user.role.value)


def revoke_token(db: Session, claims: dict) -> None:
    expires = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    if db.get(RevokedToken, claims["jti"]) is None:
        db.add(RevokedToken(jti=claims["jti"], expires_at=expires))
        db.commit()
