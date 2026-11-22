"""PB-23 start a mock interview, PB-24 submit answers, PB-25 review feedback."""
from tests.conftest import auth_header

GOOD_ANSWER = (
    "During my internship last summer, our team's dashboard took 12 seconds to load. I analyzed the slow SQL "
    "queries, I added two indexes and rewrote the heaviest report. As a result, load time dropped to 3 seconds, "
    "a 75% improvement, and the sales team started using it every morning. I learned to measure first."
)


def start(client, token, **overrides):
    body = {"role": "Software Engineering Intern", "focus": "Python, REST APIs, SQL", "question_count": 4}
    response = client.post("/api/interviews", json={**body, **overrides}, headers=auth_header(token))
    assert response.status_code == 201, response.text
    return response.json()


def test_start_creates_relevant_questions(client, student_token):
    session = start(client, student_token)
    assert len(session["questions"]) == 4
    assert "Software Engineering Intern" in session["questions"][0]
    assert any(skill in " ".join(session["questions"]) for skill in ("Python", "REST APIs", "SQL"))
    assert session["status"] == "active" and session["answered_count"] == 0


def test_answer_gets_explained_feedback(client, student_token):
    session = start(client, student_token)
    response = client.post(
        f"/api/interviews/{session['id']}/answers",
        json={"question_index": 1, "answer": GOOD_ANSWER},
        headers=auth_header(student_token),
    )
    assert response.status_code == 201, response.text
    feedback = response.json()["feedback"]
    assert feedback["rating"] in {"Strong", "Good"}
    assert feedback["strengths"] and all(point["why"] for point in feedback["strengths"])
    assert feedback["suggestion"]


def test_weak_answer_gets_specific_improvements(client, student_token):
    session = start(client, student_token)
    response = client.post(
        f"/api/interviews/{session['id']}/answers",
        json={"question_index": 0, "answer": "um we basically like, we kind of fixed it, you know, um"},
        headers=auth_header(student_token),
    )
    feedback = response.json()["feedback"]
    assert feedback["rating"] == "Needs work"
    points = {p["point"] for p in feedback["improvements"]}
    assert "Cut filler words" in points and "Say what you did" in points


def test_cannot_answer_twice_or_out_of_range(client, student_token):
    session = start(client, student_token)
    url = f"/api/interviews/{session['id']}/answers"
    assert client.post(url, json={"question_index": 0, "answer": GOOD_ANSWER},
                       headers=auth_header(student_token)).status_code == 201
    assert client.post(url, json={"question_index": 0, "answer": GOOD_ANSWER},
                       headers=auth_header(student_token)).status_code == 400
    assert client.post(url, json={"question_index": 9, "answer": GOOD_ANSWER},
                       headers=auth_header(student_token)).status_code == 400


def test_session_completes_after_last_answer_and_shows_in_history(client, student_token):
    session = start(client, student_token, question_count=3)
    for i in range(3):
        client.post(f"/api/interviews/{session['id']}/answers", json={"question_index": i, "answer": GOOD_ANSWER},
                    headers=auth_header(student_token))
    detail = client.get(f"/api/interviews/{session['id']}", headers=auth_header(student_token)).json()
    assert detail["status"] == "completed" and detail["answered_count"] == 3
    assert detail["average_score"] is not None
    history = client.get("/api/interviews", headers=auth_header(student_token)).json()
    assert history[0]["id"] == session["id"]
    # A finished session takes no more answers
    late = client.post(f"/api/interviews/{session['id']}/answers", json={"question_index": 0, "answer": "x"},
                       headers=auth_header(student_token))
    assert late.status_code == 400


def test_finish_early(client, student_token):
    session = start(client, student_token)
    assert client.post(f"/api/interviews/{session['id']}/finish",
                       headers=auth_header(student_token)).status_code == 400  # nothing answered yet
    client.post(f"/api/interviews/{session['id']}/answers", json={"question_index": 0, "answer": GOOD_ANSWER},
                headers=auth_header(student_token))
    finished = client.post(f"/api/interviews/{session['id']}/finish", headers=auth_header(student_token)).json()
    assert finished["status"] == "completed"


def test_sessions_are_private(client, student_token, other_student_token):
    session = start(client, student_token)
    other = auth_header(other_student_token)
    assert client.get(f"/api/interviews/{session['id']}", headers=other).status_code == 404
    assert client.post(f"/api/interviews/{session['id']}/answers", json={"question_index": 0, "answer": "hi there"},
                       headers=other).status_code == 404
