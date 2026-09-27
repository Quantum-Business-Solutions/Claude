"""v2 story: Manny Manual intro, Maya's team (assistant / automation / agents), the Done button gag,
Saturday, the breakup and Rick joining Maya. Idempotent: prints the ids it added."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "shots.json")
d = json.load(open(p))
P = {"aspect_ratio": "16:9", "sound": "on", "mode": "pro"}
RICK = "the tired man in the rumpled white shirt and loose tie"
MAYA = "the woman in the grey blazer with her hair pulled back"
MANNY = "the grinning older man in the beige cardigan, mustard shirt, round glasses and lanyard"
TEAM = "team members in matching charcoal polo shirts with a thin lime-green collar stripe"
NEW = [
    ("s0_cold_open_v2", "0-cold-open", ["busywork", "rick"], 8,
     f"{MANNY} from the first reference image perches casually on the edge of a cluttered office desk where {RICK} from the second reference image sits on a desk phone. The cardigan man looks straight into the camera and says in a smug, playful older American male voice: \"I'm Manny. Manny Manual. I live in every sales team.\" Then he tips a huge stack of business cards onto the tired man's lap; cards scatter everywhere and the tired man groans. Comedic, punchy, slight push-in."),
    ("sA_assistant", "2-research", ["maya"], 7,
     f"{MAYA} from the reference image sits at a bright modern desk. Without looking away from her work she asks: \"Who signs at Riverside?\" One of her {TEAM}, a sharp young man standing right beside her desk holding a tablet, answers instantly: \"Doctor Reyes. Dana recommends.\" She smiles: \"Perfect.\" Crisp, fast, witty."),
    ("sB_conveyor", "5-contracts", ["maya"], 7,
     f"{MAYA} from the reference image sits at a bright modern desk. Beside her desk a small sleek white conveyor belt glides past, delivering neat folders one after another with a soft whir. She glances over, picks up the next folder without breaking stride, and says with a grin: \"Next.\" Playful, slightly surreal, no text on the folders."),
    ("sC_done_button", "gag", ["maya"], 4,
     f"Close-up at a bright modern desk: the hand of {MAYA} from the reference image taps a large round glowing lime-green button on the desk; it lights up with a satisfying chime. She says, relaxed and pleased: \"Done.\" The button has no text or symbols on it."),
    ("sD_agents_dinner", "6-late-night", ["maya"], 8,
     f"Early evening in a bright modern office. {MAYA} from the reference image sits at her desk while behind her four {TEAM} work calmly and efficiently at screens facing away from camera. A friendly coworker in a denim jacket leans in and asks: \"Want to grab dinner?\" Maya glances back at her busy team, smiles, and says: \"Yeah... I think they've got it from here.\" She grabs her bag and stands up."),
    ("sE_rick_saturday", "7-saturday", ["rick"], 8,
     f"Saturday morning in a sunny family kitchen. {RICK} from the reference image, now in a wrinkled polo shirt, hunches over a laptop and piles of paperwork at the kitchen table. His wife, in a team sports hoodie and holding car keys, stands in the doorway with two kids in soccer uniforms behind her and says: \"Honey, it's Saturday. The kids have a game today.\" He looks up guiltily: \"I know, I know. I'm coming.\""),
    ("sF_manny_grab", "7-saturday", ["busywork", "rick"], 7,
     f"In the same sunny family kitchen, {RICK} from the second reference image stands up from the table to leave. {MANNY} from the first reference image suddenly appears beside him, grabs his arm firmly and says with a wicked grin: \"Not so fast. You're with me today.\" Then he throws his head back and lets out a big theatrical villain laugh. Comedic."),
    ("sG_breakup", "8-the-switch", ["busywork", "rick"], 8,
     f"A cluttered office. {MANNY} from the first reference image clings to the arm of {RICK} from the second reference image. The tired man finally pulls his arm free, stands tall and says firmly: \"I can't do this anymore.\" The cardigan man, wounded and pleading, clutches his chest and says: \"But... it's always been us.\" Comedic breakup-scene drama, soap-opera lighting."),
    ("sH_rick_joins", "8-the-switch", ["maya", "rick"], 8,
     f"A bright modern open-plan office. {RICK} from the second reference image walks up to the desk of {MAYA} from the first reference image, a little sheepish. She smiles warmly. One of her {TEAM} rolls a chair over for him; he sits down, relieved, and she says: \"Welcome to the team.\" He exhales and laughs. Uplifting, warm light."),
    ("sI_manny_alone", "8-the-switch", ["busywork"], 7,
     f"Night. {MANNY} from the reference image sits alone in a dark, empty office on an overturned box of paper files, under one flickering fluorescent light. He looks around the empty room and calls out hopefully: \"Anybody? ... Anybody need a spreadsheet?\" Silence. A single sheet of paper drifts to the floor. Comedic, melancholy."),
]
added = []
for sid, scene, refs, dur, prompt in NEW:
    if any(s["id"] == sid for s in d["shots"]):
        continue
    d["shots"].append({"id": sid, "scene": scene, "model": "kling-video/o3/image-reference", "refs": refs,
                       "params": dict(P, duration=dur), "prompt": prompt})
    added.append(sid)
json.dump(d, open(p, "w"), indent=2)
print(" ".join(added))
