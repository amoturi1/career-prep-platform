"""PB-15 event details, PB-17 events/announcements, PB-34 update/archive, PB-30 accounts, PB-36 analytics."""
from datetime import datetime, timedelta

from sqlalchemy import create_engine, inspect, text

from app.database import init_db
from tests.conftest import JOB_TEXT, RESUME_TEXT, auth_header

EVENT = {
    "title": "Fall Career Fair",
    "organization": "Career Center",
    "kind": "event",
    "location": "Student Union",
    "description": "Meet 40 employers.",
    "event_at": (datetime.now() + timedelta(days=10)).replace(microsecond=0).isoformat(),
}


# ------------------------------------------------------------------ content

def test_events_need_a_time_and_show_details(client, admin_token, student_token):
    missing_time = client.post("/api/opportunities", json={**EVENT, "event_at": None}, headers=auth_header(admin_token))
    assert missing_time.status_code == 422
    assert missing_time.json()["errors"][0]["field"] == "event_at"
    created = client.post("/api/opportunities", json=EVENT, headers=auth_header(admin_token)).json()
    detail = client.get(f"/api/opportunities/{created['id']}", headers=auth_header(student_token)).json()
    assert detail["kind"] == "event" and detail["location"] == "Student Union" and detail["event_at"]


def test_announcements_and_filtering_by_kind(client, admin_token, student_token):
    client.post("/api/opportunities", json={"title": "Office closed Friday", "organization": "Career Center",
                                            "kind": "announcement", "description": "Closed for the holiday."},
                headers=auth_header(admin_token))
    client.post("/api/opportunities", json=EVENT, headers=auth_header(admin_token))
    items = client.get("/api/opportunities?kind=announcement", headers=auth_header(student_token)).json()
    assert [i["title"] for i in items] == ["Office closed Friday"]
    assert items[0]["event_at"] is None


def test_update_and_archive(client, admin_token, student_token):
    created = client.post("/api/opportunities", json=EVENT, headers=auth_header(admin_token)).json()
    edited = client.put(f"/api/opportunities/{created['id']}", json={**EVENT, "location": "Main Ballroom"},
                        headers=auth_header(admin_token))
    assert edited.json()["location"] == "Main Ballroom"
    archived = client.patch(f"/api/opportunities/{created['id']}/status", json={"status": "archived"},
                            headers=auth_header(admin_token))
    assert archived.json()["status"] == "archived"
    assert client.get("/api/opportunities", headers=auth_header(student_token)).json() == []
    assert client.get(f"/api/opportunities/{created['id']}", headers=auth_header(student_token)).status_code == 404
    # Students can't edit or archive
    assert client.patch(f"/api/opportunities/{created['id']}/status", json={"status": "published"},
                        headers=auth_header(student_token)).status_code == 403


# ------------------------------------------------------------------ accounts and roles

def test_admin_promotes_student_to_mentor(client, admin_token, student_token):
    users = client.get("/api/admin/users?role=student", headers=auth_header(admin_token)).json()
    student = users[0]
    promoted = client.patch(f"/api/admin/users/{student['id']}", json={"role": "mentor"},
                            headers=auth_header(admin_token))
    assert promoted.json()["role"] == "mentor"
    # The new role applies immediately: mentor pages open, student pages don't
    assert client.get("/api/mentor/requests", headers=auth_header(student_token)).status_code == 200
    assert client.get("/api/applications", headers=auth_header(student_token)).status_code == 403


def test_deactivated_users_are_signed_out(client, admin_token, student_token):
    student = client.get("/api/admin/users?search=student@", headers=auth_header(admin_token)).json()[0]
    client.patch(f"/api/admin/users/{student['id']}", json={"is_active": False}, headers=auth_header(admin_token))
    assert client.get("/api/auth/me", headers=auth_header(student_token)).status_code == 401
    login = client.post("/api/auth/login", json={"email": "student@uncc.edu", "password": "Password123"})
    assert login.status_code == 403


def test_admin_cannot_lock_themselves_out(client, admin_token):
    me = client.get("/api/auth/me", headers=auth_header(admin_token)).json()
    response = client.patch(f"/api/admin/users/{me['id']}", json={"role": "student"}, headers=auth_header(admin_token))
    assert response.status_code == 400
    response = client.patch(f"/api/admin/users/{me['id']}", json={"is_active": False}, headers=auth_header(admin_token))
    assert response.status_code == 400


def test_only_admins_manage_accounts(client, student_token, mentor_token):
    for token in (student_token, mentor_token):
        assert client.get("/api/admin/users", headers=auth_header(token)).status_code == 403
        assert client.get("/api/admin/analytics", headers=auth_header(token)).status_code == 403


# ------------------------------------------------------------------ analytics

def test_analytics_are_aggregate_only(client, admin_token, student_token):
    client.post("/api/resumes/text", json={"text": RESUME_TEXT}, headers=auth_header(student_token))
    client.post("/api/match", json={"job_description": JOB_TEXT}, headers=auth_header(student_token))
    client.post("/api/interviews", json={"role": "Intern"}, headers=auth_header(student_token))
    data = client.get("/api/admin/analytics", headers=auth_header(admin_token)).json()
    assert data["users"]["by_role"]["student"] == 1
    assert data["match"]["total"] == 1 and data["match"]["average_score"] is not None
    assert data["interviews"]["total"] == 1
    assert sum(data["weekly"]["match_analyses"]) == 1 and len(data["weekly"]["week_starting"]) == 8
    assert "student@uncc.edu" not in str(data)  # no individual details


# ------------------------------------------------------------------ database upgrade

def test_old_database_gets_new_columns():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:  # a Sprint 1-era table without event_at / updated_at
        conn.execute(text(
            "CREATE TABLE opportunities (id INTEGER PRIMARY KEY, title VARCHAR(150), organization VARCHAR(150), "
            "kind VARCHAR(10), location VARCHAR(150), description TEXT, apply_url VARCHAR(500), deadline DATE, "
            "status VARCHAR(9), created_by INTEGER, created_at DATETIME)"
        ))
    init_db(engine)
    columns = {c["name"] for c in inspect(engine).get_columns("opportunities")}
    assert {"event_at", "updated_at"} <= columns
    assert "mentor_requests" in inspect(engine).get_table_names()
