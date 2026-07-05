"""Test the real compute_ats function from agents/cv_analyzer directly."""

from agents.cv_analyzer import compute_ats


def test_perfect_cv():
    data = {
        "has_tables": False,
        "has_images": False,
        "fonts_count": 1,
        "pages_count": 1,
        "sections_found": ["experience", "education", "skills", "summary"],
        "cv_text": "led a team of 10 engineers at Google since 2020",
    }
    result = compute_ats(data)
    assert 70 <= result["ats_score"] <= 100
    assert result["breakdown"]["format"] == 100
    assert result["breakdown"]["structure"] == 100
    assert result["breakdown"]["length"] == 100


def test_poor_cv():
    data = {
        "has_tables": True,
        "has_images": True,
        "fonts_count": 5,
        "pages_count": 3,
        "sections_found": [],
        "cv_text": "hello",
    }
    result = compute_ats(data)
    assert 0 <= result["ats_score"] <= 50
    assert result["breakdown"]["format"] == 30
    assert result["breakdown"]["structure"] == 0
    assert len(result["issues"]) >= 8


def test_missing_personal_info():
    data = {
        "has_tables": False,
        "has_images": False,
        "fonts_count": 1,
        "pages_count": 1,
        "sections_found": ["experience", "education", "skills", "summary"],
        "cv_text": "date of birth: 1990, marital status: single, managed team since 2020",
    }
    result = compute_ats(data)
    assert any("personal info" in issue.lower() for issue in result["issues"])


def test_no_dates():
    data = {
        "has_tables": False,
        "has_images": False,
        "fonts_count": 2,
        "pages_count": 1,
        "sections_found": ["experience", "education", "skills"],
        "cv_text": "worked on various projects",
    }
    result = compute_ats(data)
    assert any("dates" in issue.lower() for issue in result["issues"])


def test_no_action_verbs():
    data = {
        "has_tables": False,
        "has_images": False,
        "fonts_count": 1,
        "pages_count": 1,
        "sections_found": ["experience", "education", "skills", "summary"],
        "cv_text": "was a worker at a company since 2020. did things. was there.",
    }
    result = compute_ats(data)
    assert any("action verb" in issue.lower() for issue in result["issues"])


def test_missing_required_sections():
    data = {
        "has_tables": False,
        "has_images": False,
        "fonts_count": 1,
        "pages_count": 1,
        "sections_found": ["hobbies"],
        "cv_text": "something something since 2020",
    }
    result = compute_ats(data)
    assert any("Missing required" in issue for issue in result["issues"])
    assert result["breakdown"]["structure"] <= 50


def test_two_page_cv_penalty():
    data = {
        "has_tables": False,
        "has_images": False,
        "fonts_count": 1,
        "pages_count": 2,
        "sections_found": ["experience", "education", "skills", "summary"],
        "cv_text": "managed and led multiple teams since 2020",
    }
    result = compute_ats(data)
    assert result["breakdown"]["length"] == 100


def test_three_page_cv_penalty():
    data = {
        "has_tables": False,
        "has_images": False,
        "fonts_count": 1,
        "pages_count": 3,
        "sections_found": ["experience", "education", "skills", "summary"],
        "cv_text": "managed and led multiple teams since 2020",
    }
    result = compute_ats(data)
    assert result["breakdown"]["length"] == 70
    assert any("pages" in issue.lower() for issue in result["issues"])
