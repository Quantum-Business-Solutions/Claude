"""Lay a music bed under the finished cut, ducking it under dialogue.

python build/mix_music.py            -> build/out/<output>  (music mixed in place of the dry cut)

edit.json "music" maps scene id -> music shot id (a clip in clips/ whose audio is the score).
Adjacent scenes with the same theme share one continuous bed; beds are looped to length and
cross-faded. The dialogue drives a sidechain compressor so the music dips whenever someone talks.
"""
import json, os, subprocess
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()
B = os.path.join(ROOT, "build")
MUSIC_GAIN = 0.28


def dur(path):
    import av
    c = av.open(path)
    return float(c.duration) / 1e6


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2000:]); raise SystemExit("ffmpeg failed")


def main():
    e = json.load(open(os.path.join(ROOT, "edit.json")))
    theme = e.get("music") or {}
    runs = []  # [theme, seconds]
    for sc in e["scenes"]:
        p = os.path.join(B, "scenes", sc["id"] + ".mp4")
        if not os.path.exists(p):
            continue
        t, d = theme.get(sc["id"]), dur(p)
        if runs and runs[-1][0] == t:
            runs[-1][1] += d
        else:
            runs.append([t, d])
    parts = []
    for k, (t, d) in enumerate(runs):
        out = os.path.join(B, "tmp", "bed_%02d.wav" % k)
        if t:
            src = os.path.join(ROOT, "clips", t + ".mp4")
            run([FF, "-y", "-stream_loop", "-1", "-i", src, "-vn", "-t", "%.3f" % d, "-ac", "2", "-ar", "48000",
                 "-af", "afade=t=in:d=0.8,afade=t=out:st=%.3f:d=1.0" % max(0, d - 1.0), out])
        else:
            run([FF, "-y", "-f", "lavfi", "-t", "%.3f" % d, "-i", "anullsrc=r=48000:cl=stereo", out])
        parts.append(out)
    lst = os.path.join(B, "tmp", "beds.txt")
    with open(lst, "w") as f:
        f.writelines("file '%s'\n" % p for p in parts)
    bed = os.path.join(B, "tmp", "bed.wav")
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", bed])
    dry = os.path.join(B, "out", e["output"])
    wet = dry.replace(".mp4", "_music.mp4")
    fc = ("[0:a]asplit=2[d][key];[1:a]volume=%s[m];"
          "[m][key]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=450[md];"
          "[d][md]amix=inputs=2:normalize=0:duration=first[a]" % MUSIC_GAIN)
    run([FF, "-y", "-i", dry, "-i", bed, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", wet])
    print("music mixed ->", wet)


if __name__ == "__main__":
    main()
