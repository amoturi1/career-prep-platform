"""E7 AI Career Preparation: PB-20 compare, PB-21 skill gaps, PB-22 explanations, PB-35 past results."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Role, User
from app.schemas import MatchIn, MatchOut, MatchSummary
from app.services import analysis

router = APIRouter(prefix="/api/match", tags=["AI career preparation"])
student_only = require_role(Role.student)
_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, detail="Result not found.")


@router.post("", response_model=MatchOut, status_code=status.HTTP_201_CREATED)
def compare(data: MatchIn, user: User = Depends(student_only), db: Session = Depends(get_db)):
    try:
        return analysis.run_match(db, user, data)
    except analysis.AnalysisInputError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=list[MatchSummary])
def past_results(user: User = Depends(student_only), db: Session = Depends(get_db)):
    return analysis.history(db, user)


@router.get("/{match_id}", response_model=MatchOut)
def view(match_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)):
    result = analysis.get_owned(db, user, match_id)
    if result is None:
        raise _NOT_FOUND
    return result


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(match_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)):
    result = analysis.get_owned(db, user, match_id)
    if result is None:
        raise _NOT_FOUND
    analysis.delete(db, result)
