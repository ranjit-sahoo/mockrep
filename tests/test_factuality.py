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


RESUME = ("Handled 60+ calls/day for a US telecom client, average CSAT 92%. "
          "Resolved billing disputes, AHT 6.5 minutes vs 8 target. Trained 5 new joiners.")


def test_invented_metric_replaced_with_placeholder():
    out, fixes = scrub_with("Consistently hit 90+ CSAT & 85% FCR; trained 15+ new hires.", RESUME)
    assert "90+" not in out and "85%" not in out and "15+" not in out
    assert "[add your number - only if you know it]" in out
    assert fixes


def test_source_backed_metrics_preserved():
    out, fixes = scrub_with("Maintained 92% CSAT and 6.5-minute AHT, handled 60+ calls/day, trained 5 new hires.", RESUME)
    assert "92% CSAT" in out and "60+ calls/day" in out and "5 new hires" in out
    assert not [f for f in fixes if f.startswith("invented-metric:")]


def test_number_in_different_context_still_flagged():
    out, fixes = scrub_with("Achieved 18% retention-save rate.", RESUME)
    assert "18%" not in out
    assert any(f.startswith("invented-metric:") for f in fixes)


def scrub_with(text, source):
    fixes = []
    out = factuality.sanitize_with_source(text, source, fixes)
    return out, fixes


def test_jd_requirement_not_attributed_as_achievement():
    # JD states a target; candidate resume never mentions it.
    out, fixes = scrub_with("Maintained 90% CSAT for the account.", "Handled calls for a telecom client.")
    assert "90% CSAT" not in out
    assert any(f.startswith("invented-metric:") for f in fixes)


def test_unrelated_resume_number_not_attributed():
    # Resume has 60 for calls/day; output reuses 60 as an FCR claim.
    out, fixes = scrub_with("Achieved 60% FCR on billing calls.", RESUME)
    assert "60% FCR" not in out
    assert any(f.startswith("invented-metric:") for f in fixes)


def test_keyword_proximity_attribution_kept():
    out, fixes = scrub_with("Kept CSAT at 92% across the year.", RESUME)
    assert "92%" in out
    assert not [f for f in fixes if f.startswith("invented-metric:")]


def test_space_hyphen_variant_first_call_resolution():
    # "85% first-call resolution" (space variant) must also be caught
    out = factuality.sanitize_with_source(
        {"fix": "e.g. 'Maintained [x]% CSAT, 85% first-call resolution, and 6:30 avg handle time over 12 months'"},
        RESUME)
    fix = out["fix"]
    assert "85%" not in fix and "6:30" not in fix
    assert fix.count("[add your number - only if you know it]") >= 2


def test_number_then_keyword_within_words():
    out = factuality.sanitize_with_source(
        {"fix": "Consistently scored 88%+ on weekly QA audits"}, RESUME)
    assert "88" not in out["fix"]
    assert "[add your number - only if you know it]" in out["fix"]


def test_keyword_first_then_number():
    out = factuality.sanitize_with_source(
        {"fix": "reducing ramp-up time by 20% through root-cause documentation"}, RESUME)
    assert "20%" not in out["fix"]
    assert "ramp-up time" in out["fix"]  # sentence structure preserved


def test_hyphenated_minute_unit_attributed():
    # "6.5-minute AHT" in output is backed by resume's "AHT 6.5 minutes"
    out = factuality.sanitize_with_source(
        {"after": "Maintained 6.5-minute AHT and 92% CSAT"},
        "average CSAT 92%. Resolved billing disputes, AHT 6.5 minutes vs 8 target.")
    assert "6.5-minute AHT" in out["after"] and "92% CSAT" in out["after"]


def test_avg_handle_time_maps_to_aht_synonym():
    out = factuality.sanitize_with_source(
        {"after": "kept 6.5 average handle time"}, "AHT 6.5 minutes vs 8 target.")
    assert "6.5 average handle time" in out["after"]
