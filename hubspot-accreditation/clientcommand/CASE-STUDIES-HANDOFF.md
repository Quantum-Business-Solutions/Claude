# Case Studies — ClientCommand handoff

**Project:** ClientCommand (Supabase `zjtgesaiemlveuoymubo`)
**Surface:** Executive Hub, new section — sibling to Accreditation Hub
**Status:** **database layer built and live in production.** Two things remain: MCP tool
handlers (9, spec in §4) and the React surface (3 views, spec in §5).

---

## 1. What this is

QBS writes client engagement case studies for two audiences: HubSpot accreditation
assessors, and prospects. Today they live in chat transcripts, one-off Word files and
people's heads, which means every case study is rebuilt from scratch and none of them
know whether they are actually submittable.

**The point of putting this in the database is the readiness gate.** A case study is not
"done" when the prose reads well. It is done when it has zero unresolved blocking gaps,
at least one captured metric, MSA clearance, and the customer's HubSpot portal ID. A
Word file cannot tell you that. `v_case_study_readiness` can.

**Structural point:** a case study is an *agency-capability* object like an accreditation,
not a portal artefact. It optionally references a `portal_id` (whose engagement it
profiles) but it is owned by the agency and surfaces in Executive Hub. The rendered
portal page is an *output*, not the record.

---

## 2. Domain rules you must not break

| Rule | Implementation |
|---|---|
| **Reuse rules are per accreditation item.** Onboarding items 1 and 3 must profile the SAME engagement; item 2 may be a different customer but the same Pro-or-above subscription rule applies; Solutions Architect items 1 and 2 must be DIFFERENT customers. | `case_studies.item_nos` plus `accreditation_items.reuse_rule`. Validate before letting a user attach one case study to items that a reuse rule forbids combining. |
| **A case study is submittable only when four conditions hold** — zero unresolved blocking gaps, ≥1 captured metric, `msa_allows_sharing` true, `customer_hubspot_portal_id` present. | `v_case_study_readiness.submittable`. Never compute this in the UI; read the view. |
| **`customer_hubspot_portal_id` is the CLIENT's portal, not QBS's 20682069.** | Getting this wrong invalidates a submission. Label the field explicitly in the UI. |
| **Metrics must be actuals, not deliverable counts.** | `case_studies.metrics` is `[{label, baseline, actual, unit, captured_at, source}]`. HubSpot Onboarding item 3 requires actual numbers against the item 1 KPIs; a count of lists built does not satisfy it. |
| **Body history is automatic.** | A trigger snapshots the *previous* body into `case_study_revisions` on every body change, whatever made it. Do not write revisions by hand from the UI or from MCP — you will double-count. |
| **Never fabricate a number to fill a gap.** | Gaps exist so unknowns stay visible. An unresolved gap is a correct state, not a defect. |

---

## 3. Schema as applied

```
case_studies              the record: identity, engagement facts, body_md/body_html,
                          metrics, sources, governance flags
case_study_gaps           open items blocking submission (blocking|recommended|optional)
case_study_revisions      auto-snapshotted body history (trigger-written)
case_study_assets         diagrams, .docx packs, published portal pages
v_case_study_readiness    the gate — blocking_gaps, metrics_captured, submittable
```

Both triggers are on `case_studies`: `trg_case_studies_updated_at` and
`trg_case_studies_revision`. RLS is on, authenticated-full-access, matching the rest of
the app.

### Current data

Two case studies are loaded, both `draft`, both wired to `accreditation_artifacts` and
through `accreditation_artifact_items` to the correct Onboarding items:

| Slug | Client | Items | Blocking gaps |
|---|---|---|---|
| `calcfocus-hubspot-onboarding` | Calcfocus | 1, 3 | 4 |
| `pactec-salesforce-zoominfo-integration` | PacTec | 2 | 5 |

Neither is submittable. Both render as published HTML portal pages at slug
`hubspot-accreditation-case-study`, `internal` visibility.

---

## 4. Build task A — MCP tools

Add to the existing `client-command-mcp` edge function, following the established handler
pattern and naming conventions in that file.

### `list_case_studies`
Args: `status?`, `accreditation_key?`, `portal_id?`, `client_company?`, `limit?`.
Returns slug, title, client_company, status, accreditation_key, item_nos, and the
readiness columns joined from `v_case_study_readiness`.
**Always include `blocking_gaps` and `submittable` in the response** — an LLM consumer
that sees only a title will assume the case study is ready.

### `get_case_study`
Args: `slug` or `id`, `include_body?` (default true), `include_gaps?` (default true).
Returns the full record plus gaps, assets, and readiness.
Add `format?: 'html'|'md'` to pick which body to return; returning both doubles the
payload for no benefit.

