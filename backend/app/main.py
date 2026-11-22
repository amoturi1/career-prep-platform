"""FastAPI entry point. Run with:  uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import admin, analysis, applications, auth, interviews, mentorship, opportunities, profiles, resumes


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI Career & Internship Prep Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _friendly_message(error: dict) -> str:
    message = error.get("msg", "Invalid value")
    message = message.removeprefix("Value error, ")
    if error.get("type") == "missing":
        return "This field is required."
    if error.get("type") == "extra_forbidden":
        return "This field is not allowed."
    if "valid email" in message:
        return "Enter a valid email address."
    if error.get("type") == "string_too_short" and error.get("ctx", {}).get("min_length") == 1:
        return "This field is required."
    return message[0].upper() + message[1:] if message else "Invalid value."


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    """Turn validation failures into a clear list of field -> message (PB-03, NFR-04)."""
    errors = []
    for err in exc.errors():
        location = [str(part) for part in err.get("loc", []) if part not in ("body", "query", "path")]
        errors.append({"field": ".".join(location) or "request", "message": _friendly_message(err)})
    return JSONResponse(
        status_code=422,
        content={"detail": "Please correct the highlighted fields.", "errors": errors},
    )


@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(applications.router)
app.include_router(opportunities.router)
app.include_router(resumes.router)
app.include_router(analysis.router)
app.include_router(interviews.router)
app.include_router(mentorship.student_router)
app.include_router(mentorship.mentor_router)
app.include_router(admin.router)
