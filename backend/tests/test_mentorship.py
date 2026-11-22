"""PB-26 request, PB-27 manage, PB-28 feedback, PB-29 progress, PB-31 availability, PB-32 booking, PB-33 status."""
from datetime import datetime, timedelta

from tests.conftest import RESUME_TEXT, auth_header


def future(days=2, hour=15):
    return (datetime.now() + timedelta(days=days)).replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


def request_help(client, token, **overrides):
    body = {"request_type": "resume_review", "message": "Could you review my resume for internships?",
            "share_profile": True, "share_resume": True, "share_progress": True}
    response = client.post("/api/mentoring/requests", json={**body, **overrides}, headers=auth_header(token))
    assert response.status_code == 201, response.text
    return response.json()


def setup_student_materials(client, token):
    client.post("/api/profile", json={"education": "BS CS", "skills": "Python", "target_role": "SWE Intern"},
                headers=auth_header(token))
    client.post("/api/resumes/text", json={"text": RESUME_TEXT}, headers=auth_header(token))
    client.post("/api/applications", json={"company": "Acme", "job_title": "Intern", "status": "Applied",
                                           "notes": "private note"}, headers=auth_header(token))


# ------------------------------------------------------------------ availability and booking

def test_mentor_sets_availability_and_student_books(client, mentor_token, student_token, other_student_token):
    slot = client.post("/api/mentor/slots", json={"start_at": future(), "duration_minutes": 30},
                       headers=auth_header(mentor_token))
    assert slot.status_code == 201, slot.text
    slots = client.get("/api/mentoring/slots", headers=auth_header(student_token)).json()
    assert [s["id"] for s in slots] == [slot.json()["id"]]
    assert slots[0]["mentor"]["full_name"] == "Jordan Mentor"

    booking = request_help(client, student_token, slot_id=slot.json()["id"], request_type="interview_practice")
    assert booking["status"] == "accepted" and booking["mentor"]["full_name"] == "Jordan Mentor"
    # The slot is no longer offered, and nobody else can take it
    assert client.get("/api/mentoring/slots", headers=auth_header(other_student_token)).json() == []
    taken = client.post("/api/mentoring/requests",
                        json={"request_type": "career_guidance", "message": "Can I have this time too?",
                              "slot_id": slot.json()["id"]}, headers=auth_header(other_student_token))
    assert taken.status_code == 400


def test_slot_rules(client, mentor_token, student_token):
    past = (datetime.now() - timedelta(days=1)).isoformat()
    assert client.post("/api/mentor/slots", json={"start_at": past}, headers=auth_header(mentor_token)).status_code == 422
    first = client.post("/api/mentor/slots", json={"start_at": future(), "duration_minutes": 60},
                        headers=auth_header(mentor_token)).json()
    overlap = client.post("/api/mentor/slots", json={"start_at": future(), "duration_minutes": 30},
                          headers=auth_header(mentor_token))
    assert overlap.status_code == 400
    # Students can't add availability
    assert client.post("/api/mentor/slots", json={"start_at": future(days=4)},
                       headers=auth_header(student_token)).status_code == 403
    # A free slot can be removed
    assert client.delete(f"/api/mentor/slots/{first['id']}", headers=auth_header(mentor_token)).status_code == 204


def test_cancelling_a_booking_frees_the_slot(client, mentor_token, student_token):
    slot = client.post("/api/mentor/slots", json={"start_at": future()}, headers=auth_header(mentor_token)).json()
    booking = request_help(client, student_token, slot_id=slot["id"])
    cancelled = client.post(f"/api/mentoring/requests/{booking['id']}/cancel", headers=auth_header(student_token))
    assert cancelled.json()["status"] == "cancelled"
    assert len(client.get("/api/mentoring/slots", headers=auth_header(student_token)).json()) == 1


# ------------------------------------------------------------------ request workflow and consent

def test_open_request_hides_materials_until_accepted(client, mentor_token, student_token):
    setup_student_materials(client, student_token)
    request = request_help(client, student_token)
    assert request["status"] == "pending" and request["mentor"] is None

    queue = client.get("/api/mentor/requests?scope=open", headers=auth_header(mentor_token)).json()
    assert [r["id"] for r in queue] == [request["id"]]
    before = client.get(f"/api/mentor/requests/{request['id']}", headers=auth_header(mentor_token)).json()
    assert before["materials"]["access"] is False and before["materials"]["resume"] is None

    accepted = client.post(f"/api/mentor/requests/{request['id']}/accept", headers=auth_header(mentor_token))
    assert accepted.json()["status"] == "accepted"
    after = client.get(f"/api/mentor/requests/{request['id']}", headers=auth_header(mentor_token)).json()
    materials = after["materials"]
    assert materials["access"] is True
    assert "FastAPI" in materials["resume"]["text"]
    assert materials["profile"]["target_role"] == "SWE Intern"
    assert materials["progress"]["applications_total"] == 1
    assert "private note" not in str(materials)  # application notes are never shared


