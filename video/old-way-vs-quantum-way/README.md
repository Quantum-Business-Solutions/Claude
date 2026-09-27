# The Old Way vs. The Quantum Way

Quantum's ad series: every scene is one real sales or marketing task, done the old way (Rick, buried by
Bog Down Bob, our Mayhem-style villain, ref id `busywork`) and the Quantum way (Maya and her team: an
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
| `build/build.py` | Assembles scenes to MP4 with the Quantum logo bottom-right, then joins them (audio re-cut sample-accurately at every join). `--rejoin` re-joins without re-rendering; `EDIT=edit_30.json` builds the 30-second cut. |
| `build/mix_music.py` | Lays the music bed under the cut, ducked under dialogue, loudness-normalized to -14 LUFS. |
| `build/captions.py` | Transcribes the finished cut and burns in captions (`transcribe`, then `burn`). |
| `build/bubble.py` | Thought-bubble flashback: freezes the speaker and plays a clip in a cloud with a home-video look. |
| `build/sync_qa.py` | A/V sync check: where every clip's audio lands in the final cut vs. its picture. Should read 0 ms. |
| `build/mouth_strip.py` | Lip-sync check: face crops every 0.1 s with the audio level printed on each. |
| `build/laugh_scan.py`, `build/delaugh.py` | Find laughter (AudioSet classifier) and mute it without touching dialogue. |
| `build/tighten.py` | Pacing pass: trims dead air before the first word and after the last. |

Video files are not in git. On a fresh checkout run `python build/hf.py fetch`, then download
`shots.json` → `reused` into `clips/` by name.

## Add a scene

1. Add shots to `shots.json` (copy an existing one; use `kling-video/o3/image-reference` with `refs` for the cast).
2. `python build/hf.py submit <id> ...`, then `python build/hf.py poll` until complete.
3. `python build/hf.py qa <id>` and look at the contact sheet: faces consistent, no garbled text, real audio.
4. Add screen inserts to `inserts/insert.html` (`SCENES.<name> = function(t){...}` returns HTML for time t).
5. Add a scene block to `edit.json` and run `python build/build.py <scene-id>`.

## QA before every publish

1. `python build/sync_qa.py build/out/<cut>.mp4`: every clip at 0 ms.
2. `python build/laugh_scan.py <new clips>`: max laugh under 0.05 (we keep laughter out of the ad).
3. Whisper transcript of the full cut: every line reads as scripted (watch for "Bogdan", mangled brand names).
4. `python build/mouth_strip.py` on any new speaking shot: mouth opens on the loud syllables.

## Prompt rules that work

- One or two short spoken lines per shot, in quotes, 3–12 words each. Say the voice: "confident American female voice".
- Describe the character exactly as in the reference ("the man in the rumpled white shirt and loose tie from the reference image").
- Always end with the style suffix in `shots.json`: **no text, no letters, no logos, no signs**. Models scramble words;
  all words and logos are added by us in inserts and overlays.
- Say what we should hear: dialogue, room tone, the paper thud, the phone slam. Never write sound words like "laughs" or "groans": the model voices them or adds laughter. Add "No laughing."
- When clothes must change (Maya jogging), use a face-only reference (`refs/maya_face.jpg`) or the outfit carries over.
- Spell brand names as they sound ("Connect and Sell") so the voice pronounces them.

## Open before public release

- ConnectAndSell claim ("a week of prospecting in four hours") and use of their name/logo: confirm with ConnectAndSell.
- "2,500 competitive contracts" and "Quantum's AI Lead Finder" (scene 5): confirm the number and product name.
- Music bed: needs a licensed track.
