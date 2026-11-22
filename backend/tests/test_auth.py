"""PB-01 register, PB-02 sign in, PB-03 validation, PB-11 sign out."""
from tests.conftest import PASSWORD, auth_header, register


def test_register_creates_student_and_returns_token(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Ana Lee", "email": "Ana@UNCC.edu", "password": PASSWORD},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["user"]["role"] == "student"
    assert body["user"]["email"] == "ana@uncc.edu"  # stored lowercase


def test_register_rejects_duplicate_email_case_insensitive(client):
    register(client, email="dup@uncc.edu")
    response = client.post(
        "/api/auth/register", json={"full_name": "X", "email": "DUP@uncc.edu", "password": PASSWORD}
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_register_cannot_choose_admin_role(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Sneaky", "email": "s@uncc.edu", "password": PASSWORD, "role": "admin"},
    )
    assert response.status_code == 422


def test_register_validation_messages_name_each_field(client):
    response = client.post("/api/auth/register", json={"full_name": "", "email": "not-an-email", "password": "short"})
    assert response.status_code == 422
    errors = {e["field"]: e["message"] for e in response.json()["errors"]}
    assert errors["full_name"] == "This field is required."
    assert errors["email"] == "Enter a valid email address."
    assert "8" in errors["password"]


def test_password_needs_letter_and_number(client):
    response = client.post(
        "/api/auth/register", json={"full_name": "A", "email": "a@uncc.edu", "password": "abcdefghij"}
    )
    assert response.status_code == 422
    assert "letter and one number" in response.json()["errors"][0]["message"]


def test_login_success_and_me(client):
    register(client, email="me@uncc.edu")
    response = client.post("/api/auth/login", json={"email": "me@uncc.edu", "password": PASSWORD})
    assert response.status_code == 200
    token = response.json()["access_token"]
    me = client.get("/api/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    assert me.json()["email"] == "me@uncc.edu"


def test_login_wrong_password_and_unknown_email_give_same_error(client):
    register(client, email="me@uncc.edu")
    wrong = client.post("/api/auth/login", json={"email": "me@uncc.edu", "password": "Wrong12345"})
    unknown = client.post("/api/auth/login", json={"email": "nobody@uncc.edu", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


def test_protected_route_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=auth_header("garbage")).status_code == 401


def test_logout_revokes_token(client, student_token):
    assert client.post("/api/auth/logout", headers=auth_header(student_token)).status_code == 204
    assert client.get("/api/auth/me", headers=auth_header(student_token)).status_code == 401
