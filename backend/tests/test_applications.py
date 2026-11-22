"""PB-07 add, PB-08 view, PB-09 status, PB-10 edit, PB-12 delete, PB-13 filter."""
from datetime import date, timedelta

from tests.conftest import auth_header

APP = {
    "company": "Acme",
    "job_title": "Software Intern",
    "date_applied": "2026-10-02",
    "url": "https://acme.example.com/jobs/1",
    "status": "Applied",
    "notes": "Referred by a friend",
}


def add(client, token, **overrides):
    response = client.post("/api/applications", json={**APP, **overrides}, headers=auth_header(token))
    assert response.status_code == 201, response.text
    return response.json()


def test_add_and_list_applications(client, student_token):
    add(client, student_token)
    add(client, student_token, company="Northstar", status="Interview")
    listed = client.get("/api/applications", headers=auth_header(student_token)).json()
    assert {a["company"] for a in listed} == {"Acme", "Northstar"}


def test_add_requires_company_and_title(client, student_token):
    response = client.post(
        "/api/applications", json={"company": "", "job_title": ""}, headers=auth_header(student_token)
    )
    assert response.status_code == 422
    fields = {e["field"] for e in response.json()["errors"]}
    assert fields == {"company", "job_title"}


def test_rejects_future_date_and_bad_url_and_bad_status(client, student_token):
    future = (date.today() + timedelta(days=3)).isoformat()
    response = client.post(
        "/api/applications",
        json={**APP, "date_applied": future, "url": "acme.com", "status": "Ghosted"},
        headers=auth_header(student_token),
    )
    assert response.status_code == 422
    fields = {e["field"] for e in response.json()["errors"]}
    assert fields == {"date_applied", "url", "status"}


def test_update_status(client, student_token):
    created = add(client, student_token)
    response = client.patch(
        f"/api/applications/{created['id']}/status", json={"status": "Offer"}, headers=auth_header(student_token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Offer"


def test_edit_details(client, student_token):
    created = add(client, student_token)
    response = client.put(
        f"/api/applications/{created['id']}",
        json={**APP, "job_title": "Backend Intern", "notes": "Phone screen Friday"},
        headers=auth_header(student_token),
    )
    assert response.status_code == 200
    assert response.json()["job_title"] == "Backend Intern"


def test_filter_by_status(client, student_token):
    add(client, student_token, status="Applied")
    add(client, student_token, company="B", status="Interview")
    filtered = client.get("/api/applications?status=Interview", headers=auth_header(student_token)).json()
    assert [a["company"] for a in filtered] == ["B"]


def test_delete(client, student_token):
    created = add(client, student_token)
    assert client.delete(f"/api/applications/{created['id']}", headers=auth_header(student_token)).status_code == 204
    assert client.get("/api/applications", headers=auth_header(student_token)).json() == []


def test_students_cannot_see_or_change_each_others_applications(client, student_token, other_student_token):
    created = add(client, student_token)
    other = auth_header(other_student_token)
    assert client.get("/api/applications", headers=other).json() == []
    assert client.get(f"/api/applications/{created['id']}", headers=other).status_code == 404
    assert client.put(f"/api/applications/{created['id']}", json=APP, headers=other).status_code == 404
    assert (
        client.patch(f"/api/applications/{created['id']}/status", json={"status": "Offer"}, headers=other).status_code
        == 404
    )
    assert client.delete(f"/api/applications/{created['id']}", headers=other).status_code == 404
    # The owner's record is unchanged
    mine = client.get(f"/api/applications/{created['id']}", headers=auth_header(student_token)).json()
    assert mine["status"] == "Applied"
