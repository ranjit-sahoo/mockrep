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
    assert "employers may not always" in out


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
        {"after": "Consistently scored 88%+ on weekly QA audits"}, RESUME)
    assert "88" not in out["after"]
    assert "[add your number - only if you know it]" in out["after"]


def test_keyword_first_then_number():
    out = factuality.sanitize_with_source(
        {"after": "reducing ramp-up time by 20% through root-cause documentation"}, RESUME)
    assert "20%" not in out["after"]
    assert "ramp-up time" in out["after"]  # sentence structure preserved


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


NURSE = ("Anita Das, ICU Nurse, Bhubaneswar. 6 years in a 20-bed ICU. "
         "Administer medications and monitor vital signs. B.Sc. Nursing, Utkal University, 2018.")
JD = ("Requirements: must maintain 90% CSAT and 80% first-call resolution. "
      "Meet weekly QA scores of 85% or above. Average handle time under 7 minutes.")


def test_false_pass_state_conditionalized():
    # Resume has no NCLEX: copy-ready "NCLEX-RN passed" must not stand as fact
    out = factuality.sanitize_with_source(
        {"fix": "If you have not yet applied, write 'NCLEX-RN passed [date] - [State] RN license application submitted [date]'"},
        NURSE)
    fix = out["fix"]
    assert "only if true for you" in fix
    assert "'NCLEX-RN passed [date]'" not in fix  # bare copy-ready assertion defused


def test_false_application_state_conditionalized():
    out = factuality.sanitize_with_source(
        {"fix": "write 'CGFNS CES report completed [date]'"}, NURSE)
    # 'completed' is not a tracked status topic, but check no crash and text intact
    assert "CGFNS CES report completed" in out["fix"]


def test_screen_out_ranking_hedged():
    fixes = []
    out = factuality.sanitize("This is the first screen-out factor", fixes)
    assert "first screen-out factor" not in out
    assert "common early screening question" in out


def test_jd_threshold_preserved_as_requirement():
    # missing_keywords quotes the JD: the JD's 85% must stay verbatim
    out = factuality.sanitize_with_source(
        {"missing_keywords": ["weekly QA scores of 85%"]}, RESUME,
        requirement_source=JD, requirement_keys=("missing_keywords", "gap"))
    assert "85%" in out["missing_keywords"][0]


def test_jd_threshold_not_claimed_as_achievement():
    # the same 85% in a tailored rewrite is a candidate claim: not resume-backed
    out = factuality.sanitize_with_source(
        {"tailored_bullets": [{"before": "x", "after": "Maintained 85% QA scores weekly"}]}, RESUME,
        requirement_source=JD, requirement_keys=("missing_keywords", "gap"))
    assert "85%" not in out["tailored_bullets"][0]["after"]


def test_advice_prose_numbers_untouched():
    # general guidance numbers are not candidate facts: no broken placeholders
    out = factuality.sanitize_with_source(
        {"why_it_hurts": "recruiters spend a 6-second scan per resume",
         "fix": "Add 2-3 metrics per role from your actual performance data"}, RESUME)
    assert "6-second scan" in out["why_it_hurts"]
    assert "2-3 metrics" in out["fix"]


def test_quoted_example_in_advice_still_scrubbed():
    out = factuality.sanitize_with_source(
        {"fix": "Convert each bullet, e.g., 'Resolved issues, maintaining 85% first-call resolution'"}, RESUME)
    assert "85%" not in out["fix"]


def test_unsupported_activity_conditionalized():
    out = factuality.sanitize_with_source({"after": "Led a team of [add number] nurses"}, NURSE)
    assert out["after"].startswith("If this reflects your real experience:")


def test_supported_activity_kept():
    out = factuality.sanitize_with_source(
        {"after": "Trained [add your number - only if you know it] new hires on process workflows"}, RESUME)
    assert out["after"].startswith("Trained")


