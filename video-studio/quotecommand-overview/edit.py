#!/usr/bin/env python3
"""Assemble the QuoteCommand film from recorded scenes, cards, narration and music."""
import json, os, subprocess, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import labels as LB

FF = __import__("os").environ.get("FFMPEG") or __import__("imageio_ffmpeg").get_ffmpeg_exe()
D = os.path.dirname(os.path.abspath(__file__))
OUT = f"{D}/out"; os.makedirs(f"{OUT}/items", exist_ok=True); os.makedirs(f"{OUT}/segs", exist_ok=True)
FONT = f"{D}/fonts/Poppins-600.ttf"; FONT5 = f"{D}/fonts/Poppins-500.ttf"
VO = json.load(open(f"{D}/vo_durations.json"))
SCRIPT = {c["id"]: c["vo"] for c in json.load(open(f"{D}/script.json"))["chapters"]}
FPS = 30
VO_LEAD = 0.45      # narration starts this long into its scene
TAIL = 0.75         # breath after the narration before the cut

def run(args):
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y"] + args, capture_output=True, text=True)
    if r.returncode: print("FFMPEG FAIL", " ".join(args)[:400], r.stderr[-1500:]); sys.exit(1)

def meta(rid):
    p = f"{D}/rec/{rid}/meta.json"
    return json.load(open(p)) if os.path.exists(p) else None

def card_ready(name):
    return json.load(open(f"{D}/cards/{name}.json"))["ready"] / 1000

def esc(t): return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")

PHONE_BG = f"{OUT}/phone_bg.png"
def phone_bg():
    if os.path.exists(PHONE_BG): return
    run(["-f", "lavfi", "-i", "gradients=s=1920x1080:c0=0x0B1F3A:c1=0x081528:x0=0:y0=0:x1=1920:y1=1080:d=1", "-frames:v", "1", PHONE_BG])