### `create_case_study`
Args: `slug`, `title`, plus any column. Rejects a duplicate slug.
**Refuse to set `status` above `draft` on create** — a new case study has no gaps recorded
yet, so `submittable` would be trivially true and misleading.

### `update_case_study`
Args: `slug`, plus any updatable column, plus `change_note?`.
The revision trigger handles history. If the caller passes `change_note`, write it onto
the revision row the trigger just created (`source='mcp'`).
**Warn in the response when `status` is moved to `ready` or `submitted` while
`v_case_study_readiness.submittable` is false**, and name the blocking gaps.

### `add_case_study_gap` / `resolve_case_study_gap`
Add: `slug`, `description`, `severity?`, `section?`, `owner?`.
Resolve: `gap_id`, `resolution`. Sets `resolved`, `resolved_at`.

### `record_case_study_metric`
Args: `slug`, `label`, `actual`, `baseline?`, `unit?`, `source?`.
Appends to the `metrics` jsonb array with `captured_at = now()`.
This is the tool that unblocks most submissions — make it easy to call.

### `publish_case_study_page`
Args: `slug`, `portal_id?` (defaults to the case study's), `visibility?` (default
`internal`), `page_slug?` (default `hubspot-accreditation-case-study`).
Upserts a `knowledge_base` row with `format='html'`, content = shared stylesheet ||
`body_html`, and records the page in `case_study_assets`.
**The stylesheet lives in one place** (see §6) — do not let each publish carry its own
copy, or restyling means rewriting every page.
**Refuse `visibility='client'` when `msa_allows_sharing` is not true.**

### `render_case_study_docx`
Args: `slug`, `item_no?`.
Generates the submission-format Word document. The generator already exists at
`hubspot-accreditation/deliverables/build-docs.js` in the Claude repo; port it or call it.

---

## 5. Build task B — Executive Hub UI

Follow existing Executive Hub conventions for layout, typography and cards. Three views.

### B1. Case study library (landing)
Card grid, one per non-archived case study, newest first.
Each card: title, client, accreditation + item numbers, status chip, and a readiness
line. Readiness must be the loudest element after the title — `submittable` green, or
"N blocking" in red. A card that shows only a title invites someone to send an
unfinished case study to HubSpot.
Filter by status, accreditation, client.

### B2. Case study editor
The manual authoring surface. Two panes: metadata form left, body editor right.
- Body editor writes `body_md`; `body_html` is generated on save. Storing both is
  deliberate — Markdown is what humans edit, HTML is what gets published and printed.
- **`customer_hubspot_portal_id` needs an explicit label** ("the client's portal ID, not
  QBS 20682069") — this is the single most commonly wrong field.
- Metrics as a repeating row editor: label, baseline, actual, unit, source. Show a count
  and an empty state that says a submission needs at least one.
- Gaps as an inline checklist with severity, owner and a resolve action.
- Revision history in a side drawer, read-only, with a diff against current.
- Save writes `updated_by`; the trigger handles the snapshot.

### B3. Submission readiness panel
Per case study, the checklist that mirrors `v_case_study_readiness`:
blocking gaps · metrics captured · MSA clearance · customer portal ID · reference secured.
Plus the reuse rule for each attached item, quoted verbatim from
`accreditation_items.reuse_rule` — getting a reuse rule wrong invalidates a submission
and nobody remembers them.
Actions: publish portal page, render .docx, mark submitted.

---

## 6. Deliberate omissions — do not "fix" these

- **`metrics` is empty on both case studies.** Not an oversight. No real client outcome
  numbers were available, and inventing them would defeat the readiness gate and put
  fabricated figures in front of HubSpot.
- **`msa_allows_sharing` is null, not false.** Null means unchecked; false would mean
  checked and refused. The view treats null as blocking either way, but the distinction
  matters when someone asks whether we ever asked.
- **The shared stylesheet is currently duplicated into each published page.** It should
  live in one row or one constant in the edge function and be concatenated at publish
  time. Doing that properly is part of `publish_case_study_page`, not a migration.
- **No approval workflow.** Status is a flat enum, deliberately. Add stages only when a
  real second reviewer exists.

---

## 7. Follow-on worth scoping

- **Auto-draft from delivery data.** Both existing case studies were assembled by reading
  `client_portals`, plan phases and task titles, ticket history, and Zoom transcripts. A
  `draft_case_study_from_portal` tool could produce the skeleton — engagement facts,
  phase table, delivery record — and leave a human to write the narrative and gaps. That
  is the highest-leverage tool not in this build.
- **Gap → task.** A blocking gap with an owner is a task. Pushing gaps into the existing
  task system would stop them dying in a table nobody opens.
- **Sales reuse.** These records are also prospect collateral. A `client`-visibility
  render with the accreditation callouts stripped is a small addition with real value.
