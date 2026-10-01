#!/bin/bash
# Score lipsync candidates: amplitude/jitter (mediapipe) + embedded audio alignment vs source.
set -e
mkdir -p /home/user/lm && cd /home/user/lm
pip install -q "mediapipe==0.10.14" "opencv-python-headless<5" "numpy<2" 2>&1 | tail -1
R=https://raw.githubusercontent.com/yogayoga12/pudu-roi/nina-tmp
curl -sf -o lipmetric.py "$R/lipmetric.py?v=2"
C=https://d8j0ntlcm91z4.cloudfront.net/user_3HajHmutxaxSZa2X1DVn1D7kSaS/hf_20261001_
A=https://d2ol7oe51mr4n9.cloudfront.net/user_3HajHmutxaxSZa2X1DVn1D7kSaS/
while read n f; do [ -f $n.mp4 ] || curl -sf -o $n.mp4 $C$f.mp4; done <<'L'
c_S06a 224836_3e57b187-2933-4719-8911-6dd3a1b0b270
c_S06b 225153_8db72b65-b575-4e93-aa21-64612fb688b0
c_S09a1 225154_bab4ebd7-d329-4bf4-930f-72da05d67035
c_S09a2 225152_002ec164-35cc-4d22-9e06-076bf475f4ff
c_S09b1 225152_706a1bfb-8a4d-4bdf-919d-29ab7d35359a
c_S09b2 225152_abc24bf7-02f8-4db0-9d8e-4adb0ccac9ea
c_S10a1 224835_5659e80f-a3a1-4f5c-883f-b9d3eba4c801
c_S10a2 224834_3e91916f-f4d8-4f69-961f-3855810ba22c
c_S10b1 225152_bf413f69-d7f7-4654-9986-47fadd676adf
c_S10b2 225152_393364ed-46be-4e75-940f-7559932a3694
c_S121 225152_97acb5d8-ef34-400d-9c7a-33c1fec5de6c
c_S122 225152_9e2c6545-28e8-4b83-92de-a801a5e86f96
c_S01 225153_e5247608-67ac-4c1f-a7c9-0e852a567d5b
c_S04 225152_d8ea3a37-2eea-44e2-879a-03a74a54185e
L
[ -f c_S10aO.mp4 ] || curl -sf -o c_S10aO.mp4 ${A}bf2ed4ca-baf5-4944-8ccb-b57ea1a265b0.mp4
while read n f; do [ -f $n.mp3 ] || curl -sf -o $n.mp3 $A$f.mp3; done <<'L'
S01 7a713aa7-e5e4-4bb0-ab0f-f05fe3ac5799
S04 acb30197-2664-4851-8bf2-12a6d3a986ce
S06 510387a6-19c2-469c-bec1-801b3335025b
S09a cf248db9-e2e5-4d8e-9eec-3ce2e8a89eb8
S09b b5304a76-9e8b-47de-9812-86ce10e57afb
S10a 137b1a06-9ff0-420b-b397-9fca96a71749
S10b 5b58cf03-2aee-46de-b2fb-ea8bfa34127a
S12 d158808d-b5d7-4f6e-a584-b15c1f9a4458
L
python3 - <<'P' 2>/dev/null
import sys, subprocess, glob, re, numpy as np
sys.argv = ['x']; exec(open('lipmetric.py').read().split('args = sys.argv')[0])
def pcm(p): return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar','8000','-f','s16le','-'],capture_output=True).stdout,np.int16).astype(np.float32)
for v in sorted(glob.glob('c_*.mp4')):
    sid = re.match(r'c_(S\d+[ab]?)', v).group(1); a = sid + '.mp3'
    x = pcm(v)[:8000*6]; y = pcm(a)[:8000*4]; lag = np.argmax(np.correlate(x, y, 'valid')) / 8
    subprocess.run(['ffmpeg','-v','error','-y','-i',v,'-r','30','-an','/tmp/t30.mp4'])
    m, _ = mouth('/tmp/t30.mp4'); m = m[~np.isnan(m)]; d = np.abs(np.diff(m))
    dur = float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',v],capture_output=True,text=True).stdout)
    print(f"SCORE {v:14s} lag={lag:5.1f}ms dur={dur:5.2f} p95={np.percentile(m,95):.3f} p50={np.percentile(m,50):.3f} closed%={np.mean(m<0.015)*100:3.0f} jitter={d.mean()*1000:4.1f}", flush=True)
P
echo SCOREDONE
