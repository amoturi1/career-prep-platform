"""The interface every AI engine implements, and the shapes of its results.

Results are plain dicts so they can be stored as JSON and sent to the browser
as-is. Every result says which engine produced it, and is advisory only (NFR-08).
"""
from typing import Protocol, TypedDict


class MatchedSkill(TypedDict):
    skill: str
    category: str
    requirement: str  # the job-description line asking for it
    evidence: str  # the resume line that shows it


class SkillGap(TypedDict):
    skill: str
    category: str
    priority: str  # "high" (required) | "medium" | "low" (nice to have)
    requirement: str
    suggestion: str


class MatchAnalysis(TypedDict):
    score: int  # 0-100
    summary: str
    matched: list[MatchedSkill]
    missing: list[SkillGap]
    under_evidenced: list[SkillGap]  # on the profile but not shown in the resume
    suggestions: list[str]
    limitations: list[str]
    engine: str


class FeedbackPoint(TypedDict):
    point: str
    why: str  # what in the answer led to this (NFR-09)


class AnswerFeedback(TypedDict):
    rating: str  # "Strong" | "Good" | "Needs work"
    score: int  # 1-5
    strengths: list[FeedbackPoint]
    improvements: list[FeedbackPoint]
    suggestion: str
    word_count: int
    engine: str


class CareerAI(Protocol):
    name: str

    def analyze_match(self, resume_text: str, job_text: str, profile_skills: str = "") -> MatchAnalysis: ...

    def generate_questions(self, role: str, focus: str = "", count: int = 5) -> list[str]: ...

    def evaluate_answer(self, question: str, answer: str, role: str = "") -> AnswerFeedback: ...


DISCLAIMER = (
    "AI suggestions are advisory. They can miss context, so check them against your own judgment "
    "and your mentor's advice. They do not predict hiring outcomes."
)
