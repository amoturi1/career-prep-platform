"""Test setup: every test gets a fresh in-memory database and the built-in AI engine (NFR-11)."""
import os

# Must be set before the app is imported.
os.environ["DATABASE_URL"] = "sqlite://"  # keep tests away from the real database file
os.environ["AI_PROVIDER"] = "local"  # never call a paid AI service from tests
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256-signing"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Role, User  # noqa: E402
from app.security import hash_password  # noqa: E402

PASSWORD = "Password123"


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register(client, email="student@uncc.edu", name="Test Student", password=PASSWORD):
    response = client.post("/api/auth/register", json={"full_name": name, "email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def make_user(client, db_session, email: str, role: Role, name: str = "Staff Member") -> str:
    db_session.add(User(email=email, full_name=name, password_hash=hash_password(PASSWORD), role=role))
    db_session.commit()
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture()
def student_token(client):
    return register(client)


@pytest.fixture()
def other_student_token(client):
    return register(client, email="other@uncc.edu", name="Other Student")


@pytest.fixture()
def admin_token(client, db_session):
    return make_user(client, db_session, "admin@uncc.edu", Role.admin, "Admin")


@pytest.fixture()
def mentor_token(client, db_session):
    return make_user(client, db_session, "mentor@uncc.edu", Role.mentor, "Jordan Mentor")


@pytest.fixture()
def other_mentor_token(client, db_session):
    return make_user(client, db_session, "mentor2@uncc.edu", Role.mentor, "Sam Mentor")


RESUME_TEXT = """Akshara K - B.S. Computer Science, UNC Charlotte (expected 2027)
Skills: Python, JavaScript, React, SQL, Git
Teaching Assistant: Helped 40 students debug Python labs and led weekly review sessions.
Project: Built a FastAPI backend with REST APIs and JWT authentication, and a React frontend.
Wrote pytest unit tests and reduced API response time by 30%.
"""

JOB_TEXT = """Software Engineering Intern
Requirements:
- Proficiency in Python or Java
- Experience with REST APIs and SQL
Nice to have:
- Docker and AWS
"""
