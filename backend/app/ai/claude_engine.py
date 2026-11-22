"""Engine that uses the Anthropic Claude API (Messages API over HTTPS).

Enable it by putting ANTHROPIC_API_KEY=... in backend/.env. If a call fails or
returns something unusable, the built-in engine answers instead, so a short AI
outage never breaks the app (NFR-07). Results then say "local (fallback)".
"""
import json
import logging
import re

import httpx

from app.ai.base import AnswerFeedback, MatchAnalysis
from app.ai.local_engine import LocalEngine
from app.config import settings

log = logging.getLogger(__name__)

API_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = (
    "You are a careful career-preparation assistant inside a university platform. "
    "Your output is advisory: never promise hiring outcomes. Be specific, kind and concise. "
    "Always reply with a single JSON object and nothing else."
)


class AIServiceError(Exception):
    pass


def _extract_json(text: str):
    match = re.search(r"\{.*\}|\[.*\]", text, re.S)
    if not match:
        raise AIServiceError("No JSON in response")
    return json.loads(match.group(0))


class ClaudeEngine:
    name = "claude"

    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.fallback = LocalEngine()

    def _ask(self, prompt: str, max_tokens: int = 1500):
        try:
            response = httpx.post(
                API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            text = "".join(block.get("text", "") for block in response.json().get("content", []))
            return _extract_json(text)
        except (httpx.HTTPError, ValueError, KeyError, AIServiceError) as exc:
            log.warning("Claude API call failed, using the built-in engine instead: %s", exc)
            raise AIServiceError(str(exc)) from exc

    @staticmethod
    def _fallback_tag(result: dict) -> dict:
        result["engine"] = "local (fallback)"
        return result

    # ------------------------------------------------------------ resume vs job

    def analyze_match(self, resume_text: str, job_text: str, profile_skills: str = "") -> MatchAnalysis:
        baseline = self.fallback.analyze_match(resume_text, job_text, profile_skills)
        prompt = f"""Compare this student's resume with the job description.

Return JSON with exactly these keys:
- "score": integer 0-100 for how well the resume matches the job
- "summary": one or two sentences
- "matched": list of {{"skill", "category", "requirement", "evidence"}} where "requirement" quotes the job line and "evidence" quotes the resume line that shows the skill
- "missing": list of {{"skill", "category", "priority", "requirement", "suggestion"}} with priority "high" (required), "medium" or "low" (nice to have) and a concrete learning suggestion
- "under_evidenced": same shape as "missing", for skills listed in the student's profile skills but not shown in the resume
- "suggestions": list of 2-5 specific resume improvements, each tied to something in the resume or job
- "limitations": list of short caveats about what this analysis cannot know

Profile skills: {profile_skills or "(none given)"}

RESUME:
{resume_text[:12000]}

JOB DESCRIPTION:
{job_text[:8000]}"""
        try:
            data = self._ask(prompt, max_tokens=2500)
            result = MatchAnalysis(
                score=max(0, min(100, int(data["score"]))),
                summary=str(data.get("summary") or baseline["summary"]),
                matched=list(data.get("matched") or []),
                missing=list(data.get("missing") or []),
                under_evidenced=list(data.get("under_evidenced") or []),
                suggestions=[str(s) for s in data.get("suggestions") or baseline["suggestions"]],
                limitations=[str(s) for s in data.get("limitations") or baseline["limitations"]],
                engine=f"claude ({self.model})",
            )
            return result
        except (AIServiceError, TypeError, ValueError, KeyError):
            return self._fallback_tag(baseline)

    # ------------------------------------------------------------ interviews

    def generate_questions(self, role: str, focus: str = "", count: int = 5) -> list[str]:
        prompt = f"""Write {count} mock interview questions for a student applying for: {role}.
Mix behavioral and role-specific technical questions, start with an introduction question and end with a closing one.
Context (topic or job description): {focus[:6000] or "(none)"}
Return JSON: {{"questions": ["...", "..."]}}"""
        try:
            data = self._ask(prompt, max_tokens=1200)
            questions = [str(q).strip() for q in data["questions"] if str(q).strip()]
            if len(questions) < 2:
                raise AIServiceError("Too few questions")
            return questions[:count]
        except (AIServiceError, TypeError, KeyError):
            return self.fallback.generate_questions(role, focus, count)

    def evaluate_answer(self, question: str, answer: str, role: str = "") -> AnswerFeedback:
        baseline = self.fallback.evaluate_answer(question, answer, role)
        if baseline["word_count"] < 8:
            return baseline  # nothing for the model to evaluate
        prompt = f"""Evaluate this mock-interview answer for a {role or "student"} candidate.

QUESTION: {question}
ANSWER: {answer[:6000]}

Return JSON with:
- "score": integer 1-5
- "rating": "Strong" (4-5), "Good" (3) or "Needs work" (1-2)
- "strengths": list of {{"point", "why"}} where "why" points to the specific part of the answer
- "improvements": list of {{"point", "why"}} where "why" explains what in the answer led to it
- "suggestion": one actionable sentence for next time"""
        try:
            data = self._ask(prompt, max_tokens=1200)
            score = max(1, min(5, int(data["score"])))
            return AnswerFeedback(
                rating=str(data.get("rating") or ("Strong" if score >= 4 else "Good" if score == 3 else "Needs work")),
                score=score,
                strengths=list(data.get("strengths") or []),
                improvements=list(data.get("improvements") or []),
                suggestion=str(data.get("suggestion") or baseline["suggestion"]),
                word_count=baseline["word_count"],
                engine=f"claude ({self.model})",
            )
        except (AIServiceError, TypeError, ValueError, KeyError):
            return self._fallback_tag(baseline)
