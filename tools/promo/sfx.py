# Звуковые эффекты ролика (без музыки): синтез на numpy. Выход — sfx.wav (48 кГц, стерео).
# Запуск: python sfx.py out.wav [звуки игры: путь к sounds/]
import sys, os, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000; DUR = 16.4
out = np.zeros((int(SR * DUR), 2))
rng = np.random.default_rng(3)
def env(n, a, d, shape=2.0):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d * shape); return e
def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f, order=2): return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)
def put(t, x, gain=1.0, pan=0.0):
    i = int(t * SR); x = x * gain
    if x.ndim == 1: x = np.stack([x * (1 - max(0, pan)), x * (1 + min(0, pan))], 1)
    n = min(len(x), len(out) - i); out[i:i + n] += x[:n]

def tap():                     # мягкий «тик» касания стекла
    n = int(.05 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * 2900 * t) * env(n, .0008, .012) * .5 + bp(rng.standard_normal(n), 1800, 7000) * env(n, .0003, .006) * .6
    return s
def whoosh(dur, f0, f1, rise=.45):   # шорох воздуха: шум с плывущей полосой
    n = int(dur * SR); x = rng.standard_normal(n); y = np.zeros(n); seg = 1024
    for k in range(0, n, seg):
        p = k / n; f = f0 * (f1 / f0) ** p
        y[k:k + seg] = bp(x[k:k + seg] if k == 0 else x[max(0, k - 256):k + seg], max(60, f * .55), min(18000, f * 1.6))[-min(seg, n - k):]
    t = np.linspace(0, 1, n); e = np.where(t < rise, (t / rise) ** 2, ((1 - t) / (1 - rise)) ** 1.6)
    return y * e
def pop():                     # «буль» появления значка
    n = int(.22 * SR); t = np.arange(n) / SR
    f = 520 + 520 * (1 - np.exp(-t * 30)); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(n, .004, .07) * .55 + tap() [:n] * .0 + np.pad(tap(), (0, max(0, n - len(tap()))))[:n] * .4
def thump(dur=.6, f=48):        # низкий удар
    n = int(dur * SR); t = np.arange(n) / SR
    fr = f * (1 + 1.5 * np.exp(-t * 18)); ph = 2 * np.pi * np.cumsum(fr) / SR
    return np.sin(ph) * env(n, .003, .22) + lp(rng.standard_normal(n), 300) * env(n, .001, .05) * .5
def shimmer(dur):               # лёгкий «блеск» на финале
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for f in (1568, 2093, 2637, 3136):
        y += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * env(n, .01, .5) * rng.uniform(.5, 1)
    return y * .12

T = dict(menu=2.35, share=3.45, more=4.55, home=5.75, add=6.95, newic=7.8, icon=10.8, rot=11.6, play=13.55)
put(0.0, whoosh(1.3, 250, 2400, .55), .55)                 # телефон прилетает
put(1.05, thump(.7, 42), .35)
for t0, t1 in ((1.45, 2.15), (2.5, 3.15), (3.6, 4.2), (4.7, 5.3), (5.9, 6.55), (7.0, 7.75), (8.35, 9.0), (9.95, 10.6), (12.75, 13.35), (13.9, 14.55)):
    put(t0, whoosh(t1 - t0, 900, 1800, .5), .10, pan=rng.uniform(-.3, .3))   # движения камеры — едва слышно
for k in ('menu', 'share', 'more', 'home', 'add', 'icon', 'play'):
    put(T[k], tap(), .55)
put(T['menu'] + .06, whoosh(.25, 1500, 4000, .3), .22)       # меню раскрылось
put(T['share'] + .1, whoosh(.4, 600, 2600, .35), .3)         # шторка выехала
put(T['more'] + .06, whoosh(.45, 500, 1800, .4), .25)        # шторка раскрылась
put(T['home'] + .1, whoosh(.45, 600, 2400, .35), .3)         # экран «На экран „Домой“»
put(T['add'] + .1, whoosh(.6, 2600, 400, .25), .38)          # Safari сворачивается
put(T['newic'], pop(), .7)                                   # новый значок
put(T['icon'] + .08, whoosh(.6, 400, 2600, .55), .38)        # игра открывается
put(T['rot'], whoosh(1.0, 300, 1300, .5), .55, pan=-.2)       # поворот
put(T['rot'] + .95, thump(.45, 70), .25)
snd = sys.argv[2] if len(sys.argv) > 2 else ''
def load(name):
    p = os.path.join(snd, name)
    if not snd or not os.path.exists(p): return None
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(float)
d = load('dice-throw-2.m4a')                                 # в игре катятся кубики — настоящий звук игры
if d is not None: put(T['play'] + .25, d / (np.abs(d).max() + 1e-9), .45)
put(15.05, whoosh(1.1, 200, 6000, .9), .95)                  # финал: телефон влетает в камеру
put(16.02, thump(.38, 55), .7); put(16.0, shimmer(.4), .7)
# немного «воздуха»: короткая реверберация
ir = rng.standard_normal(int(.6 * SR)) * np.exp(-np.arange(int(.6 * SR)) / SR / .12) * .03
for c in range(2): out[:, c] += fftconvolve(out[:, c], ir)[:len(out)] * .6
out /= max(1e-9, np.abs(out).max()) / .89
# мягкий конец
out[-int(.12 * SR):] *= np.linspace(1, 0, int(.12 * SR))[:, None]
pcm = (np.clip(out, -1, 1) * 32767).astype('<i2')
import wave
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('sfx ok', DUR)
