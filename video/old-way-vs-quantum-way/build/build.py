"""Assemble the ad from edit.json.

python build/build.py            -> renders every scene to build/scenes/<scene>.mp4 and joins them into build/out/<title>.mp4
python build/build.py 1-the-dial -> renders just that scene (then re-joins everything)

Every segment is normalised to 1920x1080, 30 fps, AAC 48 kHz stereo, with the Quantum logo bottom-right.
To extend the ad: render new shots with hf.py, add a scene block to edit.json, run this again.
"""
import json, os, subprocess, sys
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()
B = os.path.join(ROOT, "build")
LOGO = os.path.join(ROOT, "assets", "quantum-white.png")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2500:]); raise SystemExit("ffmpeg failed")


def tag_png(text, color):
    out = os.path.join(B, "tmp", "tag_%s.png" % text.replace(" ", "_"))
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subprocess.run(["node", os.path.join(B, "render_inserts.js"), "--tag", text, color, out], check=True,
                       env=dict(os.environ, NODE_PATH=subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()))
    return out


def insert_frames(name, secs):
    d = os.path.join(B, "tmp", name)
    if not (os.path.isdir(d) and len(os.listdir(d)) >= round(secs * 30)):
        subprocess.run(["node", os.path.join(B, "render_inserts.js"), name, str(secs)], check=True,
                       env=dict(os.environ, NODE_PATH=subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()))
    return os.path.join(d, "f%04d.png")


def segment(seg, out):
    """Render one segment with logo and optional tag."""
    inputs, fc = [], []
    if seg["type"] == "clip":
        src = os.path.join(ROOT, seg["file"])
        inputs += ["-ss", str(seg.get("in", 0))]
        if "out" in seg:
            inputs += ["-to", str(seg["out"])]
        inputs += ["-i", src]
        dur = seg["out"] - seg.get("in", 0) if "out" in seg else None
        fc.append("[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,setsar=1[v0]")
        audio = "[0:a]aresample=48000,aformat=channel_layouts=stereo[a]"
    else:  # insert
        dur = seg["secs"]
        inputs += ["-framerate", "30", "-i", insert_frames(seg["name"], dur)]
        inputs += ["-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo"]
        z = seg.get("zoom", 1.06)
        fc.append("[0:v]scale=1920:1080,zoompan=z='min(1+(%s-1)*on/%d,%s)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,setsar=1[v0]" % (z, int(dur * 30), z))
        audio = "[1:a]anull[a]"
    n = len([x for x in inputs if x == "-i"])
    inputs += ["-i", LOGO]
    li = n; n += 1
    fc.append("[%d:v]scale=300:-1,format=rgba,colorchannelmixer=aa=0.88[lg]" % li)
    fc.append("[v0][lg]overlay=W-w-54:H-h-44[v1]")
    last = "v1"
    if seg.get("tag"):
        t = seg["tag"]
        inputs += ["-loop", "1", "-t", str(t.get("dur", 2.4)), "-i", tag_png(t["text"], t["color"])]
        ti = n; n += 1
        d = t.get("dur", 2.4); st = t.get("at", 0.3)
        fc.append("[%d:v]format=rgba,fade=in:st=0:d=0.15:alpha=1,fade=out:st=%s:d=0.3:alpha=1,setpts=PTS+%s/TB[tg]" % (ti, d - 0.3, st))
        fc.append("[%s][tg]overlay=0:0:eof_action=pass[v2]" % last)
        last = "v2"
    fc.append(audio.replace("[a]", "[a0]"))
    fc.append("[a0]afade=t=in:st=0:d=0.05[a]")
    cmd = [FF, "-y"] + inputs + ["-filter_complex", ";".join(fc), "-map", "[%s]" % last, "-map", "[a]"]
    if dur:
        cmd += ["-t", str(dur)]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    run(cmd)


def build_scene(scene):
    os.makedirs(os.path.join(B, "scenes", "parts"), exist_ok=True)
    parts = []
    for i, seg in enumerate(scene["segments"]):
        p = os.path.join(B, "scenes", "parts", "%s_%02d.mp4" % (scene["id"], i))
        segment(seg, p)
        parts.append(p)
    out = os.path.join(B, "scenes", scene["id"] + ".mp4")
    concat(parts, out)
    print("scene", scene["id"], "->", out)
    return out


def concat(parts, out):
    lst = out + ".txt"
    with open(lst, "w") as f:
        for p in parts:
            f.write("file '%s'\n" % p)
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    os.remove(lst)


if __name__ == "__main__":
    edit = json.load(open(os.path.join(ROOT, "edit.json")))
    only = sys.argv[1:]
    outs = []
    for sc in edit["scenes"]:
        path = os.path.join(B, "scenes", sc["id"] + ".mp4")
        if not only or sc["id"] in only:
            path = build_scene(sc)
        if os.path.exists(path):
            outs.append(path)
        else:
            print("skipping unbuilt scene", sc["id"])
    os.makedirs(os.path.join(B, "out"), exist_ok=True)
    final = os.path.join(B, "out", edit["output"])
    concat(outs, final)
    print("final ->", final)
