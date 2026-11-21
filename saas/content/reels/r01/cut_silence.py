"""Keeps speech, shortens every pause to GAP seconds. usage: cut_silence.py in.wav out.wav [gap] [pad]"""
import subprocess, sys, re, numpy as np, soundfile as sf
src, dst = sys.argv[1], sys.argv[2]
gap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.14
pad = float(sys.argv[4]) if len(sys.argv) > 4 else 0.06
log = subprocess.run(["ffmpeg", "-i", src, "-af", "silencedetect=noise=-35dB:d=0.15", "-f", "null", "-"], capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
if ends and (not starts or ends[0] < starts[0]):
    starts = [0.0] + starts
a, sr = sf.read(src)
dur = len(a) / sr
sil = list(zip(starts, ends + [dur] * (len(starts) - len(ends))))
speech, t = [], 0.0
for s, e in sil:
    if s > t: speech.append((max(0, t - pad), min(dur, s + pad)))
    t = e
if t < dur: speech.append((max(0, t - pad), dur))
fade = int(0.008 * sr)
out = []
for k, (s, e) in enumerate(speech):
    seg = a[int(s * sr):int(e * sr)].copy()
    if len(seg) > 2 * fade:
        seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
    out.append(seg)
    if k < len(speech) - 1: out.append(np.zeros(int(gap * sr)))
y = np.concatenate(out)
sf.write(dst, y, sr)
print(f"{dur:.2f}s -> {len(y)/sr:.2f}s, {len(speech)} speech parts")
