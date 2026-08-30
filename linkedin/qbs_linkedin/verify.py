"""The Reading Rule — employment verification from dated work experience.

QBS doctrine, established by the August 2026 list-5243 project: **dated work
experience is the source of truth; headlines are unreliable.**

The dangerous failure here is not getting a verdict wrong — it is fabricating
one. ``GET /users/{id}`` without ``linkedin_sections=experience`` returns
HTTP 200 with **no ``work_experience`` key at all**. A parser that maps "no
current role matches" to ``no`` would then write "No Longer with Company"
across every contact it touched, from one missing query parameter. So a
missing key raises :class:`InstrumentError` and is never a verdict.

Field reliability, measured across real profiles: only ``company``,
``position``, ``start`` and ``end`` are dependable. ``id``, ``company_id``,
``status`` and ``location`` are absent on many entries. Dates are US-format
strings (``"2/1/2020"``), not ISO. Entries are **not** in chronological order,
so anything taking ``work_experience[0]`` as the current role is right only by
accident.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

from .config import (
    COMPANY_SUFFIXES,
    SENIOR_TITLE_TOKENS,
    VERDICT_MOVED,
    VERDICT_NO,
    VERDICT_NO_PROFILE,
    VERDICT_UNREADABLE,
    VERDICT_YES,
)


class InstrumentError(RuntimeError):
    """The reading apparatus failed. This is never a verdict about a person."""


_PUNCT = re.compile(r"[^\w\s]")
_WS = re.compile(r"\s+")


def normalize_company(name: str | None) -> str:
    """Lowercase, strip punctuation, drop legal suffixes.

    "Acme Corporation" and "Acme, Inc." both become "acme".
    """
    if not name:
        return ""
    text = _WS.sub(" ", _PUNCT.sub(" ", name.lower())).strip()
    changed = True
    while changed:
        changed = False
        for suffix in COMPANY_SUFFIXES:
            if text.endswith(" " + suffix):
                text = text[: -len(suffix) - 1].strip()
                changed = True
    return text


def companies_match(a: str | None, b: str | None) -> bool:
    """Do two company names refer to the same employer?

    Containment either way, because LinkedIn and the CRM disagree on how much
    of a name to store ("Xactly" vs "Xactly Corp (acquired by Vista)").
    Guarded by a length floor: a two-character containment match would pair
    almost anything.
    """
    na, nb = normalize_company(a), normalize_company(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if min(len(na), len(nb)) < 4:
        return False
    return na in nb or nb in na


def parse_li_date(value: str | None) -> date | None:
    """Parse LinkedIn's US-format date string.

    Returns None rather than raising: an unparseable date is a reason to treat
    a profile as unreadable, never to call someone a mover.
    """
    if not value or not isinstance(value, str):
        return None
    for fmt in ("%m/%d/%Y", "%m/%Y", "%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


@dataclass(frozen=True)
class Role:
    company: str
    position: str
    start: date | None
    end: date | None
    #: The raw `end` string when one was present but unparseable. LinkedIn
    #: emits forms `parse_li_date` does not accept ("Jan 2023"), and an
    #: absent end and an unreadable end mean opposite things: the first says
    #: "still there", the second says "we do not know".
    end_raw: str | None = None

    @property
    def end_unreadable(self) -> bool:
        return self.end is None and self.end_raw is not None

    @property
    def is_current(self) -> bool:
        # An unreadable end must NEVER read as current. Doing so reported a
        # role that finished three years ago as the person's present job,
        # with a fabricated tenure and an evidence string asserting
        # "no end date" as fact.
        return self.end is None and not self.end_unreadable

    @property
    def is_senior(self) -> bool:
        return any(tok in self.position.lower() for tok in SENIOR_TITLE_TOKENS)


def _rank(role: Role) -> tuple[int, date]:
    """Sort key for choosing someone's primary job among several current ones.

    Seniority first, then most recent start. A board seat held since 2018
    must not outrank a CRO role started last year simply by appearing first
    in the array -- `work_experience` is not in chronological order.
    """
    return (1 if role.is_senior else 0, role.start or date.min)


def choose_destination(current: tuple[Role, ...]) -> tuple[Role | None, bool]:
    """The role that best represents where someone works now.

    Returns (role, ambiguous). `ambiguous` is True when the top two cannot be
    told apart, which is a queue-for-a-human signal rather than a reason to
    pick one: a `moved` verdict drives re-association, so guessing here binds
    the CRM record to the wrong employer.
    """
    if not current:
        return None, False
    ranked = sorted(current, key=_rank, reverse=True)
    best = ranked[0]
    ambiguous = len(ranked) > 1 and _rank(ranked[1]) == _rank(best)
    return best, ambiguous


def read_roles(profile: dict) -> list[Role]:
    """Extract roles, tolerating every optional field.

    Raises InstrumentError when the section is absent — that means the request
    omitted ``linkedin_sections=experience``, not that the person has no job.
    """
    if "work_experience" not in profile:
        raise InstrumentError(
            "profile has no work_experience key — the request almost certainly "
            "omitted linkedin_sections=experience. This is an instrument "
            "failure and must not be scored as a verdict."
        )
    entries = profile.get("work_experience") or []
    return [
        Role(
            company=(entry.get("company") or "").strip(),
            position=(entry.get("position") or "").strip(),
            start=parse_li_date(entry.get("start")),
            end=parse_li_date(entry.get("end")),
            end_raw=(entry.get("end")
                     if entry.get("end") and parse_li_date(entry.get("end")) is None
                     else None),
        )
        for entry in entries
        if entry.get("company")
    ]


@dataclass(frozen=True)
class Verification:
    verdict: str
    evidence: str
    matched_role: Role | None = None
    tenure_years: float | None = None
    tenure_confident: bool = True
    current_roles: tuple[Role, ...] = field(default_factory=tuple)
    #: The role this person appears to hold now, used as the re-association
    #: target on a `moved` verdict.
    destination: Role | None = None
    #: True when the destination could not be told apart from another current
    #: role. Queue these; never re-associate on a coin flip.
    destination_ambiguous: bool = False


def verify_employment(
    profile: dict,
    hubspot_company: str | None,
    today: date | None = None,
) -> Verification:
    """Apply the Reading Rule.

    Senior people routinely hold several current roles at once — an operating
    job plus board seats — so the current-role set is a SET, never just the
    first entry.
    """
    roles = read_roles(profile)  # raises InstrumentError if the section is absent
    today = today or date.today()

    if not roles:
        return Verification(
            VERDICT_NO_PROFILE,
            "profile carries no dated work history",
        )

    current = tuple(r for r in roles if r.is_current)

    # An end date we could not read on the very employer being checked means
    # we cannot say whether they are still there. That is an unreadable
    # profile, not a finding -- the same rule as a missing section.
    if hubspot_company:
        unreadable = next(
            (r for r in roles
             if r.end_unreadable and companies_match(r.company, hubspot_company)),
            None,
        )
        if unreadable:
            return Verification(
                VERDICT_UNREADABLE,
                f"role at '{unreadable.company}' carries an end date LinkedIn "
                f"returned as {unreadable.end_raw!r}, which could not be "
                "parsed — cannot tell whether it is current",
                current_roles=current,
            )

    if not hubspot_company:
        return Verification(
            VERDICT_UNREADABLE,
            "no company on the CRM record to compare against",
            current_roles=current,
        )

    matched = next(
        (r for r in current if companies_match(r.company, hubspot_company)), None
    )
    if matched:
        tenure, confident = _tenure(roles, matched, today)
        return Verification(
            VERDICT_YES,
            f"current role '{matched.position}' at '{matched.company}' "
            f"(from {matched.start or 'unknown'}, no end date)",
            matched_role=matched,
            tenure_years=tenure,
            tenure_confident=confident,
            current_roles=current,
        )

    # Company appears, but the role has ended -> they moved on.
    past = next(
        (r for r in roles if not r.is_current
         and companies_match(r.company, hubspot_company)), None
    )
    if past:
        dest, ambiguous = choose_destination(current)
        return Verification(
            VERDICT_MOVED if dest else VERDICT_NO,
            f"role at '{past.company}' ended {past.end}"
            + (f"; now at '{dest.company}' ({dest.position})" if dest
               else "; no current role listed")
            + ("; SEVERAL current roles rank equally — destination needs a "
               "human before re-associating" if ambiguous else ""),
            current_roles=current,
            destination=dest,
            destination_ambiguous=ambiguous,
        )

    if not current:
        return Verification(
            VERDICT_NO,
            "no current role listed and the CRM company does not appear in "
            "their history",
            current_roles=current,
        )

    # The CRM company is nowhere in a readable history. They are employed
    # elsewhere, so this is a move rather than an unreadable profile.
    dest, ambiguous = choose_destination(current)
    return Verification(
        VERDICT_MOVED,
        f"CRM company '{hubspot_company}' absent from history; currently at "
        f"'{dest.company}' ({dest.position})"
        + ("; SEVERAL current roles rank equally — destination needs a human "
           "before re-associating" if ambiguous else ""),
        current_roles=current,
        destination=dest,
        destination_ambiguous=ambiguous,
    )


def _tenure(
    roles: list[Role], matched: Role, today: date
) -> tuple[float | None, bool]:
    """Years at the matched employer.

    Measured from the EARLIEST start at that employer, not the matched role's
    own start, so an internal promotion does not reset the clock. Marked
    low-confidence when roles at that employer overlap, which LinkedIn data
    does often: one real profile carries three overlapping roles at the same
    company, so any naive sum is wrong.
    """
    same_employer = [
        r for r in roles if companies_match(r.company, matched.company) and r.start
    ]
    if not same_employer:
        return None, False

    earliest = min(r.start for r in same_employer)
    years = round((today - earliest).days / 365.25, 1)

    overlapping = False
    dated = sorted(same_employer, key=lambda r: r.start)
    for prev, nxt in zip(dated, dated[1:]):
        prev_end = prev.end or today
        if nxt.start < prev_end:
            overlapping = True
            break

    return years, not overlapping
