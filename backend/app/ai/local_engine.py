"""Built-in, rule-based engine. Works offline, gives the same output for the same input,
and explains every suggestion by pointing at the text behind it (NFR-09, NFR-11).
"""
import random
import re

from app.ai.base import AnswerFeedback, FeedbackPoint, MatchAnalysis, SkillGap
from app.ai.skills import SOFT, find_skills, learning_suggestion, parse_skill_list, skill_category

_PRIORITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

_LOW_CUES = re.compile(r"\b(prefer|preferred|nice to have|bonus|a plus|plus|desired|familiarity|exposure|optional)\b", re.I)
_HIGH_CUES = re.compile(r"\b(require|required|requirements|must|minimum|qualifications|essential|need|needs)\b", re.I)

_STOPWORDS = set(
    """about above after again against all also although among another any are around because been before being
    below between both but can could did does doing done down during each either else ever every few for from
    further had has have having here how however into its itself just least less like make many may might more
    most much must near need needs never next none nor not now off often once only other others our ours out over
    own per perhaps please rather really same several shall should since some such than that the their theirs them
    then there these they this those though through thus too toward under until upon very via was were what when
    where whether which while who whom whose why will with within without would your yours you we our team role
    work working ability able strong good great excellent including include includes experience years year
    candidate candidates position job opportunity responsibilities responsible looking join company students
    student skills skill knowledge understanding plus preferred required requirements qualifications using use
    well new etc""".split()
)


