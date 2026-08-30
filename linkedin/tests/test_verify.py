"""Tests for the Reading Rule and the Unipile error taxonomy.

The profile fixtures are trimmed from real Unipile responses, so a change in
the API's shape breaks these rather than silently changing verdicts.
"""

from datetime import date

import pytest

from qbs_linkedin.config import (
    VERDICT_MOVED,
    VERDICT_UNREADABLE,
    VERDICT_YES,
)
from qbs_linkedin.errors import Action, classify, should_abort_run
from qbs_linkedin.verify import (
    InstrumentError,
    companies_match,
    normalize_company,
    parse_li_date,
    read_roles,
    verify_employment,
)

TODAY = date(2026, 8, 29)

# Trimmed from the live response for michelinenijmeh. Note the order: the
# current role happens to be first here, but Zscaler (ended) precedes older
# entries elsewhere, so ordering must never be relied on.
REAL_PROFILE = {
    "provider_id": "ACoAAAAXYqUBKmRosX0V1O_okKokDG_a3zABHPY",
    "work_experience_total_count": 11,
    "work_experience": [
        {"company": "ThoughtSpot", "position": "Chief Marketing Officer",
         "status": "Full-time", "start": "3/1/2025", "end": None},
        {"company": "JFrog", "position": "Chief Marketing Officer",
         "start": "9/1/2020", "end": "3/1/2025"},
        {"company": "Zscaler", "position": "Chief Marketing Officer",
         "start": "10/1/2018", "end": "6/1/2020"},
        # No company_id, no status, no location — all genuinely absent in live data.
        {"company": "Xactly Corp (acquired by Vista)",
         "position": "Chief Marketing Officer",
         "start": "5/1/2016", "end": "9/1/2018"},
    ],
}

#: Overlapping internal promotions at one employer, as seen on a real profile.
OVERLAPPING_PROFILE = {
    "work_experience": [
        {"company": "Acme", "position": "Enterprise BDR",
         "start": "9/1/2017", "end": "10/1/2019"},
        {"company": "Acme", "position": "SMB AE",
         "start": "10/1/2018", "end": "11/1/2020"},
        {"company": "Acme", "position": "Principal BDR",
         "start": "2/1/2018", "end": None},
    ],
}


class TestInstrumentFailure:
    def test_missing_section_raises_rather_than_verdicts(self):
        # The whole point. Omitting linkedin_sections=experience returns 200
        # with no work_experience key; scoring that as `no` would write
        # "No Longer with Company" across the CRM.
        with pytest.raises(InstrumentError, match="linkedin_sections"):
            read_roles({"provider_id": "ACoAAA", "headline": "CMO"})

    def test_verify_propagates_it(self):
        with pytest.raises(InstrumentError):
            verify_employment({"headline": "CMO"}, "ThoughtSpot", TODAY)

    def test_empty_list_is_a_verdict_not_an_error(self):
        # Present but empty is real information: nothing to read.
        v = verify_employment({"work_experience": []}, "Acme", TODAY)
        assert v.verdict == "no_profile"


class TestCompanyMatching:
    @pytest.mark.parametrize("raw,expected", [
        ("Acme Corporation", "acme"),
        ("Acme, Inc.", "acme"),
        ("Acme LLC", "acme"),
        ("Acme Holdings Group", "acme"),
        ("  ACME  Co  ", "acme"),
    ])
    def test_normalization_strips_legal_suffixes(self, raw, expected):
        assert normalize_company(raw) == expected

    @pytest.mark.parametrize("a,b", [
        ("Acme", "Acme Corporation"),
        ("Acme, Inc.", "ACME LLC"),
        ("Xactly", "Xactly Corp (acquired by Vista)"),
        ("ThoughtSpot", "Thoughtspot"),
    ])
    def test_matches_the_same_employer(self, a, b):
        assert companies_match(a, b)

    @pytest.mark.parametrize("a,b", [
        ("Acme", "Beta Industries"),
        ("JFrog", "ThoughtSpot"),
        ("", "Acme"),
        (None, "Acme"),
    ])
    def test_rejects_different_employers(self, a, b):
        assert not companies_match(a, b)

    def test_short_names_do_not_match_by_containment(self):
        # "HP" inside "Shopify" would otherwise pair unrelated employers.
        assert not companies_match("HP", "Shopify")


class TestDateParsing:
    @pytest.mark.parametrize("raw,expected", [
        ("3/1/2025", date(2025, 3, 1)),
        ("12/31/2020", date(2020, 12, 31)),
        ("5/2016", date(2016, 5, 1)),
        ("2016", date(2016, 1, 1)),
    ])
    def test_us_formats(self, raw, expected):
        assert parse_li_date(raw) == expected

    @pytest.mark.parametrize("raw", [None, "", "not a date", "2020-03-01T00:00:00Z"])
    def test_unparseable_returns_none_rather_than_raising(self, raw):
        # An unreadable date is a reason to call a profile unreadable, never
        # a reason to call someone a mover.
        assert parse_li_date(raw) is None