def seg(kind, src, dur, out, start=0.0, caption=None):
    """Render one segment of exactly `dur` seconds, 1920x1080@30, no audio."""
    tail = f"tpad=stop_mode=clone:stop_duration=60,trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p"
    if kind == "card":
        s = card_ready(src) + 0.05 + start
        run(["-ss", f"{s:.3f}", "-i", f"{D}/cards/{src}.webm", "-vf", f"fps={FPS},scale=1920:1080,{tail}", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17", out])
    elif kind == "rec":
        m = meta(src); rd = (m or {}).get("marks", {}).get("ready")
        raw = f"{D}/rec/{src}/raw.webm"
        if rd is None or not os.path.exists(raw):
            return seg("still", f"{D}/rec/{src}/last.png" if os.path.exists(f"{D}/rec/{src}/last.png") else f"{D}/explore/cfg.png", dur, out)
        s = rd / 1000 + 0.25 + start
        run(["-ss", f"{s:.3f}", "-i", raw, "-vf", f"fps={FPS},scale=1920:1080:flags=lanczos,{tail}", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17", out])
    elif kind == "phone":
        phone_bg()
        m = meta(src); rd = (m or {}).get("marks", {}).get("ready", 0)
        s = rd / 1000 + 0.25 + start
        cap = caption or "On a phone"
        capf = out + ".cap.png"; LB.phone_caption(cap, "390 px · one hand · the same app", capf)
        fc = (f"[1:v]fps={FPS},scale=-2:960:flags=lanczos,pad=iw+16:ih+16:8:8:color=0x1c3358[ph];"
              f"[0:v][ph]overlay=x=1060:y=(H-h)/2:shortest=1[b];[b][2:v]overlay=0:0,{tail}")
        run(["-loop", "1", "-i", PHONE_BG, "-ss", f"{s:.3f}", "-i", f"{D}/rec/{src}/raw.webm", "-loop", "1", "-i", capf, "-filter_complex", fc, "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-t", f"{dur:.3f}", out])
    elif kind == "still":
        n = int(dur * FPS)
        run(["-loop", "1", "-i", src, "-vf", f"scale=1920:1080,zoompan=z='min(1+0.0004*on,1.08)':d={n}:s=1920x1080:fps={FPS},{tail}", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-t", f"{dur:.3f}", out])

def concat(files, out):
    lst = out + ".txt"
    open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])

# ── the timeline ────────────────────────────────────────────────────────────
L = lambda t: t
TL = [
  dict(vo="s00", segs=[("card", "relay", 22.45), ("card", "promise", None)]),
  dict(vo="s01", segs=[("rec", "s01", None)], label="Home · your dealership, your brand"),
  dict(card="ch1"),
  dict(vo="s02", segs=[("rec", "s02", None)], label="Fleet · Northwind Orthopedics"),
  dict(vo="s03", segs=[("rec", "s03", None)], label="Fleet assessment"),
  dict(card="ch2"),
  dict(vo="s04", segs=[("rec", "s04", None)], label="Configurator · Quick start"),
  dict(vo="s05", segs=[("rec", "s05", 0.377), ("rec", "s05b", None)], label="Configurator · 10,844 compatibility rules"),
  dict(card="ch3"),
  dict(vo="s06", segs=[("rec", "s06", None)], label="Margin guardrails"),
  dict(vo="s07", segs=[("rec", "s07", 0.55), ("phone", "s07p", None, "Approvals, anywhere")], label="Approvals inbox"),
  dict(vo="s08", segs=[("rec", "s08", None)], label="Leasing · rate cards"),
  dict(vo="s09", segs=[("rec", "s09", None)], label="Takeover · lease buyout"),
  dict(vo="s10", segs=[("rec", "s10", None)], label="Service · priced from real meter reads"),
  dict(card="ch4"),
  dict(vo="s11", segs=[("rec", "s11", None)], label="Proposal builder"),
  dict(vo="s12", segs=[("rec", "s12", 0.70), ("phone", "s12p", None, "Reads on a phone")], label="The customer's link · no login"),
  dict(vo="s13", segs=[("rec", "s13", None)], label="Choose an option · ask a question"),
  dict(vo="s14", segs=[("rec", "s14", None)], label="Customer engagement", start=4.0),
  dict(card="ch5"),
  dict(vo="s15", segs=[("rec", "s15", None)], label="Document Hub · 15 document types"),
  dict(vo="s16", segs=[("rec", "s16", None)], label="Signed orders · audit trail"),
  dict(card="ch6"),
  dict(vo="s17", segs=[("rec", "s17", None)], label="Orders · nine stages, each with a clock"),
  dict(vo="s18", segs=[("rec", "s18", None)], label="Inside an order"),
  dict(vo="s19", segs=[("rec", "s19", None)], label="ERP push · e-automate via CEO Juice"),
  dict(card="ch7"),
  dict(vo="s20", segs=[("rec", "s20", None)], label="HubSpot"),
  dict(card="ch8"),
  dict(vo="s21", segs=[("rec", "s21", None)], label="View as rep"),
  dict(vo="s22", segs=[("rec", "s22", None)], label="Teams & access"),
  dict(vo="s23", segs=[("rec", "s23", None)], label="Commissions"),
  dict(vo="s24", segs=[("rec", "s24", None)], label="Analytics · audit log"),
  dict(card="ch9"),
  dict(vo="s25", segs=[("phone", "s25", None, "Quick quote")], label=None),
  dict(vo="s26", segs=[("rec", "s26", None)], label="Connect Claude · MCP"),
  dict(vo="s27", montage=[("s01", 0.0, 2.9), ("s06", 1.0, 2.9), ("s12", 2.0, 1.8), ("s16", 4.0, 1.8), ("s17", 2.0, 2.9),
                          ("s23", 1.0, 3.0), ("s02", 3.0, 3.2), ("s18", 2.0, 3.6)], end="end"),
]

def build():
    items = []; t = 0.0; vo_events = []; captions = []
    lim = int(os.environ.get('LIMIT', '999'))
    for i, it in enumerate(TL[:lim]):
        name = f"{OUT}/items/{i:02d}.mp4"
        if "card" in it:
            d = json.load(open(f"{D}/cards/{it['card']}.json"))["ms"] / 1000 - 0.1
            seg("card", it["card"], d, f"{OUT}/segs/{i:02d}a.mp4")
            run(["-i", f"{OUT}/segs/{i:02d}a.mp4", "-vf", f"fade=t=out:st={d-0.35:.3f}:d=0.35", "-c:v", "libx264", "-crf", "17", name])
            items.append(name); t += d; continue
        vd = VO[it["vo"]]; dur = VO_LEAD + vd + TAIL
        segfiles = []
        if "montage" in it:
            used = 0.0
            for k, (rid, off, ln) in enumerate(it["montage"]):
                f = f"{OUT}/segs/{i:02d}_{k}.mp4"; seg("rec", rid, ln, f, start=off); segfiles.append(f); used += ln
            endd = max(4.0, dur - used + 2.5)
            f = f"{OUT}/segs/{i:02d}_end.mp4"; seg("card", it["end"], endd, f); segfiles.append(f); dur = used + endd
        else:
            left = dur
            for k, sgt in enumerate(it["segs"]):
                kind, src, frac = sgt[0], sgt[1], sgt[2]
                ln = left if frac is None else (frac if kind == "card" and frac > 1 else dur * frac)
                ln = min(ln, left) if frac is not None else left
                f = f"{OUT}/segs/{i:02d}_{k}.mp4"
                seg(kind, src, ln, f, start=(it.get("start", 0.0) if k == 0 else 0.0), caption=sgt[3] if len(sgt) > 3 else None); segfiles.append(f); left -= ln
        body = f"{OUT}/segs/{i:02d}_body.mp4"
        concat(segfiles, body) if len(segfiles) > 1 else os.replace(segfiles[0], body)
        fades = f"fade=t=in:st=0:d=0.3,fade=t=out:st={dur-0.3:.3f}:d=0.3"
        if it.get("label"):
            lf = f"{OUT}/segs/{i:02d}_label.png"; LB.label(it["label"], lf)
            fc = (f"[1:v]format=rgba,fade=t=in:st=0.5:d=0.5:alpha=1,fade=t=out:st=4.2:d=0.5:alpha=1[lb];"
                  f"[0:v][lb]overlay=0:0:shortest=1,{fades}")
            run(["-i", body, "-loop", "1", "-t", f"{dur:.3f}", "-i", lf, "-filter_complex", fc, "-c:v", "libx264", "-preset", "medium", "-crf", "17", name])
        else:
            run(["-i", body, "-vf", fades, "-c:v", "libx264", "-preset", "medium", "-crf", "17", name])
        items.append(name)
        vo_events.append((f"{D}/vo/{it['vo']}.mp3", t + VO_LEAD))
        captions.append((t + VO_LEAD, t + VO_LEAD + vd, SCRIPT[it["vo"]]))
        t += dur
        print(f"{i:02d} {it.get('vo')} {dur:.1f}s  t={t:.1f}", flush=True)
    return items, t, vo_events, captions

def srt(captions, path):
    def ts(x): h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return f"{h:02d}:{m:02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    out = []; n = 1
    for a, b, text in captions:
        parts = [p.strip() for p in re.split(r"(?<=[.?!:])\s+", text) if p.strip()]
        chunks = []
        for p in parts:
            words = p.split()
            while len(words) > 14: chunks.append(" ".join(words[:12])); words = words[12:]
            chunks.append(" ".join(words))
        total = sum(len(c) for c in chunks); cur = a
        for c in chunks:
            d = (b - a) * len(c) / total
            out.append(f"{n}\n{ts(cur)} --> {ts(cur + d)}\n{c}\n"); n += 1; cur += d
    open(path, "w").write("\n".join(out))

if __name__ == "__main__":
    items, total, vo_events, captions = build()
    concat(items, f"{OUT}/video.mp4")
    ins = []; fl = []
    for k, (p, st) in enumerate(vo_events):
        ins += ["-i", p]; ms = int(st * 1000)
        fl.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{k}]")
    n = len(vo_events)
    ins += ["-i", f"{D}/music_bed.wav"]
    fl.append("".join(f"[v{k}]" for k in range(n)) + f"amix=inputs={n}:normalize=0:dropout_transition=0,apad,atrim=duration={total:.3f},asplit=2[vo][sc]")
    fl.append(f"[{n}:a]aresample=48000,atrim=duration={total:.3f},volume=0.42,afade=t=in:d=3,afade=t=out:st={total-5:.3f}:d=5[mu]")
    fl.append("[mu][sc]sidechaincompress=threshold=0.015:ratio=8:attack=20:release=650:makeup=1[md]")
    fl.append("[vo][md]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    run(ins + ["-filter_complex", ";".join(fl), "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", f"{OUT}/audio.m4a"])
    run(["-i", f"{OUT}/video.mp4", "-i", f"{OUT}/audio.m4a", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", f"{OUT}/QuoteCommand-overview.mp4"])
    srt(captions, f"{OUT}/QuoteCommand-overview.srt")
    print(f"DONE total {total/60:.2f} min")
