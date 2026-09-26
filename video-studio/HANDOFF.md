# Video studio: handoff

Start here in a new chat about videos. This covers what exists, how it's built, the rules, and what's still open.

## What we've made

**QuoteCommand overview film** (`quotecommand-overview/`): a 10:48, 1080p product film with narration.
- It follows one deal, Northwind Orthopedics, PC, from the fleet all the way to the installed order.
- It uses real screens from the Quantum demo dealership on quotecommand.thequantumleap.business.
- It has 28 narrated scenes in 9 chapters, plus a cold open and an end card.
- Branding: navy #0B1F3A and gold #C9A24B, Poppins and DM Sans fonts, and the Quantum logo.
- Each scene has a label, with a visible cursor and click ripples.
- There's an original music bed, ducked under the voice, with captions in `.srt`.
- The finished MP4s are too large for git (about 100 MB). They were delivered in chat as 5 parts under 30 MB each. Re-render them with the pipeline below.

## The pipeline (all in `quotecommand-overview/`)

| Step | File | What it does |
|---|---|---|
| Script | `script.json` | 28 scenes (`s00`–`s27`): chapter, shot note, narration text |
| Voice | `vo/sNN.mp3`, `vo_durations.json` | Higgsfield TTS: `text2speech_v2`, ElevenLabs variant, preset voice `c2acff45-84b2-4974-892d-89fa2d4e5598`. About 0.6 credits per 35 words. `vocheck.py` re-transcribes with faster-whisper to check them. |
| Music | `music.py` → `music_bed.wav` | Original generated pad. Re-run it to regenerate (it isn't committed because it's 123 MB). |
| Cards | `cards.html` + `cardrec.cjs` + `cards.json` | Title, chapter and end cards rendered in the browser to webm. The relay cold open times each line to the narration. |
| Screens | `rec.cjs` + `scenes.cjs` / `scenes2.cjs` | Playwright records each scene at 1920x1080 (phone scenes at 390x844). Each scene script calls `h.ready()` once the page is presentable (the edit trims everything before that), then drives the cursor for as long as the narration runs. |
| Labels | `labels.py` | Pillow PNG lower-thirds. This ffmpeg build has **no drawtext**, so text overlays are images. |
| Edit | `edit.py` | Timeline `TL`: cards and scenes, with per-scene splits such as `("rec","s05",0.377)`, phone-over-background segments and the closing montage. Renders each item, concatenates them, mixes the voice (placed at item start + 0.45s) with the ducked music, loudnorms to -16 LUFS and muxes. Writes the SRT. `LIMIT=n` renders only the first n items. |
| Audio only | `audio_only.py` | Rebuilds the soundtrack and remuxes without re-rendering the video. |
| QC | `sheet.py` | Contact sheets of frames for a quick visual check. |

**Run it** (Node 20+, Python 3.11 with Pillow, imageio-ffmpeg, faster-whisper; Playwright Chromium):
```
export QC_EMAIL=...  QC_PASSWORD=...        # the QA login: never commit these
export PLAYWRIGHT_MODULE=/path/to/node_modules/playwright   # if playwright isn't resolvable
node cardrec.cjs                            # cards → cards/*.webm
node rec.cjs s01 s02 ...                    # scenes → rec/<id>/raw.webm + meta.json
python3 music.py                            # music_bed.wav
python3 edit.py                             # out/QuoteCommand-overview.mp4 + .srt
```
To split for chat (30 MB limit): `ffmpeg -i out/QuoteCommand-overview.mp4 -c copy -f segment -segment_time 140 -reset_timestamps 1 part%d.mp4`

## Where the film is published (v8, Sep 26 2026)

- **File:** Quantum's HubSpot file manager (portal 20682069), folder `/quotecommand`:
  - `quotecommand-overview-v8.mp4`: a 53 MB web encode (two-pass x264 at 540k, AAC 112k, faststart), made from the 103 MB master.
  - `quotecommand-overview-v8-poster.jpeg`: the title card.
  - v7 and the old poster are still there for rollback.
