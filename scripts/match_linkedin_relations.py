#!/usr/bin/env python3
"""Match LinkedIn connection headlines against the partner list.

Companion to find_partners_in_linkedin_network.py for when the network has to be
paged through the Unipile MCP tool rather than by direct HTTP - the Claude
sandbox cannot reach Unipile's port 16072, but large MCP responses are written to
disk, so the pages can be processed from those files instead.

Feed it the saved tool-result files; it accumulates matches and prints the cursor
needed for the next page.

Usage:
    python3 scripts/match_linkedin_relations.py <tool-result-file> [more...]
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from source_ma_decision_makers import is_decision_maker  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTNERS = os.path.join(REPO, "data", "hubspot_partners.csv")
OUT = os.path.join(REPO, "data", "partner_linkedin_connections.csv")
SEEN = os.path.join(os.environ.get("SCRATCH", "/tmp"), "li_seen.jsonl")

RANK = {"elite": 0, "diamond": 1, "platinum": 2, "gold": 3, "": 9}


def squash(text: str) -> str:
    """Alphanumerics only, lowercased, so "SmartBug Media" meets "smartbugmedia".

    Digits MUST be kept. Stripping them collapses numeric-prefixed domains into
    ordinary English - 215marketing -> "marketing", 1406consulting ->
    "consulting", digital360 -> "digital" - and each of those then matches every
    headline containing that word. That single bug produced 216 "matches" where
    "CEO @ M Communications" was scored as 215marketing.
    """
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


# Domain roots that are ordinary words even with digits kept. A root like
# "marketingagency" is a real domain but matches any headline mentioning it in
# passing, which is not evidence of employment.
GENERIC_ROOTS = {
    "marketing", "consulting", "solutions", "digital", "creative", "inbound",
    "revenue", "growth", "agency", "partners", "business", "company", "media",
    "content", "strategy", "sales", "software", "technology", "services",
    "consultants", "marketingagency", "digitalmarketing", "webdesign",
    "salesforce", "hubspot", "automation", "analytics", "ecommerce",
    # Found by inspecting real matches: each of these is a genuine partner
    # domain that is also an ordinary phrase, so it fires on headlines that
    # merely use the words. "Expansion Account Executive" is a job title, not
    # employment at the agency called Expansion.
    "expansion", "marketingautomation", "automationco", "datasolution",
    "socialselling", "growthoperations", "marketingwiz", "fullfunnel",
    "saasgrowth", "strategyco", "intentionly", "newhomestar",
    "marketingcommunications", "wwwmarketingcommunications",
    "positionglobal", "engagingio", "contentmarketing", "bcontentmarketing",
}


def build_index(tiers: tuple[str, ...]) -> tuple[dict, int]:
    """Index partners by DOMAIN ROOT, not by company-name words.

    Name-word matching does not work at this scale. With 7,399 partners the token
    pool swallows ordinary English - "simple", "grow", "market", "search",
    "flow", "spot", "operations" are all company names here - so 945 of 979
    connections "matched" and "President at Blue Technologies" was scored as Blue
    Frog. Domain roots ("clearpivot", "trooinbound", "smartbugmedia") are
    concatenated and effectively unique, and squashing the headline the same way
    lets them meet across spacing and punctuation.
    """
    index: dict[str, list[dict]] = {}
    n = 0
    for p in csv.DictReader(open(PARTNERS, encoding="utf-8-sig")):
        if not p["domain"] or p["tier"] not in tiers:
            continue
        n += 1
        root = squash(p["domain"].split(".")[0])
        # Precision over recall here. A squashed headline is one long string, so
        # a short root collides constantly; 8 characters loses "hubgem" but stops
        # inventing employment. Generic roots are dropped whatever their length.
        if len(root) >= 8 and root not in GENERIC_ROOTS:
            index.setdefault(root, []).append(p)
    return index, n


def candidates(headline: str) -> set[str]:
    """Every run of 1-3 whole words in the headline, concatenated.

    Inverted from testing each root against the headline, which was both slow
    (11,000 headlines x 1,600 roots of regex) and imprecise. Generating the
    headline's own word-runs and looking them up is O(words) and exact on word
    boundaries: "SmartBug Media" yields "smartbugmedia" so the spaced form still
    matches, while "Positioning" yields "positioning" and never equals
    "position". Substring matching is gone entirely.
    """
    words = re.findall(r"[a-z0-9]+", (headline or "").lower())
    out = set()
    for i in range(len(words)):
        for n in (1, 2, 3):
            if i + n <= len(words):
                out.add("".join(words[i:i + n]))
    return out


def extract_items(path: str) -> tuple[list[dict], str]:
    """Pull the items array and cursor out of a saved MCP response."""
    raw = open(path, encoding="utf-8", errors="replace").read()
    start = raw.find('{"object":"UserRelationsList"')
    if start < 0:
        start = raw.find("{")
    blob = raw[start:]
    # The file may have trailing prose after the JSON; walk back to the last
    # closing brace that parses.
    for end in range(len(blob), max(len(blob) - 400, 0), -1):
        try:
            data = json.loads(blob[:end])
            return data.get("items") or [], data.get("cursor") or ""
        except json.JSONDecodeError:
            continue
    # Fall back to regex-extracting individual records.
    items = []
    for m in re.finditer(r'\{"object":"UserRelation".*?"profile_picture_url":"[^"]*"\}', blob):
        try:
            items.append(json.loads(m.group(0)))
        except json.JSONDecodeError:
            continue
    return items, ""


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    TIERS = ("elite", "diamond", "platinum", "gold")
    index, npartners = build_index(TIERS)

    seen = set()
    if os.path.exists(SEEN):
        seen = {json.loads(l)["slug"] for l in open(SEEN, encoding="utf-8")
                if l.strip()}

    existing = []
    if os.path.exists(OUT):
        existing = list(csv.DictReader(open(OUT, encoding="utf-8-sig")))

    rows, total, cursor, fresh = list(existing), 0, "", []
    for path in sys.argv[1:]:
        items, cursor = extract_items(path)
        total += len(items)
        for r in items:
            slug = r.get("public_identifier") or ""
            if slug in seen:
                continue
            seen.add(slug)
            fresh.append(slug)
            head = r.get("headline") or ""
            hits = [p for c in candidates(head) if c in index
                    for p in index[c]]
            if not hits:
                continue
            hits.sort(key=lambda p: RANK.get(p["tier"], 9))
            p = hits[0]
            rows.append({
                "name": f"{r.get('first_name','')} {r.get('last_name','')}".strip(),
                "headline": head[:170],
                "is_decision_maker": "YES" if is_decision_maker(head) else "",
                "partner_company": p["company_name"],
                "partner_domain": p["domain"],
                "tier": p["tier"] or "untiered",
                "country": p["country"],
                "linkedin_url": r.get("public_profile_url") or "",
                "slug": slug,
                "connected_since": time.strftime(
                    "%Y-%m-%d", time.gmtime((r.get("created_at") or 0) / 1000))
                if r.get("created_at") else "",
                "email": "",
            })

    with open(SEEN, "a", encoding="utf-8") as fh:
        for slug in fresh:
            fh.write(json.dumps({"slug": slug}) + "\n")

    rows.sort(key=lambda r: (not r["is_decision_maker"],
                             RANK.get(r["tier"], 9), r["partner_company"]))
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else
                           ["name"])
        w.writeheader()
        w.writerows(rows)

    dm = [r for r in rows if r["is_decision_maker"]]
    print(f"tiered partners indexed   {npartners}")
    print(f"connections in this batch {total}   (cumulative seen {len(seen)})")
    print(f"matched a partner         {len(rows)}")
    print(f"  owner/founder/CEO level {len(dm)}")
    print(f"  distinct agencies       {len({r['partner_domain'] for r in dm})}")
    tier_counts: dict[str, int] = {}
    for r in dm:
        tier_counts[r["tier"]] = tier_counts.get(r["tier"], 0) + 1
    print("  by tier: " + ", ".join(f"{k}={v}" for k, v in
                                    sorted(tier_counts.items(),
                                           key=lambda kv: RANK.get(kv[0], 9))))
    print(f"\nwrote {OUT}")
    if cursor:
        print(f"\nNEXT CURSOR: {cursor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
