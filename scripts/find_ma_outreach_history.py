#!/usr/bin/env python3
"""Reconstruct the full HubSpot Partner M&A outreach history from the CRM.

The M&A outreach went out as HubSpot email campaigns, so the portal holds the
authoritative recipient list. This pages every email whose subject matches a
known campaign, then separates the one-way blasts from contacts who actually
engaged - a reply is the signal worth acting on, not the send.

Read-only.

Usage:
    export QBS_HUBSPOT_TOKEN=pat-na1-...
    python3 scripts/find_ma_outreach_history.py
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.hubapi.com"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTNERS = os.path.join(REPO, "data", "hubspot_partners.csv")
OUT = os.path.join(REPO, "data", "ma_outreach_history.csv")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from domainutil import registrable_domain  # noqa: E402

# Subject tokens that identify the M&A campaigns. Kept broad because the
# December send has a typo ("Acquisiton") and later one-to-one follow-ups drop
# the "HubSpot Partner" prefix entirely.
SUBJECT_TOKENS = ["M & A", "M &", "merger", "acquisiton", "acquisition"]

# A subject must contain one of these to count as M&A outreach, filtering out
# unrelated hits like "client acquisition" prospecting copy.
def is_ma_subject(subject: str) -> bool:
    s = (subject or "").lower()
    if "partner m & a" in s or "partner merger" in s:
        return True
    if "hubspot m & a" in s or "hubspot - m & a" in s:
        return True
    # one-to-one follow-ups
    return ("m & a" in s or "m&a" in s) and "client" not in s


def post(token: str, path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    for attempt in range(6):
        req = urllib.request.Request(
            f"{API}{path}", data=data, method="POST",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()[:200]
            if exc.code in (429, 500, 502, 503, 504):
                time.sleep(min(2 ** attempt, 20))
                continue
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError):
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError("gave up")


def search_emails(token: str, kw: str) -> list[dict]:
    """Page every email whose subject contains kw."""
    out, after = [], None
    while True:
        body = {
            "limit": 100,
            "filterGroups": [{"filters": [
                {"propertyName": "hs_email_subject",
                 "operator": "CONTAINS_TOKEN", "value": kw}]}],
            "properties": ["hs_email_subject", "hs_timestamp",
                           "hs_email_direction", "hs_email_to_email",
                           "hs_email_from_email", "hs_email_status"],
            "sorts": [{"propertyName": "hs_timestamp", "direction": "ASCENDING"}],
        }
        if after:
            body["after"] = after
        page = post(token, "/crm/v3/objects/emails/search", body)
        out.extend(page.get("results", []))
        after = page.get("paging", {}).get("next", {}).get("after")
        print(f"    {kw!r}: {len(out)}", end="\r", flush=True)
        if not after:
            break
        time.sleep(0.12)
    return out


def main() -> int:
    token = os.environ.get("QBS_HUBSPOT_TOKEN", "")
    if not token:
        print("set QBS_HUBSPOT_TOKEN", file=sys.stderr)
        return 1

    partners = {}
    for r in csv.DictReader(open(PARTNERS, encoding="utf-8-sig")):
        if r["domain"]:
            partners[r["domain"]] = r

    emails: dict[str, dict] = {}
    for kw in SUBJECT_TOKENS:
        for e in search_emails(token, kw):
            emails[e["id"]] = e
    print(f"\nemails whose subject matched any token: {len(emails)}")

    ma = [e for e in emails.values()
          if is_ma_subject(e["properties"].get("hs_email_subject"))]
    print(f"of those, genuinely M&A outreach: {len(ma)}")

    # Group by campaign (subject + send date) and by counterparty domain.
    people: dict[str, dict] = {}
    campaigns: dict[str, int] = {}
    for e in ma:
        p = e["properties"]
        subj = (p.get("hs_email_subject") or "").strip()
        when = (p.get("hs_timestamp") or "")[:10]
        direction = p.get("hs_email_direction") or ""
        campaigns[f"{when}  {subj}"] = campaigns.get(f"{when}  {subj}", 0) + 1

        # Outbound: counterparty is the recipient. Inbound: the sender.
        addr = (p.get("hs_email_to_email") if direction != "INCOMING_EMAIL"
                else p.get("hs_email_from_email")) or ""
        addr = addr.split(";")[0].strip().lower()
        if not addr or "thequantumleap.business" in addr:
            continue
        dom = registrable_domain(addr.split("@")[-1])
        rec = people.setdefault(addr, {
            "email": addr, "domain": dom, "sends": 0, "replies": 0,
            "first_touch": when, "last_touch": when, "subjects": set()})
        rec["subjects"].add(subj)
        rec["last_touch"] = max(rec["last_touch"], when)
        rec["first_touch"] = min(rec["first_touch"], when)
        if direction == "INCOMING_EMAIL":
            rec["replies"] += 1
        else:
            rec["sends"] += 1

    print("\n=== campaigns ===")
    for k, v in sorted(campaigns.items()):
        print(f"  {k[:72]:72s} {v:>4} emails")

    rows = []
    for rec in people.values():
        pr = partners.get(rec["domain"])
        rows.append({
            "email": rec["email"],
            "domain": rec["domain"],
            "is_directory_partner": "YES" if pr else "no",
            "partner_company": pr["company_name"] if pr else "",
            "tier": (pr["tier"] or "untiered") if pr else "",
            "country": pr["country"] if pr else "",
            "review_count": pr["review_count"] if pr else "",
            "replied": "YES" if rec["replies"] else "no",
            "sends": rec["sends"],
            "replies": rec["replies"],
            "first_touch": rec["first_touch"],
            "last_touch": rec["last_touch"],
            "subjects": " | ".join(sorted(rec["subjects"]))[:200],
            "directory_url": pr["directory_url"] if pr else "",
        })

    rank = {"elite": 0, "diamond": 1, "platinum": 2, "gold": 3, "untiered": 4, "": 5}
    rows.sort(key=lambda r: (r["replied"] != "YES",
                             r["is_directory_partner"] != "YES",
                             rank.get(r["tier"], 5),
                             -int(r["review_count"] or 0)))
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    prs = [r for r in rows if r["is_directory_partner"] == "YES"]
    rep = [r for r in rows if r["replied"] == "YES"]
    print(f"\nwrote {OUT}")
    print(f"  distinct people approached about M&A   {len(rows)}")
    print(f"    confirmed directory partners         {len(prs)}")
    print(f"    who replied                          {len(rep)}")
    tiers: dict[str, int] = {}
    for r in prs:
        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    print("  partner tier spread: " + ", ".join(
        f"{k}={v}" for k, v in sorted(tiers.items(), key=lambda kv: rank.get(kv[0], 9))))
    if rep:
        print("\n=== replied to M&A outreach ===")
        for r in rep:
            print(f"  {r['email'][:40]:40s} {r['partner_company'][:24]:24s} "
                  f"{r['tier']:9s} {r['first_touch']} -> {r['last_touch']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
