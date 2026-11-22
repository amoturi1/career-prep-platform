"""Resume versions (PB-18, PB-19). Every upload is a new version; one is current."""
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import MatchResult, Resume, User


def list_versions(db: Session, student: User) -> list[Resume]:
    return list(
        db.scalars(
            select(Resume).where(Resume.student_id == student.id).order_by(Resume.uploaded_at.desc(), Resume.id.desc())
        )
    )


def current(db: Session, student_id: int) -> Resume | None:
    return db.scalar(select(Resume).where(Resume.student_id == student_id, Resume.is_current.is_(True)))


def get_owned(db: Session, student: User, resume_id: int) -> Resume | None:
    return db.scalar(select(Resume).where(Resume.id == resume_id, Resume.student_id == student.id))


def add_version(db: Session, student: User, filename: str, source: str, text: str) -> Resume:
    db.execute(update(Resume).where(Resume.student_id == student.id).values(is_current=False))
    resume = Resume(student_id=student.id, filename=filename[:255], source=source, text=text, is_current=True)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def make_current(db: Session, student: User, resume: Resume) -> Resume:
    db.execute(update(Resume).where(Resume.student_id == student.id).values(is_current=False))
    resume.is_current = True
    db.commit()
    db.refresh(resume)
    return resume


def delete(db: Session, student: User, resume: Resume) -> None:
    was_current = resume.is_current
    # Keep past analyses, but unlink them from the deleted version.
    db.execute(update(MatchResult).where(MatchResult.resume_id == resume.id).values(resume_id=None))
    db.delete(resume)
    db.flush()
    if was_current:
        latest = db.scalar(
            select(Resume).where(Resume.student_id == student.id).order_by(Resume.uploaded_at.desc(), Resume.id.desc())
        )
        if latest is not None:
            latest.is_current = True
    db.commit()


def word_count(resume: Resume) -> int:
    return len(resume.text.split())
