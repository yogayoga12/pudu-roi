# Lip-sync quality metric: mouth opening (MediaPipe FaceMesh) vs speech envelope.
# usage: python3 lipmetric.py NAME VIDEO AUDIO [NAME VIDEO AUDIO ...]
import sys, subprocess, numpy as np, cv2
import mediapipe as mp

def envelope(audio, n, fps=30):
    x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', audio, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                                     capture_output=True).stdout, np.int16).astype(np.float32) / 32768
    hop = 16000 // fps
    e = np.array([np.sqrt((x[i * hop:(i + 1) * hop] ** 2).mean()) if i * hop < len(x) else 0 for i in range(n)])
    return e

def mouth(video):
    fm = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, refine_landmarks=True, max_num_faces=1)
    cap = cv2.VideoCapture(video); out = []
    while True:
        ok, fr = cap.read()
        if not ok: break
        r = fm.process(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        if not r.multi_face_landmarks: out.append(np.nan); continue
        L = r.multi_face_landmarks[0].landmark
        gap = abs(L[14].y - L[13].y); width = abs(L[291].x - L[61].x) + 1e-6; face = abs(L[152].y - L[10].y) + 1e-6
        out.append(gap / face)
    return np.array(out), cap.get(cv2.CAP_PROP_FPS) or 30

args = sys.argv[1:]
for i in range(0, len(args), 3):
    name, v, a = args[i:i + 3]
    m, fps = mouth(v)
    if abs(fps - 30) > 0.5:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', v, '-r', '30', '/tmp/_m30.mp4']); m, fps = mouth('/tmp/_m30.mp4')
    e = envelope(a, len(m))
    ok = ~np.isnan(m); det = ok.mean()
    mm = np.where(ok, m, np.nanmean(m))
    sm = lambda z: np.convolve(z, np.ones(3) / 3, 'same')
    mm, ee = sm(mm), sm(e)
    best = (-9, 0)
    for lag in range(-12, 13):
        if lag >= 0: x, y = mm[lag:], ee[:len(ee) - lag]
        else: x, y = mm[:lag], ee[-lag:]
        k = min(len(x), len(y)); r = np.corrcoef(x[:k], y[:k])[0, 1]
        if r > best[0]: best = (r, lag)
    speech = ee > np.percentile(ee, 60); sil = ee < np.percentile(ee, 20)
    act = mm[speech].mean() / (mm[sil].mean() + 1e-6)
    print(f"{name:10s} r={best[0]:.3f} lag={best[1]:+d}f ({best[1]*33:+d}ms) r0={np.corrcoef(mm,ee)[0,1]:.3f} open_speech/silence={act:.2f} meanopen={np.nanmean(m):.3f} face={det:.2f}", flush=True)
