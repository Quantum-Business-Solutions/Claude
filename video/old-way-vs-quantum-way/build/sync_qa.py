"""A/V sync QA: for every clip segment, find where its source audio actually lands in the final cut
(cross-correlation) and compare with where its picture lands (the timeline). Offset > 40 ms = visible."""
import json, os, subprocess, sys
import numpy as np, imageio_ffmpeg
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 8000
def pcm(path, ss, t):
    r = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % max(ss, 0), "-t", "%.3f" % t, "-i", path, "-vn", "-ac", "1",
                        "-ar", str(SR), "-f", "s16le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32)
def main(final):
    e = json.load(open(os.path.join(ROOT, os.environ.get("EDIT", "edit.json"))))
    import av
    t = 0.0; rows = []
    for sc in e["scenes"]:
        for i, sg in enumerate(sc["segments"]):
            d = (sg["out"] - sg.get("in", 0)) if sg["type"] == "clip" else sg["secs"]
            part = os.path.join(ROOT, "build", "scenes", "parts", "%s_%02d.mp4" % (sc["id"], i))
            if os.path.exists(part):  # the real picture length (whole frames), not the nominal one
                vs = av.open(part).streams.video[0]; d = float(vs.duration * vs.time_base)
            if sg["type"] == "clip":
                src = pcm(os.path.join(ROOT, sg["file"]), sg.get("in", 0) + 0.3, min(2.5, d - 0.4))
                W = 0.6
                dst = pcm(final, t + 0.3 - W, len(src) / SR + 2 * W)
                if src.std() > 30 and len(dst) > len(src):
                    c = np.correlate(dst - dst.mean(), src - src.mean(), "valid")
                    lag = (np.argmax(c) / SR) - W
                    conf = c.max() / (np.linalg.norm(src) * np.linalg.norm(dst[:len(src)]) + 1e-9)
                else:
                    lag, conf = float("nan"), 0
                rows.append((sc["id"], os.path.basename(sg["file"]), t, lag, conf))
                print("%-16s %-32s at %7.2f  audio offset %+6.0f ms  (match %.2f)" % (sc["id"], rows[-1][1], t, lag * 1000, conf))
            t += d
    print("timeline total %.2f s" % t)


def frames(path, ss, t, w=96, h=54):
    r = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % max(ss, 0), "-t", "%.3f" % t, "-i", path, "-vf",
                        "fps=30,scale=%d:%d,format=gray" % (w, h), "-f", "rawvideo", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, h, w).astype(np.float32)


def true_sync(final):
    """Picture lag (frame matching) vs audio lag (cross-correlation) per clip; the difference is the real error."""
    import av
    e = json.load(open(os.path.join(ROOT, os.environ.get("EDIT", "edit.json"))))
    t = 0.0; worst = 0
    for sc in e["scenes"]:
        st = t
        for i, sg in enumerate(sc["segments"]):
            part = os.path.join(ROOT, "build", "scenes", "parts", "%s_%02d.mp4" % (sc["id"], i))
            vs = av.open(part).streams.video[0]; d = float(vs.duration * vs.time_base)
            if sg["type"] == "clip" and d > 1.6:
                ref = frames(part, 0.6, 0.04)[0]
                W = 0.4; win = frames(final, t + 0.6 - W, 2 * W + 0.04)
                pl = (np.argmin([((f - ref) ** 2).mean() for f in win]) / 30.0) - W
                src = pcm(part, 0.3, min(1.2, d - 0.4)); A = 0.4
                dst = pcm(final, t + 0.3 - A, len(src) / SR + 2 * A)
                al = (np.argmax(np.correlate(dst - dst.mean(), src - src.mean(), "valid")) / SR - A) if src.std() > 30 else float("nan")
                err = (al - pl) * 1000
                if not np.isnan(err): worst = max(worst, abs(err))
                print("%-16s %-30s picture %+5.0f ms  audio %+5.0f ms  sync error %+5.0f ms" % (sc["id"], os.path.basename(sg["file"]), pl * 1000, al * 1000, err))
            t += d
    print("worst sync error %.0f ms" % worst)


if __name__ == "__main__":
    f = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "build/out/old-way-vs-quantum-way-v4.mp4")
    true_sync(f) if "--true" in sys.argv else main(f)
