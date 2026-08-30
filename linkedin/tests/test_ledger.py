"""Tests for send-ledger accounting and date arithmetic.

Every assertion here guards a failure that would be invisible in production:
an off-by-one day, or a cap that reads zero because the ledger died.
"""

from datetime import date, datetime, timezone

import pytest

from qbs_linkedin.config import TIMEZONE
from qbs_linkedin.ledger import (
    CapDecision,
    chicago_day_bounds,
    date_to_hubspot_date,
    days_since,
    decide_allowance,
    hubspot_date_to_date,
    within_active_hours,
)


class TestHubSpotDateProperties:
    """HubSpot `date` properties are UTC midnight, and must stay that way."""

    def test_roundtrip_preserves_the_calendar_date(self):
        for value in (date(2026, 1, 16), date(2026, 7, 4), date(2026, 12, 31)):
            assert hubspot_date_to_date(date_to_hubspot_date(value)) == value

    def test_utc_midnight_reads_as_that_day_not_the_day_before(self):
        # THE off-by-one. UTC midnight Jan 16 is 18:00 Jan 15 in Chicago, so a
        # local conversion returns the 15th and every "re-attempt after N days"
        # guard fires a day early -- always toward re-attempting too soon.
        stored = date_to_hubspot_date(date(2026, 1, 16))
        assert hubspot_date_to_date(stored) == date(2026, 1, 16)

        naive_local = datetime.fromtimestamp(stored / 1000, tz=TIMEZONE).date()
        assert naive_local == date(2026, 1, 15)  # what the bug would produce

    def test_summer_date_has_the_same_hazard(self):
        stored = date_to_hubspot_date(date(2026, 7, 4))
        assert hubspot_date_to_date(stored) == date(2026, 7, 4)
        assert datetime.fromtimestamp(stored / 1000, tz=TIMEZONE).date() == date(2026, 7, 3)

    def test_missing_values(self):
        assert hubspot_date_to_date(None) is None
        assert hubspot_date_to_date("") is None
        assert days_since(None) is None

    def test_days_since_counts_whole_days(self):
        stored = date_to_hubspot_date(date(2026, 8, 1))
        assert days_since(stored, today=date(2026, 8, 1)) == 0
        assert days_since(stored, today=date(2026, 8, 15)) == 14
        # A 14-day retry window must not open on day 13.
        assert days_since(stored, today=date(2026, 8, 14)) == 13


class TestChicagoDayBounds:
    """Datetime properties bucket on LOCAL midnight, and DST moves it."""

    def test_cdt_day_is_utc_0500_to_0500(self):
        start, end = chicago_day_bounds(date(2026, 8, 29))  # CDT, UTC-5
        s = datetime.fromtimestamp(start / 1000, tz=timezone.utc)
        e = datetime.fromtimestamp(end / 1000, tz=timezone.utc)
        assert (s.hour, s.day) == (5, 29)
        assert (e.hour, e.day) == (5, 30)

    def test_cst_day_shifts_an_hour(self):
        start, _ = chicago_day_bounds(date(2026, 1, 15))  # CST, UTC-6
        s = datetime.fromtimestamp(start / 1000, tz=timezone.utc)
        assert (s.hour, s.day) == (6, 15)

    def test_span_is_exactly_one_day_outside_transitions(self):
        start, end = chicago_day_bounds(date(2026, 8, 29))
        assert end - start == 24 * 60 * 60 * 1000

    def test_dst_spring_forward_day_is_23_hours(self):
        # 2026-03-08. A hardcoded 24h window would overrun into the next day
        # and double-count the first hour of it.
        start, end = chicago_day_bounds(date(2026, 3, 8))
        assert end - start == 23 * 60 * 60 * 1000

    def test_dst_fall_back_day_is_25_hours(self):
        start, end = chicago_day_bounds(date(2026, 11, 1))
        assert end - start == 25 * 60 * 60 * 1000

    def test_a_late_evening_instant_still_lands_in_its_local_day(self):
        # 23:30 Chicago on Aug 29 is 04:30 UTC on Aug 30. Bucketing by UTC
        # would file it under the wrong day and split a run's tally in two.
        local = datetime(2026, 8, 29, 23, 30, tzinfo=TIMEZONE)
        start, end = chicago_day_bounds(local)
        assert start <= int(local.timestamp() * 1000) < end
        assert chicago_day_bounds(local) == chicago_day_bounds(date(2026, 8, 29))


