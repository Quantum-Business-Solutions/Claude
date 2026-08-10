#!/usr/bin/env python3
"""Build ZoomInfo company-list upload files for M&A decision-maker sourcing.

ZoomInfo's platform list-build costs fewer credits per contact than API
enrichment and pushes straight into HubSpot through the native integration, so
the workflow is: upload domains here -> filter to Head of Organization titles ->
preview credit cost -> redeem -> push.

Excludes companies that already have an owner/CEO/president contact in HubSpot
and the 83 already enriched, so no credit is spent twice. Flags companies that
have already received M&A outreach so they can be paced rather than re-blasted.

Usage:
    python3 scripts/build_zoominfo_upload.py
"""

from __future__ import annotations

import csv
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(REPO, "data")

DM_TITLES = ("owner", "founder", "president", "ceo", "chief executive",
             "principal", "partner", "chairman")


def load(name: str) -> list[dict]:
    path = os.path.join(D, name)
    if not os.path.exists(path):
        return []
    return list(csv.DictReader(open(path, encoding="utf-8-sig")))


def main() -> None:
    partners = load("hubspot_partners.csv")
    contacts = load("partner_contacts.csv")
    enriched = load("acquisition_decision_makers.csv")
    history = load("ma_outreach_history.csv")

    have_dm = {c["partner_domain"] for c in contacts
               if any(t in (c["job_title"] or "").lower() for t in DM_TITLES)}
    already = {e["domain"] for e in enriched}
    pitched = {h["domain"]: h for h in history if h["domain"]}

    stages = {
        "diamond_platinum": ("diamond", "platinum"),
        "all_dpg": ("diamond", "platinum", "gold"),
    }
    for label, tiers in stages.items():
        rows = []
        for p in partners:
            if p["tier"] not in tiers or not p["domain"]:
                continue
            if p["domain"] in have_dm or p["domain"] in already:
                continue  # already covered - do not spend credits again
            h = pitched.get(p["domain"])
            rows.append({
                "domain": p["domain"],
                "company_name": p["company_name"],
                "tier": p["tier"],
                "country": p["country"],
                "state": p["state"],
                "city": p["city"],
                "review_count": p["review_count"],
                "rating": p["rating"],
                "accreditations": p["accreditations"],
                "website": p["website"],
                "previously_pitched_ma": "YES" if h else "no",
                "previously_replied": h["replied"] if h else "",
                "directory_url": p["directory_url"],
            })
        rank = {"diamond": 0, "platinum": 1, "gold": 2}
        rows.sort(key=lambda r: (rank[r["tier"]], -int(r["review_count"] or 0)))
        out = os.path.join(D, f"zoominfo_upload_{label}.csv")
        with open(out, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        pitched_n = sum(1 for r in rows if r["previously_pitched_ma"] == "YES")
        print(f"wrote {os.path.basename(out)}: {len(rows)} domains "
              f"({pitched_n} already pitched at least once)")


if __name__ == "__main__":
    main()
