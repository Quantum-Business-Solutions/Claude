# The Old Way vs. The Quantum Way: character bible

Use this to make new videos with the same cast. Everything referenced here lives in this folder of the
`Quantum-Business-Solutions/Claude` repo (`video/old-way-vs-quantum-way/`). Model: Higgsfield
`kling-video/o3/image-reference`, 16:9, `sound: on`, `mode: pro`, 4 to 10 seconds per shot.

## The cast

Pass the reference image in `image_urls` and describe the person the same way every time. With two
references, say "from the first reference image" and "from the second reference image" in the prompt.

| Character | Ref id | Reference image | Describe as |
|---|---|---|---|
| **Bog Down Bob**, the villain: Busywork in human form, a Mayhem-style character. Smug, cheerful, clingy. Never wins. | `busywork` | https://d3snorpfx4xhv8.cloudfront.net/e4d416f7-7355-4276-8c8e-26821a906ac8/bac57b4c-8f34-43cf-9e75-e9f9c8099015.jpeg | "the grinning older man in the beige cardigan, mustard shirt, round glasses and lanyard" · smug older American male voice |
| **Rick**, the old-way rep. Tired, decent, buried. Joins Maya at the end. | `rick` | https://d3snorpfx4xhv8.cloudfront.net/e4d416f7-7355-4276-8c8e-26821a906ac8/9bcd5329-516a-4635-8371-3f4981e51cfb.jpeg | "the tired man in the rumpled white shirt and loose tie" · tired American male voice. Weekend: navy polo shirt. |
| **Maya**, the Quantum-way rep. Calm, confident, always done early. | `maya_face` (use this one) | https://d3snorpfx4xhv8.cloudfront.net/e4d416f7-7355-4276-8c8e-26821a906ac8/436eb159-8bfa-4f93-a44c-7cb9d43c7654.jpeg | "the woman from the reference image, same face, in a grey blazer and white blouse, dark hair pulled back" · confident American female voice |
| Maya's team (her assistant, automation and AI agents as people) | none | | "team members in matching charcoal polo shirts with a thin lime-green collar stripe" |
| Rick's wife | `wife` | https://d3snorpfx4xhv8.cloudfront.net/e4d416f7-7355-4276-8c8e-26821a906ac8/d32e2d82-1508-4d1b-af32-6b8b0c9be542.jpeg | "his wife from the reference image" |
| Rick's son (about 7) | `kid` | https://d3snorpfx4xhv8.cloudfront.net/e4d416f7-7355-4276-8c8e-26821a906ac8/0ab63855-f419-4b63-b1e0-9f94d18d5e13.jpeg | "the boy in a plain blue soccer jersey with no numbers" |
| The businesswoman: turns Bob down ("Pass. We use Quantum.") and delivers the CTA to camera | `blonde` | https://d3snorpfx4xhv8.cloudfront.net/e4d416f7-7355-4276-8c8e-26821a906ac8/2c3d54d8-7f76-449c-82c6-fe2b53be381c.jpeg | "the stunning blonde businesswoman in the navy suit from the reference image" · looks straight into the camera |

The older `maya` reference has a hologram in it. Don't use it: every shot made with it grows floating glowing
screens. Use `maya_face` and describe her outfit in words; that is also how she changes clothes (running gear).

## The world

- **Tone:** Allstate-Mayhem-style comedy. Every scene is one real, relatable sales or marketing task, done the old
  way (Rick and Bob) and then the Quantum way (Maya and her team). Short lines, deadpan beats.
- **The three rungs** Maya's team represents: Rung 01 Assistant (you ask, it answers), Rung 02 Automation (a trigger
  runs it, shown as the little white conveyor belt), Rung 03 Agents (they decide, you approve, shown as the team with
  floating agent-name tags).
- **Running gag:** Maya's round glowing lime-green **Done.** button, with no text on it. Never use Staples' "That was easy".
- **Scoreboard:** selling time this week, Rick 4h 12m vs. Maya 42h, always labelled "Dramatization".
- **Look:** Quantum white logo bottom-right on every frame. Old-way tags are amber (#FFB43C) and Quantum-way tags are
  lime (#B6FF3C), with the Q icon. Fonts: Anton (headlines), DM Sans (body).
- **Tagline:** "Same job. Same hours. Different system." End card: "Leave Bob behind." + thequantumleap.business + QR.

## Bob's catchphrases so far

"I'm Bob. Bog Down Bob. I live in every sales team." · "I'm the voicemail you'll never hear back from." ·
"He won't." · "I'm the file named Final, Final, Version Three." · "I jammed it. You're welcome." · "I'm the 200 unread
emails." · "You forgot to change the name." · "He'll remember. Probably." · "Not so fast. You're with me today." ·
"But... it's always been us." · "I knew your dad." · "Remember the fax machine? Good times." · "Wait! Don't go! We
had something." · "Anybody need some data entry?" · "Got any manual processes? ... I'll see myself out." ·
"Hey... I'm available now."

## Prompt rules that work (learned the hard way)

1. End every prompt with: **"No laughing. No text, no letters, no logos, no signs."** Models scramble words, and
   they add laughter that plays at odd moments. All real words and logos are added afterwards as overlays.
2. **Never write sound words** ("groans", "laughs", "sighs"). The model says them out loud or adds a laugh.
3. One or two short spoken lines per shot, in quotes, 3 to 12 words each, and name the voice.
4. Spell brand names the way they sound: "Hub Spot", "Connect and Sell". Say "Bog... Down... Bob" if a take comes
   out as "Bogdan".
5. Screens face away from camera, or they will show fake gibberish text.
6. Car interiors come out on the wrong side. Shoot cars from outside.
7. Render two takes of anything important and keep the one whose transcript and lip sync are right.

## QA before anything ships

- Transcribe every new clip (faster-whisper) and check that every line is exactly as scripted.
- `python build/laugh_scan.py <clip>`: the max laugh score should be under 0.05.
- `python build/mouth_strip.py <clip> out.jpg <start> <end>`: the mouth opens on the loud syllables.
- After assembling, `python build/sync_qa.py <final.mp4> --true`: every clip within one frame.

## Tools in this folder

`build/hf.py` (submit, poll, fetch renders) · `build/build.py` (assemble from `edit.json`) · `build/mix_music.py` ·
`build/captions.py` · `build/bubble.py` (thought-bubble flashback) · `build/float_labels.py` (floating name tags) ·
`inserts/insert.html` (all screens: HubSpot, ConnectAndSell, inbox, scoreboard, end card). README.md explains the
workflow. `shots.json` holds every shot's exact prompt, and is the best place to copy from.
