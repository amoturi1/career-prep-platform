"""Mentor requests, sessions, feedback and progress (PB-26 to PB-29, PB-31 to PB-33).

Privacy rules (NFR-01, NFR-02):
  * A mentor sees an open request's message, but none of the student's materials.
  * A student's profile, resume and progress are visible only to the mentor who has
    taken that request, only while it is accepted/in progress/completed, and only
    for the items the student chose to share on that request.
"""
from collections import Counter
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import (
    Application,
    InterviewSession,
    InterviewStatus,
    MatchResult,
    MentorFeedback,
    MentorRequest,
    MentorRequestStatus as S,
    MentorSlot,
    Profile,
    Resume,
    Role,
    User,
)
from app.schemas import MentorRequestIn

ACTIVE = {S.accepted, S.in_progress, S.completed}
OPEN_FOR_STUDENT = {S.pending, S.accepted, S.in_progress}

# Status changes a mentor may make with the status control.
MENTOR_TRANSITIONS = {
    S.accepted: {S.in_progress, S.completed},
    S.in_progress: {S.completed},
}


class MentorshipError(ValueError):
    """A request that isn't allowed in the current state; the message is safe to show."""


class NotFound(LookupError):
    pass


# ------------------------------------------------------------------ slots (PB-31)

def mentor_slots(db: Session, mentor: User) -> list[MentorSlot]:
    return list(
        db.scalars(select(MentorSlot).where(MentorSlot.mentor_id == mentor.id).order_by(MentorSlot.start_at))
    )


def add_slot(db: Session, mentor: User, start_at: datetime, duration: int) -> MentorSlot:
    end = start_at.timestamp() + duration * 60
    for slot in mentor_slots(db, mentor):
        other_end = slot.start_at.timestamp() + slot.duration_minutes * 60
        if start_at.timestamp() < other_end and slot.start_at.timestamp() < end:
            raise MentorshipError("This time overlaps another slot you've already added.")
    slot = MentorSlot(mentor_id=mentor.id, start_at=start_at, duration_minutes=duration)
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


def remove_slot(db: Session, mentor: User, slot_id: int) -> None:
    slot = db.scalar(select(MentorSlot).where(MentorSlot.id == slot_id, MentorSlot.mentor_id == mentor.id))
    if slot is None:
        raise NotFound
    if slot.is_booked:
        raise MentorshipError("A student has booked this slot. Decline the booking first if you can't make it.")
    db.delete(slot)
    db.commit()


def available_slots(db: Session) -> list[MentorSlot]:
    """Future, unbooked slots from active mentors (PB-32)."""
    return list(
        db.scalars(
            select(MentorSlot)
            .join(User, User.id == MentorSlot.mentor_id)
            .where(MentorSlot.is_booked.is_(False), MentorSlot.start_at > datetime.now(), User.is_active.is_(True))
            .order_by(MentorSlot.start_at)
        )
    )


# ------------------------------------------------------------------ student side (PB-26, PB-32, PB-33)

def create_request(db: Session, student: User, data: MentorRequestIn) -> MentorRequest:
    request = MentorRequest(
        student_id=student.id,
        request_type=data.request_type,
        message=data.message,
        share_profile=data.share_profile,
        share_resume=data.share_resume,
        share_progress=data.share_progress,
        status=S.pending,
    )
    if data.slot_id is not None:
        slot = db.get(MentorSlot, data.slot_id)
        if slot is None or slot.is_booked or slot.start_at <= datetime.now():
            raise MentorshipError("That time is no longer available. Please pick another slot.")
        mentor = db.get(User, slot.mentor_id)
        if mentor is None or not mentor.is_active or mentor.role != Role.mentor:
            raise MentorshipError("That mentor isn't available right now.")
        slot.is_booked = True
        request.slot_id = slot.id
        request.mentor_id = slot.mentor_id
        request.status = S.accepted  # a booked time is confirmed straight away
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def student_requests(db: Session, student: User) -> list[MentorRequest]:
    return list(
        db.scalars(
            select(MentorRequest)
            .where(MentorRequest.student_id == student.id)
            .order_by(MentorRequest.created_at.desc(), MentorRequest.id.desc())
        )
    )


def cancel(db: Session, student: User, request_id: int) -> MentorRequest:
    request = db.scalar(
        select(MentorRequest).where(MentorRequest.id == request_id, MentorRequest.student_id == student.id)
    )
    if request is None:
        raise NotFound
    if request.status not in {S.pending, S.accepted}:
        raise MentorshipError("Only pending or accepted requests can be cancelled.")
    request.status = S.cancelled
    _free_slot(request)
    db.commit()
    db.refresh(request)
    return request


def _free_slot(request: MentorRequest) -> None:
    if request.slot is not None:
        request.slot.is_booked = False


# ------------------------------------------------------------------ mentor side (PB-27, PB-28)

def mentor_queue(db: Session, mentor: User, scope: str) -> list[MentorRequest]:
    query = select(MentorRequest)
    if scope == "open":
        query = query.where(MentorRequest.mentor_id.is_(None), MentorRequest.status == S.pending)
    elif scope == "mine":
        query = query.where(MentorRequest.mentor_id == mentor.id)
    else:  # "all" that this mentor may see
        query = query.where(
            or_(
                MentorRequest.mentor_id == mentor.id,
                (MentorRequest.mentor_id.is_(None)) & (MentorRequest.status == S.pending),
            )
        )
    return list(db.scalars(query.order_by(MentorRequest.created_at.desc(), MentorRequest.id.desc())))


def visible_to_mentor(db: Session, mentor: User, request_id: int) -> MentorRequest:
    request = db.get(MentorRequest, request_id)
    if request is None:
        raise NotFound
    is_open = request.mentor_id is None and request.status == S.pending
    if request.mentor_id != mentor.id and not is_open:
        raise NotFound
    return request


