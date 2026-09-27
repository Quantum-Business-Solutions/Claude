"""Floating name tags over people in a (static) shot, e.g. the AI agent names above Maya's team.
python build/float_labels.py <in.mp4> <out.mp4> <start> <end> "Name@x,y" ["Name@x,y" ...]
x,y = the point just above each head in 1920x1080 frame coords. Tags pop in one after another from
<start>, bob gently, and fade out at <end>."""
import json, os, subprocess, sys
import imageio_ffmpeg
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()
JS = r"""
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => { const [dir, A] = process.argv.slice(2); const names = JSON.parse(fs.readFileSync(path.join(dir, 'names.json')));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 520, height: 92 } });
  for (let i = 0; i < names.length; i++) {
    const f = path.join(dir, 'page.html');
    fs.writeFileSync(f, `<!doctype html><meta charset="utf-8"><style>@font-face{font-family:'DM Sans';font-weight:700;src:url(${A}dm-sans-latin-700-normal.woff2)}
      html,body{margin:0;background:transparent}.w{position:absolute;left:0;right:0;top:4px;display:flex;flex-direction:column;align-items:center}
      .t{display:flex;align-items:center;gap:12px;font:700 30px 'DM Sans';color:#06070C;background:#B6FF3C;padding:12px 24px;border-radius:99px;box-shadow:0 0 28px rgba(182,255,60,.75),0 10px 30px rgba(0,0,0,.45)}
      .t img{height:30px}.s{width:3px;height:18px;background:linear-gradient(#B6FF3C,rgba(182,255,60,0))}</style>
      <div class="w"><div class="t"><img src="${A}quantum-q-dark.png">${names[i]}</div><div class="s"></div></div>`);
    await p.goto('file://' + f); await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(dir, 'tag' + i + '.png'), omitBackground: true });
  }
  await b.close(); })();
"""


def main(src, out, a, b, specs):
    d = os.path.join(ROOT, "build", "tmp", "float_labels"); os.makedirs(d, exist_ok=True)
    names = [s.split("@")[0] for s in specs]
    pts = [tuple(float(v) for v in s.split("@")[1].split(",")) for s in specs]
    json.dump(names, open(os.path.join(d, "names.json"), "w"))
    q = os.path.join(ROOT, "assets", "quantum-q-dark.png")
    if not os.path.exists(q):  # dark version of the Q icon for the lime pill
        from PIL import Image
        im = Image.open(os.path.join(ROOT, "assets", "quantum-q.png")).convert("RGBA")
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, bb, al = px[x, y]; px[x, y] = (6, 7, 12, al)
        im.save(q)
    js = os.path.join(d, "tags.js"); open(js, "w").write(JS)
    subprocess.run(["node", js, d, "file://" + os.path.join(ROOT, "assets") + "/"], check=True,
                   env=dict(os.environ, NODE_PATH=subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()))
    ins, fc, last = ["-i", src], [], "0:v"
    for i, (x, y) in enumerate(pts):
        ins += ["-loop", "1", "-i", os.path.join(d, "tag%d.png" % i)]
        st = a + 0.22 * i
        fc.append("[%d:v]format=rgba,scale=iw*0.8:-1,fade=in:st=%.2f:d=0.25:alpha=1,fade=out:st=%.2f:d=0.35:alpha=1[t%d]" % (i + 1, st, b - 0.35, i))
        fc.append("[%s][t%d]overlay=x=%d-w/2:y='%d-h+6*sin(2*PI*t/2.4+%d)':enable='between(t,%.2f,%.2f)':shortest=1[o%d]" % (last, i, x, y, i, st, b, i))
        last = "o%d" % i
    subprocess.run([FF, "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fc), "-map", "[%s]" % last, "-map", "0:a",
                    "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "copy", out], check=True)
    print("labels ->", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5:])
