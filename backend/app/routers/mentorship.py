"""E9 Human Mentorship.

Student side (/api/mentoring): PB-26 request support, PB-32 book a session, PB-33 view status and feedback.
Mentor side (/api/mentor):    PB-27 manage requests, PB-28 review shared materials and give feedback,
                              PB-29 monitor supported students, PB-31 set availability.
"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Role, User
from app.schemas import (
    FeedbackIn,
    FeedbackOut,
    MentorRequestIn,
    MentorRequestOut,
    RequestStatusUpdate,
    SlotIn,
    SlotOut,
)
from app.services import mentorship as svc

student_router = APIRouter(prefix="/api/mentoring", tags=["Mentorship (students)"])
mentor_router = APIRouter(prefix="/api/mentor", tags=["Mentorship (mentors)"])
student_only = require_role(Role.student)
mentor_only = require_role(Role.mentor)

_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, detail="Request not found.")


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ------------------------------------------------------------------ students

@student_router.get("/slots", response_model=list[SlotOut])
def available_slots(user: User = Depends(student_only), db: Session = Depends(get_db)):
    return svc.available_slots(db)


@student_router.post("/requests", response_model=MentorRequestOut, status_code=status.HTTP_201_CREATED)
def request_support(data: MentorRequestIn, user: User = Depends(student_only), db: Session = Depends(get_db)):
    try:
        return svc.create_request(db, user, data)
    except svc.MentorshipError as exc:
        raise _bad_request(exc)


@student_router.get("/requests", response_model=list[MentorRequestOut])
def my_requests(user: User = Depends(student_only), db: Session = Depends(get_db)):
    return svc.student_requests(db, user)


@student_router.post("/requests/{request_id}/cancel", response_model=MentorRequestOut)
def cancel_request(request_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)):
    try:
        return svc.cancel(db, user, request_id)
    except svc.NotFound:
        raise _NOT_FOUND
    except svc.MentorshipError as exc:
        raise _bad_request(exc)


# ------------------------------------------------------------------ mentors

@mentor_router.get("/requests", response_model=list[MentorRequestOut])
def request_queue(
    scope: Literal["all", "open", "mine"] = "all",
    user: User = Depends(mentor_only),
    db: Session = Depends(get_db),
):
    return svc.mentor_queue(db, user, scope)


@mentor_router.get("/requests/{request_id}")
def request_detail(request_id: int, user: User = Depends(mentor_only), db: Session = Depends(get_db)):
    try:
        request = svc.visible_to_mentor(db, user, request_id)
    except svc.NotFound:
        raise _NOT_FOUND
    return {
        "request": MentorRequestOut.model_validate(request),
        "materials": svc.shared_materials(db, user, request),
    }


def _mentor_action(action, *args):
    try:
        return action(*args)
    except svc.NotFound:
        raise _NOT_FOUND
    except svc.MentorshipError as exc:
        raise _bad_request(exc)


@mentor_router.post("/requests/{request_id}/accept", response_model=MentorRequestOut)
def accept_request(request_id: int, user: User = Depends(mentor_only), db: Session = Depends(get_db)):
    return _mentor_action(svc.accept, db, user, request_id)


@mentor_router.post("/requests/{request_id}/decline", response_model=MentorRequestOut)
def decline_request(request_id: int, user: User = Depends(mentor_only), db: Session = Depends(get_db)):
    return _mentor_action(svc.decline, db, user, request_id)


@mentor_router.patch("/requests/{request_id}/status", response_model=MentorRequestOut)
def update_request_status(
    request_id: int, data: RequestStatusUpdate, user: User = Depends(mentor_only), db: Session = Depends(get_db)
):
    return _mentor_action(svc.set_status, db, user, request_id, data.status)


@mentor_router.post("/requests/{request_id}/feedback", response_model=FeedbackOut, status_code=201)
def give_feedback(request_id: int, data: FeedbackIn, user: User = Depends(mentor_only), db: Session = Depends(get_db)):
    return _mentor_action(svc.add_feedback, db, user, request_id, data.body)


@mentor_router.get("/slots", response_model=list[SlotOut])
def my_slots(user: User = Depends(mentor_only), db: Session = Depends(get_db)):
    return svc.mentor_slots(db, user)


@mentor_router.post("/slots", response_model=SlotOut, status_code=status.HTTP_201_CREATED)
def add_slot(data: SlotIn, user: User = Depends(mentor_only), db: Session = Depends(get_db)):
    try:
        return svc.add_slot(db, user, data.start_at, data.duration_minutes)
    except svc.MentorshipError as exc:
        raise _bad_request(exc)


@mentor_router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_slot(slot_id: int, user: User = Depends(mentor_only), db: Session = Depends(get_db)):
    try:
        svc.remove_slot(db, user, slot_id)
    except svc.NotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Slot not found.")
    except svc.MentorshipError as exc:
        raise _bad_request(exc)


@mentor_router.get("/students")
def supported_students(user: User = Depends(mentor_only), db: Session = Depends(get_db)):
    return svc.supported_students(db, user)
