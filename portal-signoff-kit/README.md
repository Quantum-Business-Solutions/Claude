# Client sign-off page kit (FAQs, copy, any list of items a client must approve)

Built for CCi Voice's FAQ approval (Nov 2026). Gives the client one polished page where they answer our open
questions, edit every item in place, approve / send back / skip, comment, and submit. Everything saves to the
Client Command portal and can be read back with `get_page_state` / exported as CSV.

## The process (about 1 hour per client once content exists)

1. **Draft the content** from the client's real pages (crawl or HubSpot API). One row per page/post:
   `{g, id, n, u, f, qa:[[q,a],...]}`. Put unverified facts in the answer as `[CONFIRM: what to check]`.
   Add `f` (freshness note) for anything that may be out of date. Keep answers 40 to 70 words, answer first.
2. **Collect open questions** into `meta.questions` (`{g: group, t: text}`), ~20 max, grouped, each answerable in one line.
3. `python3 build.py content.json out/`
4. **Test locally**: `cd test`, copy `out/full.html` next to `host.html`, `node qa2.js` (needs Playwright). Host.html
   simulates the portal frame (sandboxed iframe, postMessage state). Check desktop + 390px mobile + dark mode screenshots.
5. **Create the page**: `create_signoff_sheet` once with one dummy row (gives an HTML *sectioned* page with
   scripts allowed), then replace its sections with `upsert_document_section`:
   `app` order 0, `data1..N` orders 10+, `metadata` order 30, `boot` order 31 (write boot last). Copy bodies byte for byte;
   delegate to a subagent that reads each file and verifies the stored page equals the files concatenated.
6. Keep it **internal**, open it yourself, then `set_page_visibility` to client and email the link.
7. After they submit: `get_page_state(portal_id, slug)` for approvals, edits (`faq:<id>` keys), confirm answers and
   `faq:_answers`, `faq:_submit`. Turn decisions into tickets.

## Lessons learned (do not repeat)

- Never `innerHTML` re-render on every incoming state message: it collapses the page and scrolls to the top. Keep open
  cards in a map, preserve scrollY, debounce, and skip when nothing changed.
- The portal frame is sandboxed: no `localStorage`, no `confirm()`/`alert()`. Use postMessage state (`ready` / `state:set`) and
  inline two-step confirmations.
- Sticky headers hide cards on scroll-into-view: use `scroll-margin-top`, and make the bar static on short/mobile screens.
- Check horizontal overflow at 390px (tags + chevrons in flex rows).
- Count totals from the data, not from agent reports (we once told the client 292 blog FAQs; it was 256).
- The portal's `check_signoff_sheet` does not recognise this custom page; ignore its warning but verify section order manually.
- Tool results over ~60 KB are saved to a file: read with Python, do not paste.

## Top 10 features in the template
1. 3-step guide with live status (answer questions, review, submit)
2. Questions for CCi, open by default, one-line answers, live count
3. Inline editable question and answer boxes with Restore original and an "edited" marker
4. Inline answer field on every [CONFIRM] note
5. Approve / Needs edits / Skip, then auto-advance to the next unreviewed item
6. Filters: All, type, To do, Needs edits, Edited by you, To confirm, Check freshness; plus search
7. Comments on every item
8. Submit review (recorded with name and time) and re-submit
9. Two-step "Approve all shown", status CSV and edits CSV (original vs edited) for QBS
10. Phone layout, dark mode, keyboard focus rings, aria labels, autosave status
