"""Thought-bubble flashback: freeze a frame of the speaker, pop a cloud bubble out of their head and play a
flashback clip inside it with a faded home-video look.
python build/bubble.py <speaker_clip> <freeze_t> <flashback_clip> <fb_in> <fb_out> <out.mp4>
Layout constants below are for sG2_knew_your_dad (Bob's head right of center)."""
import math, os, subprocess, sys
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1920, 1080
RECT = (46, 50, 730, 435)            # 16:9 core of the cloud
R = 40                                # scallop radius
DOTS = [(846, 520, 16), (876, 570, 23), (916, 628, 30)][::-1]  # from Bob's head up to the cloud (small last)
DOTS = [(846, 352, 11), (817, 322, 16), (786, 290, 22)]


def cloud_mask(scale=1.0):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    x0, y0, x1, y1 = RECT
    d.rounded_rectangle(RECT, radius=R, fill=255)
    per = 2 * ((x1 - x0) + (y1 - y0)); n = int(per / (R * 1.6))
    for i in range(n):
        s = i * per / n
        if s < x1 - x0: x, y = x0 + s, y0
        elif s < (x1 - x0) + (y1 - y0): x, y = x1, y0 + s - (x1 - x0)
        elif s < 2 * (x1 - x0) + (y1 - y0): x, y = x1 - (s - (x1 - x0) - (y1 - y0)), y1
        else: x, y = x0, y1 - (s - 2 * (x1 - x0) - (y1 - y0))
        d.ellipse((x - R, y - R, x + R, y + R), fill=255)
    return m


def main(spk, ft, fb, a, b, out):
    tmp = os.path.join(ROOT, "build", "tmp", "bubble"); os.makedirs(tmp, exist_ok=True)
    m = cloud_mask()
    m.save(os.path.join(tmp, "mask.png"))
    grow = m.filter(ImageFilter.MaxFilter(17))
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = grow.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.55))
    ring.paste((0, 0, 0, 255), (12, 18), sh)
    ring.paste((255, 255, 255, 255), (0, 0), grow)
    ring.save(os.path.join(tmp, "ring.png"))
    dots = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(dots)
    for x, y, r in DOTS:
        dd.ellipse((x - r + 6, y - r + 9, x + r + 6, y + r + 9), fill=(0, 0, 0, 120))
        dd.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 255))
    dots.save(os.path.join(tmp, "dots.png"))
    subprocess.run([FF, "-v", "error", "-y", "-ss", str(ft), "-i", spk, "-frames:v", "1", "-vf", "scale=%d:%d" % (W, H),
                    os.path.join(tmp, "freeze.png")], check=True)
    D = b - a + 0.5
    x0, y0, x1, y1 = RECT
    bw, bh = x1 - x0 + 2 * R + 20, y1 - y0 + 2 * R + 20
    fw = max(bw, int(bh * 16 / 9)); fh = int(fw * 9 / 16)
    fx = (x0 + x1) // 2 - fw // 2; fy = (y0 + y1) // 2 - fh // 2
    fc = ("[0:v]scale=%d:%d,zoompan=z='1+0.00025*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=%dx%d:fps=30,eq=brightness=-0.06:saturation=0.85,boxblur=2:1,setsar=1[bg];" % (W, H, W, H) +
          "[1:v]trim=%s:%s,setpts=PTS-STARTPTS,tpad=start_duration=0.45:start_mode=clone,scale=%d:%d,fps=30,"
          "eq=saturation=0.55:contrast=0.9:brightness=0.03:gamma_r=1.08:gamma_b=0.9,noise=alls=16:allf=t+u,gblur=sigma=0.7,format=rgba[fb];" % (a, b, fw, fh) +
          "color=c=black@0:s=%dx%d:r=30:d=%.3f,format=rgba[cv];[cv][fb]overlay=%d:%d:shortest=1[fbc];" % (W, H, D, fx, fy) +
          "[4:v]format=gray,loop=-1:1:0,trim=0:%.3f[mk];[fbc][mk]alphamerge,fade=in:st=0.3:d=0.25:alpha=1,fade=out:st=%.3f:d=0.3:alpha=1[fbm];" % (D, D - 0.3) +
          "[2:v]format=rgba,loop=-1:1:0,trim=0:%.3f,fade=in:st=0.3:d=0.25:alpha=1,fade=out:st=%.3f:d=0.3:alpha=1[rg];" % (D, D - 0.3) +
          "[3:v]format=rgba,loop=-1:1:0,trim=0:%.3f,fade=in:st=0.05:d=0.2:alpha=1,fade=out:st=%.3f:d=0.3:alpha=1[dt];" % (D, D - 0.3) +
          "[bg][dt]overlay=0:0[b1];[b1][rg]overlay=0:0[b2];[b2][fbm]overlay=0:0,trim=0:%.3f[v];" % D +
          "[1:a]atrim=%s:%s,asetpts=PTS-STARTPTS,adelay=450|450,apad,atrim=0:%.3f,afade=t=out:st=%.3f:d=0.3[a]" % (a, b, D, D - 0.3))
    subprocess.run([FF, "-v", "error", "-y", "-loop", "1", "-t", "%.3f" % D, "-i", os.path.join(tmp, "freeze.png"), "-i", fb,
                    "-i", os.path.join(tmp, "ring.png"), "-i", os.path.join(tmp, "dots.png"), "-i", os.path.join(tmp, "mask.png"),
                    "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", "%.3f" % D, "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", out], check=True)
    print("bubble ->", out, "%.2fs" % D)


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]), sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), sys.argv[6])
