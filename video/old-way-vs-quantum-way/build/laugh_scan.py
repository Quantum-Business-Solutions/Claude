"""Scan every clip used in edit.json for laughter (AudioSet classifier, 0.5 s hops).
Prints spans where Laughter-family classes score high. Output: build/laughs.json"""
import json, os, subprocess, sys
import numpy as np, torch, imageio_ffmpeg
from transformers import ASTFeatureExtractor, ASTForAudioClassification
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()
M = "MIT/ast-finetuned-audioset-10-10-0.4593"
fe = ASTFeatureExtractor.from_pretrained(M); model = ASTForAudioClassification.from_pretrained(M).eval()
lab = model.config.id2label
LAUGH = [i for i, n in lab.items() if any(k in n.lower() for k in ("laugh", "giggle", "chuckle", "snicker", "belly laugh", "chortle"))]
print("laugh classes:", [lab[i] for i in LAUGH])
def pcm(p):
    r = subprocess.run([FF, "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768
e = json.load(open(os.path.join(ROOT, "edit.json")))
files = sorted({sg["file"] for sc in e["scenes"] for sg in sc["segments"] if sg["type"] == "clip"})
if sys.argv[1:]:  # scan only these, merged into the existing results
    files = sys.argv[1:]
OUT = os.path.join(ROOT, "build", "laughs.json")
out = json.load(open(OUT)) if sys.argv[1:] and os.path.exists(OUT) else {}
WIN, HOP = 1.0, 0.25
for f in files:
    x = pcm(os.path.join(ROOT, f)); rows = []
    for st in np.arange(0, max(len(x) / 16000 - WIN, 0) + 1e-6, HOP):
        seg = x[int(st * 16000): int((st + WIN) * 16000)]
        with torch.no_grad():
            p = torch.sigmoid(model(**fe(seg, sampling_rate=16000, return_tensors="pt")).logits)[0]
        rows.append((round(float(st), 2), float(p[LAUGH].max()), float(p[0])))  # 0 = Speech
    out[f] = rows
    hits = [r for r in rows if r[1] > 0.15]
    print("%-38s max laugh %.2f  %s" % (f, max(r[1] for r in rows), " ".join("%.2f(%.2f)" % (r[0], r[1]) for r in hits)))
json.dump(out, open(OUT, "w"))
