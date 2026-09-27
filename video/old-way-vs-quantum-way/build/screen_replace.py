"""Put a rendered screen insert onto a green laptop screen in a generated shot.

python build/screen_replace.py <clip.mp4> <insert_name> <out.mp4> [screen_start_seconds]

Finds the chroma-green screen in each frame, fits its four corners (smoothed over time so it doesn't jitter),
warps the insert's matching frame into it, and keeps anything in front of the screen (a hand, an earbud)
because only green pixels are replaced. Audio is copied from the clip.
"""
import os, subprocess, sys
import cv2, numpy as np
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()


def green_mask(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (38, 70, 70), (88, 255, 255))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return m


def quad(mask):
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cs:
        return None
    c = max(cs, key=cv2.contourArea)
    if cv2.contourArea(c) < 0.02 * mask.size:
        return None
    hull = cv2.convexHull(c)
    for eps in (0.02, 0.03, 0.05, 0.08):
        ap = cv2.approxPolyDP(hull, eps * cv2.arcLength(hull, True), True)
        if len(ap) == 4:
            break
    else:
        r = cv2.minAreaRect(c); ap = cv2.boxPoints(r).reshape(-1, 1, 2)
    pts = ap.reshape(4, 2).astype(np.float32)
    s = pts.sum(1); d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], np.float32)  # tl,tr,br,bl


def main(clip, insert, out, start=0.0):
    frames_dir = os.path.join(ROOT, "build", "tmp", insert)
    n_ins = len([f for f in os.listdir(frames_dir) if f.endswith(".png")])
    cap = cv2.VideoCapture(clip)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    w, h = int(cap.get(3)), int(cap.get(4))
    tmp = out + ".video.mp4"
    enc = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (w, h), "-r", str(fps), "-i", "-",
                            "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    # pass 1: the camera is locked off, so find the screen once, from the frames where it is fully visible
    quads = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        q = quad(green_mask(fr))
        if q is not None:
            quads.append((cv2.contourArea(q.reshape(-1, 1, 2)), q))
    if not quads:
        raise SystemExit("no green screen found")
    top = max(a for a, _ in quads)
    Q = np.median(np.array([q for a, q in quads if a >= 0.97 * top]), axis=0).astype(np.float32)
    region = np.zeros((h, w), np.uint8)
    cv2.fillConvexPoly(region, cv2.convexHull(Q.astype(np.int32)), 255)
    region = cv2.dilate(region, np.ones((9, 9), np.uint8))
    cap.release(); cap = cv2.VideoCapture(clip)
    i = 0; hits = len(quads)
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        m = cv2.bitwise_and(green_mask(fr), region)  # only green pixels on the screen itself
        if m.any():
            t = max(0.0, i / fps - start)
            k = min(n_ins - 1, int(t * 30))
            src = cv2.imread(os.path.join(frames_dir, "f%04d.png" % k))
            sh, sw = src.shape[:2]
            H = cv2.getPerspectiveTransform(np.float32([[0, 0], [sw, 0], [sw, sh], [0, sh]]), Q)
            warp = cv2.warpPerspective(src, H, (w, h), flags=cv2.INTER_LINEAR)
            a = cv2.GaussianBlur(cv2.dilate(m, np.ones((3, 3), np.uint8)), (5, 5), 0).astype(np.float32)[..., None] / 255.0
            fr = (fr * (1 - a) + np.clip(warp * 1.02, 0, 255) * a).astype(np.uint8)
        enc.stdin.write(fr.tobytes())
        i += 1
    enc.stdin.close(); enc.wait(); cap.release()
    subprocess.run([FF, "-y", "-i", tmp, "-i", clip, "-map", "0:v", "-map", "1:a?", "-c:v", "copy", "-c:a", "aac", "-shortest", out],
                   check=True, capture_output=True)
    os.remove(tmp)
    print("frames", i, "screen found in", hits, "->", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 0.0)
