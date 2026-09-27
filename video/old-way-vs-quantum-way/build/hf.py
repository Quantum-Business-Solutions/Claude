"""Higgsfield helper for the Quantum video productions.

Usage:
  python build/hf.py upload refs/rick_ref.jpg          -> prints public URL
  python build/hf.py submit <shot_id>                   -> submits a shot from shots.json
  python build/hf.py poll                               -> checks every submitted shot, downloads finished ones
  python build/hf.py qa <shot_id>                       -> contact sheet + audio level for a downloaded clip
  python build/hf.py fetch                              -> re-download finished clips on a fresh checkout

Needs HIGGSFIELD_API_KEY in the environment ("id:secret").
Every shot's request id and output URL are written back into shots.json, so the
production can be resumed or extended at any time.
"""
import json, os, sys, time, urllib.request, mimetypes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "shots.json")
API = "https://platform.higgsfield.ai"
UA = "Mozilla/5.0 (quantum-videographer)"


def _req(method, path, body=None):
    key = os.environ["HIGGSFIELD_API_KEY"]
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={"Authorization": "Key " + key, "Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())


def upload(path):
    ctype = mimetypes.guess_type(path)[0] or "image/jpeg"
    meta = _req("POST", "/files/generate-upload-url", {"content_type": ctype})
    with open(path, "rb") as f:
        hdrs = {"Content-Type": ctype}
        hdrs.update(meta.get("upload_headers") or {})
        put = urllib.request.Request(meta["upload_url"], data=f.read(), method="PUT", headers=hdrs)
        urllib.request.urlopen(put, timeout=120).read()
    return meta["public_url"]


def load():
    with open(SHOTS) as f:
        return json.load(f)


def save(d):
    with open(SHOTS, "w") as f:
        json.dump(d, f, indent=2)


def submit(shot_id):
    d = load()
    shot = next(s for s in d["shots"] if s["id"] == shot_id)
    body = dict(shot["params"])
    body["prompt"] = shot["prompt"] + " " + d["style_suffix"]
    if shot.get("refs"):
        body["image_urls"] = [d["refs"][r] for r in shot["refs"]]
    res = _req("POST", "/" + shot["model"], body)
    shot["request_id"] = res["request_id"]
    shot["status"] = "queued"
    save(d)
    print(shot_id, res["request_id"])


def poll():
    d = load()
    for s in d["shots"]:
        if s.get("request_id") and s.get("status") not in ("completed", "failed"):
            st = _req("GET", "/requests/%s/status" % s["request_id"])
            s["status"] = st["status"]
            if st["status"] == "completed":
                url = (st.get("video") or st.get("images", [{}])[0]).get("url")
                s["output_url"] = url
                ext = ".mp4" if url.endswith(".mp4") else os.path.splitext(url)[1]
                out = os.path.join(ROOT, "clips", s["id"] + ext)
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=300) as r, open(out, "wb") as f:
                    f.write(r.read())
                s["file"] = os.path.relpath(out, ROOT)
            print(s["id"], s["status"])
    save(d)


def qa(shot_id, sheet_dir=None):
    import av, numpy as np
    from PIL import Image
    path = os.path.join(ROOT, "clips", shot_id + ".mp4")
    c = av.open(path)
    level = None
    if c.streams.audio:
        pk, rms = 0, []
        for fr in c.decode(c.streams.audio[0]):
            x = fr.to_ndarray().astype(float)
            pk = max(pk, abs(x).max()); rms.append(np.sqrt((x ** 2).mean()))
        level = (round(float(pk), 2), round(float(np.mean(rms)), 3))
    c = av.open(path)
    frames = [f.to_image() for f in c.decode(video=0)]
    picks = [frames[int(len(frames) * p)] for p in (0.1, 0.4, 0.7, 0.95)]
    sheet = Image.new("RGB", (1280, 720))
    for i, im in enumerate(picks):
        sheet.paste(im.resize((640, 360)), ((i % 2) * 640, (i // 2) * 360))
    out = os.path.join(sheet_dir or os.path.join(ROOT, "build"), shot_id + "_sheet.jpg")
    sheet.save(out)
    print(shot_id, "frames", len(frames), "audio(peak,rms)", level, "sheet", out)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "upload":
        print(upload(sys.argv[2]))
    elif cmd == "submit":
        for sid in sys.argv[2:]:
            submit(sid)
    elif cmd == "poll":
        poll()
    elif cmd == "fetch":  # re-download every finished clip (clips/ is not in git)
        d = load()
        for s in d["shots"]:
            if s.get("output_url") and s.get("file") and not os.path.exists(os.path.join(ROOT, s["file"])):
                with urllib.request.urlopen(urllib.request.Request(s["output_url"], headers={"User-Agent": UA}), timeout=300) as r, open(os.path.join(ROOT, s["file"]), "wb") as f:
                    f.write(r.read())
                print("fetched", s["id"])
    elif cmd == "qa":
        qa(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