def test_only_shared_items_are_visible(client, mentor_token, student_token):
    setup_student_materials(client, student_token)
    request = request_help(client, student_token, share_resume=False, share_progress=False)
    client.post(f"/api/mentor/requests/{request['id']}/accept", headers=auth_header(mentor_token))
    materials = client.get(f"/api/mentor/requests/{request['id']}", headers=auth_header(mentor_token)).json()["materials"]
    assert materials["profile"] is not None
    assert materials["resume"] is None and materials["progress"] is None


def test_other_mentors_cannot_see_a_taken_request(client, mentor_token, other_mentor_token, student_token):
    request = request_help(client, student_token)
    client.post(f"/api/mentor/requests/{request['id']}/accept", headers=auth_header(mentor_token))
    other = auth_header(other_mentor_token)
    assert client.get(f"/api/mentor/requests/{request['id']}", headers=other).status_code == 404
    assert client.post(f"/api/mentor/requests/{request['id']}/accept", headers=other).status_code == 404
    assert client.get("/api/mentor/requests", headers=other).json() == []


def test_status_flow_feedback_and_student_view(client, mentor_token, student_token):
    request = request_help(client, student_token)
    rid = request["id"]
    mentor = auth_header(mentor_token)
    # Feedback before accepting is refused
    assert client.post(f"/api/mentor/requests/{rid}/feedback", json={"body": "Looks good overall."},
                       headers=mentor).status_code == 400
    client.post(f"/api/mentor/requests/{rid}/accept", headers=mentor)
    feedback = client.post(f"/api/mentor/requests/{rid}/feedback",
                           json={"body": "Lead with your FastAPI project and add numbers."}, headers=mentor)
    assert feedback.status_code == 201
    # Feedback moves an accepted request to in progress; then it can be completed
    done = client.patch(f"/api/mentor/requests/{rid}/status", json={"status": "completed"}, headers=mentor)
    assert done.json()["status"] == "completed"
    # Completed requests can't go backwards
    back = client.patch(f"/api/mentor/requests/{rid}/status", json={"status": "in_progress"}, headers=mentor)
    assert back.status_code == 400
    # PB-33: the student sees the status and the feedback
    mine = client.get("/api/mentoring/requests", headers=auth_header(student_token)).json()
    assert mine[0]["status"] == "completed"
    assert mine[0]["feedback"][0]["body"].startswith("Lead with your FastAPI project")


def test_decline_and_student_privacy(client, mentor_token, student_token, other_student_token):
    request = request_help(client, student_token)
    mentor = auth_header(mentor_token)
    # Can't decline an open request that isn't assigned to you
    assert client.post(f"/api/mentor/requests/{request['id']}/decline", headers=mentor).status_code == 400
    client.post(f"/api/mentor/requests/{request['id']}/accept", headers=mentor)
    assert client.post(f"/api/mentor/requests/{request['id']}/decline", headers=mentor).json()["status"] == "declined"
    # Another student sees none of this
    assert client.get("/api/mentoring/requests", headers=auth_header(other_student_token)).json() == []
    assert client.post(f"/api/mentoring/requests/{request['id']}/cancel",
                       headers=auth_header(other_student_token)).status_code == 404


def test_request_validation(client, student_token):
    response = client.post("/api/mentoring/requests", json={"request_type": "homework", "message": "short"},
                           headers=auth_header(student_token))
    assert response.status_code == 422
    assert {e["field"] for e in response.json()["errors"]} == {"request_type", "message"}


# ------------------------------------------------------------------ progress (PB-29)

def test_progress_only_for_supported_students_who_shared_it(client, mentor_token, student_token, other_student_token):
    setup_student_materials(client, student_token)
    setup_student_materials(client, other_student_token)
    shared = request_help(client, student_token)
    private = request_help(client, other_student_token, share_progress=False)
    request_help(client, other_student_token)  # still pending: not a supported student yet
    mentor = auth_header(mentor_token)
    client.post(f"/api/mentor/requests/{shared['id']}/accept", headers=mentor)
    client.post(f"/api/mentor/requests/{private['id']}/accept", headers=mentor)

    students = {s["student"]["full_name"]: s for s in client.get("/api/mentor/students", headers=mentor).json()}
    assert set(students) == {"Test Student", "Other Student"}
    assert students["Test Student"]["progress"]["has_resume"] is True
    assert students["Other Student"]["progress"] is None  # didn't share progress
