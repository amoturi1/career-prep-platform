"""Account administration (PB-30) and platform analytics (PB-36)."""
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Application,
    InterviewSession,
    InterviewStatus,
    MatchResult,
    MentorRequest,
    Opportunity,
    Role,
    User,
)
from app.schemas import UserAdminUpdate


class AdminError(ValueError):
    """A change that isn't allowed; the message is safe to show."""


def list_users(db: Session, role: Role | None = None, search: str = "") -> list[User]:
    query = select(User)
    if role is not None:
        query = query.where(User.role == role)
    if search:
        like = f"%{search.lower()}%"
        query = query.where(func.lower(User.email).like(like) | func.lower(User.full_name).like(like))
    return list(db.scalars(query.order_by(User.created_at.desc(), User.id.desc())))


def update_user(db: Session, admin: User, user_id: int, data: UserAdminUpdate) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise LookupError
    if user.id == admin.id and (
        (data.role is not None and data.role != Role.admin) or data.is_active is False
    ):
        raise AdminError("You can't remove your own admin access or deactivate your own account.")
    if user.role == Role.admin and user.id != admin.id and (
        (data.role is not None and data.role != Role.admin) or data.is_active is False
    ):
        active_admins = db.scalar(
            select(func.count()).select_from(User).where(User.role == Role.admin, User.is_active.is_(True))
        )
        if active_admins <= 1:
            raise AdminError("At least one active administrator is required.")
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def analytics(db: Session, weeks: int = 8) -> dict:
    """Aggregate numbers only; nothing that identifies an individual student."""
    users = list(db.execute(select(User.role, User.is_active)))
    matches = list(db.execute(select(MatchResult.score, MatchResult.created_at)))
    sessions = list(db.execute(select(InterviewSession.status, InterviewSession.created_at)))

    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    buckets = [week_start - timedelta(weeks=i) for i in reversed(range(weeks))]

    def weekly(rows, keep=lambda row: True):
        counts = [0] * weeks
        for row in rows:
            if not keep(row):
                continue
            created = _as_utc(row.created_at)
            for i in reversed(range(weeks)):
                if created >= buckets[i]:
                    counts[i] += 1
                    break
        return counts

    scores = [m.score for m in matches]
    return {
        "generated_at": now,
        "users": {
            "total": len(users),
            "active": sum(1 for u in users if u.is_active),
            "by_role": {role.value: sum(1 for u in users if u.role == role) for role in Role},
        },
        "applications_by_status": {
            status.value: count
            for status, count in Counter(db.scalars(select(Application.status))).items()
        },
        "match": {
            "total": len(scores),
            "average_score": round(sum(scores) / len(scores), 1) if scores else None,
            "score_bands": {
                "0-24": sum(1 for s in scores if s < 25),
                "25-49": sum(1 for s in scores if 25 <= s < 50),
                "50-74": sum(1 for s in scores if 50 <= s < 75),
                "75-100": sum(1 for s in scores if s >= 75),
            },
        },
        "interviews": {
            "total": len(sessions),
            "completed": sum(1 for s in sessions if s.status == InterviewStatus.completed),
        },
        "weekly": {
            "week_starting": [b.date().isoformat() for b in buckets],
            "match_analyses": weekly(matches),
            "interview_sessions": weekly(sessions),
        },
        "mentor_requests_by_status": {
            status.value: count for status, count in Counter(db.scalars(select(MentorRequest.status))).items()
        },
        "content": {
            f"{kind.value}:{status.value}": count
            for (kind, status), count in Counter(db.execute(select(Opportunity.kind, Opportunity.status))).items()
        },
    }
