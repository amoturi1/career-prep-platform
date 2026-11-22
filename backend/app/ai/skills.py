"""Skill vocabulary used by the built-in engine to find skills in free text.

Each skill has a canonical name, a category, and the phrases that count as
mentioning it. Matching is case-insensitive and respects word boundaries, so
"Java" is not found inside "JavaScript" and "SQL" is not found inside "MySQL".
Ambiguous one-letter names (C, R) and "Go" are only matched in unambiguous forms.
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    name: str
    category: str
    aliases: tuple[str, ...]


def _s(name: str, category: str, *aliases: str) -> Skill:
    return Skill(name, category, (name.lower(), *[a.lower() for a in aliases]))


LANG, WEB, DATA, CLOUD, DB, TOOLS, PRACTICE, SOFT, MOBILE, SECURITY = (
    "Programming languages",
    "Web development",
    "Data and AI",
    "Cloud and DevOps",
    "Databases",
    "Tools",
    "Engineering practices",
    "Professional skills",
    "Mobile",
    "Security",
)

SKILLS: list[Skill] = [
    # Programming languages
    _s("Python", LANG),
    _s("Java", LANG),
    _s("JavaScript", LANG, "js", "es6", "ecmascript"),
    _s("TypeScript", LANG, "ts"),
    _s("C++", LANG, "cpp", "c/c++"),
    _s("C#", LANG, "c sharp", "csharp"),
    _s("C", LANG, "c programming", "c language", "ansi c"),
    _s("Go", LANG, "golang", "go language"),
    _s("Rust", LANG),
    _s("Kotlin", LANG),
    _s("Swift", LANG),
    _s("Ruby", LANG),
    _s("PHP", LANG),
    _s("R", LANG, "r programming", "rstudio", "r language"),
    _s("MATLAB", LANG),
    _s("Scala", LANG),
    _s("Bash", LANG, "shell scripting", "shell script", "bash scripting"),
    # Web
    _s("HTML", WEB, "html5"),
    _s("CSS", WEB, "css3", "sass", "scss"),
    _s("React", WEB, "react.js", "reactjs"),
    _s("Angular", WEB, "angularjs"),
    _s("Vue", WEB, "vue.js", "vuejs"),
    _s("Next.js", WEB, "nextjs"),
    _s("Node.js", WEB, "nodejs", "node"),
    _s("Express", WEB, "express.js", "expressjs"),
    _s("Django", WEB),
    _s("Flask", WEB),
    _s("FastAPI", WEB),
    _s("Spring Boot", WEB, "spring", "spring framework"),
    _s(".NET", WEB, "dotnet", "asp.net"),
    _s("REST APIs", WEB, "rest api", "restful", "rest", "api development", "apis"),
    _s("GraphQL", WEB),
    _s("Tailwind CSS", WEB, "tailwind"),
    # Mobile
    _s("Android", MOBILE),
    _s("iOS", MOBILE),
    _s("Flutter", MOBILE),
    _s("React Native", MOBILE),
    # Data and AI
    _s("SQL", DATA, "structured query language"),
    _s("Pandas", DATA),
    _s("NumPy", DATA),
    _s("scikit-learn", DATA, "sklearn", "scikit learn"),
    _s("TensorFlow", DATA),
    _s("PyTorch", DATA),
    _s("Machine learning", DATA, "ml", "machine-learning"),
    _s("Deep learning", DATA, "neural networks", "neural network"),
    _s("Natural language processing", DATA, "nlp"),
    _s("Large language models", DATA, "llm", "llms", "generative ai", "genai"),
    _s("Data analysis", DATA, "data analytics", "analyze data", "analyzing data", "data analyst"),
    _s("Data visualization", DATA, "visualization", "dashboards", "dashboard"),
    _s("Statistics", DATA, "statistical analysis", "statistical"),
    _s("Excel", DATA, "microsoft excel", "spreadsheets", "pivot tables"),
    _s("Tableau", DATA),
    _s("Power BI", DATA, "powerbi"),
    _s("Spark", DATA, "apache spark", "pyspark"),
    _s("ETL", DATA, "data pipelines", "data pipeline"),
    # Databases
    _s("PostgreSQL", DB, "postgres"),
    _s("MySQL", DB),
    _s("MongoDB", DB, "mongo"),
    _s("SQLite", DB),
    _s("Redis", DB),
    _s("Oracle Database", DB, "oracle db", "oracle sql"),
    _s("NoSQL", DB),
    # Cloud and DevOps
    _s("AWS", CLOUD, "amazon web services", "ec2", "s3", "lambda"),
    _s("Azure", CLOUD, "microsoft azure"),
    _s("Google Cloud", CLOUD, "gcp", "google cloud platform"),
    _s("Docker", CLOUD, "containers", "containerization"),
    _s("Kubernetes", CLOUD, "k8s"),
    _s("CI/CD", CLOUD, "continuous integration", "continuous delivery", "github actions", "jenkins"),
    _s("Linux", CLOUD, "unix"),
    _s("Terraform", CLOUD, "infrastructure as code"),
    _s("Cloud computing", CLOUD, "cloud"),
    _s("Monitoring", CLOUD, "observability", "logging"),
    _s("Networking", CLOUD, "tcp/ip", "dns", "network protocols"),
    # Security
    _s("Cybersecurity", SECURITY, "information security", "security"),
    _s("Authentication", SECURITY, "oauth", "jwt", "authorization"),
    # Tools
    _s("Git", TOOLS, "github", "gitlab", "version control"),
    _s("Jira", TOOLS),
    _s("Figma", TOOLS),
    _s("Postman", TOOLS),
    _s("VS Code", TOOLS, "visual studio code"),
    # Engineering practices
    _s("Object-oriented programming", PRACTICE, "oop", "object oriented", "object-oriented"),
    _s("Data structures", PRACTICE, "algorithms", "data structures and algorithms"),
    _s("Testing", PRACTICE, "unit testing", "unit tests", "pytest", "jest", "test automation", "qa"),
    _s("Agile", PRACTICE, "scrum", "sprints", "kanban"),
    _s("System design", PRACTICE, "software design", "software architecture", "architecture"),
    _s("Debugging", PRACTICE, "troubleshooting", "troubleshoot"),
    _s("UML", PRACTICE, "use case diagrams", "class diagrams", "sequence diagrams"),
    _s("Accessibility", PRACTICE, "wcag", "a11y"),
    # Professional skills
    _s("Communication", SOFT, "communication skills", "communicate", "presenting", "presentation"),
    _s("Teamwork", SOFT, "collaboration", "collaborate", "team player", "cross-functional"),
    _s("Leadership", SOFT, "led", "lead", "mentored", "mentoring"),
    _s("Problem solving", SOFT, "problem-solving", "analytical skills", "critical thinking"),
    _s("Project management", SOFT, "project manager", "managed projects"),
    _s("Customer service", SOFT, "customer support", "client-facing"),
    _s("Time management", SOFT, "deadlines", "prioritize", "prioritization"),
]

# Short or very common words that are only skills in some contexts; they need an
# explicit nearby technical signal and so are excluded from bare matching.
_AMBIGUOUS_ALIASES = {"node", "cloud", "security", "architecture", "spring", "visualization", "logging",
                      "qa", "ts", "js", "ml", "lambda", "s3", "swift", "rust", "spark", "presentation"}

# Words that only count as a skill when they appear as an item in a list ("Python, C, Go").
_LIST_ONLY_ALIASES = {"c", "r", "go", "rest"}

# "led"/"lead" count as leadership only when someone led something.
_LEAD_PATTERN = re.compile(
    r"\b(led|lead|leading)\s+(a|an|the|my|our|team|teams|group|groups|project|projects|development|efforts?|"
    r"workshops?|sessions?|meetings?|initiative)\b",
    re.I,
)

_TECH_CONTEXT = re.compile(
    r"\b(languages?|programming|framework|stack|experience with|proficien|skills?|technolog|tools?|using|built|develop)",
    re.I,
)


def _pattern(alias: str) -> re.Pattern:
    return re.compile(r"(?<![a-z0-9+#.])" + re.escape(alias) + r"(?![a-z0-9+#]|\.[a-z])", re.I)


_COMPILED: list[tuple[Skill, list[tuple[str, re.Pattern]]]] = [
    (skill, [(alias, _pattern(alias)) for alias in skill.aliases]) for skill in SKILLS
]


def _line_has_alias(line: str, alias: str, pattern: re.Pattern) -> bool:
    if not pattern.search(line):
        return False
    if alias in _LIST_ONLY_ALIASES:
        return bool(re.search(r"(^|[,;:/|(]\s*)" + re.escape(alias) + r"\s*([,;/|)]|$)", line, re.I))
    if alias in {"led", "lead"}:
        return bool(_LEAD_PATTERN.search(line))
    if alias in _AMBIGUOUS_ALIASES:
        return bool(_TECH_CONTEXT.search(line)) or "," in line
    return True


def find_skills(text: str) -> dict[str, str]:
    """Return {skill name: the line of text where it was found}."""
    found: dict[str, str] = {}
    lines = [ln.strip() for ln in re.split(r"[\n\r]+|(?<=[.!?])\s+", text or "") if ln.strip()]
    for skill, patterns in _COMPILED:
        for line in lines:
            if any(_line_has_alias(line, alias, pattern) for alias, pattern in patterns):
                found[skill.name] = line
                break
    return found


def skill_category(name: str) -> str:
    for skill in SKILLS:
        if skill.name == name:
            return skill.category
    return "Other"


def parse_skill_list(text: str) -> list[str]:
    """Split a comma-separated skills field (from the profile) into recognised skill names."""
    names: list[str] = []
    for part in re.split(r"[,;\n]", text or ""):
        part = part.strip()
        if not part:
            continue
        hits = find_skills(part + ",")  # trailing comma lets short names like C or R match as a list item
        names.extend(name for name in hits if name not in names)
    return names


LEARNING_SUGGESTIONS = {
    LANG: "Build a small project in {skill} and add it to your resume with a link to the code.",
    WEB: "Build and deploy a small web app that uses {skill}, then describe what you built on your resume.",
    MOBILE: "Follow an official {skill} tutorial and publish a simple app you can show in interviews.",
    DATA: "Practice {skill} on a public dataset (for example, from Kaggle) and summarize your findings.",
    DB: "Design a small database in {skill} for one of your projects and write a few non-trivial queries.",
    CLOUD: "Try {skill} through a free tier or student credits, and deploy one of your projects with it.",
    SECURITY: "Study the basics of {skill} (OWASP is a good start) and apply them to a project you've built.",
    TOOLS: "Use {skill} in your next team or class project so you can talk about it from experience.",
    PRACTICE: "Practice {skill} deliberately in your next project and note one concrete example for interviews.",
    SOFT: "Prepare a short story (Situation, Task, Action, Result) that shows your {skill}.",
}


def learning_suggestion(skill: str) -> str:
    template = LEARNING_SUGGESTIONS.get(skill_category(skill), "Look for a course or project that builds {skill}.")
    return template.format(skill=skill)
