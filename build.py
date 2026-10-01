# -*- coding: utf-8 -*-
# Nina monthly news — segment renderer + final assembly (runs in Higgsfield sandbox)
import os, subprocess, json, re, sys, math, numpy as np
from concurrent.futures import ThreadPoolExecutor
W, H, FPS = 1920, 1080, 30
CDN_A = 'https://d2ol7oe51mr4n9.cloudfront.net/user_3HajHmutxaxSZa2X1DVn1D7kSaS/'
CDN_G = 'https://d8j0ntlcm91z4.cloudfront.net/user_3HajHmutxaxSZa2X1DVn1D7kSaS/'
SPEC = json.load(open('spec.json'))
ASSETS = {k: v.replace('a:', CDN_A).replace('g:', CDN_G + 'hf_20261001_') for k, v in SPEC['assets'].items()}
for _s in SPEC['segments']:
    if 'subs' in _s: _s['subs'] = [c if isinstance(c, list) else [c, c] for c in _s['subs']]
os.makedirs('a', exist_ok=True); os.makedirs('s', exist_ok=True)

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print('FAIL', cmd[:300], r.stderr[-1500:]); raise SystemExit(1)
    return r.stdout

SS = {}
for _k, _v in list(ASSETS.items()):
    if '#ss=' in _v: _v, _ss = _v.split('#ss='); ASSETS[_k] = _v; SS[_k] = float(_ss)
def fetch(k):
    url = ASSETS[k]; ext = url.split('?')[0].rsplit('.', 1)[-1].lower()
    p = f'a/{k}.{ext}'
    if not os.path.exists(p): sh(f"curl -sfL -A 'Mozilla/5.0 (compatible; NinaNewsVideo/1.0; +https://pertechtual.co.jp)' -o {p} '{url}'")
    return p
with ThreadPoolExecutor(12) as ex: PATHS = dict(zip(ASSETS, ex.map(fetch, ASSETS)))

