"""PB-04 create, PB-05 edit, PB-06 view."""
from tests.conftest import auth_header

PROFILE = {
    "education": "B.S. Computer Science, UNC Charlotte (2027)",
    "skills": "Python, React, SQL",
    "experience": "TA for ITSC 1212",
    "interests": "Backend development",
    "target_role": "Software Engineering Intern",
}


def test_view_before_create_is_404(client, student_token):
    response = client.get("/api/profile", headers=auth_header(student_token))
    assert response.status_code == 404


def test_create_then_view_profile(client, student_token):
    created = client.post("/api/profile", json=PROFILE, headers=auth_header(student_token))
    assert created.status_code == 201
    viewed = client.get("/api/profile", headers=auth_header(student_token))
    assert viewed.status_code == 200
    assert viewed.json()["skills"] == "Python, React, SQL"


def test_cannot_create_profile_twice(client, student_token):
    client.post("/api/profile", json=PROFILE, headers=auth_header(student_token))
    again = client.post("/api/profile", json=PROFILE, headers=auth_header(student_token))
    assert again.status_code == 409


def test_create_profile_requires_core_fields(client, student_token):
    response = client.post("/api/profile", json={**PROFILE, "skills": "  "}, headers=auth_header(student_token))
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "skills"
    # Nothing was saved
    assert client.get("/api/profile", headers=auth_header(student_token)).status_code == 404


def test_edit_profile(client, student_token):
    client.post("/api/profile", json=PROFILE, headers=auth_header(student_token))
    edited = client.put(
        "/api/profile", json={**PROFILE, "target_role": "Data Analyst Intern"}, headers=auth_header(student_token)
    )
    assert edited.status_code == 200
    assert edited.json()["target_role"] == "Data Analyst Intern"


def test_profiles_are_private_to_each_student(client, student_token, other_student_token):
    client.post("/api/profile", json=PROFILE, headers=auth_header(student_token))
    assert client.get("/api/profile", headers=auth_header(other_student_token)).status_code == 404


def test_admin_cannot_use_student_profile_routes(client, admin_token):
    assert client.get("/api/profile", headers=auth_header(admin_token)).status_code == 403
