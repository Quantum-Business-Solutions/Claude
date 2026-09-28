"""Pacing pass: find dead air before the first word / after the last word of each dialogue segment.
python build/tighten.py          -> report only
python build/tighten.py --apply  -> write the trims into edit.json
Leaves alone clips whose payoff is visual (listed in KEEP) and gaps under the thresholds."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEAD, TAIL = 0.6, 1.1          # trim only gaps longer than these
PRE, POST = 0.3, 0.7          # breathing room kept around the words
KEEP = ("sC_done_button", "g6_conveyor", "sI_bob_alone", "sJ_leg_drag", "g7_fax", "g9_available", "sK_game",
        "g10_cta", "sF_grab", "s6b_maya_jog", "sH_", "s1f_maya_screen", "s2b_maya_screen", "g4_copier", "sB_conveyor", "sD_agents_dinner", "g8_stinger", "n3_reply_all", "n8_bob_done", "sG3_bubble", "sH_welcome", "g10_cta", "sL_kid", "sK_game")
def main():
    from faster_whisper import WhisperModel
    wm = WhisperModel("small.en", compute_type="int8")
    e = json.load(open(os.path.join(ROOT, "edit.json"))); saved = 0
    for sc in e["scenes"]:
        for sg in sc["segments"]:
            f = sg.get("file")
            if not f or any(k in f for k in KEEP):
                continue
            segs, _ = wm.transcribe(os.path.join(ROOT, f), word_timestamps=True)
            a, b = sg.get("in", 0), sg["out"]
            ws = [(max(w.start, w.end - 0.9), w.end) for s in segs for w in s.words if w.end > a and w.start < b]
            if not ws:
                continue
            na, nb = a, b
            if ws[0][0] - a > LEAD: na = round(ws[0][0] - PRE, 2)
            if b - ws[-1][1] > TAIL: nb = round(ws[-1][1] + POST, 2)
            if (na, nb) != (a, b):
                saved += (na - a) + (b - nb)
                print("%-34s %5.2f-%5.2f -> %5.2f-%5.2f  (-%.1fs)" % (os.path.basename(f), a, b, na, nb, (na - a) + (b - nb)))
                if "--apply" in sys.argv: sg["in"], sg["out"] = na, nb
    print("total saved %.1f s" % saved)
    if "--apply" in sys.argv: json.dump(e, open(os.path.join(ROOT, "edit.json"), "w"), indent=2)
main()
