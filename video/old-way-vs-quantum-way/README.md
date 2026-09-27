# The Old Way vs. The Quantum Way

Quantum's ad series: every scene is one real sales or marketing task, done the old way (Rick, buried by
Bogged Down Bob, our Mayhem-style villain, ref id `busywork`) and the Quantum way (Maya and her team: an
assistant, a conveyor belt of leads, an AI agent crew). A selling-time scoreboard runs through the week
(Rick 4h 12m vs Maya 42h, marked as a dramatization). v1 cut: `edit_v1.json`; current: `edit.json`.
The running gag is Maya's glowing "Done." button (not Staples' "That was easy", which is their trademark).

## Files

| Path | What it is |
|---|---|
| `shots.json` | Every generated shot: model, prompt, character refs, request id, output URL. The source of truth for footage. |
| `edit.json` | The timeline. Scenes in order, each a list of clip and insert segments, with optional OLD WAY / QUANTUM WAY tags. |
| `refs/` | Character reference stills (Rick, Maya, Busywork). Uploaded copies are in `shots.json` → `refs`. |
| `inserts/insert.html` | Screen inserts drawn in HTML with real logos and real text (ConnectAndSell dialer, HubSpot record, title card). |
| `assets/` | Official logos (HubSpot, ZoomInfo, ConnectAndSell, Quantum white) and fonts. |
| `build/hf.py` | Higgsfield helper: upload, submit, poll, fetch, qa. |
| `build/render_inserts.js` | Renders an insert frame by frame, or a tag overlay. |
| `build/build.py` | Assembles scenes to MP4 with the Quantum logo bottom-right, then joins them. |

Video files are not in git. On a fresh checkout run `python build/hf.py fetch`, then download
`shots.json` → `reused` into `clips/` by name.

## Add a scene

1. Add shots to `shots.json` (copy an existing one; use `kling-video/o3/image-reference` with `refs` for the cast).
2. `python build/hf.py submit <id> ...`, then `python build/hf.py poll` until complete.
3. `python build/hf.py qa <id>` and look at the contact sheet: faces consistent, no garbled text, real audio.
4. Add screen inserts to `inserts/insert.html` (`SCENES.<name> = function(t){...}` returns HTML for time t).
5. Add a scene block to `edit.json` and run `python build/build.py <scene-id>`.

## Prompt rules that work

- One or two short spoken lines per shot, in quotes, 3–12 words each. Say the voice: "confident American female voice".
- Describe the character exactly as in the reference ("the man in the rumpled white shirt and loose tie from the reference image").
- Always end with the style suffix in `shots.json`: **no text, no letters, no logos, no signs**. Models scramble words;
  all words and logos are added by us in inserts and overlays.
- Say what we should hear: dialogue, room tone, the paper thud, the phone slam.
- Spell brand names as they sound ("Connect and Sell") so the voice pronounces them.

## Open before public release

- ConnectAndSell claim ("a week of prospecting in four hours") and use of their name/logo: confirm with ConnectAndSell.
- "2,500 competitive contracts" and "Quantum's AI Lead Finder" (scene 5): confirm the number and product name.
- Music bed: needs a licensed track.
