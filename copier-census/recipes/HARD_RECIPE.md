# Getting ONE decision-maker at a dealer that has defeated every prior attempt

These 35 dealers have already been through: company website, firecrawl search, ZoomInfo, and a
LinkedIn company-to-people sweep. All failed. Do NOT simply repeat those. Assume the easy
sources are exhausted and go to the ones that are slower but authoritative.

## SOURCE ORDER, by what has actually cracked these before

1. **Secretary of State officer/registered-agent filing** for the dealer's state. Officers are
   filed under legal obligation. Search "<state> secretary of state business entity search".
   Florida Sunbiz works reliably via Firecrawl with `proxy: stealth`. WV, MO, WA, GA, SC, NC, NE,
   OK are bot-walled or POST-only.
2. **corporationwiki.com via Firecrawl stealth proxy** — returns state-SoS / D&B officer records
   WITH titles, and defeats the Cloudflare-gated registries. This single source cracked 8 dealers
   in an earlier wave. Use it when the state registry blocks you.
3. **BBB profile** — the "Business Management" / "Principal" block names owners. `site:bbb.org
   <dealer name>`. VERIFY the city: a BBB slug once resolved to an Oregon construction firm.
4. **Manta** — the "Detailed Information -> Contacts" block names owners where registries are dry.
5. **State / county / school-district contract awards and bid tabulations.** These publish an
   owner's name AND often a direct email. `"<dealer name>" bid OR contract OR RFP filetype:pdf`.
   One NY State OGS document carried name + title + direct email for ~13 dealers.
6. **Trade press**: ENX Magazine (incl. Difference Makers and Elite Dealers), The Cannata Report,
   Industry Analysts, The Imaging Channel, Workflow, BTA.
7. **Manufacturer dealer locators** (Sharp, Kyocera, Canon, Ricoh, Konica Minolta, Toshiba,
   Xerox, Lexmark) — confirms the dealer still trades, sometimes names a principal.
8. **Wayback Machine** on the dealer's own site — an old /about or /team page often names the
   owner even when the current site does not.
9. **LinkedIn people search by QUOTED COMPANY NAME as keywords** (not the company filter). This
   is the one LinkedIn route not yet tried on these: it found an owner at a dealer with no
   company page at all. Via the Unipile MCP tool `mcp__Unipile__execute-request`, account_id
   `S6ua4SfUT4SMRFZFOmyUzQ` ONLY, key ${UNIPILE_API_KEY}   <-- REDACTED. Supply via environment; never commit the key.

## RULES
- ONE validated decision-maker is the goal; two is a bonus. Breadth before depth.
- Every person needs an evidence URL and a verbatim quote. No evidence, no report.
- LinkedIn is authoritative for a CURRENT title.
- An obituary name-match is a HOLD for a human, never a verdict. Never assert anyone has died.
- Never report someone whose title or evidence says former/retired/departed as current.
- Verify the company by city/state/domain before trusting any person. Same-name dealers in
  different states are the most common error in this dataset.
- A dealer that is DEFUNCT, NON-US, or NOT A COPIER DEALER is a valid and valuable answer.
  Say so with evidence instead of forcing a contact.
- If genuinely exhausted, say precisely what you ruled out and what the ONE remaining lead is
  (usually: phone the main line and ask for the owner by name).
- Do NOT write anything to HubSpot.
