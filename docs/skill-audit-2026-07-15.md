# QBS Skill Library Audit — 2026-07-15

Four parallel reviewers examined all 13 skills for stale facts, contradictions,
trigger overlap, script defects, and secrets. **No leaked credentials were found
anywhere.** Everything else below, ranked.

## Cross-cutting problems (affect most skills)

1. **Missing bundled files.** Four skills reference scripts/references that were
   never included in the claude.ai upload: qbs-hubspot-private-app (all 6 helper
   files), qbs-blog-post-creator (all 7), qbs-atlas-page-builder (its only
   reference file), qbs-marko-ticket-cleanup (all 5). These skills have been
   running at partial capacity. Files may be recoverable from old session
   downloads; otherwise rebuild.
2. **Three incompatible path roots** (`/mnt/skills/user/`, `/home/claude/`,
   `/mnt/user-data/outputs/`) — authored in different environments, never
   re-pathed. Skills should locate their own files relative to the skill dir and
   write outputs to the working directory.
3. **Environment-specific tool names** (`present_files`, `ask_user_input_v0`,
   `bash_tool`, `HubSpot:search_crm_objects`) that don't exist in Claude Code.
4. **Hardcoded volatile facts** duplicated across files: client lists/codes,
   record IDs, project tables, pricing (3 places), tool counts, timezone offsets
   (winter-only, wrong during DST), "Q2 SOW" logic in Q3. Fix: fetch live where
   possible; otherwise consolidate into one shared facts file with an as-of date.
5. **Trigger collisions**: reconcile-family (3 skills claim "reconcile [client]");
   stack-solver vs automation-scout (both claim "how do I automate...");
   atlas-page-builder claims all of "update/fix the website".

## Per-skill verdicts

### Tier 1 — broken or dangerous, fix first

**qbs-marko-ticket-cleanup / qbs-ticket-reconciliation-flagging /
qbs-client-reconciliation (treat as one problem — merge them)**
- Verbatim trigger collision on "reconcile [client]" etc.; which skill fires is
  random, and they encode opposite behaviors (never-close vs direct-close).
- marko-cleanup: all scripts/references missing (steps unexecutable); Bucket E
  encodes the exact prefix-stripping dedup that flagging says caused a
  341-ticket wrongful mass-delete; Bucket C hard-deletes.
- client-reconciliation: hardcodes `hs_pipeline_stage: "4"` = Closed
  unconditionally; other skills document that's Support-pipeline-only
  (Internal = 32751023). Would mis-stage non-Support tickets.
- Conflicting doctrines across the family: meeting-notes-win vs portal-wins;
  user-pastes-PAT vs never-paste-PAT (use Client Command); noon-UTC close-date
  rule present in one skill, absent where closes happen.
- Assorted: qbs_seats.md contradicts itself on owner-vs-createdById; Spectrum
  company-name drift (SPT → two different company names); ±1day vs +24h vs ±7day
  same-call windows; stale Q2 SOW references.

**qbs-hubspot-private-app**
- All 6 helper files missing, including the write-safety protocol the skill
  calls "non-negotiable". Foundation skill for atlas, zoominfo-deployer, and all
  client-portal work — rebuild first.
- Lists one-liner mixes v1/v3 API generations (returns an error); legacy
  `/email/public/v1/events` endpoint; stale rate-limit figures.

