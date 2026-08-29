"""Send-ledger accounting and the date arithmetic it depends on.

This is the module whose failure costs the most. An undercount reads as spare
capacity, spare capacity authorises more sends, and over-sending is what gets a
LinkedIn account restricted. So every path here fails CLOSED: when the ledger
cannot be trusted, the allowance is zero, not the cap.

TWO KINDS OF HUBSPOT TIMESTAMP, TWO DIFFERENT RULES
---------------------------------------------------
Mixing these up is a silent off-by-one day, and it hides well because it is
only ever wrong by a few hours.

**date** properties (``ai__contact_verified_date``, ``ai__li_last_attempt_date``,
``ai__reassociated_on``, ``ai__verification_issue_on``) store **UTC midnight of
the intended calendar date**. They are a *date*, not an instant. Converting one
to America/Chicago yields 18:00 or 19:00 the PREVIOUS day, so every
"don't re-attempt within N days" guard fires a day early — always in the
direction of re-attempting too soon. Read these with :func:`hubspot_date_to_date`.

**datetime** properties (``hs_createdate``, ``hs_timestamp``,
``hublead_last_linkedin_message_sent_date``) are real instants. Bucketing them
by day is a genuine timezone question and must use Chicago-local midnight
boundaries. Use :func:`chicago_day_bounds`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from .config import TIMEZONE

#: Days without a single ledger write before the ledger is judged dead.
#: All three of this program's logging paths stopped on 2026-06-01 while sends
#: continued, and nobody noticed for twelve weeks. This is the tripwire.
LEDGER_STALE_DAYS = 3

#: How far the independent count may exceed the ledger before a run halts.
#: Unipile's own counts are themselves approximate (``/users/invite/sent``
#: returns pending invitations only, with synthesised timestamps), so a small
#: gap is expected. A large one means the ledger is not recording sends.
RECONCILE_TOLERANCE = 2


# --- Date arithmetic ------------------------------------------------------

def chicago_day_bounds(when: datetime | date | None = None) -> tuple[int, int]:
    """Epoch-ms bounds of one America/Chicago calendar day.

    For bucketing HubSpot **datetime** properties. Handles DST automatically:
    the same local 07:00-18:00 window is 12:00-23:00 UTC in CDT and
    13:00-00:00 UTC in CST, which is why the boundary cannot be hardcoded.
    """
    if when is None:
        local_date = datetime.now(TIMEZONE).date()
    elif isinstance(when, datetime):
        local_date = when.astimezone(TIMEZONE).date()
    else:
        local_date = when

    start = datetime.combine(local_date, time.min, tzinfo=TIMEZONE)
    end = start + timedelta(days=1)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def hubspot_date_to_date(epoch_ms: int | str | None) -> date | None:
    """Read a HubSpot **date** property as the calendar date it means.

    Deliberately UTC, not local. HubSpot stores these at UTC midnight, so
    ``.astimezone(TIMEZONE).date()`` would return the previous day.
    """
    if epoch_ms in (None, ""):
        return None
    return datetime.fromtimestamp(int(epoch_ms) / 1000, tz=timezone.utc).date()


def date_to_hubspot_date(value: date) -> int:
    """Write a calendar date as HubSpot stores one: UTC midnight, epoch ms."""
    return int(
        datetime.combine(value, time.min, tzinfo=timezone.utc).timestamp() * 1000
    )


def days_since(epoch_ms: int | str | None, today: date | None = None) -> int | None:
    """Whole days between a HubSpot date property and today (Chicago)."""
    stored = hubspot_date_to_date(epoch_ms)
    if stored is None:
        return None
    today = today or datetime.now(TIMEZONE).date()
    return (today - stored).days


# --- Cap accounting -------------------------------------------------------

@dataclass(frozen=True)
class CapDecision:
    """How many actions this run may take, and why."""

    allowance: int
    posted_today: int
    reason: str
    halted: bool = False

    def __bool__(self) -> bool:
        return self.allowance > 0


def decide_allowance(
    *,
    posted_today: int,
    per_day: int,
    per_run: int,
    ledger_writes_in_window: int,
    ledger_writes_ever: int,
    independent_count: int | None = None,
    stale_days: int = LEDGER_STALE_DAYS,
    tolerance: int = RECONCILE_TOLERANCE,
) -> CapDecision:
    """Compute this run's allowance, failing closed on every doubt.

    ``independent_count`` is a second opinion from outside the ledger — for
    engagement, Shawn's own comments from Unipile; for outreach, pending
    invitations. When it materially exceeds the ledger, the ledger is not
    recording sends and the run must stop rather than trust a low number.
    """
    # A dead ledger reads zero, and zero reads as full capacity. That is the
    # over-send direction, so it is the one case that must never pass.
    if ledger_writes_ever > 0 and ledger_writes_in_window == 0:
        return CapDecision(
            0, posted_today,
            f"ledger has no write in {stale_days}d but holds "
            f"{ledger_writes_ever:,} historic records — it is not recording. "
            "A zero count here means 'unknown', not 'nothing sent'.",
            halted=True,
        )

    if independent_count is not None and independent_count - posted_today > tolerance:
        return CapDecision(
            0, posted_today,
            f"ledger says {posted_today} today but an independent count says "
            f"{independent_count} (tolerance {tolerance}). The ledger is "
            "missing sends; reconcile before sending more.",
            halted=True,
        )

    if posted_today >= per_day:
        return CapDecision(
            0, posted_today,
            f"daily cap reached ({posted_today}/{per_day})",
        )

    allowance = min(per_run, per_day - posted_today)
    return CapDecision(
        allowance, posted_today,
        f"{allowance} allowed ({posted_today}/{per_day} used today)",
    )


def within_active_hours(
    active_hours: tuple[int, int],
    when: datetime | None = None,
) -> bool:
    """Is it currently inside the local posting window?

    Checked PER ACTION, not once per run: a run starting at 17:55 must not
    place its next comment at 18:02 after a 90-180s pause.
    """
    now = (when or datetime.now(TIMEZONE)).astimezone(TIMEZONE)
    start, end = active_hours
    return start <= now.hour < end
