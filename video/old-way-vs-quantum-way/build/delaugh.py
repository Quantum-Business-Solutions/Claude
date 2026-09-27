"""Remove laughter: mute every laugh span found by laugh_scan.py, never touching spoken words.

python build/delaugh.py [threshold]   -> clips/<id>_nl.mp4 (video copied, audio muted in laugh spans)
                                         and edit.json segments repointed to the _nl files.
Spans come from build/laughs.json (1 s windows, 0.25 s hop). Word timings from Whisper protect dialogue:
a laugh window that overlaps a word is cut back to the gap around that word.
"""
import json, os, subprocess, sys
import imageio_ffmpeg
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()
THR = float(sys.argv[1]) if len(sys.argv) > 1 else 0.2
PAD, FADE = 0.05, 0.06


def merge(spans):
    out = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1] + 0.05:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def minus(spans, words):
    """Remove word intervals (padded) from spans."""
    res = []
    for a, b in spans:
        cur = [[a, b]]
        for wa, wb in words:
            wa, wb = wa - PAD, wb + PAD
            nxt = []
            for x, y in cur:
                if wb <= x or wa >= y:
                    nxt.append([x, y]); continue
                if wa > x: nxt.append([x, wa])
                if wb < y: nxt.append([wb, y])
            cur = nxt
        res += [s for s in cur if s[1] - s[0] >= 0.15]
    return res


def main():
    from faster_whisper import WhisperModel
    wm = WhisperModel("small.en", compute_type="int8")
    L = json.load(open(os.path.join(ROOT, "build", "laughs.json")))
    report = {}
    for f, rows in L.items():
        hot = merge([[st, st + 1.0] for st, p, _ in rows if p >= THR])
        if not hot:
            continue
        segs, _ = wm.transcribe(os.path.join(ROOT, f), word_timestamps=True)
        words = [(w.start, w.end) for s in segs for w in s.words]
        # Whisper stretches a word's start back over a preceding laugh; cap words at 0.9 s
        words = [(max(a, b - 0.9), b) for a, b in words]
        spans = minus(hot, words)
        report[f] = {"laugh_windows": hot, "muted": spans, "words": len(words)}
        print("%-40s laugh %s -> mute %s" % (f, [[round(a, 2), round(b, 2)] for a, b in hot], [[round(a, 2), round(b, 2)] for a, b in spans]))
        if not spans:
            continue
        g = "+".join("min(1,max(0,(t-%.3f)/%.3f))*min(1,max(0,(%.3f-t)/%.3f))" % (a - FADE, FADE, b + FADE, FADE) for a, b in spans)
        dst = f.replace(".mp4", "_nl.mp4")
        subprocess.run([FF, "-v", "error", "-y", "-i", os.path.join(ROOT, f), "-map", "0:v", "-map", "0:a", "-c:v", "copy",
                        "-af", "volume=eval=frame:volume='max(0,1-(%s))'" % g, "-c:a", "aac", "-b:a", "192k", os.path.join(ROOT, dst)], check=True)
    json.dump(report, open(os.path.join(ROOT, "build", "delaugh_report.json"), "w"), indent=1)
    e = json.load(open(os.path.join(ROOT, "edit.json")))
    n = 0
    for sc in e["scenes"]:
        for sg in sc["segments"]:
            f = sg.get("file")
            if f and f in report and report[f]["muted"]:
                sg["file"] = f.replace(".mp4", "_nl.mp4"); n += 1
    json.dump(e, open(os.path.join(ROOT, "edit.json"), "w"), indent=2)
    print("repointed", n, "segments")


if __name__ == "__main__":
    main()