def accept(db: Session, mentor: User, request_id: int) -> MentorRequest:
    request = visible_to_mentor(db, mentor, request_id)
    if request.status != S.pending:
        raise MentorshipError("Only pending requests can be accepted.")
    request.mentor_id = mentor.id
    request.status = S.accepted
    db.commit()
    db.refresh(request)
    return request


def decline(db: Session, mentor: User, request_id: int) -> MentorRequest:
    request = visible_to_mentor(db, mentor, request_id)
    if request.mentor_id != mentor.id:
        raise MentorshipError("You can only decline requests assigned to you.")
    if request.status not in {S.pending, S.accepted}:
        raise MentorshipError("This request can't be declined at this stage.")
    request.status = S.declined
    _free_slot(request)
    db.commit()
    db.refresh(request)
    return request


def set_status(db: Session, mentor: User, request_id: int, status: S) -> MentorRequest:
    request = visible_to_mentor(db, mentor, request_id)
    if request.mentor_id != mentor.id:
        raise MentorshipError("Accept this request before updating it.")
    if status not in MENTOR_TRANSITIONS.get(request.status, set()):
        raise MentorshipError(f"A request that is {request.status.value.replace('_', ' ')} can't be moved to "
                              f"{status.value.replace('_', ' ')}.")
    request.status = status
    db.commit()
    db.refresh(request)
    return request


def add_feedback(db: Session, mentor: User, request_id: int, body: str) -> MentorFeedback:
    request = visible_to_mentor(db, mentor, request_id)
    if request.mentor_id != mentor.id or request.status not in ACTIVE:
        raise MentorshipError("Accept this request before giving feedback.")
    feedback = MentorFeedback(request_id=request.id, mentor_id=mentor.id, body=body)
    db.add(feedback)
    if request.status == S.accepted:
        request.status = S.in_progress
    db.commit()
    db.refresh(feedback)
    return feedback


def shared_materials(db: Session, mentor: User, request: MentorRequest) -> dict:
    """Only what the student agreed to share, only for the mentor who took the request (PB-28)."""
    allowed = request.mentor_id == mentor.id and request.status in ACTIVE
    materials: dict = {"access": allowed, "profile": None, "resume": None, "progress": None}
    if not allowed:
        return materials
    if request.share_profile:
        profile = db.scalar(select(Profile).where(Profile.user_id == request.student_id))
        materials["profile"] = (
            {
                "target_role": profile.target_role,
                "education": profile.education,
                "skills": profile.skills,
                "experience": profile.experience,
                "interests": profile.interests,
            }
            if profile
            else None
        )
    if request.share_resume:
        resume = db.scalar(
            select(Resume).where(Resume.student_id == request.student_id, Resume.is_current.is_(True))
        )
        materials["resume"] = (
            {"filename": resume.filename, "uploaded_at": resume.uploaded_at, "text": resume.text} if resume else None
        )
    if request.share_progress:
        materials["progress"] = student_progress(db, request.student_id)
    return materials


# ------------------------------------------------------------------ progress (PB-29)

def student_progress(db: Session, student_id: int) -> dict:
    """Preparation activity in summary form. Application notes and answers stay private."""
    applications = list(db.scalars(select(Application.status).where(Application.student_id == student_id)))
    matches = list(
        db.scalars(
            select(MatchResult).where(MatchResult.student_id == student_id).order_by(MatchResult.created_at.desc())
        )
    )
    sessions = list(db.scalars(select(InterviewSession).where(InterviewSession.student_id == student_id)))
    session_scores = []
    for session in sessions:
        scores = [a.feedback.get("score") for a in session.answers if isinstance(a.feedback.get("score"), (int, float))]
        if scores:
            session_scores.append(sum(scores) / len(scores))
    profile = db.scalar(select(Profile).where(Profile.user_id == student_id))
    has_resume = db.scalar(select(Resume.id).where(Resume.student_id == student_id).limit(1)) is not None
    return {
        "profile_complete": bool(profile and profile.education and profile.skills and profile.target_role),
        "target_role": profile.target_role if profile else "",
        "has_resume": has_resume,
        "applications_total": len(applications),
        "applications_by_status": {status.value: count for status, count in Counter(applications).items()},
        "analyses_total": len(matches),
        "latest_match": (
            {"job_title": matches[0].job_title, "company": matches[0].company, "score": matches[0].score,
             "date": matches[0].created_at}
            if matches else None
        ),
        "best_match_score": max((m.score for m in matches), default=None),
        "interviews_completed": sum(1 for s in sessions if s.status == InterviewStatus.completed),
        "interview_average_score": round(sum(session_scores) / len(session_scores), 1) if session_scores else None,
    }


def supported_students(db: Session, mentor: User) -> list[dict]:
    """Students this mentor is actively helping, with progress only where it was shared."""
    requests = list(
        db.scalars(
            select(MentorRequest)
            .where(MentorRequest.mentor_id == mentor.id, MentorRequest.status.in_(ACTIVE))
            .order_by(MentorRequest.updated_at.desc())
        )
    )
    students: dict[int, dict] = {}
    for request in requests:
        entry = students.setdefault(
            request.student_id,
            {"student": {"id": request.student.id, "full_name": request.student.full_name},
             "requests": [], "progress_shared": False, "progress": None},
        )
        entry["requests"].append(
            {"id": request.id, "request_type": request.request_type, "status": request.status,
             "updated_at": request.updated_at}
        )
        if request.share_progress:
            entry["progress_shared"] = True
    for student_id, entry in students.items():
        if entry["progress_shared"]:
            entry["progress"] = student_progress(db, student_id)
    return list(students.values())
