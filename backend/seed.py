"""Create demo accounts and sample content.

Usage (from the backend folder):
    python seed.py
    python seed.py --admin-email you@school.edu --admin-password "Secret123"

Creates (only if missing):
  * an administrator account   admin@careerprep.com  / Admin12345
  * a mentor account           mentor@careerprep.com / Mentor12345, with a few open session times
  * sample jobs, internships, a career event and an announcement

Self-registration only creates students; admins can promote users to mentor or admin
on the Users page (PB-30).
"""
import argparse
from datetime import date, datetime, timedelta

from app.database import SessionLocal, init_db
from app.models import MentorSlot, Opportunity, OpportunityKind, Role, User
from app.security import hash_password
from app.services.accounts import find_by_email

SAMPLE_LISTINGS = [
    dict(
        title="Software Engineering Intern",
        organization="Northstar Labs",
        kind=OpportunityKind.internship,
        location="Charlotte, NC (Hybrid)",
        description="Build internal tools with a small product team.\n"
        "Requirements:\n- Proficiency in Python or Java\n- Experience with REST APIs and SQL\n- Git and code reviews\n"
        "Nice to have:\n- React or another frontend framework\n- Docker and AWS",
        apply_url="https://example.com/northstar-intern",
        deadline=date.today() + timedelta(days=30),
    ),
    dict(
        title="Data Analyst Intern",
        organization="BrightTech",
        kind=OpportunityKind.internship,
        location="Remote",
        description="Clean and analyze product data and present findings to stakeholders.\n"
        "Requirements:\n- SQL and Excel\n- Python with Pandas\n- Clear communication skills\n"
        "Preferred:\n- Tableau or Power BI dashboards\n- Statistics coursework",
        apply_url="https://example.com/brighttech-analyst",
        deadline=date.today() + timedelta(days=21),
    ),
    dict(
        title="Junior Backend Developer",
        organization="Acme Corp",
        kind=OpportunityKind.job,
        location="Raleigh, NC",
        description="Entry-level role maintaining REST APIs.\n"
        "Requirements:\n- Python and FastAPI or Django\n- PostgreSQL\n- Testing with pytest\n"
        "Nice to have:\n- Docker, Kubernetes and CI/CD",
        apply_url="https://example.com/acme-backend",
        deadline=None,
    ),
]

SAMPLE_EVENT = dict(
    title="Fall Tech Career Fair",
    organization="University Career Center",
    kind=OpportunityKind.event,
    location="Student Union, Main Ballroom",
    description="Meet recruiters from 40+ companies hiring interns and new graduates. "
    "Bring printed copies of your resume and dress business casual.",
    apply_url="https://example.com/career-fair",
)

SAMPLE_ANNOUNCEMENT = dict(
    title="Resume review week",
    organization="University Career Center",
    kind=OpportunityKind.announcement,
    description="Mentors are offering extra resume-review sessions this week. "
    "Book a time on the Mentors page and share your resume when you request help.",
)


def _ensure_user(db, email: str, password: str, name: str, role: Role) -> User:
    user = find_by_email(db, email)
    if user is None:
        user = User(email=email.lower(), full_name=name, password_hash=hash_password(password), role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created {role.value} account: {user.email}")
    else:
        print(f"{role.value.capitalize()} account already exists: {user.email}")
    return user


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--admin-email", default="admin@careerprep.com")
    parser.add_argument("--admin-password", default="Admin12345")
    parser.add_argument("--mentor-email", default="mentor@careerprep.com")
    parser.add_argument("--mentor-password", default="Mentor12345")
    parser.add_argument("--no-samples", action="store_true", help="Skip creating sample content and slots")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        admin = _ensure_user(db, args.admin_email, args.admin_password, "Platform Administrator", Role.admin)
        mentor = _ensure_user(db, args.mentor_email, args.mentor_password, "Jordan Rivera", Role.mentor)
        if args.no_samples:
            return

        kinds = {kind for (kind,) in db.query(Opportunity.kind).all()}
        added = 0
        if not kinds & {OpportunityKind.job, OpportunityKind.internship}:
            for listing in SAMPLE_LISTINGS:
                db.add(Opportunity(created_by=admin.id, **listing))
                added += 1
        if OpportunityKind.event not in kinds:
            event_day = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=14)
            db.add(Opportunity(created_by=admin.id, event_at=event_day, **SAMPLE_EVENT))
            added += 1
        if OpportunityKind.announcement not in kinds:
            db.add(Opportunity(created_by=admin.id, **SAMPLE_ANNOUNCEMENT))
            added += 1
        if added:
            print(f"Added {added} sample items (jobs, internships, events, announcements).")

        if db.query(MentorSlot).filter(MentorSlot.mentor_id == mentor.id).count() == 0:
            base = datetime.now().replace(minute=0, second=0, microsecond=0)
            for days, hour in [(2, 15), (3, 11), (5, 16), (7, 14)]:
                db.add(MentorSlot(mentor_id=mentor.id, start_at=(base + timedelta(days=days)).replace(hour=hour),
                                  duration_minutes=30))
            print("Added 4 open mentor session times.")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
