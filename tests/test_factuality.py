"""Tests for the deterministic factuality backstop (app/factuality.py).

Fixtures use phrases actually observed in production output before the fix.
"""
from app import factuality


def scrub(text):
    fixes = []
    out = factuality.sanitize(text, fixes)
    return out, fixes


def test_legally_require_hedged():
    out, fixes = scrub("ICU roles legally require an active RN license in the state of practice.")
    assert "legally require" not in out.lower()
    assert "commonly ask for" in out
    assert "RN license" in out  # factual content preserved
    assert fixes


def test_employers_cannot_hedged():
    out, _ = scrub("Employers cannot consider candidates without it.")
    assert "employers cannot" not in out.lower()
    assert "not all employers will" in out


def test_causal_certainty_softened():
    out, _ = scrub("Silence forces them to assume sponsorship is needed and often leads to auto-reject.")
    assert "forces them to assume" not in out
    assert "auto-reject" not in out.lower()
    assert "may lead them to assume" in out


def test_ranking_certainty_softened():
    out, _ = scrub("Missing dates = incomplete record = lower ranking.")
    assert "= lower ranking" not in out
    assert "can lower ranking" in out


def test_real_facts_untouched():
    text = ("Maintained 92% CSAT and 6.5-min AHT. [add your FCR % - only if you know it] "
            "Verify the exact requirement for the specific employer.")
    out, fixes = scrub(text)
    assert out == text
    assert not fixes


def test_structure_and_types_preserved():
    data = {
        "score": 4,
        "weaknesses": [
            {"issue": "No license", "why": "US ICU positions legally require an RN license.",
             "fix": "Add [license number - only if true]."}
        ],
        "strengths": ["6 years ICU experience"],
        "nested": {"list": ["Mandatory CCRN.", 7, None, True]},
    }
    fixes = []
    out = factuality.sanitize(data, fixes)
    assert out["score"] == 4
    assert out["strengths"] == ["6 years ICU experience"]
    assert "legally require" not in out["weaknesses"][0]["why"].lower()
    assert "[license number - only if true]" in out["weaknesses"][0]["fix"]
    assert "often requested" in out["nested"]["list"][0]
    assert out["nested"]["list"][1:] == [7, None, True]
    assert fixes


def test_watch_phrases_flagged():
    _, fixes = scrub("Without this you are never hired.")
    assert any(f.startswith("WATCH:") for f in fixes)


def test_outcome_certainty_softened():
    out, _ = scrub("With no timeline, no numbers, and no license, it will not pass an initial screen.")
    assert "will not pass" not in out
    assert "may not pass" in out
