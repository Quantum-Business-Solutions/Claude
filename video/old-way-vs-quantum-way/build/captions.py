"""Burn-in captions from the finished cut's own dialogue.

python build/captions.py transcribe <in.mp4>   -> build/captions.json (edit it by hand if a word is wrong)
python build/captions.py burn <in.mp4> <out.mp4>
Chunks: up to 7 words / 2.6 s, split at sentence ends and pauses. FIX maps Whisper spellings to ours.
"""
import json, os, re, subprocess, sys
import imageio_ffmpeg
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()
CJ = os.path.join(ROOT, "build", "captions.json")
PROMPT = "Bog Down Bob, Maya, Rick, Quantum, HubSpot, Connect and Sell, Dana, Riverside, Dr. Reyes."
FIX = [(r"\bBog ?dan\b", "Bog Down"), (r"\bBogdown\b", "Bog Down"), (r"\bConnect ?(and|&) ?Sell\b", "ConnectAndSell"),
       (r"\bHub ?spot\b", "HubSpot"), (r"\bspreadshit\b", "spreadsheet"),
       (r"\bHan\b", "hon"), (r"\b902\b", "9:02"), (r"(\d) ,(\d)", r"\1,\2"), (r" -up\b", "-up"), (r"\bAI lead finder\b", "AI Lead Finder"),
       (r"\bdone button\b", "Done button")]


def transcribe(src):
    from faster_whisper import WhisperModel
    m = WhisperModel("small.en", compute_type="int8")
    segs, _ = m.transcribe(src, word_timestamps=True, initial_prompt=PROMPT, vad_filter=True)
    words = [(w.start, w.end, w.word.strip()) for s in segs for w in s.words if w.word.strip()]
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= 7 or w[1] - cur[0][0] > 2.6 or w[0] - cur[-1][1] > 0.5):
            chunks.append(cur); cur = []
        cur.append(w)
        if re.search(r"[.?!]$", w[2]) and len(cur) >= 2:
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    out = []
    for c in chunks:
        txt = " ".join(x[2] for x in c)
        for a, b in FIX: txt = re.sub(a, b, txt, flags=re.I)
        out.append({"start": round(c[0][0], 2), "end": round(c[-1][1] + 0.25, 2), "text": txt})
    for i in range(len(out) - 2, -1, -1):  # a lone greeting far from its line belongs to the next chunk
        if re.fullmatch(r"(Hi|Hey|Oh|So),?", out[i]["text"]) and out[i + 1]["start"] - out[i]["end"] > 1.5:
            out[i + 1]["text"] = out[i]["text"].rstrip(",") + ", " + out[i + 1]["text"]; out.pop(i)
    for i in range(len(out) - 1):  # no overlaps
        out[i]["end"] = min(out[i]["end"], out[i + 1]["start"])
    json.dump(out, open(CJ, "w"), indent=1)
    for c in out: print("%7.2f %7.2f  %s" % (c["start"], c["end"], c["text"]))


def burn(src, dst):
    caps = json.load(open(CJ))
    d = os.path.join(ROOT, "build", "tmp", "captions"); os.makedirs(d, exist_ok=True)
    json.dump([c["text"] for c in caps], open(os.path.join(d, "list.json"), "w"))
    subprocess.run(["node", os.path.join(ROOT, "build", "render_captions.js"), d], check=True,
                   env=dict(os.environ, NODE_PATH=subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()))
    lines, t = [], 0.0
    for i, c in enumerate(caps):
        if c["start"] > t:
            lines += ["file 'blank.png'", "duration %.3f" % (c["start"] - t)]
        lines += ["file 'c%03d.png'" % i, "duration %.3f" % (c["end"] - c["start"])]
        t = c["end"]
    lines += ["file 'blank.png'", "duration 5", "file 'blank.png'"]
    open(os.path.join(d, "track.txt"), "w").write("\n".join(lines) + "\n")
    subprocess.run([FF, "-v", "error", "-y", "-i", src, "-f", "concat", "-safe", "0", "-i", os.path.join(d, "track.txt"),
                    "-filter_complex", "[1:v]fps=30,format=rgba[c];[0:v][c]overlay=0:0:shortest=1:eof_action=pass[v]",
                    "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "copy", "-movflags", "+faststart", dst], check=True)
    print("captions ->", dst)


if __name__ == "__main__":
    {"transcribe": lambda: transcribe(sys.argv[2]), "burn": lambda: burn(sys.argv[2], sys.argv[3])}[sys.argv[1]]()
