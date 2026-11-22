"""PB-16 publish (admin), PB-14 browse (student)."""
from tests.conftest import auth_header

LISTING = {
    "title": "Software Engineering Intern",
    "organization": "Northstar Labs",
    "kind": "internship",
    "location": "Charlotte, NC",
    "description": "Build internal tools.",
    "apply_url": "https://example.com/apply",
    "deadline": "2026-12-01",
}


def test_admin_publishes_and_student_browses(client, admin_token, student_token):
    published = client.post("/api/opportunities", json=LISTING, headers=auth_header(admin_token))
    assert published.status_code == 201
    listings = client.get("/api/opportunities", headers=auth_header(student_token)).json()
    assert [item["title"] for item in listings] == ["Software Engineering Intern"]
    detail = client.get(f"/api/opportunities/{published.json()['id']}", headers=auth_header(student_token))
    assert detail.json()["organization"] == "Northstar Labs"


def test_student_cannot_publish(client, student_token):
    response = client.post("/api/opportunities", json=LISTING, headers=auth_header(student_token))
    assert response.status_code == 403


def test_browsing_requires_sign_in(client):
    assert client.get("/api/opportunities").status_code == 401


def test_drafts_are_hidden_from_students(client, admin_token, student_token):
    draft = client.post(
        "/api/opportunities", json={**LISTING, "status": "draft"}, headers=auth_header(admin_token)
    ).json()
    assert client.get("/api/opportunities", headers=auth_header(student_token)).json() == []
    assert client.get(f"/api/opportunities/{draft['id']}", headers=auth_header(student_token)).status_code == 404
    admin_view = client.get("/api/opportunities/manage", headers=auth_header(admin_token)).json()
    assert len(admin_view) == 1


def test_filter_by_kind(client, admin_token, student_token):
    client.post("/api/opportunities", json=LISTING, headers=auth_header(admin_token))
    client.post("/api/opportunities", json={**LISTING, "kind": "job", "title": "Analyst"}, headers=auth_header(admin_token))
    jobs = client.get("/api/opportunities?kind=job", headers=auth_header(student_token)).json()
    assert [j["title"] for j in jobs] == ["Analyst"]


def test_publish_validation(client, admin_token):
    response = client.post(
        "/api/opportunities", json={**LISTING, "title": "", "apply_url": "ftp://x"}, headers=auth_header(admin_token)
    )
    assert response.status_code == 422
    assert {e["field"] for e in response.json()["errors"]} == {"title", "apply_url"}
