#!/usr/bin/env python3
"""Match the HubSpot partner directory export against a HubSpot portal's companies.

Answers "how many of these partners do we already have as company records?" by
comparing registrable domains, which is the only reliable join key — partner
company names in the directory are marketing strings ("Bluleadz | GTM Strategy
& HubSpot Implementation"), not legal or CRM names.

Reads the token from $QBS_HUBSPOT_TOKEN (or --token). Read-only: this script
issues no writes.

Usage:
    export QBS_HUBSPOT_TOKEN=pat-na1-...
    python3 scripts/match_partners_to_hubspot.py
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.hubapi.com"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
PARTNERS_CSV = os.path.join(DATA_DIR, "hubspot_partners.csv")

# Portal dump lives outside the repo: it is QBS CRM data, not a deliverable.
SCRATCH = os.environ.get("SCRATCH_DIR", "/tmp")
COMPANIES_CACHE = os.path.join(SCRATCH, "qbs_companies.jsonl")

MATCHED_CSV = os.path.join(DATA_DIR, "partners_matched_in_hubspot.csv")
MISSING_CSV = os.path.join(DATA_DIR, "partners_missing_from_hubspot.csv")

# Multi-part public suffixes we care about, so "foo.co.uk" keeps two labels.
TWO_LABEL_SUFFIXES = {
    "co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au", "org.au",
    "co.nz", "com.br", "com.mx", "co.za", "co.jp", "or.jp", "ne.jp",
    "co.in", "com.sg", "com.tr", "com.ar", "com.co", "co.il", "com.hk",
}

# Hosts that are never a company's own identity.
GENERIC_HOSTS = {
    "hubspot.com", "www.hubspot.com", "sites.google.com", "google.com",
    "facebook.com", "linkedin.com", "wixsite.com", "squarespace.com",
    "wordpress.com", "godaddysites.com", "myshopify.com", "webflow.io",
    "github.io", "notion.site", "carrd.co", "framer.website",
}


def registrable_domain(value: str) -> str:
    """Reduce a URL or host to its registrable domain, or '' if unusable."""
    if not value:
        return ""
    raw = value.strip().lower()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "http://" + raw
    try:
        host = urllib.parse.urlsplit(raw).hostname or ""
    except ValueError:
        return ""
    host = host.rstrip(".")
    if not host or "." not in host:
        return ""
    # Strip common leading noise.
    host = re.sub(r"^(www|www\d|ww2|web|info|en|us|m)\.", "", host)
    if host in GENERIC_HOSTS:
        return ""
    labels = host.split(".")
    if len(labels) >= 3 and ".".join(labels[-2:]) in TWO_LABEL_SUFFIXES:
        host = ".".join(labels[-3:])
    elif len(labels) > 2:
        host = ".".join(labels[-2:])
    if host in GENERIC_HOSTS:
        return ""
    return host


# --------------------------------------------------------------------------- #
# portal dump
# --------------------------------------------------------------------------- #

def hs_get(token: str, path: str, params: dict) -> dict:
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(6):
        req = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {token}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 429 or exc.code >= 500:
                time.sleep(min(2**attempt, 20))
                continue
            raise RuntimeError(f"HTTP {exc.code}: {exc.read()[:300]!r}") from exc
        except (urllib.error.URLError, TimeoutError):
            time.sleep(min(2**attempt, 20))
    raise RuntimeError(f"giving up on {path}")


def dump_companies(token: str) -> list[dict]:
    """Page every company record, caching to disk so re-runs are instant."""
    if os.path.exists(COMPANIES_CACHE):
        with open(COMPANIES_CACHE, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        print(f"companies: {len(rows)} loaded from cache")
        return rows

    rows: list[dict] = []
    after: str | None = None
    props = "name,domain,website,hs_object_id,lifecyclestage,createdate"

    with open(COMPANIES_CACHE, "w", encoding="utf-8") as fh:
        while True:
            params = {"limit": 100, "properties": props, "archived": "false"}
            if after:
                params["after"] = after
            page = hs_get(token, "/crm/v3/objects/companies", params)
            for obj in page.get("results", []):
                p = obj.get("properties", {})
                rec = {
                    "id": obj.get("id"),
                    "name": p.get("name") or "",
                    "domain": p.get("domain") or "",
                    "website": p.get("website") or "",
                    "lifecyclestage": p.get("lifecyclestage") or "",
                    "createdate": (p.get("createdate") or "")[:10],
                }
                rows.append(rec)
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            paging = page.get("paging", {}).get("next", {})
            after = paging.get("after")
            print(f"  companies: {len(rows)}", end="\r", flush=True)
            if not after:
                break
            # STANDARD private apps allow 100 requests / 10s. Stay well under.
            time.sleep(0.12)

    print(f"  companies: {len(rows)} fetched")
    return rows


# --------------------------------------------------------------------------- #
# matching
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=os.environ.get("QBS_HUBSPOT_TOKEN", ""))
    args = ap.parse_args()
    if not args.token:
        print("no token: set QBS_HUBSPOT_TOKEN or pass --token", file=sys.stderr)
        return 1

    partners = list(csv.DictReader(open(PARTNERS_CSV, encoding="utf-8-sig")))
    print(f"partners: {len(partners)}")

    companies = dump_companies(args.token)

    # Index the portal by registrable domain. A domain can map to several
    # records - that duplication is itself a finding.
    portal: dict[str, list[dict]] = {}
    for comp in companies:
        for source in (comp["domain"], comp["website"]):
            dom = registrable_domain(source)
            if dom:
                portal.setdefault(dom, []).append(comp)
                break

    print(f"portal companies with a usable domain: "
          f"{sum(len(v) for v in portal.values())} across {len(portal)} domains")

    matched, missing, no_domain = [], [], []
    for row in partners:
        dom = registrable_domain(row["website"])
        if not dom:
            no_domain.append(row)
            continue
        hits = portal.get(dom)
        if hits:
            best = hits[0]
            matched.append({
                "partner_company": row["company_name"],
                "domain": dom,
                "tier": row["tier"],
                "country": row["country"],
                "review_count": row["review_count"],
                "hs_company_id": best["id"],
                "hs_company_name": best["name"],
                "hs_lifecyclestage": best["lifecyclestage"],
                "hs_created": best["createdate"],
                "hs_duplicate_records": len(hits),
                "directory_url": row["directory_url"],
            })
        else:
            missing.append({
                "partner_company": row["company_name"],
                "domain": dom,
                "tier": row["tier"],
                "country": row["country"],
                "review_count": row["review_count"],
                "rating": row["rating"],
                "accreditations": row["accreditations"],
                "services": row["services"],
                "directory_url": row["directory_url"],
                "website": row["website"],
            })

    def write(path: str, rows: list[dict]) -> None:
        if not rows:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {path} ({len(rows)} rows)")

    # Most valuable prospects first.
    tier_rank = {"elite": 0, "diamond": 1, "platinum": 2, "gold": 3, "": 4}
    missing.sort(key=lambda r: (tier_rank.get(r["tier"], 4),
                                -int(r["review_count"] or 0)))
    matched.sort(key=lambda r: (tier_rank.get(r["tier"], 4),
                                -int(r["review_count"] or 0)))
    write(MATCHED_CSV, matched)
    write(MISSING_CSV, missing)

    print("\n--- result ---")
    total = len(partners)
    print(f"partners in directory export      {total}")
    print(f"  already in HubSpot (by domain)  {len(matched)} "
          f"({100*len(matched)//total}%)")
    print(f"  not in HubSpot                  {len(missing)} "
          f"({100*len(missing)//total}%)")
    print(f"  unusable/blank website          {len(no_domain)}")

    dupes = [m for m in matched if m["hs_duplicate_records"] > 1]
    print(f"\nmatched partners hitting >1 company record: {len(dupes)}")

    print("\nmatch rate by tier:")
    for tier in ("elite", "diamond", "platinum", "gold", ""):
        p = [r for r in partners if r["tier"] == tier]
        if not p:
            continue
        m = [r for r in matched if r["tier"] == tier]
        label = tier or "(untiered)"
        pct = 100 * len(m) // len(p) if p else 0
        print(f"  {label:11s} {len(m):>5}/{len(p):<5} ({pct}%)")

    stages: dict[str, int] = {}
    for m in matched:
        key = m["hs_lifecyclestage"] or "(none)"
        stages[key] = stages.get(key, 0) + 1
    print("\nlifecycle stage of matched records:")
    for k, v in sorted(stages.items(), key=lambda kv: -kv[1]):
        print(f"  {k:16s} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
