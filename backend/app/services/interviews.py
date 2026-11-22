"""Mock interview sessions (PB-23, PB-24, PB-25)."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import get_engine
from app.models import InterviewAnswer, InterviewSession, InterviewStatus, Opportunity, PublishStatus, User
from app.schemas import InterviewStart


class InterviewError(ValueError):
    """A request that doesn't fit the session's state; the message is safe to show."""


def start(db: Session, student: User, data: InterviewStart) -> InterviewSession:
    focus = data.focus
    if data.opportunity_id is not None:
        listing = db.get(Opportunity, data.opportunity_id)
        if listing is None or listing.status != PublishStatus.published:
            raise InterviewError("That listing isn't available.")
        focus = f"{focus}\n{listing.description}".strip()

    engine = get_engine()
    questions = engine.generate_questions(data.role, focus, data.question_count)
    session = InterviewSession(
        student_id=student.id,
        role=data.role,
        focus=focus,
        questions=questions,
        engine=getattr(engine, "name", "local"),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_for_student(db: Session, student: User) -> list[InterviewSession]:
    return list(
        db.scalars(
            select(InterviewSession)
            .where(InterviewSession.student_id == student.id)
            .order_by(InterviewSession.created_at.desc(), InterviewSession.id.desc())
        )
    )


def get_owned(db: Session, student: User, session_id: int) -> InterviewSession | None:
    return db.scalar(
        select(InterviewSession).where(InterviewSession.id == session_id, InterviewSession.student_id == student.id)
    )


def submit_answer(db: Session, session: InterviewSession, index: int, answer: str) -> InterviewAnswer:
    if session.status != InterviewStatus.active:
        raise InterviewError("This practice session is finished. Start a new one to keep practicing.")
    if index >= len(session.questions):
        raise InterviewError("That question isn't part of this session.")
    if any(a.question_index == index for a in session.answers):
        raise InterviewError("You've already answered this question.")

    question = session.questions[index]
    feedback = dict(get_engine().evaluate_answer(question, answer, session.role))
    record = InterviewAnswer(
        session_id=session.id, question_index=index, question=question, answer=answer, feedback=feedback
    )
    db.add(record)
    db.flush()
    db.refresh(session)
    if len(session.answers) >= len(session.questions):
        session.status = InterviewStatus.completed
        session.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return record


def finish(db: Session, session: InterviewSession) -> InterviewSession:
    if session.status == InterviewStatus.active:
        if not session.answers:
            raise InterviewError("Answer at least one question before finishing.")
        session.status = InterviewStatus.completed
        session.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
    return session


def summarize(session: InterviewSession) -> dict:
    scores = [a.feedback.get("score") for a in session.answers if isinstance(a.feedback.get("score"), (int, float))]
    return {
        "id": session.id,
        "role": session.role,
        "status": session.status,
        "engine": session.engine,
        "created_at": session.created_at,
        "completed_at": session.completed_at,
        "question_count": len(session.questions),
        "answered_count": len(session.answers),
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
    }


def detail(session: InterviewSession) -> dict:
    return {
        **summarize(session),
        "focus": session.focus,
        "questions": session.questions,
        "answers": session.answers,
    }
