"""LinkedIn URL canonicalization.

``linkedin_profile_url__unique_value`` is the portal's dedupe key. Because it
is a URL rather than an ID, the unique constraint only fires on an EXACT string
match -- so a differently-formatted write for the same person creates precisely
the duplicate the property exists to prevent.

Measured over a 2,000-contact live sample (2026-08-29):

===============  =========================================  ==========
scheme           https on 100%                              consistent
trailing slash   absent on 100%                             consistent
query string     absent on 100%                             consistent
case             all lowercase                              consistent
host             linkedin.com 94.9% / www.linkedin.com 5.1%  **SPLIT**
===============  =========================================  ==========

Same slug already stored in two host forms: 0 pairs. So no duplicates exist
yet, but ~1 in 20 records is in the minority form and any new write in the
other form manufactures one.

The dedupe mechanism is HubSpot's ``idProperty`` lookup, and it is BYTE-EXACT.
Verified live against contact 251 (Clark Peterson), whose stored value is
``https://linkedin.com/in/clarkpeterson1``::

    GET /crm/v3/objects/contacts/{url}?idProperty=linkedin_profile_url__unique_value

    https://linkedin.com/in/clarkpeterson1       -> 200 FOUND (id 251)
    https://www.linkedin.com/in/clarkpeterson1   -> 404 MISS
    https://linkedin.com/in/clarkpeterson1/      -> 404 MISS
    https://linkedin.com/in/ClarkPeterson1       -> 404 MISS

On an upsert, every one of those 404s becomes a CREATE. So the unique property
prevents duplicates only for values already in the exact stored form; this
module is what guarantees that. It is not a replacement for the unique key --
it is the guard that makes the unique key actually fire.

A second, separate hazard: a unique constraint enforces "one contact per URL",
so it dedupes a WRONG value just as confidently as a right one. Writing a
relative's URL into the key does not create a duplicate; it permanently binds
the wrong identity to the record. That is what :func:`choose_profile_url`
guards, and why it skips rather than guesses.
"""

from __future__ import annotations

import re

#: The portal's dominant stored form (94.9% of records). Match it exactly.
#: Canonicalizing to the "more correct" www form would fail to match 94.9% of
#: existing data, which is the bug rather than the fix.
CANONICAL_PREFIX = "https://linkedin.com/in/"

_SLUG_RE = re.compile(r"/in/([^/?#]+)")

#: UTF-8 bytes decoded as Latin-1 and re-encoded. Present in live data:
#:   "hervã©-amar-24722650"  should be "hervé-amar-24722650"
#:   "renã©-logans-0a5561102"          "rené-logans-0a5561102"
#: A mojibake slug can never match the real profile, so it breaks lookups AND
#: guarantees a duplicate on the next write.
_MOJIBAKE_RE = re.compile("[ÃãÂâ][ -¿©®]")


class UrlError(ValueError):
    """The value is not a usable LinkedIn profile URL."""


def extract_slug(url: str | None) -> str | None:
    """Pull the vanity slug out of any LinkedIn profile URL form."""
    if not url:
        return None
    match = _SLUG_RE.search(url.strip())
    return match.group(1).lower() if match else None


def looks_mojibake(value: str | None) -> bool:
    """True if the string shows double-encoded UTF-8."""
    return bool(value) and bool(_MOJIBAKE_RE.search(value))


def canonical_url(url: str | None) -> str:
    """Normalize to the portal's stored form so the unique key actually matches.

    Raises :class:`UrlError` rather than returning something almost-right: a
    wrong upsert key silently creates a duplicate, so failing loudly is cheaper.
    """
    slug = extract_slug(url)
    if not slug:
        raise UrlError(f"No /in/<slug> segment in {url!r}")
    if looks_mojibake(slug):
        raise UrlError(
            f"Slug {slug!r} appears to be double-encoded UTF-8. Repair the "
            "source value; writing it would create an unmatchable record."
        )
    return CANONICAL_PREFIX + slug


def same_profile(a: str | None, b: str | None) -> bool:
    """Do two URLs refer to the same profile, ignoring host and scheme form?"""
    slug_a, slug_b = extract_slug(a), extract_slug(b)
    return bool(slug_a) and slug_a == slug_b


#: Shortened first names accepted when checking a slug against a contact name.
NICKNAMES = {
    "chuck": "charles", "mike": "michael", "bob": "robert", "danny": "daniel",
    "zach": "zachary", "ken": "kenneth", "bill": "william", "jim": "james",
    "dave": "david", "rick": "richard", "steve": "steven", "tom": "thomas",
    "dick": "richard", "nan": "nancy", "pat": "patrick", "greg": "gregory",
}


