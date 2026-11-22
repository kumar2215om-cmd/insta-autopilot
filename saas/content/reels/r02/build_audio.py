"""public/mix.wav = voiceover + synthesized SFX (ticks per word, clicks on cuts, kicks on drops/stamps) + a soft lo-fi bed."""
import json, numpy as np, soundfile as sf
SR = 48000
tl = json.load(open('src/timeline.json'))
vo, sr = sf.read('public/vo.wav'); assert sr == SR
END = tl['end']; N = int(END * SR)
mix = np.zeros(N)
mix[:len(vo)] += vo[:N]
rng = np.random.default_rng(7)
def env(n, a=0.002, d=0.05):
    t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / d)
def tick():
    n = int(0.03 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * 2400 * t) * env(n, 0.001, 0.008) * 0.10
def click():
    n = int(0.025 * SR); return rng.normal(0, 1, n) * env(n, 0.0005, 0.004) * 0.22
def kick():
    n = int(0.25 * SR); t = np.arange(n) / SR; f = 120 * np.exp(-t * 18) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.09) * 0.55
def whoosh():
    n = int(0.28 * SR); x = rng.normal(0, 1, n); x = np.convolve(x, np.ones(30) / 30, 'same')
    w = np.sin(np.linspace(0, np.pi, n)); return x * w * 0.10
def put(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if 0 <= i < N: mix[i:j] += sig[:j - i]
for ph in tl['phrases']:
    for w in ph['words']:
        put(tick() * (1.5 if w['key'] else 1.0), w['s'])
cuts = [7.7, 10.7, 12.5, 13.6, 16.75, 21.15, 23.1, 24.5, 25.2, 26.55, 28.7, 30.55, 31.8, tl['vo']]
for c in cuts: put(click(), c); put(whoosh(), max(0, c - 0.12))
drops = [0.1, 1.9, 3.03, 5.22, 6.46, 9.42, 11.45, 12.6, 20.75, 30.0, 31.0, 32.0, tl['vo'] + 0.02]
for d in drops: put(kick(), d)
# lo-fi bed: soft chords (Fmaj7 - Em7 - Dm7 - Cmaj7), 80 bpm, with gentle noise
t = np.arange(N) / SR
chords = [[174.6, 220.0, 261.6, 329.6], [164.8, 196.0, 246.9, 293.7], [146.8, 174.6, 220.0, 261.6], [130.8, 164.8, 196.0, 246.9]]
bar = 3.0
bed = np.zeros(N)
for k in range(int(END / bar) + 1):
    i0 = int(k * bar * SR); i1 = min(N, int((k + 1) * bar * SR))
    if i0 >= N: break
    tt = t[i0:i1] - k * bar
    e = np.minimum(1, tt / 0.4) * np.exp(-tt / 2.2)
    for fr in chords[k % 4]:
        bed[i0:i1] += np.sin(2 * np.pi * fr * tt) * e * 0.018
bed += np.convolve(rng.normal(0, 0.004, N), np.ones(8) / 8, 'same')
mix += bed
peak = np.max(np.abs(mix)); mix = mix / max(1.0, peak / 0.95)
sf.write('public/mix.wav', np.stack([mix, mix], 1), SR)
print('mix', len(mix) / SR, 's peak', round(float(peak), 3))
