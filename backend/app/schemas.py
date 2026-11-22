"""Request and response shapes, plus input validation rules (PB-03, NFR-03)."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import (
    ApplicationStatus,
    InterviewStatus,
    MentorRequestStatus,
    MentorRequestType,
    OpportunityKind,
    PublishStatus,
    Role,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


def _check_url(value: str) -> str:
    if value and not value.startswith(("http://", "https://")):
        raise ValueError("Link must start with http:// or https://")
    return value


# ---------- Accounts (PB-01, PB-02, PB-03, PB-11) ----------

class RegisterIn(StrictModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one letter and one number")
        return value


class LoginIn(StrictModel):
    # Sign-in accepts any address an account was created with; format rules apply at registration.
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: Role
    is_active: bool


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Profiles (PB-04, PB-05, PB-06) ----------

class ProfileIn(StrictModel):
    education: str = Field(min_length=1, max_length=2000)
    skills: str = Field(min_length=1, max_length=2000)
    experience: str = Field(default="", max_length=4000)
    interests: str = Field(default="", max_length=2000)
    target_role: str = Field(min_length=1, max_length=150)


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    education: str
    skills: str
    experience: str
    interests: str
    target_role: str
    updated_at: datetime


# ---------- Applications (PB-07 to PB-10, PB-12, PB-13) ----------

class ApplicationCreate(StrictModel):
    company: str = Field(min_length=1, max_length=150)
    job_title: str = Field(min_length=1, max_length=150)
    date_applied: date | None = None
    url: str = Field(default="", max_length=500)
    status: ApplicationStatus = ApplicationStatus.saved
    notes: str = Field(default="", max_length=4000)

    _url = field_validator("url")(_check_url)

    @field_validator("date_applied")
    @classmethod
    def not_in_future(cls, value: date | None) -> date | None:
        if value and value > date.today():
            raise ValueError("Date applied cannot be in the future")
        return value


class ApplicationUpdate(ApplicationCreate):
    """Editing uses the same rules as creating (PB-10)."""


class StatusUpdate(StrictModel):
    status: ApplicationStatus


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    job_title: str
    date_applied: date | None
    url: str
    status: ApplicationStatus
    notes: str
    created_at: datetime
    updated_at: datetime


# ---------- Opportunities and content (PB-14 to PB-17, PB-34) ----------

class OpportunityCreate(StrictModel):
    title: str = Field(min_length=1, max_length=150)
    organization: str = Field(min_length=1, max_length=150)
    kind: OpportunityKind = OpportunityKind.internship
    location: str = Field(default="", max_length=150)
    description: str = Field(min_length=1, max_length=8000)
    apply_url: str = Field(default="", max_length=500)
    deadline: date | None = None
    event_at: datetime | None = Field(default=None, validate_default=True)
    status: PublishStatus = PublishStatus.published

    _url = field_validator("apply_url")(_check_url)

    @field_validator("event_at")
    @classmethod
    def event_needs_time(cls, value: datetime | None, info) -> datetime | None:
        kind = info.data.get("kind")
        if kind == OpportunityKind.event and value is None:
            raise ValueError("Events need a date and time")
        if kind != OpportunityKind.event:
            return None
        return value.replace(tzinfo=None)


class OpportunityUpdate(OpportunityCreate):
    """Editing uses the same rules as publishing (PB-34)."""


class PublishStatusUpdate(StrictModel):
    status: PublishStatus


class OpportunityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    organization: str
    kind: OpportunityKind
    location: str
    description: str
    apply_url: str
    deadline: date | None
    event_at: datetime | None = None
    status: PublishStatus
    created_at: datetime
    updated_at: datetime | None = None


# ---------- Resumes (PB-18, PB-19) ----------

class ResumeTextIn(StrictModel):
    text: str = Field(min_length=50, max_length=30000)
    label: str = Field(default="Pasted resume", max_length=100)


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    source: str
    is_current: bool
    uploaded_at: datetime
    word_count: int = 0


class ResumeDetail(ResumeOut):
    text: str


# ---------- AI career preparation (PB-20, PB-21, PB-22, PB-35) ----------

class MatchIn(StrictModel):
    opportunity_id: int | None = None
    resume_id: int | None = None
    job_title: str = Field(default="", max_length=150)
    company: str = Field(default="", max_length=150)
    job_description: str = Field(default="", max_length=15000, validate_default=True)

    @field_validator("job_description")
    @classmethod
    def needs_a_job(cls, value: str, info) -> str:
        if info.data.get("opportunity_id") is None and len(value) < 30:
            raise ValueError("Paste a job description (at least 30 characters) or choose a published listing")
        return value


class MatchSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_title: str
    company: str
    opportunity_id: int | None
    score: int
    engine: str
    created_at: datetime


class MatchOut(MatchSummary):
    resume_id: int | None
    job_description: str
    result: dict


# ---------- Mock interviews (PB-23, PB-24, PB-25) ----------

class InterviewStart(StrictModel):
    role: str = Field(min_length=1, max_length=150)
    focus: str = Field(default="", max_length=8000)
    opportunity_id: int | None = None
    question_count: int = Field(default=5, ge=3, le=8)


class AnswerIn(StrictModel):
    question_index: int = Field(ge=0)
    answer: str = Field(min_length=1, max_length=6000)


class AnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_index: int
    question: str
    answer: str
    feedback: dict
    created_at: datetime


class InterviewSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    status: InterviewStatus
    engine: str
    created_at: datetime
    completed_at: datetime | None
    question_count: int = 0
    answered_count: int = 0
    average_score: float | None = None


class InterviewOut(InterviewSummary):
    focus: str
    questions: list[str]
    answers: list[AnswerOut]


# ---------- Mentorship (PB-26 to PB-29, PB-31 to PB-33) ----------

class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


class SlotIn(StrictModel):
    start_at: datetime
    duration_minutes: int = Field(default=30, ge=15, le=180)

    @field_validator("start_at")
    @classmethod
    def in_future(cls, value: datetime) -> datetime:
        value = value.replace(tzinfo=None)
        if value <= datetime.now():
            raise ValueError("Pick a time in the future")
        return value


class SlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_at: datetime
    duration_minutes: int
    is_booked: bool
    mentor: PersonOut


class MentorRequestIn(StrictModel):
    request_type: MentorRequestType
    message: str = Field(min_length=10, max_length=2000)
    share_profile: bool = False
    share_resume: bool = False
    share_progress: bool = False
    slot_id: int | None = None


class RequestStatusUpdate(StrictModel):
    status: MentorRequestStatus


class FeedbackIn(StrictModel):
    body: str = Field(min_length=5, max_length=5000)


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    created_at: datetime


class MentorRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_type: MentorRequestType
    message: str
    status: MentorRequestStatus
    share_profile: bool
    share_resume: bool
    share_progress: bool
    created_at: datetime
    updated_at: datetime
    student: PersonOut
    mentor: PersonOut | None
    slot: SlotOut | None
    feedback: list[FeedbackOut]


# ---------- Administration (PB-30) ----------

class UserAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime


class UserAdminUpdate(StrictModel):
    role: Role | None = None
    is_active: bool | None = None