def slug_matches_name(
    slug: str | None,
    firstname: str | None,
    lastname: str | None = None,
) -> bool:
    """Does a vanity slug plausibly belong to this person?

    This is the guard that catches bad enrichment matches. Live data holds
    contacts whose two LinkedIn URL properties point at DIFFERENT PEOPLE --
    usually a relative matched on surname::

        Jim Becker      -> hs_linkedin_url  margie-becker-267034a
        Nan Strohmaier  -> hs_linkedin_url  alec-strohmaier-411a915
        Froy C. Perez   -> hs_linkedin_url  elvira-perez-5640b1227
        Patrick Kelley  -> unique_value     virginia-kelley-5223b563

    1.3% of sampled contacts carry such a conflict. Messaging one of them
    sends a cold pitch addressed to Jim to his relative Margie, as Shawn.
    Note the Patrick Kelley row: the *unique* property is the wrong one there,
    so neither field is reliably authoritative and both must be checked.

    Two acceptance rules:

    1. The slug contains the first name, or a nickname of it.
    2. The slug contains the surname AND begins with the first initial.
       This admits initial-style slugs like ``pmkelley`` for Patrick Kelley,
       which rule 1 alone rejects -- a first-name-only check silently drops
       every prospect who uses that (common) slug style. It still rejects
       every relative case above, because ``margie-becker`` does not begin
       with ``j``, ``alec-strohmaier`` does not begin with ``n``, and
       ``virginia-kelley`` does not begin with ``p``.
    """
    if not slug:
        return False
    first = (firstname or "").strip().lower()
    last = (lastname or "").strip().lower()
    if not first and not last:
        return False

    if first:
        alts = {first, NICKNAMES.get(first, first)}
        alts |= {short for short, full in NICKNAMES.items() if full == first}
        if any(alt and alt in slug for alt in alts):
            return True

    if last and first and last in slug and slug.startswith(first[0]):
        return True

    # A bare-surname slug ("grahl" for Mike Grahl) is a real and common style.
    # Requiring the first initial rejects it, and rejecting it drops a valid
    # prospect. Exact equality only -- "becker" alone would pass here, but a
    # relative case is always "margie-becker", never bare.
    if last and slug == last:
        return True

    return False


def choose_profile_url(
    unique_value: str | None,
    hs_url: str | None,
    firstname: str | None,
    lastname: str | None = None,
) -> tuple[str | None, str | None]:
    """Pick the trustworthy LinkedIn URL for a contact.

    Returns ``(url, problem)``. When the two stored URLs disagree about who
    the person is, returns ``(None, reason)`` so the caller SKIPS rather than
    guessing -- 1.3% of contacts have a conflict, and guessing wrong means
    messaging someone else's relative under Shawn's name.
    """
    slug_u, slug_h = extract_slug(unique_value), extract_slug(hs_url)

    if not slug_u and not slug_h:
        return None, "no LinkedIn URL on the contact"
    if slug_u and slug_h and slug_u != slug_h:
        # A corrupted slug can never match the real profile, so if exactly one
        # side is mojibake the other is simply the answer. Live case:
        # Helen Pina, stored as "helen-piã±a-7b83773" vs a clean "helenpina".
        mojibake_u, mojibake_h = looks_mojibake(slug_u), looks_mojibake(slug_h)
        if mojibake_u and not mojibake_h:
            return canonical_url(hs_url), None
        if mojibake_h and not mojibake_u:
            return canonical_url(unique_value), None

        ok_u = slug_matches_name(slug_u, firstname, lastname)
        ok_h = slug_matches_name(slug_h, firstname, lastname)
        if ok_u and not ok_h:
            return canonical_url(unique_value), None
        if ok_h and not ok_u:
            return canonical_url(hs_url), None
        if ok_u and ok_h:
            # Both plausibly this person -- usually one vanity slug and one
            # auto-generated ("shivani-chakravarthy-130138197" vs
            # "shivanich"). Not a wrong-person conflict, so take the unique
            # property: it is the dedupe key, and skipping here would drop a
            # valid prospect over a cosmetic difference.
            return canonical_url(unique_value), None
        return None, (
            f"conflicting LinkedIn URLs ({slug_u} vs {slug_h}) and neither "
            "matches the contact's name"
        )

    winner = unique_value or hs_url
    if not slug_matches_name(extract_slug(winner), firstname, lastname):
        return None, f"slug {extract_slug(winner)!r} does not match first name"
    return canonical_url(winner), None
