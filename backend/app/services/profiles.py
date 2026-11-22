"""Career profile rules (PB-04, PB-05, PB-06)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Profile, User
from app.schemas import ProfileIn


class ProfileExistsError(Exception):
    pass


def get_profile(db: Session, user: User) -> Profile | None:
    return db.scalar(select(Profile).where(Profile.user_id == user.id))


def create_profile(db: Session, user: User, data: ProfileIn) -> Profile:
    if get_profile(db, user) is not None:
        raise ProfileExistsError
    profile = Profile(user_id=user.id, **data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_profile(db: Session, profile: Profile, data: ProfileIn) -> Profile:
    for field, value in data.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
