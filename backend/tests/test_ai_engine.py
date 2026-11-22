"""Unit tests for the built-in AI engine and skill detection (NFR-09, NFR-11)."""
from app.ai.local_engine import LocalEngine
from app.ai.skills import find_skills, parse_skill_list

engine = LocalEngine()


def test_skill_detection_respects_word_boundaries():
    found = find_skills("Experience with JavaScript and MySQL.")
    assert "JavaScript" in found and "MySQL" in found
    assert "Java" not in found and "SQL" not in found


def test_ambiguous_words_are_not_skills_in_ordinary_sentences():
    found = find_skills("Go to the meeting, then rest. This can lead to delays.")
    assert not {"Go", "REST APIs", "Leadership"} & set(found)


def test_short_skill_names_in_lists():
    assert set(parse_skill_list("Python, C, Go, R, C++, C#")) == {"Python", "C", "Go", "R", "C++", "C#"}


def test_required_skills_weigh_more_than_nice_to_have():
    job = "Requirements:\n- Python\n- SQL\nNice to have:\n- Docker\n- AWS"
    has_required = engine.analyze_match("Skills: Python, SQL", job)
    has_optional = engine.analyze_match("Skills: Docker, AWS", job)
    assert has_required["score"] > has_optional["score"]
    priorities = {gap["skill"]: gap["priority"] for gap in has_optional["missing"]}
    assert priorities == {"Python": "high", "SQL": "high"}


def test_job_with_no_known_skills_says_so():
    result = engine.analyze_match("Skills: Python", "We want a cheerful person for our front desk.")
    assert any("No specific skills" in note for note in result["limitations"])


def test_questions_are_deterministic_and_role_specific():
    first = engine.generate_questions("Data Analyst Intern", "SQL, Tableau", 5)
    assert first == engine.generate_questions("Data Analyst Intern", "SQL, Tableau", 5)
    assert len(first) == 5 and "Data Analyst Intern" in first[0] and "Data Analyst Intern" in first[-1]


def test_feedback_explains_itself():
    feedback = engine.evaluate_answer("Tell me about a project.", "I built it.")
    assert feedback["rating"] == "Needs work" and "words" in feedback["improvements"][0]["why"]