**qbs-zoominfo-property-deployer**
- deploy.py fires 81 property writes without verifying portal identity or auth
  success — contradicts its own prerequisite ("confirm not QBS portal
  20682069"). Add a hard portal/auth guard, 429 handling, exception handling.
- verify_parity.py reports auth failures as "0/42 matched — MISSING" instead of
  an auth error.
- Dead pointer to nonexistent `check_existing.sh` under wrong path root.
- Property list itself verified consistent (42 contact + 39 company across all
  3 files) — but it is hand-maintained in triplicate.

**hubspot-audit**
- CONFIDENTIALITY: `scripts/audit_input_example.json` appears to be a real
  client audit (SMP Security, named contact, partner, pipeline figures, dates).
  Sanitize immediately — it's now in the repo too.
- Two different "Phase 5"s; phases presented out of order vs "always execute in
  order".
- Feature-ID conflict: BR-03/BR-04 mean different features in the two detect
  scripts; deduction mapper would deduct Reporting points for the wrong feature.
- Scripts query several nonexistent/unofficial HubSpot endpoints (sequences,
  playbooks, snippets, KB, social) that fail silently → false "not configured"
  findings; `total` read from list-GETs that never return it (always 0).
- Sampling silently capped at 100 records while docs promise full-base
  coverage; percentages computed as 100-sample numerator over full-base
  denominator (systematically understated).
- Hardcoded "2026-01-23" dates labeled "last 90 days" (now ~173 and growing).
- NameError on SH-04 failure path (`pct_dm` undefined if try-block throws).
- Dual-engagement check always fires (`and True  # Zoom is default assumed`)
  and cites AP-15 when the catalog says AP-01.
- "17 required lists" is 17 in prose, 18 in the table, 15 in code.
- Positive score credits (+5/+3) contradict the deduction-only rubric.
- Content/Commerce Hub cataloged but never detected; null dimension renders as
  0/100; overall-score "minimum" rule violated by its own example.
- Two competing deliverable paths (build_audit_docx.js vs docx skill); docx
  validator referenced but doesn't exist; "55+ portals" baked into output.

### Tier 2 — impaired, fix soon

**qbs-blog-post-creator**
- Entire scripts/references tree missing (7 dead pointers): cannibalization
  check, internal links, safe publish — the core pipeline. Description promises
  what the body can't deliver.
- Instructs `state=PUBLISHED` on create while atlas warns that pattern never
  publishes on CMS pages — reconcile (blogs API may differ; document why).
- Hardcoded content-group/author IDs whose canonical home (`_common.py`)
  doesn't exist; drifting counts ("265+ posts", "146+ style attributes");
  Unsplash promised, no implementation; stale env paths.

**qbs-atlas-page-builder**
- Publish-state guidance incomplete: warns against `state: "PUBLISHED"` but
  never documents `PUBLISHED_OR_SCHEDULED` as the correct expected value.
- `references/atlas-pattern.md` (clone workflow + dual-href validator) missing.
- Depends on private-app's missing verify.sh/helpers.sh.
- Hardcoded reference page IDs (breaks silently if pages deleted/re-themed);
  ~1,200-char description bloats routing and includes implementation trivia;
  "update/fix the website" over-claims vs blog/email surfaces.

**qbs-email-builder** (only skill whose file map fully matches disk)
- push_email.py indexes QBS-specific widget IDs with no existence check —
  KeyError on any other template/portal, despite "works for client
  engagements"; `meeting_field` stuffed with every CTA URL; `_api` has no
  error handling/retries (its own reference prescribes them).
- scan_deliverability.py: white-text check effectively disabled; substring
  false positives ("freedom" → "free"); preview param never scanned;
  image-ratio check silently vanishes; its own 1px spacers self-flag.
- hubspot-push.md scheduler: DST-wrong (hour=14 year-round) and returns a
  past timestamp when run on a Wednesday.
- Stale example dates; naive-local time labeled Z; hardcoded list IDs and
  hub_id default.

**qbs-hubspot-ticketing**
- Winter-only timezone offsets in description and body (wrong since March).
- Project table stale ("Last updated: March 27, 2026"; Q1/Q2 projects listed
  as current; DVL/PTL end at March); orphan POA row; SPT company-name drift;
  suspected typos in internal names (Deringer/Commerical/Tascoso).
- Over-broad triggers (any 3-letter code, "BackOffice", "weekly meetings")
  co-fire with the reconciliation family; description never says
  "creation/logging only, not cleanup".
- 301-line SKILL.md with the two fastest-drifting tables inline — move to
  references (or fetch live).
- Call-vs-Meeting shell-naming drift across the family breaks pattern matching.

### Tier 3 — functional, polish

**sow-creator**
- Section numbering contradicts across all three files (Confidentiality 13 vs
  SECTION 12, etc.) — generated SOWs cite wrong sections. Pick one source.
- Wrong-environment output path and `present_files`; "use docx skill" vs
  "npm install -g docx" contradiction.
- Pricing defaults duplicated in 3 files; #D5E8F0 called gray (it's light blue).

**qbs-stack-solver + qbs-automation-scout**
- Verbatim trigger collision ("how do I automate...") with no mutual routing.
  Real split: scout = discover/score opportunities; solver = design against the
  owned stack. Put that in both descriptions (or merge scout into solver as a
  proactive mode).
- tech-stack.md: undated; "37-tool" claim vs 36 entries; conflicting Sales Hub
  tiers listed; version-pinned Runway details; "Sora when available" (~18mo
  stale); one staffer's Windows path; "future Finch sync" drift.
- Scout duplicates solver's stack-mapping without reading tech-stack.md.

## Recommended sequence

1. **Merge the ticket family** into one `qbs-ticket-reconciliation` skill
   (modes: flag / close-with-evidence / full-reconciliation; owner filter
   replaces the Marko skill). Resolve stage-ID, dedup, credential, and
   source-of-truth doctrines once. Retire the three old skills in claude.ai.
2. **Sanitize hubspot-audit's example JSON** (real client data) — quick, do
   immediately.
3. **Rebuild qbs-hubspot-private-app's helper layer** (other skills depend on
   it), then atlas/blog missing files.
4. **Safety-patch deploy.py** (portal guard) — small, high value.
5. **hubspot-audit** structural fixes (phases, feature IDs, endpoints,
   sampling honesty).
6. Ticketing/email/sow/stack-solver cleanups; de-hardcode volatile facts into
   one shared reference; fix DST handling everywhere (compute from timezone,
   never fixed offsets).
