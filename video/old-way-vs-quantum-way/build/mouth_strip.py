"""Lip-sync check: a strip of frames every 0.1 s (face crop) with the audio loudness of that instant printed on each.
python build/mouth_strip.py clip.mp4 out.jpg start end [x y w h]"""
import sys, subprocess, numpy as np, imageio_ffmpeg, os
FF = imageio_ffmpeg.get_ffmpeg_exe()
src, out, a, b = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
crop = sys.argv[5:9]
r = subprocess.run([FF, "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True)
x = np.frombuffer(r.stdout, np.int16).astype(np.float32)
from PIL import Image, ImageDraw
ts = np.arange(a, b, 0.1); tiles = []
for t in ts:
    w = x[int((t - .05) * 8000): int((t + .05) * 8000)]
    db = 20 * np.log10(np.sqrt((w ** 2).mean()) + 1) if len(w) else 0
    vf = ("crop=%s:%s:%s:%s," % (crop[2], crop[3], crop[0], crop[1]) if crop else "") + "scale=240:-2"
    r = subprocess.run([FF, "-v", "error", "-ss", "%.3f" % t, "-i", src, "-frames:v", "1", "-vf", vf, "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    import io
    im = Image.open(io.BytesIO(r.stdout)).convert("RGB"); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 240, 22], fill=(0, 0, 0)); d.text((5, 5), "%.1fs  %2.0f dB %s" % (t, db, "#" * max(0, int((db - 40) / 4))), fill=(255, 230, 0))
    tiles.append(im)
cols = 8; W, H = tiles[0].size; rows = -(-len(tiles) // cols)
sheet = Image.new("RGB", (cols * W, rows * H))
for i, im in enumerate(tiles):
    sheet.paste(im, ((i % cols) * W, (i // cols) * H))
sheet.save(out, quality=85)