class TestCapFailsClosed:
    """Every doubt must reduce the allowance to zero, never raise it."""

    def test_normal_run_gets_its_allowance(self):
        d = decide_allowance(posted_today=3, per_day=12, per_run=2,
                             ledger_writes_in_window=9, ledger_writes_ever=150,
                             independent_count=None)
        assert d.allowance == 2 and not d.halted and bool(d)

    def test_allowance_is_clamped_by_remaining_daily_capacity(self):
        d = decide_allowance(posted_today=11, per_day=12, per_run=2,
                             ledger_writes_in_window=9, ledger_writes_ever=150,
                             independent_count=None)
        assert d.allowance == 1

    def test_daily_cap_reached(self):
        d = decide_allowance(posted_today=12, per_day=12, per_run=2,
                             ledger_writes_in_window=9, ledger_writes_ever=150,
                             independent_count=None)
        assert d.allowance == 0 and not bool(d)
        assert "daily cap reached" in d.reason

    def test_dead_ledger_halts_instead_of_authorising_a_full_day(self):
        # The live condition: 153 historic tasks, none since 2026-06-01. A
        # naive reading is "0 sent today, full capacity available".
        d = decide_allowance(posted_today=0, per_day=12, per_run=2,
                             ledger_writes_in_window=0, ledger_writes_ever=153,
                             independent_count=None)
        assert d.allowance == 0
        assert d.halted
        assert "not recording" in d.reason

    def test_a_genuinely_new_ledger_proceeds_ONLY_on_a_second_opinion(self):
        # No history and no recent writes is ambiguous: a first run and a
        # ledger that has never recorded anything read identically. Unipile
        # confirming zero sends is what separates them.
        d = decide_allowance(posted_today=0, per_day=12, per_run=2,
                             ledger_writes_in_window=0, ledger_writes_ever=0,
                             independent_count=0)
        assert d.allowance == 2 and not d.halted

    def test_an_empty_ledger_without_a_second_opinion_refuses_to_send(self):
        # The hole this closed: omitting independent_count used to grant a
        # full day's capacity out of a ledger that had never recorded a
        # single send. Send 20, lose every write, read 0, send 20 more.
        d = decide_allowance(posted_today=0, per_day=12, per_run=2,
                             ledger_writes_in_window=0, ledger_writes_ever=0,
                             independent_count=None)
        assert d.allowance == 0 and d.halted
        assert d.needs_independent_count
        assert "refusing to send blind" in d.reason

    def test_an_empty_ledger_contradicted_by_unipile_halts(self):
        d = decide_allowance(posted_today=0, per_day=12, per_run=2,
                             ledger_writes_in_window=0, ledger_writes_ever=0,
                             independent_count=20)
        assert d.halted and not d.needs_independent_count

    def test_independent_count_has_no_default(self):
        # It was optional once, which made the fail-closed guarantee opt-in.
        import inspect
        sig = inspect.signature(decide_allowance)
        assert sig.parameters["independent_count"].default is inspect.Parameter.empty

    def test_divergence_from_an_independent_count_halts(self):
        # Unipile shows 9 sends today, the ledger shows 1. The ledger is
        # missing sends, so its low number must not authorise more.
        d = decide_allowance(posted_today=1, per_day=12, per_run=2,
                             ledger_writes_in_window=1, ledger_writes_ever=153,
                             independent_count=9)
        assert d.allowance == 0 and d.halted
        assert "independent count" in d.reason

    def test_small_divergence_is_tolerated(self):
        # Unipile's own counts are approximate, so a gap inside tolerance is
        # expected and must not stop an otherwise healthy run.
        d = decide_allowance(posted_today=5, per_day=12, per_run=2,
                             ledger_writes_in_window=5, ledger_writes_ever=153,
                             independent_count=7)
        assert d.allowance == 2 and not d.halted

    def test_staleness_is_checked_before_the_cap(self):
        # A dead ledger with a plausible-looking count is still a halt: the
        # count cannot be trusted, so neither can "under the cap".
        d = decide_allowance(posted_today=4, per_day=12, per_run=2,
                             ledger_writes_in_window=0, ledger_writes_ever=153,
                             independent_count=None)
        assert d.halted

    @pytest.mark.parametrize("posted", [0, 1, 5, 11, 12, 50])
    def test_allowance_is_never_negative_or_above_per_run(self, posted):
        d = decide_allowance(posted_today=posted, per_day=12, per_run=2,
                             ledger_writes_in_window=9, ledger_writes_ever=150,
                             independent_count=None)
        assert 0 <= d.allowance <= 2

    def test_decision_is_falsy_when_it_blocks(self):
        assert not CapDecision(0, 0, "blocked", halted=True)
        assert CapDecision(1, 0, "ok")


