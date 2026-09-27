"""One-off: adds the shots for scenes 2-7 to shots.json (idempotent). Kept for the record of prompts used."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "shots.json")
d = json.load(open(p))
P = {"duration": 8, "aspect_ratio": "16:9", "sound": "on", "mode": "pro"}
RICK = "the tired man in the rumpled white shirt and loose tie from the reference image"
RICK2 = "the tired man in the rumpled white shirt and loose tie from the second reference image"
MAYA = "the woman in the grey blazer with her hair pulled back from the reference image"
MAYA2 = "the woman in the grey blazer with her hair pulled back from the second reference image"
BW = "the grinning older man in the beige cardigan, mustard shirt, round glasses and lanyard from the first reference image"
GS = ("The laptop screen is a flat, evenly lit, solid bright chroma-key green filling the entire display, with nothing on it. "
      "Camera locked off on a tripod, completely static.")
NEW = [
    ("s1f_maya_screen", "1-the-dial", ["maya"], 8,
     f"Over-the-shoulder shot from just behind and to the right of {MAYA}, sitting at a bright modern office desk in daytime with a small white earbud in her ear, looking at an open laptop that fills the right half of the frame. {GS} She speaks cheerfully: \"Tuesday at ten works. See you then!\" and taps the trackpad."),
    ("s2a_rick_research", "2-research", ["busywork", "rick"], 8,
     f"Late afternoon in a cluttered office. {RICK2} squints at his monitor, surrounded by printouts and sticky notes, rubbing his temples, and mutters wearily: \"Three hours on one account, and I still don't know who signs.\" Then {BW} drops a thick pile of printouts onto his lap with a thud and says brightly: \"Only three more hours, champ.\" The monitor faces away from camera."),
    ("s2b_maya_screen", "2-research", ["maya"], 8,
     f"Over-the-shoulder shot from just behind and to the right of {MAYA}, at a bright modern office desk, looking at an open laptop that fills the right half of the frame. {GS} She clicks once, leans back with a satisfied smile, glances back over her shoulder at the camera and says: \"Done. Three seconds.\""),
    ("s3a_rick_meeting", "3-the-meeting", ["rick"], 8,
     f"In a small client conference room, {RICK} scribbles frantically on a yellow legal pad, head down, while a woman across the table keeps talking. His pen runs out; he shakes it in frustration, sighs and says under his breath: \"Hang on, can you repeat that?\" Comedic, natural light."),
    ("s3b_maya_meeting", "3-the-meeting", ["maya"], 8,
     f"In a bright client conference room, {MAYA} sits across the table from a friendly female office manager in a navy cardigan. Maya places her phone face-down on the table and says warmly: \"Mind if I turn on my notetaker, so I can give you my full attention?\" The office manager smiles and says: \"Please.\" Maya leans in, fully engaged, eye contact."),
    ("s4a_rick_car", "4-parking-lot", ["busywork", "rick"], 8,
     f"Inside a car in a sunny office parking lot. {RICK2} gets into the driver's seat and tosses a business card onto a messy pile of dozens of business cards on the passenger seat, saying: \"I'll enter that later.\" Then {BW} is revealed sitting in the passenger seat, seatbelt on, grinning at the camera, and says: \"He won't.\""),
    ("s4b_maya_car", "4-parking-lot", ["maya"], 8,
     f"{MAYA} walks confidently out of a glass office building to her car in a sunny parking lot, holding her phone up and speaking into it: \"Claude, log my meeting with Dana, send her the recap, and set a follow-up for Tuesday.\" She smiles as her phone chimes, and gets into her car. Tracking shot."),
    ("s5a_rick_contracts", "5-contracts", ["rick"], 7,
     f"{RICK} sits at his office desk beside a monitor that faces away from camera, next to a filing cabinet with its drawers hanging open and paper contracts spilling out. He turns to the camera with regret and says: \"I wish I'd done a better job tracking contract end dates.\""),
    ("s5b_maya_contracts", "5-contracts", ["maya"], 8,
     f"{MAYA} sits relaxed in a bright modern office, turns to the camera with a confident smile and says: \"I ran every past engagement through Quantum's AI Lead Finder. Twenty-five hundred competitive contracts, coming up.\""),
    ("s6a_rick_latenight", "6-late-night", ["busywork", "rick"], 8,
     f"Night, an empty dark office lit only by a desk lamp. {RICK2} holds a cell phone to his ear, exhausted, and says softly: \"Hey hon... it's going to be another late night.\" Behind him, {BW} cheerfully tips a huge box of envelopes and paper mail over his head; it rains down onto his lap and desk. Comedic."),
    ("s6b_owner_jog", "6-late-night", None, 8,
     "A fit, happy man in his fifties, a business owner, jogging on a scenic riverside trail at golden hour, wearing running gear and a small wireless earbud. He answers a call without stopping, smiling, and says in a relaxed, confident American male voice: \"No problem. I'll get my team on it right away.\" He keeps running, enjoying the sunset. Tracking shot."),
    ("s7a_busywork_finale", "7-finale", ["busywork", "maya"], 8,
     f"In a bright modern office, {BW} peers over the shoulder of {MAYA2}, who is calmly finishing her work and closing her laptop. He looks at the camera, shrugs sadly and says: \"Well... nobody needs me anymore.\" He slowly shuffles out of frame."),
    ("s7b_maya_tagline", "7-finale", ["maya"], 6,
     f"{MAYA} closes her laptop at a bright desk at the end of the day, picks up her bag, turns to the camera and says with a confident smile: \"Same job. Same hours. Different system.\" Warm golden light."),
]
added = []
for sid, scene, refs, dur, prompt in NEW:
    if any(s["id"] == sid for s in d["shots"]):
        continue
    sh = {"id": sid, "scene": scene, "prompt": prompt}
    if refs:
        sh.update(model="kling-video/o3/image-reference", refs=refs, params=dict(P, duration=dur))
    else:
        sh.update(model="kling-video/v3.0/pro/text-to-video", params={"duration": dur, "aspect_ratio": "16:9", "sound": "on"})
    d["shots"].append(sh)
    added.append(sid)
json.dump(d, open(p, "w"), indent=2)
print(" ".join(added))
