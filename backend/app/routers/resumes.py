"""E6 Resume Management: PB-18 add a resume, PB-19 replace it (versions, one current)."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import require_role
from app.models import Resume, Role, User
from app.schemas import ResumeDetail, ResumeOut, ResumeTextIn
from app.services import resumes
from app.services.resume_parser import ResumeFileError, clean_text, extract_text

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])
student_only = require_role(Role.student)
_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, detail="Resume not found.")


def _out(resume: Resume, with_text: bool = False):
    data = {
        "id": resume.id,
        "filename": resume.filename,
        "source": resume.source,
        "is_current": resume.is_current,
        "uploaded_at": resume.uploaded_at,
        "word_count": resumes.word_count(resume),
    }
    return ResumeDetail(**data, text=resume.text) if with_text else ResumeOut(**data)


@router.get("", response_model=list[ResumeOut])
def list_versions(user: User = Depends(student_only), db: Session = Depends(get_db)):
    return [_out(r) for r in resumes.list_versions(db, user)]


@router.get("/current", response_model=ResumeDetail)
def current(user: User = Depends(student_only), db: Session = Depends(get_db)):
    resume = resumes.current(db, user.id)
    if resume is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="You haven't added a resume yet.")
    return _out(resume, with_text=True)


@router.get("/{resume_id}", response_model=ResumeDetail)
def view(resume_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)):
    resume = resumes.get_owned(db, user, resume_id)
    if resume is None:
        raise _NOT_FOUND
    return _out(resume, with_text=True)


@router.post("/upload", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
def upload(file: UploadFile = File(...), user: User = Depends(student_only), db: Session = Depends(get_db)):
    data = file.file.read(settings.max_resume_bytes + 1)
    try:
        kind, text = extract_text(file.filename or "", data, settings.max_resume_bytes, settings.max_resume_chars)
    except ResumeFileError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _out(resumes.add_version(db, user, file.filename or f"resume.{kind}", kind, text), with_text=True)


@router.post("/text", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
def add_text(data: ResumeTextIn, user: User = Depends(student_only), db: Session = Depends(get_db)):
    text = clean_text(data.text)
    return _out(resumes.add_version(db, user, data.label or "Pasted resume", "pasted", text), with_text=True)


@router.post("/{resume_id}/make-current", response_model=ResumeOut)
def make_current(resume_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)):
    resume = resumes.get_owned(db, user, resume_id)
    if resume is None:
        raise _NOT_FOUND
    return _out(resumes.make_current(db, user, resume))


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(resume_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)):
    resume = resumes.get_owned(db, user, resume_id)
    if resume is None:
        raise _NOT_FOUND
    resumes.delete(db, user, resume)
