"""Resume-to-job analysis and skill gaps (PB-20, PB-21, PB-22), with saved history (PB-35)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import get_engine
from app.ai.base import DISCLAIMER
from app.models import MatchResult, Opportunity, Profile, PublishStatus, Resume, User
from app.schemas import MatchIn


class AnalysisInputError(ValueError):
    """Missing or unusable input; the message is safe to show to the user."""


def run_match(db: Session, student: User, data: MatchIn) -> MatchResult:
    # Which resume: the one asked for, or the current version.
    if data.resume_id is not None:
        resume = db.scalar(select(Resume).where(Resume.id == data.resume_id, Resume.student_id == student.id))
        if resume is None:
            raise AnalysisInputError("That resume version wasn't found.")
    else:
        resume = db.scalar(select(Resume).where(Resume.student_id == student.id, Resume.is_current.is_(True)))
        if resume is None:
            raise AnalysisInputError("Add your resume first, then run the comparison.")

    # Which job: a published listing, or pasted text.
    job_title, company, job_text = data.job_title, data.company, data.job_description
    opportunity_id = None
    if data.opportunity_id is not None:
        listing = db.get(Opportunity, data.opportunity_id)
        if listing is None or listing.status != PublishStatus.published:
            raise AnalysisInputError("That listing isn't available.")
        opportunity_id = listing.id
        job_title = job_title or listing.title
        company = company or listing.organization
        job_text = job_text or listing.description

    profile = db.scalar(select(Profile).where(Profile.user_id == student.id))
    profile_skills = profile.skills if profile else ""

    analysis = get_engine().analyze_match(resume.text, job_text, profile_skills)
    analysis = dict(analysis)
    analysis["disclaimer"] = DISCLAIMER

    result = MatchResult(
        student_id=student.id,
        resume_id=resume.id,
        opportunity_id=opportunity_id,
        job_title=(job_title or "Untitled role")[:150],
        company=(company or "")[:150],
        job_description=job_text,
        score=int(analysis["score"]),
        result=analysis,
        engine=str(analysis.get("engine", "local"))[:30],
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def history(db: Session, student: User) -> list[MatchResult]:
    return list(
        db.scalars(
            select(MatchResult)
            .where(MatchResult.student_id == student.id)
            .order_by(MatchResult.created_at.desc(), MatchResult.id.desc())
        )
    )


def get_owned(db: Session, student: User, match_id: int) -> MatchResult | None:
    return db.scalar(select(MatchResult).where(MatchResult.id == match_id, MatchResult.student_id == student.id))


def delete(db: Session, result: MatchResult) -> None:
    db.delete(result)
    db.commit()
