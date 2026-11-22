"""E2 Student Profiles: PB-04 create, PB-05 edit, PB-06 view."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Role, User
from app.schemas import ProfileIn, ProfileOut
from app.services import profiles

router = APIRouter(prefix="/api/profile", tags=["Profiles"])
student_only = require_role(Role.student)


@router.get("", response_model=ProfileOut)
def view_profile(user: User = Depends(student_only), db: Session = Depends(get_db)):
    profile = profiles.get_profile(db, user)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="You haven't created a profile yet.")
    return profile


@router.post("", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(data: ProfileIn, user: User = Depends(student_only), db: Session = Depends(get_db)):
    try:
        return profiles.create_profile(db, user, data)
    except profiles.ProfileExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="You already have a profile. Edit it instead.")


@router.put("", response_model=ProfileOut)
def edit_profile(data: ProfileIn, user: User = Depends(student_only), db: Session = Depends(get_db)):
    profile = profiles.get_profile(db, user)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="You haven't created a profile yet.")
    return profiles.update_profile(db, profile, data)
