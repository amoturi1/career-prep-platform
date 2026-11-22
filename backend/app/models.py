"""Database tables (data layer).

Accounts and profiles ........ users, profiles, revoked_tokens
Application tracking ......... applications
Opportunities and content .... opportunities (jobs, internships, events, announcements)
Resumes and AI preparation ... resumes, match_results
Mock interviews .............. interview_sessions, interview_answers
Mentorship ................... mentor_slots, mentor_requests, mentor_feedback
"""
import enum
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- enums

class Role(str, enum.Enum):
    student = "student"
    mentor = "mentor"
    admin = "admin"


class ApplicationStatus(str, enum.Enum):
    saved = "Saved"
    applied = "Applied"
    interview = "Interview"
    offer = "Offer"
    rejected = "Rejected"
    withdrawn = "Withdrawn"


class OpportunityKind(str, enum.Enum):
    job = "job"
    internship = "internship"
    event = "event"
    announcement = "announcement"


class PublishStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class InterviewStatus(str, enum.Enum):
    active = "active"
    completed = "completed"


class MentorRequestType(str, enum.Enum):
    resume_review = "resume_review"
    interview_practice = "interview_practice"
    career_guidance = "career_guidance"


class MentorRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    in_progress = "in_progress"
    completed = "completed"
    declined = "declined"
    cancelled = "cancelled"


# ---------------------------------------------------------------- accounts

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.student)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    profile: Mapped[Optional["Profile"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    education: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[str] = mapped_column(Text, default="")
    experience: Mapped[str] = mapped_column(Text, default="")
    interests: Mapped[str] = mapped_column(Text, default="")
    target_role: Mapped[str] = mapped_column(String(150), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="profile")


class RevokedToken(Base):
    """Tokens ended by sign-out (PB-11); they can no longer access protected routes."""

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


# ---------------------------------------------------------------- tracker

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    company: Mapped[str] = mapped_column(String(150))
    job_title: Mapped[str] = mapped_column(String(150))
    date_applied: Mapped[date | None] = mapped_column(Date, nullable=True)
    url: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus), default=ApplicationStatus.saved)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    student: Mapped[User] = relationship(back_populates="applications")


# ---------------------------------------------------------------- content

class Opportunity(Base):
    """A published item: job, internship, career event or announcement."""

    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    organization: Mapped[str] = mapped_column(String(150))
    kind: Mapped[OpportunityKind] = mapped_column(Enum(OpportunityKind), default=OpportunityKind.internship)
    location: Mapped[str] = mapped_column(String(150), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    apply_url: Mapped[str] = mapped_column(String(500), default="")
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    event_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # events only, local time
    status: Mapped[PublishStatus] = mapped_column(Enum(PublishStatus), default=PublishStatus.published)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=True)


# ---------------------------------------------------------------- resumes and AI

class Resume(Base):
    """Every upload is kept as a version; exactly one is current (PB-18, PB-19).

    Only the extracted text is stored, not the original file (NFR-02).
    """

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(20))  # "pdf", "docx", "txt" or "pasted"
    text: Mapped[str] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MatchResult(Base):
    """A saved resume-to-job-description analysis (PB-20, PB-21, PB-22, PB-35)."""

    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id"), nullable=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id"), nullable=True)
    job_title: Mapped[str] = mapped_column(String(150))
    company: Mapped[str] = mapped_column(String(150), default="")
    job_description: Mapped[str] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer)
    result: Mapped[dict] = mapped_column(JSON)  # matched/missing skills, explanations, suggestions
    engine: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---------------------------------------------------------------- mock interviews

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(150))
    focus: Mapped[str] = mapped_column(Text, default="")  # topic or job description used for questions
    questions: Mapped[list] = mapped_column(JSON)
    status: Mapped[InterviewStatus] = mapped_column(Enum(InterviewStatus), default=InterviewStatus.active)
    engine: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    answers: Mapped[list["InterviewAnswer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="InterviewAnswer.question_index"
    )


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"
    __table_args__ = (UniqueConstraint("session_id", "question_index"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id"), index=True)
    question_index: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    feedback: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    session: Mapped[InterviewSession] = relationship(back_populates="answers")


# ---------------------------------------------------------------- mentorship

class MentorSlot(Base):
    """A time a mentor is available (PB-31). Times are local wall-clock times."""

    __tablename__ = "mentor_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    mentor: Mapped[User] = relationship()


class MentorRequest(Base):
    """A student's request for help (PB-26). A booked session is a request with a slot (PB-32)."""

    __tablename__ = "mentor_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mentor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    slot_id: Mapped[int | None] = mapped_column(ForeignKey("mentor_slots.id"), nullable=True)
    request_type: Mapped[MentorRequestType] = mapped_column(Enum(MentorRequestType))
    message: Mapped[str] = mapped_column(Text)
    share_profile: Mapped[bool] = mapped_column(Boolean, default=False)
    share_resume: Mapped[bool] = mapped_column(Boolean, default=False)
    share_progress: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[MentorRequestStatus] = mapped_column(Enum(MentorRequestStatus), default=MentorRequestStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    student: Mapped[User] = relationship(foreign_keys=[student_id])
    mentor: Mapped[Optional[User]] = relationship(foreign_keys=[mentor_id])
    slot: Mapped[Optional[MentorSlot]] = relationship()
    feedback: Mapped[list["MentorFeedback"]] = relationship(
        back_populates="request", cascade="all, delete-orphan", order_by="MentorFeedback.created_at"
    )


class MentorFeedback(Base):
    __tablename__ = "mentor_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("mentor_requests.id"), index=True)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    request: Mapped[MentorRequest] = relationship(back_populates="feedback")
