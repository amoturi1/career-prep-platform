"""PB-20 compare, PB-21 skill gaps, PB-22 explanations, PB-35 past results."""
from tests.conftest import JOB_TEXT, RESUME_TEXT, auth_header


def add_resume(client, token, text=RESUME_TEXT):
    response = client.post("/api/resumes/text", json={"text": text}, headers=auth_header(token))
    assert response.status_code == 201
    return response.json()


def test_requires_a_resume_first(client, student_token):
    response = client.post("/api/match", json={"job_description": JOB_TEXT}, headers=auth_header(student_token))
    assert response.status_code == 400
    assert "resume" in response.json()["detail"].lower()


def test_requires_job_text_or_listing(client, student_token):
    add_resume(client, student_token)
    response = client.post("/api/match", json={"job_description": "short"}, headers=auth_header(student_token))
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "job_description"


def test_comparison_explains_matches_and_gaps(client, student_token):
    add_resume(client, student_token)
    client.post(
        "/api/profile",
        json={"education": "BS CS", "skills": "Python, Docker", "target_role": "SWE Intern"},
        headers=auth_header(student_token),
    )
    response = client.post(
        "/api/match",
        json={"job_description": JOB_TEXT, "job_title": "SWE Intern", "company": "Northstar"},
        headers=auth_header(student_token),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    result = body["result"]
    assert 0 <= body["score"] <= 100 and body["score"] == result["score"]
    matched = {m["skill"]: m for m in result["matched"]}
    assert {"Python", "SQL", "REST APIs"} <= set(matched)
    # PB-22: each match points to the job line and the resume evidence behind it
    assert "Python" in matched["Python"]["requirement"] and "Python" in matched["Python"]["evidence"]
    # "Python or Java": having Python covers it, so Java is not reported as a gap
    assert "Java" not in {g["skill"] for g in result["missing"]}
    # PB-21: Docker is on the profile but not the resume -> under-evidenced, not missing
    assert [g["skill"] for g in result["under_evidenced"]] == ["Docker"]
    assert "AWS" in {g["skill"] for g in result["missing"]}
    assert result["disclaimer"] and result["limitations"]
    assert body["engine"] == "local"


def test_compare_with_published_listing(client, admin_token, student_token):
    add_resume(client, student_token)
    listing = client.post(
        "/api/opportunities",
        json={"title": "Backend Intern", "organization": "Acme", "description": JOB_TEXT},
        headers=auth_header(admin_token),
    ).json()
    response = client.post("/api/match", json={"opportunity_id": listing["id"]}, headers=auth_header(student_token))
    assert response.status_code == 201
    assert response.json()["job_title"] == "Backend Intern" and response.json()["company"] == "Acme"


def test_history_is_saved_and_private(client, student_token, other_student_token):
    add_resume(client, student_token)
    for title in ["First", "Second"]:
        client.post("/api/match", json={"job_description": JOB_TEXT, "job_title": title},
                    headers=auth_header(student_token))
    history = client.get("/api/match", headers=auth_header(student_token)).json()
    assert [h["job_title"] for h in history] == ["Second", "First"]
    match_id = history[0]["id"]
    assert client.get(f"/api/match/{match_id}", headers=auth_header(student_token)).status_code == 200
    assert client.get("/api/match", headers=auth_header(other_student_token)).json() == []
    assert client.get(f"/api/match/{match_id}", headers=auth_header(other_student_token)).status_code == 404


def test_mentors_and_admins_cannot_run_student_analysis(client, mentor_token, admin_token):
    for token in (mentor_token, admin_token):
        response = client.post("/api/match", json={"job_description": JOB_TEXT}, headers=auth_header(token))
        assert response.status_code == 403