def dur(p): return float(sh(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {p}").strip())

def pcm(p):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768

def chunk_times(audio, weights, offset):
    """Map subtitle chunks to time by distributing over voiced frames (silence-aware)."""
    x = pcm(audio); fr = 320; n = len(x) // fr
    e = np.sqrt((x[:n * fr].reshape(n, fr) ** 2).mean(1)) if n else np.zeros(1)
    thr = max(0.012, np.percentile(e, 60) * 0.25)
    v = e > thr
    idx = np.where(v)[0]
    if len(idx) == 0: idx = np.arange(n); v[:] = True
    voiced = v.copy()
    prev = idx[0]
    for i in idx[1:]:
        if 1 < i - prev <= 22: voiced[prev:i] = True
        prev = i
    vt = np.where(voiced)[0]; total = len(vt)
    cum = np.cumsum([0] + weights) / sum(weights)
    res = []
    for i in range(len(weights)):
        a = vt[min(int(cum[i] * total), total - 1)] * fr / 16000
        b = vt[min(int(cum[i + 1] * total) - 1, total - 1)] * fr / 16000 + 0.12
        res.append((offset + a, offset + b))
    # make contiguous display (extend to next start, but no more than 0.6s past speech)
    out = []
    for i, (a, b) in enumerate(res):
        nb = res[i + 1][0] - 0.02 if i + 1 < len(res) else b + 0.4
        out.append((a, min(nb, b + 0.6)))
    return out

from PIL import Image, ImageFilter
def prep_still(k, p):
    im = Image.open(p).convert('RGB')
    # trim dark letterbox bars
    g = im.convert('L'); px = g.load(); w, h = im.size
    cols = [x for x in range(w) if sum(px[x, y] for y in range(0, h, max(1, h // 50))) / (h // max(1, h // 50) + 1) > 60]
    if k.startswith('u_') and cols and (cols[0] > w * 0.03 or cols[-1] < w * 0.97): im = im.crop((cols[0], 0, cols[-1] + 1, h))
    w, h = im.size; ar = w / h
    if 1.3 <= ar <= 2.0:
        if k.startswith('u_'): out = f'a/{k}_169.png'; im.save(out); return out
        return p
    bg = im.resize((1920, int(1920 / ar)) if ar < 16 / 9 else (int(1080 * ar), 1080))
    bw, bh = bg.size; bg = bg.crop(((bw - 1920) // 2, (bh - 1080) // 2, (bw - 1920) // 2 + 1920, (bh - 1080) // 2 + 1080))
    bg = bg.filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(v * 0.45))
    if ar < 1.6:
        fh = 1000; fw = int(fh * ar); fg = im.resize((fw, fh), Image.LANCZOS); cx = int(1920 * 0.30)
        bg.paste(fg, (max(40, cx - fw // 2), 40))
    else:
        fw = 1760; fh = int(fw / ar); fg = im.resize((fw, fh), Image.LANCZOS); bg.paste(fg, (80, (1080 - fh) // 2))
    out = f'a/{k}_169.png'; bg.save(out); return out
for _k, _p in list(PATHS.items()):
    if _p.lower().endswith(('.png', '.jpg', '.jpeg')): PATHS[_k] = prep_still(_k, _p)

def face_cx(video):
    try:
        import cv2
        cap = cv2.VideoCapture(video); cap.set(cv2.CAP_PROP_POS_MSEC, 800); ok, fr = cap.read()
        if not ok: return None
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        cc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        fs = cc.detectMultiScale(g, 1.1, 6, minSize=(fr.shape[1] // 12, fr.shape[1] // 12))
        if len(fs) == 0: return None
        x, y, w, h = max(fs, key=lambda f: f[2] * f[3]); return (x + w / 2) / fr.shape[1]
    except Exception as e:
        print('face err', e); return None

ENC = '-c:v libx264 -preset veryfast -crf 19 -pix_fmt yuv420p -r 30'
SCALE = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"

def shot(src, d, outp, i):
    p = PATHS[src]
    if p.endswith(('.mp4', '.webm', '.mov')):
        ss = SS.get(src, 0)
        sh(f"ffmpeg -v error -y -stream_loop -1 -ss {ss} -i {p} -t {d + 1:.3f} -vf {SCALE},fps={FPS},tpad=stop_mode=clone:stop_duration=30 -frames:v {int(round(d * FPS))} -an {ENC} {outp}")
    else:
        fr = int(round(d * FPS)) + 2; z = ['min(zoom+0.0007,1.15)', 'if(eq(on,0),1.15,max(zoom-0.0007,1.0))'][i % 2]
        xs = ["iw/2-(iw/zoom/2)", "iw/2-(iw/zoom/2)+on*0.4"][i % 3 == 2]
        sh(f"ffmpeg -v error -y -loop 1 -i {p} -vf \"scale=2400:1350:force_original_aspect_ratio=increase,crop=2400:1350,zoompan=z='{z}':x='{xs}':y='ih/2-(ih/zoom/2)':d={fr}:s={W}x{H}:fps={FPS},setsar=1\" -t {d:.3f} {ENC} {outp}")

def build(seg):
    sid = seg['id']; out = f"s/{sid}.mkv"
    pad = seg.get('pad', 0.35)
    if seg['type'] == 'card':
        d = math.ceil(seg['dur'] * FPS) / FPS; base = f"s/{sid}_base.mp4"
        if 'bg' in seg: shot(seg['bg'], d, base, 0)
        else: sh(f"ffmpeg -v error -y -f lavfi -i color=c=0x0F1A30:s={W}x{H}:r={FPS} -t {d} {ENC} {base}")
        audio_in = f"-f lavfi -t {d} -i anullsrc=r=48000:cl=stereo"; total = d
    else:
        aud = PATHS[seg['audio']]; ad = dur(aud); total = math.ceil((ad + pad) * FPS) / FPS
        seg['_ad'] = ad
        if seg['type'] == 'A':
            base = f"s/{sid}_base.mp4"
            cx = face_cx(PATHS[seg['video']]); cx = 0.5 if cx is None else cx
            side = 'R' if cx <= 0.5 else 'L'; seg['_side'] = side
            Z = 1.15; tgt = 0.36 if side == 'R' else 0.64
            off = int(min(max(cx * W * Z - tgt * W, 0), W * Z - W))
            print(sid, 'face', round(cx, 3), 'side', side, 'off', off, flush=True)
            sh(f"ffmpeg -v error -y -i {PATHS[seg['video']]} -vf {SCALE},scale={int(W*Z)}:{int(H*Z)},crop={W}:{H}:{off}:{int((H*Z-H)/2)},fps={FPS},tpad=stop_mode=clone:stop_duration=3 -t {total:.3f} -an {ENC} {base}")
        else:
            times = chunk_times(aud, [len(c[1]) for c in seg['subs']], 0)
            seg['_ct'] = times
            starts = [0.0] + [times[s[1]][0] for s in seg['shots'][1:]] + [total]
            parts = []
            for i, s in enumerate(seg['shots']):
                d = max(0.5, starts[i + 1] - starts[i]); pp = f"s/{sid}_{i}.mp4"; shot(s[0], d, pp, i); parts.append(pp)
            open(f"s/{sid}_l.txt", 'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p in parts))
            base = f"s/{sid}_base.mp4"; sh(f"ffmpeg -v error -y -f concat -safe 0 -i s/{sid}_l.txt -c copy {base}")
        audio_in = f"-i {aud}"
    # overlays: [png, start, end]; start/end can be number or 'cN' (chunk N start) / 'end'
    ct = seg.get('_ct')
    if seg['type'] == 'A' and seg.get('subs'):
        ct = chunk_times(PATHS[seg['audio']], [len(c[1]) for c in seg['subs']], 0); seg['_ct'] = ct
    if seg['type'] == 'card' and seg.get('subs'): seg['_ct'] = []
    def T(v):
        if isinstance(v, (int, float)): return float(v)
        if v == 'end': return total
        return ct[int(v[1:])][0]
    ovs = [[o[0][:-1] + '_' + seg.get('_side', 'R')] + o[1:] if o[0].endswith('@') else o for o in seg.get('ov', [])]
    inputs = ' '.join(f"-loop 1 -framerate 30 -t {total:.3f} -i g/{o[0]}.png" for o in ovs)
    fc = ['[0:v]tpad=stop_mode=clone:stop_duration=10[b0]']; last = '[b0]'
    for k, o in enumerate(ovs):
        a, b = T(o[1]), T(o[2]); fi = min(0.25, (b - a) / 3)
        fc.append(f"[{k + 2}:v]format=rgba,fade=in:st={a:.2f}:d={fi:.2f}:alpha=1,fade=out:st={max(a, b - fi):.2f}:d={fi:.2f}:alpha=1[o{k}]")
        fc.append(f"{last}[o{k}]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[v{k}]"); last = f'[v{k}]'
    fc.append(f"{last}format=yuv420p[vout]")
    NF = int(round(total * FPS)); NS = int(round(total * 48000))
    fc.append(f"[1:a]aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo,apad=whole_len={NS},atrim=end_sample={NS},asetpts=PTS-STARTPTS[aout]")
    sh(f"ffmpeg -v error -y -i {base} {audio_in} {inputs} -filter_complex \"{';'.join(fc)}\" -map '[vout]' -map '[aout]' -t {total:.6f} {ENC} -c:a pcm_s16le -ar 48000 {out}")
    seg['_total'] = total
    return seg

segs = SPEC['segments']
with ThreadPoolExecutor(6) as ex: segs = list(ex.map(build, segs))

# ---------- subtitles (ASS) ----------
def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
       "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Sub,BIZ UDPGothic,58,&H00FFFFFF,&H00FFFFFF,&H00301A0F,&H96000000,-1,0,0,0,100,100,1,0,1,5,2,2,120,120,54,1", "",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
def wrap(t, lim=25):
    if len(t) <= lim: return t
    mid = len(t) / 2; cands = [i + 1 for i, ch in enumerate(t) if ch in '、。！？」' and 6 < i + 1 < len(t) - 4]
    k = min(cands, key=lambda i: abs(i - mid)) if cands else int(mid)
    return t[:k] + '\\N' + t[k:]
t0 = 0.0
for seg in segs:
    for i, c in enumerate(seg.get('subs', [])):
        a, b = seg['_ct'][i]
        ass.append(f"Dialogue: 0,{ts(t0 + a)},{ts(t0 + b)},Sub,,0,0,0,,{wrap(c[0])}")
    t0 += seg['_total']
open('subs.ass', 'w').write('\n'.join(ass) + '\n')
open('list.txt', 'w').write(''.join(f"file 's/{seg['id']}.mkv'\n" for seg in segs))
sh("ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy body.mkv")
for _st in ('v', 'a'):
    print('body', _st, sh(f"ffprobe -v error -select_streams {_st}:0 -count_packets -show_entries stream=nb_read_packets,duration -of csv=p=0 body.mkv").strip(), flush=True)
print('expected', round(t0, 3), 'frames', int(round(t0 * FPS)), flush=True)
# BGM: loop, duck under voice, louder on cards
bgm = PATHS['bgm']
sh(f"ffmpeg -v error -y -i body.mkv -stream_loop -1 -i {bgm} -filter_complex "
   f"\"[1:a]aresample=48000,volume=0.30,afade=t=in:d=1.5,afade=t=out:st={t0 - 4:.2f}:d=4[m];"
   f"[0:a]asplit=2[v1][v2];[m][v1]sidechaincompress=threshold=0.02:ratio=8:attack=40:release=500[md];"
   f"[v2][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11[a];"
   f"[0:v]ass=subs.ass:fontsdir=f[v]\" -map '[v]' -map '[a]' -t {t0:.3f} -c:v libx264 -preset veryfast -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart final.mp4")
print('DONE', round(t0, 2), dur('final.mp4'))
json.dump([{'id': s['id'], 'total': s['_total']} for s in segs], open('timeline.json', 'w'))
