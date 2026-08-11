#!/usr/bin/env python3
"""Load sourced M&A decision-makers into HubSpot and link them to their partner.

Reads data/ma_decision_makers.csv (whatever produced it - ZoomInfo API, ZoomInfo
platform export, LinkedIn) and upserts each person as a contact keyed on email,
falling back to the unique LinkedIn URL property when no email was found. Then
associates the contact to the partner company that already exists in the portal.

Deliberate choices worth knowing about:

* The flag set here is ma_target, NOT hubspot_partner_contact. The latter is the
  cold-outreach *suppression* list (1,304 contacts), so tagging acquisition
  targets with it would exclude them from the very outreach they were sourced
  for.
* An existing contact's email, first name and last name are never overwritten.
  These records are often ones a human has already corrected; sourced data is
  the weaker claim.
* LinkedIn URNs (/in/ACwAAA...) are rejected. ZoomInfo returns them alongside
  the real vanity URL, and they are not stable identifiers - writing one into a
  unique property poisons the key for that person forever.

Dry run by default. Pass --commit to write.

Usage:
    export QBS_HUBSPOT_TOKEN=pat-na1-...
    python3 scripts/load_ma_contacts_to_hubspot.py                # preview
    python3 scripts/load_ma_contacts_to_hubspot.py --create-props --commit
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hubspot_api import HubSpotError, batched, call, search_all  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(REPO, "data", "ma_decision_makers.csv")
PREVIEW = os.path.join(REPO, "data", "ma_load_preview.csv")
REJECTS = os.path.join(REPO, "data", "ma_load_rejects.csv")

LINKEDIN_PROP = "linkedin_profile_url__unique_value"
GROUP = "ma_acquisition"

# A LinkedIn "URN slug" is an opaque per-viewer identifier, not a profile name.
URN_SLUG = re.compile(r"^AC[waoQ][A-Za-z0-9_-]{10,}$")

ROLE_OPTIONS = ["Owner", "Founder", "Co-Founder", "Chairman", "CEO",
                "President", "Managing Director", "Managing Partner",
                "Partner", "COO", "Other Executive"]
TIER_OPTIONS = ["Elite", "Diamond", "Platinum", "Gold", "Untiered"]

NEW_PROPS = [
    {"name": "ma_target", "label": "M&A Target (Acquisition)",
     "type": "enumeration", "fieldType": "booleancheckbox",
     "description": "Sourced decision-maker at an acquisition-target agency. "
                    "Separate from hubspot_partner_contact, which suppresses "
                    "cold outreach.",
     "options": [{"label": "Yes", "value": "true", "displayOrder": 0},
                 {"label": "No", "value": "false", "displayOrder": 1}]},
    {"name": "ma_target_role", "label": "M&A Target Role",
     "type": "enumeration", "fieldType": "select",
     "description": "Normalised decision-making authority.",
     "options": [{"label": r, "value": r, "displayOrder": i}
                 for i, r in enumerate(ROLE_OPTIONS)]},
    {"name": "ma_target_tier", "label": "M&A Target Partner Tier",
     "type": "enumeration", "fieldType": "select",
     "description": "HubSpot Solutions Partner tier of the target agency.",
     "options": [{"label": t, "value": t, "displayOrder": i}
                 for i, t in enumerate(TIER_OPTIONS)]},
    {"name": "ma_target_source", "label": "M&A Target Source",
     "type": "string", "fieldType": "text",
     "description": "Where the contact was sourced (ZoomInfo, LinkedIn, ...)."},
    {"name": "ma_target_sourced_on", "label": "M&A Target Sourced On",
     "type": "date", "fieldType": "date"},
    {"name": "ma_target_confidence", "label": "M&A Target Confidence",
     "type": "number", "fieldType": "number",
     "description": "Source accuracy score, 0-100."},
]


# --------------------------------------------------------------- normalising
def norm_linkedin(url: str) -> str:
    """Canonicalise a LinkedIn profile URL, or return '' if unusable."""
    u = (url or "").strip()
    if not u:
        return ""
    u = re.sub(r"^https?://", "", u, flags=re.I).rstrip("/")
    u = re.sub(r"^[a-z]{2,3}\.linkedin\.com", "linkedin.com", u, flags=re.I)
    u = re.sub(r"^www\.", "", u, flags=re.I)
    u = u.split("?")[0].split("#")[0]
    m = re.match(r"^linkedin\.com/(?:in|pub)/([^/]+)$", u, flags=re.I)
    if not m:
        return ""
    slug = m.group(1)
    if URN_SLUG.match(slug):
        return ""  # opaque URN, not a real profile identifier
    return f"https://www.linkedin.com/in/{slug.lower()}"


def norm_email(value: str) -> str:
    e = (value or "").strip().lower()
    return e if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e) else ""


def norm_phone(value: str) -> str:
    return (value or "").strip()


def pick_role(job_title: str, declared: str) -> str:
    """Map a free-text title onto the ROLE_OPTIONS dropdown.

    Ordered most- to least-authoritative so "Founder & CEO" lands on Founder:
    equity beats office when deciding who can actually sell the business.
    """
    if declared in ROLE_OPTIONS:
        return declared
    t = (job_title or "").lower()
    for needle, role in (
        ("co-founder", "Co-Founder"), ("cofounder", "Co-Founder"),
        ("owner", "Owner"), ("founder", "Founder"),
        ("chairman", "Chairman"), ("chairwoman", "Chairman"),
        ("managing partner", "Managing Partner"),
        ("managing director", "Managing Director"),
        ("chief executive", "CEO"), ("ceo", "CEO"),
        ("president", "President"),
        ("chief operating", "COO"), ("coo", "COO"),
        ("partner", "Partner"), ("principal", "Owner"),
    ):
        if needle in t:
            return role
    return "Other Executive"


# ------------------------------------------------------------------ lookups
def resolve_companies(domains: list[str]) -> dict[str, str]:
    """domain -> HubSpot company id, for partner companies only.

    Searching in batches of 100 domains keeps this to ~15 calls for the full
    D/P/G set instead of one call per company.
    """
    found: dict[str, str] = {}
    todo = sorted({d for d in domains if d})
    for chunk in batched(todo, 100):
        body = {
            "filterGroups": [{"filters": [
                {"propertyName": "domain", "operator": "IN", "values": chunk}]}],
            "properties": ["domain", "name", "hubspot_partner",
                           "hubspot_partner_tier"],
        }
        for r in search_all("companies", body):
            dom = (r["properties"].get("domain") or "").lower()
            # First match wins; the duplicate merges already collapsed the
            # known same-domain pairs.
            if dom and dom not in found:
                found[dom] = r["id"]
        time.sleep(0.1)
    return found


def resolve_contacts(prop: str, values: list[str]) -> dict[str, str]:
    """value of `prop` -> existing contact id, via batch/read."""
    found: dict[str, str] = {}
    todo = sorted({v for v in values if v})
    for chunk in batched(todo, 100):
        body = {"idProperty": prop, "properties": ["email", prop],
                "inputs": [{"id": v} for v in chunk]}
        try:
            res = call("/crm/v3/objects/contacts/batch/read", body)
        except HubSpotError as exc:
            # batch/read 207s partial success but 404s when nothing matches.
            if exc.code == 404:
                continue
            raise
        for r in res.get("results", []):
            key = (r["properties"].get(prop) or "").strip()
            if prop == "email":
                key = key.lower()
            if key:
                found[key] = r["id"]
        time.sleep(0.1)
    return found


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=IN)
    ap.add_argument("--commit", action="store_true",
                    help="actually write to HubSpot")
    ap.add_argument("--create-props", action="store_true",
                    help="create the ma_target_* contact properties first")
    ap.add_argument("--source", default="",
                    help="override the ma_target_source value")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        print(f"no input file: {args.input}", file=sys.stderr)
        return 1
    rows = list(csv.DictReader(open(args.input, encoding="utf-8-sig")))
    print(f"read {len(rows)} sourced rows from {os.path.basename(args.input)}")

    if args.create_props:
        ensure_props(args.commit)

    # ---- clean and de-duplicate ------------------------------------------
    today = dt.date.today().isoformat()
    clean, rejects = [], []
    seen_email: dict[str, dict] = {}
    seen_li: dict[str, dict] = {}
    for r in rows:
        email = norm_email(r.get("email", ""))
        li = norm_linkedin(r.get("linkedin_url", ""))
        domain = (r.get("company_domain") or "").strip().lower()
        rec = {
            "first_name": (r.get("first_name") or "").strip(),
            "last_name": (r.get("last_name") or "").strip(),
            "email": email,
            "linkedin_url": li,
            "job_title": (r.get("job_title") or "").strip(),
            "role": pick_role(r.get("job_title", ""), r.get("role", "")),
            "tier": (r.get("tier") or "").strip().title(),
            "company_domain": domain,
            "partner_company": (r.get("partner_company") or "").strip(),
            "phone": norm_phone(r.get("phone", "")),
            "mobile_phone": norm_phone(r.get("mobile_phone", "")),
            "source": args.source or (r.get("source") or "").strip() or "ZoomInfo",
            "accuracy": (r.get("accuracy") or "").strip(),
            "zi_person_id": (r.get("zi_person_id") or "").strip(),
        }
        why = ""
        if not email and not li:
            why = ("no usable email or LinkedIn URL"
                   + (" (LinkedIn value was a URN, not a profile)"
                      if r.get("linkedin_url") else ""))
        elif not domain:
            why = "no company_domain to associate against"
        elif not rec["last_name"]:
            why = "no last name"
        if why:
            rejects.append({**r, "reject_reason": why})
            continue
        # Collapse duplicates: the same person can surface from two sources.
        prior = seen_email.get(email) if email else None
        prior = prior or (seen_li.get(li) if li else None)
        if prior:
            # Prefer the row that carries an email, then the higher accuracy.
            better = (bool(email) > bool(prior["email"])) or (
                bool(email) == bool(prior["email"])
                and float(rec["accuracy"] or 0) > float(prior["accuracy"] or 0))
            if not better:
                continue
            prior.update(rec)
            rec = prior
        else:
            clean.append(rec)
        if email:
            seen_email[email] = rec
        if li:
            seen_li[li] = rec

    print(f"  usable            {len(clean)}")
    print(f"  rejected          {len(rejects)}")
    print(f"  with email        {sum(1 for r in clean if r['email'])}")
    print(f"  LinkedIn only     {sum(1 for r in clean if not r['email'])}")
    print(f"  with LinkedIn URL {sum(1 for r in clean if r['linkedin_url'])}")
    if not clean:
        write_csv(REJECTS, rejects)
        return 1

    # ---- resolve the HubSpot side ----------------------------------------
    companies = resolve_companies([r["company_domain"] for r in clean])
    missing_co = [r for r in clean if r["company_domain"] not in companies]
    print(f"\ncompanies matched   {len(companies)} domains")
    if missing_co:
        print(f"  ! {len(missing_co)} rows have no company in the portal "
              f"(e.g. {', '.join(r['company_domain'] for r in missing_co[:5])})")

    by_email = resolve_contacts("email", [r["email"] for r in clean])
    by_li = resolve_contacts(LINKEDIN_PROP,
                             [r["linkedin_url"] for r in clean])
    print(f"existing by email   {len(by_email)}")
    print(f"existing by LinkedIn{len(by_li)}")

    updates, creates = [], []
    for r in clean:
        hs_id = by_email.get(r["email"]) or by_li.get(r["linkedin_url"])
        props = {
            "jobtitle": r["job_title"],
            "ma_target": "true",
            "ma_target_role": r["role"],
            "ma_target_source": r["source"],
            "ma_target_sourced_on": today,
        }
        if r["tier"] in TIER_OPTIONS:
            props["ma_target_tier"] = r["tier"]
        if r["accuracy"]:
            props["ma_target_confidence"] = r["accuracy"]
        if r["linkedin_url"]:
            props[LINKEDIN_PROP] = r["linkedin_url"]
            props["zoominfo_person_linkedin_url_"] = r["linkedin_url"]
        if r["phone"]:
            props["phone"] = r["phone"]
        if r["mobile_phone"]:
            props["mobilephone"] = r["mobile_phone"]
        r["hs_contact_id"] = hs_id or ""
        r["hs_company_id"] = companies.get(r["company_domain"], "")
        r["action"] = "update" if hs_id else "create"
        if hs_id:
            # Identity fields stay as they are - a human may have fixed them.
            updates.append({"id": hs_id, "properties": props})
        else:
            props.update({"firstname": r["first_name"],
                          "lastname": r["last_name"]})
            if r["email"]:
                props["email"] = r["email"]
            creates.append({"properties": props})

    print(f"\nplan: {len(updates)} updates, {len(creates)} creates, "
          f"{sum(1 for r in clean if r['hs_company_id'])} associations")
    write_csv(PREVIEW, clean)
    write_csv(REJECTS, rejects)
    print(f"wrote {PREVIEW}")
    print(f"wrote {REJECTS}")

    if not args.commit:
        print("\nDRY RUN - nothing written. Re-run with --commit to apply.")
        return 0

    # ---- write ------------------------------------------------------------
    done_u = done_c = 0
    for chunk in batched(updates, 100):
        call("/crm/v3/objects/contacts/batch/update", {"inputs": chunk})
        done_u += len(chunk)
        print(f"  updated {done_u}/{len(updates)}", end="\r", flush=True)
        time.sleep(0.15)
    new_ids: dict[str, str] = {}
    done_r = 0
    for chunk in batched(creates, 100):
        made, recovered = create_chunk(chunk)
        new_ids.update(made)
        new_ids.update(recovered)
        done_c += len(made)
        done_r += len(recovered)
        print(f"  created {done_c}, recovered {done_r} "
              f"of {len(creates)}", end="\r", flush=True)
        time.sleep(0.15)
    print(f"\nupdated {done_u}, created {done_c}, "
          f"converted to update on conflict {done_r}")

    assoc = 0
    for r in clean:
        cid = r["hs_contact_id"] or new_ids.get(
            r["email"] or r["linkedin_url"], "")
        if not cid or not r["hs_company_id"]:
            continue
        try:
            call(f"/crm/v4/objects/contacts/{cid}/associations/default/"
                 f"companies/{r['hs_company_id']}", None, "PUT")
            assoc += 1
        except HubSpotError as exc:
            print(f"  ! assoc {cid}->{r['hs_company_id']}: {exc}",
                  file=sys.stderr)
        if assoc % 50 == 0:
            print(f"  associated {assoc}", end="\r", flush=True)
        time.sleep(0.08)
    print(f"associated {assoc} contact-company links")
    return 0


EXISTING_ID = re.compile(r"Existing ID:\s*(\d+)")


def key_of(props: dict) -> str:
    return (props.get("email") or "").lower() or props.get(LINKEDIN_PROP) or ""


def create_chunk(chunk: list[dict]) -> tuple[dict, dict]:
    """Create a batch of contacts, recovering from already-exists conflicts.

    batch/create is atomic: one conflicting row 409s the whole batch of 100 and
    nothing is written. Conflicts are unavoidable here because a lookup on the
    primary email cannot see a contact that holds the same address as a
    *secondary* email - HubSpot still refuses the create.

    So on a 409, fall back to creating one at a time, and turn each individual
    conflict into an update against the ID HubSpot names in the error. Identity
    fields are stripped from those updates for the same reason they are stripped
    from all updates: the existing record may have been corrected by a human.
    """
    try:
        res = call("/crm/v3/objects/contacts/batch/create", {"inputs": chunk})
        return ({key_of(r.get("properties", {})): r["id"]
                 for r in res.get("results", [])
                 if key_of(r.get("properties", {}))}, {})
    except HubSpotError as exc:
        if exc.code != 409:
            raise

    made, recovered = {}, {}
    for item in chunk:
        props = item["properties"]
        try:
            r = call("/crm/v3/objects/contacts", {"properties": props})
            if key_of(props):
                made[key_of(props)] = r["id"]
        except HubSpotError as inner:
            m = EXISTING_ID.search(inner.body or "")
            if inner.code != 409 or not m:
                print(f"  ! create {key_of(props)}: {inner}", file=sys.stderr)
                continue
            hs_id = m.group(1)
            patch = {k: v for k, v in props.items()
                     if k not in ("firstname", "lastname", "email")}
            try:
                call(f"/crm/v3/objects/contacts/{hs_id}", {"properties": patch},
                     "PATCH")
                if key_of(props):
                    recovered[key_of(props)] = hs_id
            except HubSpotError as patch_err:
                print(f"  ! patch {hs_id}: {patch_err}", file=sys.stderr)
        time.sleep(0.08)
    return made, recovered


def ensure_props(commit: bool) -> None:
    existing = {p["name"] for p in call("/crm/v3/properties/contacts")
                .get("results", [])}
    groups = {g["name"] for g in call("/crm/v3/properties/contacts/groups")
              .get("results", [])}
    todo = [p for p in NEW_PROPS if p["name"] not in existing]
    print(f"properties: {len(NEW_PROPS) - len(todo)} exist, {len(todo)} to create"
          + (f" -> {', '.join(p['name'] for p in todo)}" if todo else ""))
    if not commit:
        return
    if GROUP not in groups:
        call("/crm/v3/properties/contacts/groups",
             {"name": GROUP, "label": "M&A Acquisition"})
        print(f"  created property group {GROUP}")
    for p in todo:
        call("/crm/v3/properties/contacts", {**p, "groupName": GROUP})
        print(f"  created {p['name']}")


def write_csv(path: str, rows: list[dict]) -> None:
    if not rows:
        # Truncate rather than leave a stale file from an earlier run.
        open(path, "w", encoding="utf-8-sig").close()
        return
    cols: list[str] = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