class TestActiveHours:
    @pytest.mark.parametrize("hour,expected", [
        (6, False), (7, True), (12, True), (17, True), (18, False), (23, False),
    ])
    def test_window_start_is_inclusive_and_end_exclusive(self, hour, expected):
        when = datetime(2026, 8, 29, hour, 30, tzinfo=TIMEZONE)
        assert within_active_hours((7, 18), when) is expected

    def test_a_utc_instant_is_judged_in_local_terms(self):
        # 23:00 UTC is 18:00 Chicago in CDT -- outside the window, even though
        # the UTC hour looks like the middle of the night.
        when = datetime(2026, 8, 29, 23, 0, tzinfo=timezone.utc)
        assert within_active_hours((7, 18), when) is False

    def test_the_1755_case(self):
        # A run may start at 17:55 and must be re-checked before each action:
        # after a 90-180s pause the next one would land past 18:00.
        assert within_active_hours((7, 18), datetime(2026, 8, 29, 17, 55, tzinfo=TIMEZONE))
        assert not within_active_hours((7, 18), datetime(2026, 8, 29, 18, 2, tzinfo=TIMEZONE))


class TestLedgerEpoch:
    """The Jun 1 -> Aug 29 gap is written off, not back-filled.

    Writing it off has a consequence: 153 historic records with nothing recent
    is exactly the shape the staleness rule halts on, so counting history from
    all time would deadlock every run forever — the routine cannot make its
    first ledger entry without sending, and cannot send while the ledger looks
    dead. Scoping "history" to the epoch breaks that honestly.
    """

    def test_counting_history_from_all_time_would_deadlock(self):
        # What the pre-epoch behaviour did: 153 historic, none recent -> halt,
        # on every run, with no way out.
        d = decide_allowance(posted_today=0, per_day=60, per_run=20,
                             ledger_writes_in_window=0, ledger_writes_ever=153,
                             independent_count=None)
        assert d.halted

    def test_scoped_to_the_epoch_the_first_run_proceeds(self):
        # Same portal, same day — but history counted from LEDGER_EPOCH is 0,
        # which is a fresh ledger rather than a dead one. It still needs
        # Unipile to confirm the zero before it may send.
        d = decide_allowance(posted_today=0, per_day=60, per_run=20,
                             ledger_writes_in_window=0, ledger_writes_ever=0,
                             independent_count=0)
        assert not d.halted and d.allowance == 20

    def test_the_standard_applies_again_from_the_second_run(self):
        # Once post-epoch writes exist, silence is a fault once more.
        d = decide_allowance(posted_today=0, per_day=60, per_run=20,
                             ledger_writes_in_window=0, ledger_writes_ever=8,
                             independent_count=None)
        assert d.halted

    def test_epoch_is_a_date_not_a_datetime(self):
        from qbs_linkedin.ledger import LEDGER_EPOCH
        assert isinstance(LEDGER_EPOCH, date)