class TestReadingRule:
    def test_current_role_at_the_crm_company_is_yes(self):
        v = verify_employment(REAL_PROFILE, "ThoughtSpot", TODAY)
        assert v.verdict == "yes"
        assert v.matched_role.position == "Chief Marketing Officer"
        assert v.tenure_years == pytest.approx(1.5, abs=0.2)

    def test_ended_role_with_a_new_employer_is_moved(self):
        v = verify_employment(REAL_PROFILE, "JFrog", TODAY)
        assert v.verdict == "moved"
        assert "ThoughtSpot" in v.evidence

    def test_company_absent_from_history_is_moved_not_unreadable(self):
        # They are demonstrably employed elsewhere, which is information.
        v = verify_employment(REAL_PROFILE, "Some Other Corp", TODAY)
        assert v.verdict == "moved"

    def test_ended_role_with_no_current_role_is_no(self):
        profile = {"work_experience": [
            {"company": "Acme", "position": "VP", "start": "1/1/2020", "end": "1/1/2024"},
        ]}
        assert verify_employment(profile, "Acme", TODAY).verdict == "no"

    def test_missing_crm_company_is_unreadable(self):
        v = verify_employment(REAL_PROFILE, None, TODAY)
        assert v.verdict == "unreadable"

    def test_suffix_difference_still_matches(self):
        profile = {"work_experience": [
            {"company": "Acme Corporation", "position": "CRO",
             "start": "1/1/2020", "end": None},
        ]}
        assert verify_employment(profile, "Acme, Inc.", TODAY).verdict == "yes"

    def test_concurrent_current_roles_are_a_set(self):
        # Senior people hold an operating role plus board seats. Taking the
        # first entry would miss the one that matters.
        profile = {"work_experience": [
            {"company": "Board Co", "position": "Board Member",
             "start": "1/1/2022", "end": None},
            {"company": "Acme", "position": "CRO",
             "start": "1/1/2021", "end": None},
        ]}
        v = verify_employment(profile, "Acme", TODAY)
        assert v.verdict == "yes"
        assert len(v.current_roles) == 2

    def test_entries_are_not_assumed_chronological(self):
        profile = {"work_experience": [
            {"company": "Old Co", "position": "VP", "start": "1/1/2010", "end": "1/1/2015"},
            {"company": "Acme", "position": "CRO", "start": "1/1/2021", "end": None},
        ]}
        assert verify_employment(profile, "Acme", TODAY).verdict == "yes"

    def test_tenure_runs_from_the_earliest_role_at_that_employer(self):
        # An internal promotion must not reset the clock.
        v = verify_employment(OVERLAPPING_PROFILE, "Acme", TODAY)
        assert v.verdict == "yes"
        assert v.tenure_years == pytest.approx(9.0, abs=0.2)  # from 9/2017

    def test_overlapping_roles_mark_tenure_low_confidence(self):
        v = verify_employment(OVERLAPPING_PROFILE, "Acme", TODAY)
        assert v.tenure_confident is False

    def test_clean_history_is_confident(self):
        assert verify_employment(REAL_PROFILE, "ThoughtSpot", TODAY).tenure_confident

    def test_entries_without_a_company_are_ignored(self):
        profile = {"work_experience": [
            {"position": "Advisor", "start": "1/1/2020", "end": None},
            {"company": "Acme", "position": "CRO", "start": "1/1/2021", "end": None},
        ]}
        assert verify_employment(profile, "Acme", TODAY).verdict == "yes"


class TestErrorTaxonomy:
    @pytest.mark.parametrize("kind", [
        "account_restricted", "checkpoint_error", "disconnected_account",
        "multiple_sessions", "invalid_credentials",
    ])
    def test_session_and_account_problems_halt(self, kind):
        v = classify({"status": 401, "type": f"errors/{kind}", "detail": "x"})
        assert v.action is Action.HALT and v.is_fatal

    @pytest.mark.parametrize("kind", ["too_many_requests", "limit_exceeded"])
    def test_provider_limits_stop_for_the_day(self, kind):
        v = classify({"status": 429, "type": f"errors/{kind}"})
        assert v.action is Action.STOP_FOR_DAY and v.is_fatal

    def test_already_invited_is_benign_but_must_still_be_logged(self):
        # Skipping the CRM write here burns the prospect on every future run.
        v = classify({"status": 422, "type": "errors/already_invited_recently"})
        assert v.action is Action.SKIP
        assert v.log_anyway
        assert not v.is_fatal

    def test_invalid_recipient_skips_just_this_candidate(self):
        v = classify({"status": 422, "type": "errors/invalid_recipient"})
        assert v.action is Action.SKIP and not v.log_anyway

    @pytest.mark.parametrize("kind", ["provider_error", "request_timeout"])
    def test_transient_faults_retry(self, kind):
        assert classify({"status": 500, "type": f"errors/{kind}"}).action is Action.RETRY

    def test_success_proceeds(self):
        assert classify({"object": "InvitationSent"}).action is Action.PROCEED

    def test_quota_signal_in_a_success_body_stops_the_day(self):
        # The only authoritative throttle signal, and it rides on a 200. A
        # status-code-only check throws it away.
        v = classify({"object": "InvitationSent", "usage": 90})
        assert v.action is Action.STOP_FOR_DAY
        assert "quota" in v.reason

    def test_low_quota_is_fine(self):
        assert classify({"object": "InvitationSent", "usage": 50}).action is Action.PROCEED

    def test_unknown_errors_halt_rather_than_retry(self):
        # Guessing through an unrecognised failure on a live account is how
        # accounts get restricted.
        v = classify({"status": 418, "type": "errors/brand_new_thing"})
        assert v.action is Action.HALT

    def test_empty_response_retries(self):
        assert classify(None).action is Action.RETRY

    def test_error_budget(self):
        assert not should_abort_run(2)
        assert should_abort_run(3)


