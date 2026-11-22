"""E1 Account Management: PB-01 register, PB-02 sign in, PB-03 validation, PB-11 sign out."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_token_claims
from app.models import User
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from app.services import accounts

router = APIRouter(prefix="/api/auth", tags=["Accounts"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    try:
        accounts.register_student(db, data)
    except accounts.DuplicateEmailError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="An account with this email already exists.")
    user, token = accounts.authenticate(db, data.email, data.password)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    try:
        user, token = accounts.authenticate(db, data.email, data.password)
    except accounts.InvalidCredentialsError:
        # Same message for unknown email and wrong password, so accounts can't be probed.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    except accounts.InactiveAccountError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(claims: dict = Depends(get_token_claims), db: Session = Depends(get_db)):
    accounts.revoke_token(db, claims)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
