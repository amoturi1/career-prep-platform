"""Application tracker rules (PB-07 to PB-10, PB-12, PB-13).

Every query is scoped to the signed-in student, so one student can never
read or change another student's records (NFR-01).
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Application, ApplicationStatus, User
from app.schemas import ApplicationCreate, ApplicationUpdate


def list_for_student(db: Session, student: User, status: ApplicationStatus | None = None) -> list[Application]:
    query = select(Application).where(Application.student_id == student.id)
    if status is not None:
        query = query.where(Application.status == status)
    query = query.order_by(Application.updated_at.desc(), Application.id.desc())
    return list(db.scalars(query))


def get_owned(db: Session, student: User, application_id: int) -> Application | None:
    """Return the record only if this student owns it."""
    return db.scalar(
        select(Application).where(Application.id == application_id, Application.student_id == student.id)
    )


def create(db: Session, student: User, data: ApplicationCreate) -> Application:
    application = Application(student_id=student.id, **data.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def update(db: Session, application: Application, data: ApplicationUpdate) -> Application:
    for field, value in data.model_dump().items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application


def set_status(db: Session, application: Application, status: ApplicationStatus) -> Application:
    application.status = status
    db.commit()
    db.refresh(application)
    return application


def delete(db: Session, application: Application) -> None:
    db.delete(application)
    db.commit()