- **CDN URL:** `https://20682069.fs1.hubspotusercontent-na1.net/hubfs/20682069/quotecommand/quotecommand-overview-v8.mp4`.
- **quotecommand.thequantumleap.business/auth:** `src/components/marketing/copy.ts` (`OVERVIEW_VIDEO_SRC`, `OVERVIEW_VIDEO_POSTER`, `OVERVIEW_VIDEO_CAPTION`). Merged in QuoteCommand PR #98.
- **thequantumleap.business/command-apps:** site page `207621019801`. The `<video>` sits inside the prose of `layoutSections.main.rows[2]` (the QuoteCommand block). Swap the two URLs in the draft, then `POST .../draft/push-live`.
- **Quantum's site is on the Quantum Void theme now** (`Quantum Void/templates/mv-shell.html`), not atlas. The saved `qbs-atlas-page-builder` skill still describes atlas. For Void pages, change only content strings in place and keep the structure.
- **Uploading video to HubSpot:** send the part as `type=video/mp4` and include `.mp4` in `fileName`. Without that, HubSpot stores it as type OTHER with no extension and serves `application/octet-stream`, which Safari won't play.
- **To publish a new cut:** upload it as v9, point both places at it, and leave v8 in place for rollback.

## Recorder tricks worth keeping

- **Film dressing** (`DRESS` in `rec.cjs`): a drawn cursor and click ripple, since headless video has no cursor.
  - It hides the signed-in email and the floating "Tour this page" / "Next:" pills.
  - It scrubs the "ZZ TEST" prefix from on-screen text. This is display only; the data is untouched.
  - DRESS is a JS template literal, so regex backslashes must be doubled.
- **Clock**: a scene can set `clock: "<ISO time>"`. The browser starts at real time, so sign-in works: a past clock breaks the auth token. The scene then calls `h.setClock()` and refreshes. The orders board uses Sep 10 2026 09:00 CDT, so it shows a natural green/amber/red mix instead of everything overdue.
- **Flaky proxy**: JS chunks sometimes return 502, which leaves a blank app. `h.go()` retries and waits for `#root` to render text.
- **Configurator search** is a dropdown. Type, then press Enter on the highlighted result, then press the row's "Add … to the quote" button. Ticking FS-539 automatically adds the RU-519 relay, with a toast giving the reason.

## Rules (from the owner, Shawn Peterson)

- Reps never see dealer cost, dealer margin, finance reserve or GP. Scenes filmed in rep view must respect this. Admin/manager scenes may show margin.
- Don't change dealer-specific data without approval. Demo-data changes on the live Supabase project (`msgxechfpyxnvlcrmoqh`) have been blocked by the permission checker when attempted from a session. Ask Shawn, or have him run them.
- Never commit credentials. The QA login lives only in local env vars.
- Keep the `demo_seed` sign_events: they're integrity markers.

## Key demo IDs (Quantum dealer `8c3dfd49-71ad-4615-a727-96689bdb4bc0`)

- Flagship deal: `f1a95000-0000-4000-8000-000000000001` (won, ORD-00054). Copies `…00c1`, `…00d1`. Proposals `…00c2`, `…00d2`.
- The public proposal link uses the token in `scenes.cjs` (`TOKEN`).
- Flagship numbers on screen: $112,260 total, 29.1% margin, $4,119.04/mo.

## Reshoot log

- **v2 (Sep 26)** fixed four scenes:
  - s01 and s07: "ZZ TEST" scrubbed from the screen.
  - s05: split into two shots. The Northwind build sheet, then a fresh quote where the C450i is added off camera and ticking the FS-539 staple finisher adds RU-519 with the reason shown. `start2=3.5` lines up the click with the narration.
  - s17: the orders board with the browser clock set to Sep 10 09:00 CDT.
- Also fixed: the soundtrack was 3s short (the voice track wasn't padded, so the music ducking stopped early). `apad` was added in `edit.py`.

## Open items for the next film pass

1. **Northwind fleet assessment**: s03 still shows Summit Regional Credit Union's assessment. Creating a Northwind one on the live account was blocked. Shawn can create it in the app: Assessments → New assessment → name "Northwind Orthopedics, PC" → import Northwind's fleet (7 Canon devices; volumes come from the Sep/Aug meter reads). Then re-record s03.
2. **Per-funder rate cards**: every funder has identical rates. s08 only shows one funder, so it isn't visible. Change it only with approval, and don't touch the funder the flagship deal uses, or its totals shift.
3. **ZZ TEST approval**: it's hidden on film by the text scrub. The deal avatar on Home still reads "ZT" (tiny). For good, rename or resolve the test deal "ZZ TEST - Meridian Dental Group - MFP Refresh" (owner decision).
4. **ERP push row** and **HubSpot sandbox** scenes: the sandbox needs a credential from Shawn.
5. Ideas: 60–90s cut-downs per chapter for social, a rep-view-only training cut, and a voice pick-up for any line that changes.
