"""Pin a rendered screen onto a monitor in a moving shot: track the monitor with SIFT features from the
first frame, carry the screen's four corners through each frame's homography, and warp the screen in.
python build/screen_track.py <in.mp4> <frames_dir> <out.mp4> <until_s> x0,y0 x1,y1 x2,y2 x3,y3 [start_s]
   (TL TR BR BL corners at start_s, default 0; the screen is composited from start_s to until_s)"""
import os, subprocess, sys, glob
import cv2, numpy as np, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
src, fdir, out, until = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
quad0 = np.float32([[float(v) for v in p.split(",")] for p in sys.argv[5:9]])
start = float(sys.argv[9]) if len(sys.argv) > 9 else 0.0
shots = sorted(glob.glob(os.path.join(fdir, "f*.png")))
cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS); W = int(cap.get(3)); H = int(cap.get(4))
tmp = out + ".v.mp4"
wr = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(fps), "-i", "-",
                       "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
sift = cv2.SIFT_create(4000); bf = cv2.BFMatcher()
cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(start * fps))); ok, f0 = cap.read(); cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
g0 = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
mask = np.zeros_like(g0); x0, y0 = quad0.min(0).astype(int); x1, y1 = quad0.max(0).astype(int)
cv2.rectangle(mask, (max(0, x0 - 250), max(0, y0 - 120)), (min(W, x1 + 50), min(H, y1 + 260)), 255, -1)
k0, d0 = sift.detectAndCompute(g0, mask)
ok, frame = cap.read(); i, Hprev, first = 0, np.eye(3), True
while ok:
    t = i / fps
    if start - 1e-6 <= t < until and shots:
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        k, d = sift.detectAndCompute(g, None)
        Hm = Hprev
        if d is not None and len(k) > 20:
            m = [a for a, b in bf.knnMatch(d0, d, k=2) if a.distance < 0.72 * b.distance]
            if len(m) > 25:
                A = np.float32([k0[x.queryIdx].pt for x in m]); B = np.float32([k[x.trainIdx].pt for x in m])
                Hn, inl = cv2.findHomography(A, B, cv2.RANSAC, 3.0)
                if Hn is not None: Hm = Hn if first else 0.5 * Hprev + 0.5 * Hn  # light smoothing
        Hprev, first = Hm, False
        q = cv2.perspectiveTransform(quad0[None], Hm)[0]
        scr = cv2.imread(shots[min(len(shots) - 1, int(round((t - start) * 30)))])
        sh, sw = scr.shape[:2]
        P = cv2.getPerspectiveTransform(np.float32([[0, 0], [sw, 0], [sw, sh], [0, sh]]), q)
        warp = cv2.warpPerspective(scr, P, (W, H), flags=cv2.INTER_AREA)
        mk = cv2.warpPerspective(np.full((sh, sw), 255, np.uint8), P, (W, H))
        mk = cv2.GaussianBlur(mk, (5, 5), 0).astype(np.float32)[..., None] / 255.0
        warp = cv2.GaussianBlur(warp, (3, 3), 0).astype(np.float32) * 0.93 + 6  # screen glow, slightly soft like the lens
        frame = (frame.astype(np.float32) * (1 - mk) + warp * mk).clip(0, 255).astype(np.uint8)
    wr.stdin.write(frame.tobytes()); i += 1
    ok, frame = cap.read()
wr.stdin.close(); wr.wait()
subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-i", src, "-map", "0:v", "-map", "1:a", "-c", "copy", out], check=True); os.remove(tmp)
print("screen ->", out)
