"""E3 Application Tracking: PB-07 add, PB-08 view, PB-09 status, PB-10 edit, PB-12 delete, PB-13 filter."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import ApplicationStatus, Role, User
from app.schemas import ApplicationCreate, ApplicationOut, ApplicationUpdate, StatusUpdate
from app.services import applications

router = APIRouter(prefix="/api/applications", tags=["Applications"])
student_only = require_role(Role.student)

# Records owned by someone else get the same 404 as missing ones, so IDs can't be probed.
_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, detail="Application not found.")


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    user: User = Depends(student_only),
    db: Session = Depends(get_db),
):
    return applications.list_for_student(db, user, status_filter)


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def add_application(data: ApplicationCreate, user: User = Depends(student_only), db: Session = Depends(get_db)):
    return applications.create(db, user, data)


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)):
    application = applications.get_owned(db, user, application_id)
    if application is None:
        raise _NOT_FOUND
    return application


@router.put("/{application_id}", response_model=ApplicationOut)
def edit_application(
    application_id: int, data: ApplicationUpdate, user: User = Depends(student_only), db: Session = Depends(get_db)
):
    application = applications.get_owned(db, user, application_id)
    if application is None:
        raise _NOT_FOUND
    return applications.update(db, application, data)


@router.patch("/{application_id}/status", response_model=ApplicationOut)
def update_status(
    application_id: int, data: StatusUpdate, user: User = Depends(student_only), db: Session = Depends(get_db)
):
    application = applications.get_owned(db, user, application_id)
    if application is None:
        raise _NOT_FOUND
    return applications.set_status(db, application, data.status)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)):
    application = applications.get_owned(db, user, application_id)
    if application is None:
        raise _NOT_FOUND
    applications.delete(db, application)