def test_cert_with_expiry_conditionalized():
    out = factuality.sanitize_with_source(
        {"fix": "write 'AHA ACLS (exp. [date])'"}, NURSE)
    assert "only if true for you" in out["fix"]


def test_fallback_invented_specifics():
    out = factuality.sanitize_with_source(
        {"after": "Cared for 2 critically ill patients per shift (1:2 ratio); maintained 100% medication-safety compliance"}, NURSE)
    after = out["after"]
    assert "2 critically" not in after and "1:2" not in after and "100%" not in after
    assert after.count("[add your number - only if you know it]") >= 3


def test_fallback_preserves_real_facts():
    out = factuality.sanitize_with_source(
        {"after": "ICU RN with 6 years in a 20-bed unit"}, NURSE)
    assert "6 years" in out["after"] and "20-bed" in out["after"]


def test_fallback_req_cue_uses_jd():
    out = factuality.sanitize_with_source(
        {"fix": "Add your actual CSAT against the JD's 90% CSAT target"}, RESUME,
        requirement_source=JD)
    assert "90%" in out["fix"]


def test_h1b_not_mangled():
    out = factuality.sanitize_with_source(
        {"fix": "state your status: H-1B / TN / OPT - only if true"}, NURSE)
    assert "H-1B" in out["fix"]


def test_will_auto_reject_grammar():
    fixes = []
    out = factuality.sanitize("ATS will auto-reject or deprioritize", fixes)
    assert "will rejection" not in out
    assert "may deprioritize" in out


def test_eb3_not_mangled():
    out = factuality.sanitize_with_source(
        {"fix": "sponsorship needs (H-1B, TN, EB-3, OPT) - only if true"}, NURSE)
    assert "EB-3" in out["fix"] and "H-1B" in out["fix"]


def test_screened_out_automatically_hedged():
    fixes = []
    out = factuality.sanitize("the application is screened out automatically", fixes)
    assert "screened out automatically" not in out


def test_causes_immediate_rejection_hedged():
    fixes = []
    out = factuality.sanitize("Absence of this causes immediate rejection or delay", fixes)
    assert "immediate rejection" not in out


def test_auto_rejected_grammar():
    fixes = []
    out = factuality.sanitize("the application is typically auto-rejected", fixes)
    assert "typically rejection" not in out
    assert "set aside" in out


def test_polish_invented_tool_and_metric_scrubbed():
    out = factuality.scrub_invented_tools(
        "Handled inbound calls using Zendesk, resolving 95% of issues on first contact",
        "Handled inbound calls", [])
    assert "Zendesk" not in out
    out = factuality.sanitize_with_source(out, "Handled inbound calls", [])
    assert "95%" not in out
    assert "Handled inbound calls" in out


def test_polish_real_tool_and_number_kept():
    src = "Trained 5 new team members on CRM tools"
    out = factuality.scrub_invented_tools(
        "Trained 5 new team members on CRM tools, improving ramp time", src, [])
    assert "CRM" in out
    out = factuality.sanitize_with_source(out, src, [])
    assert "5" in out and "CRM" in out


def test_scrub_invented_tools_sentence_initial_capital_safe():
    out = factuality.scrub_invented_tools(
        "Resolved billing issues for a US telecom client",
        "Resolve billing and technical issues for a US telecom client", [])
    assert out.startswith("Resolved billing issues")
    assert "US" in out


def test_polish_outcome_clause_is_whole_conditional():
    out = factuality.scrub_invented_tools(
        "Handled inbound calls, achieving [X%] first-call resolution",
        "Handled inbound calls", [])
    out = factuality.sanitize_with_source(out, "Handled inbound calls", [])
    assert "only if true" in out
    assert out.startswith(factuality._CONDITIONAL_PREFIX)
    assert "Handled inbound calls" in out


def test_supported_ing_activity_not_conditionalized():
    out = factuality.sanitize_with_source(
        "Handled inbound calls, improving first-call resolution",
        "Handled inbound calls and improved first-call resolution", [])
    assert not out.startswith(factuality._CONDITIONAL_PREFIX)
