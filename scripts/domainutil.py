"""Shared domain normalisation for partner-directory matching.

Both the exporter and the CRM matcher must agree exactly on what a company's
domain is, or the match silently produces false positives. This module is the
single source of truth.

Uses tldextract's bundled Public Suffix List snapshot (offline: suffix_list_urls
is empty) rather than a hand-maintained suffix list. A hand-rolled list is the
wrong tool here: missing an entry like "com.ph" or "co.ke" collapses every
company on that suffix into one bucket, which reads as a duplicate cluster and
cross-matches unrelated companies.
"""

from __future__ import annotations

import tldextract

_EXTRACT = tldextract.TLDExtract(suffix_list_urls=())

# Hosts that identify a platform, not a company. Partners sometimes list a
# LinkedIn page, Linktree or site builder as their website. Using these as a
# match key would join every such partner to the same CRM record.
GENERIC_HOSTS = frozenset({
    "hubspot.com",
    # social / link aggregators
    "linkedin.com", "linktr.ee", "facebook.com", "instagram.com", "twitter.com",
    "x.com", "youtube.com", "tiktok.com", "medium.com", "substack.com",
    "beacons.ai", "carrd.co", "bio.link", "about.me",
    # site builders and hosts on shared apex domains
    "wixsite.com", "wix.com", "squarespace.com", "wordpress.com",
    "godaddysites.com", "myshopify.com", "webflow.io", "framer.website",
    "github.io", "notion.site", "notion.so", "weebly.com", "webnode.com",
    "business.site", "sites.google.com", "google.com", "blogspot.com",
    "netlify.app", "vercel.app", "pages.dev", "herokuapp.com",
    "clickfunnels.com", "systeme.io", "hubspotpagebuilder.com",
    # generic mail/registrar parking
    "gmail.com", "outlook.com", "yahoo.com", "hotmail.com",
    "sedo.com", "domain.com",
    # marketplaces / directories
    "upwork.com", "fiverr.com", "clutch.co", "g2.com", "trustpilot.com",
})

# Link shorteners and tracking redirectors. These resolve to the real site, so
# callers should follow the redirect rather than discard the row: several Elite
# partners (Aptitude8, Huble, Fuelius, Avidly) list a hubs.ly CTA link as their
# website, and treating that as their domain collapses them onto one record.
REDIRECT_HOSTS = frozenset({
    "hubs.ly", "hubs.li", "hubs.la", "hsforms.com", "hubspotlinks.com",
    "bit.ly", "tinyurl.com", "ow.ly", "buff.ly", "rebrand.ly", "lnkd.in",
    "t.co", "goo.gl", "cutt.ly", "shorturl.at", "s.hubspot.com",
})


def needs_redirect_resolution(value: str) -> bool:
    """True when the URL is a shortener/tracker whose target must be followed."""
    if not value:
        return False
    raw = value.strip().lower()
    if "://" not in raw:
        raw = "http://" + raw
    try:
        domain = (_EXTRACT(raw).top_domain_under_public_suffix or "").strip(".")
    except Exception:  # noqa: BLE001
        return False
    return domain in REDIRECT_HOSTS


def registrable_domain(value: str) -> str:
    """Return the registrable domain for a URL or host, or '' if unusable.

    Returns '' for platform hosts in GENERIC_HOSTS so callers never treat them
    as an identity. Callers should skip empty results rather than matching them.
    """
    if not value:
        return ""
    raw = value.strip().lower()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "http://" + raw
    try:
        result = _EXTRACT(raw)
    except Exception:  # noqa: BLE001 - malformed input is just unusable
        return ""
    domain = (result.top_domain_under_public_suffix or "").strip(".")
    if not domain or "." not in domain:
        return ""
    if domain in GENERIC_HOSTS:
        return ""
    return domain


def resolve_final_domain(value: str, timeout: int = 15) -> str:
    """Follow redirects on a shortener URL and return the destination domain.

    Returns '' if the link is dead or lands somewhere unusable. Import errors
    matter more than coverage here, so anything ambiguous returns ''.
    """
    import urllib.error
    import urllib.request

    raw = value.strip()
    if "://" not in raw:
        raw = "https://" + raw
    req = urllib.request.Request(
        raw,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; qbs-partner-export/1.0)",
            "Accept": "text/html,*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            final = resp.geturl()
    except urllib.error.HTTPError as exc:
        final = exc.url or ""
    except Exception:  # noqa: BLE001 - dead links are expected
        return ""
    domain = registrable_domain(final)
    # A shortener that redirects to another shortener, or to hubspot.com itself,
    # tells us nothing.
    if not domain or needs_redirect_resolution(final):
        return ""
    return domain


def is_generic(value: str) -> bool:
    """True when the URL points at a platform rather than a company site."""
    if not value:
        return False
    raw = value.strip().lower()
    if "://" not in raw:
        raw = "http://" + raw
    try:
        domain = (_EXTRACT(raw).top_domain_under_public_suffix or "").strip(".")
    except Exception:  # noqa: BLE001
        return False
    return domain in GENERIC_HOSTS
