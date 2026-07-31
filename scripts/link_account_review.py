#!/usr/bin/env python3
"""Put a link to the account review on the HubSpot company record.

WHY THIS EXISTS
The first question asked about this whole feature was "where inside HubSpot do I look at
it?" — and the answer was nowhere: the review lives in the app, and a rep sitting on a
company record had to know to leave HubSpot and navigate to it by hand. A link on the
record closes that, and it is the cheapest thing on the list by an order of magnitude.

WHY NOT A PROPER UI EXTENSION
A HubSpot CRM card rendering the review inside the record is the better product and is
blocked: the app is `distribution: marketplace`, so `hs project upload` requires a personal
access key for the developer account that owns the build. Until that exists, this is the
whole of what can be done without one.

THE FIELD TYPE, MEASURED
HubSpot documents a URL field type whose values render as clickable links. THIS PORTAL DOES
NOT HAVE IT: the API answers 400 and lists the permitted enum, which is
[calculation_equation, checkbox, phonenumber, number, textarea, booleancheckbox, file,
text, ...] with no url member. So the property is created as single-line `text`, which per
HubSpot's docs auto-detects a URL value and renders a click-to-open affordance on the
record. The url attempt is left in the code so a portal that does support it gets the
better type without an edit.

Known limitation, stated because a rep will hit it: HubSpot's own community reports URL
rendering is inconsistent — reliable in index/table views, truncated on the record card,
and not functional on mobile. Worst case the URL is on the record and can be copied, which
beats not being there.

  export HUBSPOT_TOKEN=pat-na1-...
  python3 scripts/link_account_review.py --base-url https://... --plan
  python3 scripts/link_account_review.py --base-url https://...

`--base-url` IS REQUIRED AND HAS NO DEFAULT, deliberately. The repo contains two candidate
hosts (`https://app.quotecommand.com` in an OAuth comment, `https://quotecommand.vercel.app`
elsewhere) and no canonical config that settles it. A wrong link written onto every company
record is worse than no link: it looks authoritative and 404s.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.hubapi.com"
PROP = "qc_account_review_url"
# The group the fleet properties on COMPANIES actually live in. Measured, not assumed:
# of the 50 `ea_` company properties, 13 are in `e_automate_fleet` and 37 in `e_automate`.
# The first guess (`ceojuice_fleet`) does not exist on companies and HubSpot rejects the
# whole property with a 400 rather than defaulting the group.
GROUP = "e_automate_fleet"


def call(token: str, method: str, path: str, body=None, tries: int = 4,
         read_only: bool = False, dry: bool = False):
    # A POST that only reads must go through in plan mode: HubSpot's search endpoint is
    # one, and stubbing it makes --plan unable to count what it would touch. A plan that
    # cannot see reports a decision it would not actually make.
    if dry and method != "GET" and not read_only:
        print(f"    [plan] {method} {path}")
        return 0, {}
    data = json.dumps(body).encode() if body is not None else None
    last = None
    for attempt in range(tries):
        req = urllib.request.Request(
            API + path, data=data, method=method,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                raw = resp.read()
                return resp.status, (json.loads(raw) if raw.strip() else {})
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                parsed = json.loads(raw or b"{}")
            except Exception:
                parsed = {}
            if exc.code == 409:          # already exists — success for an idempotent run
                return exc.code, parsed
            if exc.code >= 500 and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            return exc.code, parsed
        except Exception as exc:
            last = exc
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(str(last))


def ensure_property(token: str, dry: bool) -> str | None:
    """Create the property, preferring the clickable URL field type. Returns its fieldType."""
    s, d = call(token, "GET", f"/crm/v3/properties/companies/{PROP}")
    if s == 200:
        ft = d.get("fieldType")
        print(f"  property {PROP}: exists, fieldType={ft}")
        return ft

    base = {
        "name": PROP,
        "label": "Account review",
        "groupName": GROUP,
        "type": "string",
        "description": (
            "Link to this company's account review in QuoteCommand — the fleet by device, "
            "contract and lease. Written by scripts/link_account_review.py. Not editable by "
            "hand: it is derived from the record id."),
    }
    # URL first, because its values would render as links — but THIS PORTAL REJECTS IT.
    # Measured: HubSpot answered 400 with the permitted enum, which is
    # [calculation_equation, checkbox, phonenumber, number, textarea, booleancheckbox,
    # file, text, ...] and contains no url type. So `text` is what actually gets created
    # here, and per HubSpot's own docs a single-line text property auto-detects a URL and
    # renders a click-to-open affordance on the record.
    #
    # The url attempt is KEPT rather than deleted: it costs one rejected request on first
    # run, and portals differ by HubSpot version and tier. If a portal does accept it, that
    # portal gets the better field type without anyone editing this file.
    for field_type in ("url", "text"):
        s, d = call(token, "POST", "/crm/v3/properties/companies",
                    {**base, "fieldType": field_type}, dry=dry)
        if dry:
            print(f"    [plan] would create {PROP} as fieldType={field_type}")
            return field_type
        if s in (200, 201):
            print(f"  property {PROP}: created, fieldType={d.get('fieldType')}")
            return d.get("fieldType")
        if s == 409:
            print(f"  property {PROP}: already exists")
            return None
        msg = str(d.get("message", ""))[:160]
        print(f"    fieldType={field_type} rejected: HTTP {s} {msg}")
    return None


def companies_with_fleet(token: str) -> list[dict]:
    """Companies that HAVE a fleet — the only ones a review says anything about.

    Filtered on `ea_fleet_monthly_volume` HAS_PROPERTY rather than fetched wholesale,
    because a link on a company with no equipment leads to an empty review and teaches a
    rep the feature is broken.

    NOTE ON SEARCH: HubSpot's search index lags batch writes by seconds to minutes, and
    caps at 100 results PER PAGE regardless of the `limit` asked for — both of which have
    produced wrong counts in this project before. So this pages to exhaustion on `after`
    and reports the total it actually walked.
    """
    out: list[dict] = []
    after: str | None = None
    while True:
        body = {
            "limit": 100,
            "properties": ["name", PROP],
            "filterGroups": [{"filters": [
                {"propertyName": "ea_fleet_monthly_volume", "operator": "HAS_PROPERTY"}]}],
        }
        if after:
            body["after"] = after
        s, d = call(token, "POST", "/crm/v3/objects/companies/search", body,
                    read_only=True)
        if s >= 300:
            print(f"  ! search HTTP {s} {str(d.get('message'))[:140]}", file=sys.stderr)
            break
        out.extend(d.get("results", []))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True,
                    help="App origin, no trailing slash, e.g. https://app.quotecommand.com")
    ap.add_argument("--plan", action="store_true", help="Report without writing")
    args = ap.parse_args()

    token = os.environ.get("HUBSPOT_TOKEN")
    if not token:
        print("Set HUBSPOT_TOKEN for the target portal.", file=sys.stderr)
        return 2

    base = args.base_url.rstrip("/")
    if not base.startswith("https://"):
        print("--base-url must be https. A link written to every company record is "
              "outward-facing.", file=sys.stderr)
        return 2

    print(f"Account review link  base={base}  {'PLAN' if args.plan else 'WRITE'}")
    ensure_property(token, args.plan)

    companies = companies_with_fleet(token)
    print(f"  {len(companies)} companies carry a fleet rollup")

    # Only write where the value would actually change. HubSpot counts a no-op PATCH as a
    # property modification, which pollutes "last modified" and any workflow keyed on it.
    todo = []
    for c in companies:
        want = f"{base}/accounts/{c['id']}"
        if (c.get("properties") or {}).get(PROP) != want:
            todo.append({"id": c["id"], "properties": {PROP: want}})

    print(f"  {len(todo)} need the link written, {len(companies) - len(todo)} already correct")
    if todo[:1]:
        print(f"  example: {todo[0]['properties'][PROP]}")
    if args.plan or not todo:
        return 0

    wrote = 0
    for i in range(0, len(todo), 100):
        chunk = todo[i:i + 100]
        s, d = call(token, "POST", "/crm/v3/objects/companies/batch/update",
                    {"inputs": chunk})
        # 207 is PARTIAL failure, not success. Treated as success once in this project and
        # it silently dropped records.
        if s == 207:
            errs = d.get("errors", [])
            print(f"    ! partial: {len(errs)} of {len(chunk)} failed — "
                  f"{str(errs[:1])[:200]}")
            wrote += len(chunk) - len(errs)
        elif s in (200, 201):
            wrote += len(d.get("results", chunk))
        else:
            print(f"    ! batch HTTP {s} {str(d.get('message'))[:160]}")
    print(f"  wrote {wrote} of {len(todo)}")
    return 0 if wrote == len(todo) else 1


if __name__ == "__main__":
    raise SystemExit(main())