def _keywords(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z+#.]{3,}", (text or "").lower()) if w not in _STOPWORDS}


def _clip(text: str, limit: int = 180) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _job_requirements(job_text: str) -> dict[str, tuple[str, str]]:
    """Map each skill the job description mentions to (the line, its priority).

    A line's priority comes from its own wording ("required", "nice to have"),
    or else from the section heading above it.
    """
    requirements: dict[str, tuple[str, str]] = {}
    section = "medium"
    for raw in (job_text or "").splitlines():
        line = raw.strip(" \t-•*·")
        if not line:
            continue
        is_heading = len(line) <= 60 and (line.endswith(":") or not re.search(r"[.,;]", line)) and not find_skills(line)
        if is_heading:
            if _LOW_CUES.search(line):
                section = "low"
            elif _HIGH_CUES.search(line):
                section = "high"
            else:
                section = "medium"
            continue
        priority = "low" if _LOW_CUES.search(line) else "high" if _HIGH_CUES.search(line) else section
        for skill in find_skills(line):
            current = requirements.get(skill)
            if current is None or _PRIORITY_ORDER[priority] < _PRIORITY_ORDER[current[1]]:
                requirements[skill] = (_clip(line), priority)
    return requirements


def _alternative_groups(job_text: str) -> list[set[str]]:
    """Skills offered as alternatives ("Python or Java"): having any one of them is enough."""
    groups: list[set[str]] = []
    for raw in (job_text or "").splitlines():
        for clause in re.split(r"[;.]|\band\b", raw):
            if not re.search(r"\bor\b|/", clause):
                continue
            skills = set(find_skills(clause))
            if len(skills) >= 2:
                groups.append(skills)
    return groups


class LocalEngine:
    name = "local"

    # ------------------------------------------------------------ resume vs job (PB-20, PB-21, PB-22)

    def analyze_match(self, resume_text: str, job_text: str, profile_skills: str = "") -> MatchAnalysis:
        requirements = _job_requirements(job_text)
        resume_skills = find_skills(resume_text)
        profile_list = set(parse_skill_list(profile_skills))

        # In "Python or Java", a resume with either one covers the requirement; the other
        # alternatives are then left out instead of being reported as gaps.
        covered_alternatives: set[str] = set()
        for group in _alternative_groups(job_text):
            if group & set(resume_skills):
                covered_alternatives |= group - set(resume_skills)

        matched, missing, under_evidenced = [], [], []
        total_weight = matched_weight = 0
        for skill, (line, priority) in sorted(requirements.items(), key=lambda kv: (_PRIORITY_ORDER[kv[1][1]], kv[0])):
            if skill in covered_alternatives:
                continue
            weight = _PRIORITY_WEIGHT[priority]
            total_weight += weight
            if skill in resume_skills:
                matched_weight += weight
                matched.append(
                    {"skill": skill, "category": skill_category(skill), "requirement": line,
                     "evidence": _clip(resume_skills[skill])}
                )
            elif skill in profile_list:
                under_evidenced.append(
                    SkillGap(skill=skill, category=skill_category(skill), priority=priority, requirement=line,
                             suggestion=f"Your profile lists {skill}, but your resume doesn't show it. Add a bullet "
                             f"describing where you used {skill} and what came of it.")
                )
            else:
                missing.append(
                    SkillGap(skill=skill, category=skill_category(skill), priority=priority, requirement=line,
                             suggestion=learning_suggestion(skill))
                )

        job_words = _keywords(job_text)
        resume_words = _keywords(resume_text)
        overlap = len(job_words & resume_words) / len(job_words) if job_words else 0.0

        limitations = [
            "This analysis matches skills and keywords. It can't judge how deep your experience is, "
            "so a mentor's review is still valuable."
        ]
        if total_weight:
            score = round(100 * (0.8 * matched_weight / total_weight + 0.2 * overlap))
        else:
            score = round(100 * overlap * 0.9)
            limitations.append(
                "No specific skills were recognized in this job description, so the score is based only on "
                "shared keywords."
            )
        score = max(0, min(100, score))
        word_count = len((resume_text or "").split())
        if word_count < 120:
            limitations.append(f"Your resume text is short ({word_count} words), which limits the analysis.")

        suggestions = self._resume_suggestions(resume_text, matched, missing, under_evidenced)

        n_req = len(requirements) - len(covered_alternatives & set(requirements))
        band = (
            "a strong match" if score >= 75 else "a moderate match" if score >= 50
            else "an early-stage match" if score >= 25 else "a weak match"
        )
        if n_req:
            summary = (f"Your resume shows {len(matched)} of the {n_req} skills this posting mentions, "
                       f"which makes it {band} ({score}/100).")
        else:
            summary = f"Based on shared keywords, this looks like {band} ({score}/100)."

        return MatchAnalysis(
            score=score, summary=summary, matched=matched, missing=missing, under_evidenced=under_evidenced,
            suggestions=suggestions, limitations=limitations, engine=self.name,
        )

    @staticmethod
    def _resume_suggestions(resume_text, matched, missing, under_evidenced) -> list[str]:
        text = resume_text or ""
        suggestions: list[str] = []
        high_missing = [g["skill"] for g in missing if g["priority"] == "high"]
        if high_missing:
            suggestions.append(
                "Focus first on the required skills you're missing: " + ", ".join(high_missing[:4]) + "."
            )
        if under_evidenced:
            suggestions.append(
                "Some skills on your profile don't appear in your resume ("
                + ", ".join(g["skill"] for g in under_evidenced[:4])
                + "). If you have them, add a line that shows where you used each one."
            )
        if matched:
            suggestions.append(
                "Make sure your strongest matching skills ("
                + ", ".join(m["skill"] for m in matched[:3])
                + ") are easy to spot, for example in a skills section near the top."
            )
        if not re.search(r"\d", text):
            suggestions.append(
                "Your resume has no numbers. Add measurable results where you can, like "
                "\"cut page load time by 30%\" or \"tutored 40 students\"."
            )
        verbs = len(re.findall(r"\b(built|developed|designed|implemented|created|led|improved|analy[sz]ed|"
                               r"launched|automated|reduced|increased|organized|managed)\b", text, re.I))
        if verbs < 3:
            suggestions.append(
                "Start bullet points with strong action verbs (built, designed, improved, led) so your "
                "contributions stand out."
            )
        if len(text.split()) > 900:
            suggestions.append("Your resume is long. For internships, one page is usually best.")
        return suggestions

    # ------------------------------------------------------------ mock interviews (PB-23)

    _BEHAVIORAL = [
        "Tell me about a time you worked on a team project that faced a setback. What did you do?",
        "Describe a situation where you had to learn something new quickly. How did you approach it?",
        "Tell me about a time you disagreed with a teammate. How did you handle it?",
        "Describe a project you're proud of. What was your specific contribution?",
        "Tell me about a time you made a mistake. What happened and what did you learn?",
        "Describe a time you had several deadlines at once. How did you prioritize?",
        "Tell me about a time you received critical feedback. How did you respond?",
        "Describe a time you took the initiative without being asked.",
    ]

    _TECHNICAL = [
        "Walk me through a project where you used {skill}. What was your role, and what would you do differently?",
        "How would you explain {skill} to a teammate who has never used it?",
        "What's a challenging problem you solved using {skill}, and how did you debug it?",
        "How do you make sure work you do with {skill} is reliable and easy for others to maintain?",
    ]

    _GENERIC_TECHNICAL = [
        "Describe a technical problem you solved recently. How did you break it down?",
        "How do you keep your skills current for a {role} position?",
        "Tell me about a tool or technology you learned on your own. Why did you pick it?",
    ]

    def generate_questions(self, role: str, focus: str = "", count: int = 5) -> list[str]:
        role = role.strip() or "this"
        rng = random.Random(sum(ord(ch) for ch in role + focus))
        found = list(find_skills(focus))
        technical_skills = [s for s in found if skill_category(s) != SOFT]
        rng.shuffle(technical_skills)

        behavioral = self._BEHAVIORAL[:]
        rng.shuffle(behavioral)
        technical = [
            self._TECHNICAL[i % len(self._TECHNICAL)].format(skill=skill)
            for i, skill in enumerate(technical_skills[:3])
        ]
        generic = [q.format(role=role) for q in self._GENERIC_TECHNICAL]
        technical += generic[: max(0, 3 - len(technical))]

        ordered = [f"Tell me about yourself and what draws you to the {role} role."]
        pools = [behavioral, technical]
        turn = 0
        while len(ordered) < count - 1 and (behavioral or technical):
            pool = pools[turn % 2] or pools[(turn + 1) % 2]
            ordered.append(pool.pop(0))
            turn += 1
        ordered.append(f"Why are you a good fit for this {role} position, and what questions do you have for us?")
        return ordered[:count]

    # ------------------------------------------------------------ answer feedback (PB-25)

    _SITUATION = re.compile(r"\b(when|while|during|at my|in my|last (year|semester|summer|spring|fall)|project|"
                            r"internship|class|course|club|job)\b", re.I)
    _ACTION = re.compile(r"\bI\s+(?:\w+ly\s+)?(built|led|created|designed|developed|implemented|wrote|organized|"
                         r"analy[sz]ed|fixed|solved|improved|managed|decided|proposed|coordinated|taught|tested|"
                         r"learned|researched|presented|started|helped|reduced|increased|reached out|talked|"
                         r"set up|scheduled|split|rewrote|automated|asked|made|took|volunteered|planned|"
                         r"debugged|refactored|trained|mentored)\b", re.I)
    _RESULT = re.compile(r"\b(result|resulted|as a result|outcome|led to|which (led|helped|meant)|improved|"
                         r"reduced|increased|saved|achieved|grew|won|finished|delivered|launched|so that|in the end|"
                         r"ended up|successfully)\b", re.I)
    _METRIC = re.compile(r"\d+\s*(%|percent|hours?|days?|weeks?|users?|students?|people|x\b)|\$\s?\d", re.I)
    _FILLER = re.compile(r"\b(um+|uh+|you know|basically|kind of|sort of|like,)", re.I)

    def evaluate_answer(self, question: str, answer: str, role: str = "") -> AnswerFeedback:
        words = re.findall(r"[A-Za-z0-9']+", answer or "")
        wc = len(words)
        strengths: list[FeedbackPoint] = []
        improvements: list[FeedbackPoint] = []

        if wc < 8:
            return AnswerFeedback(
                rating="Needs work", score=1, strengths=[],
                improvements=[FeedbackPoint(point="Give a full answer",
                                            why=f"Your answer is {wc} word{'s' if wc != 1 else ''}, which is too "
                                            "short to show your experience.")],
                suggestion="Answer with a specific example: the situation, what you did, and the result.",
                word_count=wc, engine=self.name,
            )

        situation = self._SITUATION.search(answer)
        action = self._ACTION.search(answer)
        result = self._RESULT.search(answer)
        metric = self._METRIC.search(answer)
        fillers = self._FILLER.findall(answer)
        we_count = len(re.findall(r"\bwe\b", answer, re.I))
        i_count = len(re.findall(r"\bI\b", answer))

        score = 1
        if 60 <= wc <= 350:
            score += 1
            strengths.append(FeedbackPoint(point="Good length",
                                           why=f"At {wc} words, the answer has room for detail without rambling."))
        elif wc < 60:
            improvements.append(FeedbackPoint(point="Add more detail",
                                              why=f"Your answer is {wc} words. Aim for about 90–250 words so you "
                                              "can explain the situation, your actions and the result."))
        else:
            improvements.append(FeedbackPoint(point="Tighten your answer",
                                              why=f"Your answer is {wc} words. Interview answers land best at "
                                              "about 1–2 minutes (roughly 150–300 words)."))

        if situation:
            score += 1
            strengths.append(FeedbackPoint(point="Sets the scene",
                                           why=f"You gave context (\"{situation.group(0)}…\"), so the listener "
                                           "knows where this happened."))
        else:
            improvements.append(FeedbackPoint(point="Set the scene first",
                                              why="The answer doesn't say when or where this happened. Start with "
                                              "one sentence of context: the project, class or job."))

        if action:
            score += 1
            strengths.append(FeedbackPoint(point="Shows your own actions",
                                           why=f"You described what you personally did (\"{action.group(0)}\"), "
                                           "which shows ownership."))
        else:
            improvements.append(FeedbackPoint(point="Say what you did",
                                              why="There's no sentence describing your own actions (for example "
                                              "\"I built…\" or \"I organized…\")."))
        if we_count >= 3 and we_count > i_count * 2:
            improvements.append(FeedbackPoint(point="Balance \"we\" with \"I\"",
                                              why=f"You said \"we\" {we_count} times and \"I\" {i_count} times. "
                                              "Interviewers want to know your part."))

        if result or metric:
            score += 1
            evidence = (metric or result).group(0)
            strengths.append(FeedbackPoint(point="Ends with an outcome",
                                           why=f"You mentioned a result (\"{evidence}\"), which shows impact."))
            if not metric:
                improvements.append(FeedbackPoint(point="Quantify the result",
                                                  why="The result has no numbers. A figure (time saved, users "
                                                  "helped, grade, percentage) makes it more convincing."))
        else:
            improvements.append(FeedbackPoint(point="Finish with the result",
                                              why="The answer doesn't say how things turned out or what changed "
                                              "because of your work."))

        if len(fillers) >= 3:
            score -= 1
            improvements.append(FeedbackPoint(point="Cut filler words",
                                              why=f"Filler words appeared {len(fillers)} times "
                                              f"(e.g. \"{fillers[0]}\"). They can make you sound less sure."))

        score = max(1, min(5, score))
        rating = "Strong" if score >= 4 else "Good" if score == 3 else "Needs work"
        if improvements:
            suggestion = f"Next time: {improvements[0]['point'].lower()}. {improvements[0]['why']}"
        else:
            suggestion = "Keep using this structure: context, your actions, and a measurable result."

        return AnswerFeedback(rating=rating, score=score, strengths=strengths, improvements=improvements,
                              suggestion=suggestion, word_count=wc, engine=self.name)
