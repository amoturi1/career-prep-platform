"""E8 Mock Interviews: PB-23 start, PB-24 submit an answer, PB-25 review feedback."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Role, User
from app.schemas import AnswerIn, AnswerOut, InterviewOut, InterviewStart, InterviewSummary
from app.services import interviews

router = APIRouter(prefix="/api/interviews", tags=["Mock interviews"])
student_only = require_role(Role.student)
_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, detail="Practice session not found.")


@router.post("", response_model=InterviewOut, status_code=status.HTTP_201_CREATED)
def start(data: InterviewStart, user: User = Depends(student_only), db: Session = Depends(get_db)):
    try:
        session = interviews.start(db, user, data)
    except interviews.InterviewError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return interviews.detail(session)


@router.get("", response_model=list[InterviewSummary])
def history(user: User = Depends(student_only), db: Session = Depends(get_db)):
    return [interviews.summarize(s) for s in interviews.list_for_student(db, user)]


@router.get("/{session_id}", response_model=InterviewOut)
def view(session_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)):
    session = interviews.get_owned(db, user, session_id)
    if session is None:
        raise _NOT_FOUND
    return interviews.detail(session)


@router.post("/{session_id}/answers", response_model=AnswerOut, status_code=status.HTTP_201_CREATED)
def answer(session_id: int, data: AnswerIn, user: User = Depends(student_only), db: Session = Depends(get_db)):
    session = interviews.get_owned(db, user, session_id)
    if session is None:
        raise _NOT_FOUND
    try:
        return interviews.submit_answer(db, session, data.question_index, data.answer)
    except interviews.InterviewError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{session_id}/finish", response_model=InterviewOut)
def finish(session_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)):
    session = interviews.get_owned(db, user, session_id)
    if session is None:
        raise _NOT_FOUND
    try:
        return interviews.detail(interviews.finish(db, session))
    except interviews.InterviewError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
