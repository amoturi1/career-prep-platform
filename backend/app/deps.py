"""Shared request dependencies: who is signed in, and are they allowed (NFR-01)."""
from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RevokedToken, Role, User
from app.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Please sign in to continue.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_token_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> dict:
    if credentials is None:
        raise _UNAUTHORIZED
    try:
        claims = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise _UNAUTHORIZED
    if db.get(RevokedToken, claims.get("jti", "")) is not None:
        raise _UNAUTHORIZED
    return claims


def get_current_user(claims: dict = Depends(get_token_claims), db: Session = Depends(get_db)) -> User:
    user = db.get(User, int(claims["sub"]))
    if user is None or not user.is_active:
        raise _UNAUTHORIZED
    return user


def require_role(*roles: Role) -> Callable[..., User]:
    """Dependency factory: allow only users whose role is in `roles`."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="You do not have permission to do this.")
        return user

    return checker