class TestAnUnreadableEndDateIsNeverAVerdict:
    """LinkedIn emits end-date forms parse_li_date does not accept.

    `is_current` was `end is None`, so an unparseable end read as "still
    there": verdict `yes`, a fabricated tenure, and an evidence string
    asserting "no end date" about a role that finished years earlier. A rep
    then dials the old employer — the outcome this program exists to prevent.
    """

    ENDED = {"work_experience": [
        {"company": "Acme Corp", "position": "VP Sales",
         "start": "1/1/2019", "end": "Jan 2023"},
    ]}

    def test_an_unparseable_end_is_unreadable_not_yes(self):
        v = verify_employment(self.ENDED, "Acme Corp", today=date(2026, 8, 30))
        assert v.verdict == VERDICT_UNREADABLE
        assert "could not be parsed" in v.evidence
        assert "'Jan 2023'" in v.evidence

    def test_it_never_reports_a_tenure_it_cannot_support(self):
        v = verify_employment(self.ENDED, "Acme Corp", today=date(2026, 8, 30))
        assert v.tenure_years is None

    def test_an_absent_end_still_means_current(self):
        # The fix must not break the ordinary case it sits next to.
        v = verify_employment(
            {"work_experience": [{"company": "Acme Corp", "position": "VP Sales",
                                  "start": "1/1/2019", "end": None}]},
            "Acme Corp", today=date(2026, 8, 30))
        assert v.verdict == VERDICT_YES
        assert v.tenure_years == 7.7

    def test_a_role_with_an_unreadable_end_cannot_be_a_destination(self):
        # It must not surface as "now at X" either.
        v = verify_employment(
            {"work_experience": [
                {"company": "Mystery Co", "position": "CEO",
                 "start": "1/1/2020", "end": "sometime"},
                {"company": "Acme Corp", "position": "VP Sales",
                 "start": "1/1/2015", "end": "5/1/2024"}]},
            "Acme Corp", today=date(2026, 8, 30))
        assert v.destination is None


class TestDestinationRanking:
    """`moved` drives re-association, so the destination must be the person's
    actual job — not whichever role the array happens to list first."""

    MOVED = {"work_experience": [
        {"company": "Riverside Youth Baseball", "position": "Board Member",
         "start": "3/1/2018", "end": None},
        {"company": "Globex", "position": "Chief Revenue Officer",
         "start": "6/1/2024", "end": None},
        {"company": "Acme Corp", "position": "VP Sales",
         "start": "1/1/2019", "end": "5/1/2024"},
    ]}

    def test_a_senior_role_outranks_a_longer_held_board_seat(self):
        v = verify_employment(self.MOVED, "Acme Corp", today=date(2026, 8, 30))
        assert v.verdict == VERDICT_MOVED
        assert v.destination.company == "Globex"
        assert v.destination_ambiguous is False

    def test_array_order_does_not_decide(self):
        reversed_profile = {"work_experience":
                            list(reversed(self.MOVED["work_experience"]))}
        v = verify_employment(reversed_profile, "Acme Corp",
                              today=date(2026, 8, 30))
        assert v.destination.company == "Globex"

    def test_two_equal_senior_roles_are_flagged_for_a_human(self):
        v = verify_employment(
            {"work_experience": [
                {"company": "Globex", "position": "Chief Revenue Officer",
                 "start": "6/1/2024", "end": None},
                {"company": "Initech", "position": "Chief Operating Officer",
                 "start": "6/1/2024", "end": None},
                {"company": "Acme Corp", "position": "VP Sales",
                 "start": "1/1/2019", "end": "5/1/2024"}]},
            "Acme Corp", today=date(2026, 8, 30))
        assert v.destination_ambiguous is True
        assert "needs a human" in v.evidence

    def test_the_absent_company_path_ranks_too(self):
        # The other branch that used to take current[0] blindly.
        v = verify_employment(
            {"work_experience": [
                {"company": "Riverside Youth Baseball", "position": "Board Member",
                 "start": "3/1/2018", "end": None},
                {"company": "Globex", "position": "Chief Revenue Officer",
                 "start": "6/1/2024", "end": None}]},
            "Nowhere Ltd", today=date(2026, 8, 30))
        assert v.verdict == VERDICT_MOVED
        assert v.destination.company == "Globex"
