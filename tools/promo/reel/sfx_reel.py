# Звук ролика «Задача дня»: синтез (шорохи, тики отсчёта, удары) + настоящие звуки игры (шашки, кубики). Без музыки.
# Запуск: python sfx_reel.py out.wav <путь к sounds/>
import sys, os, subprocess, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
SR = 48000; DUR = {'pov': 34.0, 'grav': 26.0}.get(os.environ.get('PLAN'), 21.0)
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
    tp = tap(); tp = np.pad(tp, (0, max(0, n - len(tp))))[:n]
    return np.sin(ph) * env(n, .004, .07) * .55 + tp * .4
def thump(dur=.6, f=48):        # низкий удар
    n = int(dur * SR); t = np.arange(n) / SR
    fr = f * (1 + 1.5 * np.exp(-t * 18)); ph = 2 * np.pi * np.cumsum(fr) / SR
    return np.sin(ph) * env(n, .003, .22) + lp(rng.standard_normal(n), 300) * env(n, .001, .05) * .5
def shimmer(dur):               # лёгкий «блеск» на финале
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for f in (1568, 2093, 2637, 3136):
        y += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * env(n, .01, .5) * rng.uniform(.5, 1)
    return y * .12
def tick(f=1250, g=1.0):        # тик отсчёта: короткий деревянный щелчок
    n = int(.09 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) * env(n, .001, .03) * .6 + bp(rng.standard_normal(n), 2000, 6000) * env(n, .0005, .008) * .5) * g
def chime(dur=1.4):             # «Верно!»: мягкий двухнотный колокольчик
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for t0, f in ((0, 784), (.11, 1175)):
        k = int(t0 * SR); tt = t[:n - k]
        y[k:] += sum(np.sin(2 * np.pi * f * h * tt) * a for h, a in ((1, 1), (2.01, .35), (3.02, .12))) * env(n - k, .004, .55, 1.6)
    return y * .35
snd = sys.argv[2] if len(sys.argv) > 2 else ''
def load(name):
    p = os.path.join(snd, name)
    if not snd or not os.path.exists(p): return None
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).astype(float); return x / (np.abs(x).max() + 1e-9)

PLAN = os.environ.get('PLAN', 'puzzle')
if PLAN == 'grav':                                           # ролик «Гравюра»
    put(0.0, whoosh(1.3, 250, 2400, .55), .55); put(1.05, thump(.7, 42), .35)
    n = int(2.9 * SR); sc = rng.standard_normal(n); sc = np.diff(np.concatenate([[0], sc]))     # резец: тихий шорох по акрилу
    scr_env = (np.sin(np.linspace(0, np.pi, n)) ** .6) * (.6 + .4 * np.abs(np.sin(np.linspace(0, 60, n))))
    put(1.65, sc * scr_env * .18, .5)
    put(4.55, chime(1.6), .55); put(4.55, shimmer(.7), .5)    # меч вспыхнул
    put(6.1, whoosh(.9, 1500, 400, .4), .3)                    # нарды уезжают в меню
    put(9.15, tap(), .5); put(9.3, whoosh(.9, 300, 1500, .5), .35)   # крышка открывается
    put(12.35, pop(), .5)                                        # реплика судьи
    for t, nm in ((13.95, 'dice-throw-2.m4a'), (18.15, 'dice-throw-1.m4a')):
        x = load(nm)
        if x is not None: put(t, x, .5)
    for k, t in enumerate((15.6, 16.2, 21.7)):
        x = load('chip-lay-%d.m4a' % (k % 3 + 1))
        if x is not None: put(t, x, .55)
    put(22.0, whoosh(1.0, 200, 6000, .9), .95); put(22.95, thump(.5, 52), .75); put(22.95, shimmer(.9), .9); put(23.1, chime(2.2), .45)
elif PLAN == 'pov':                                            # ролик «POV: соседи по двору»
    put(0.0, whoosh(1.3, 250, 2400, .55), .55); put(1.05, thump(.7, 42), .35)
    for t in (6.4, 12.55, 22.68): put(t, whoosh(.45, 600, 3800, .4), .45)          # смена соседа — резкий «вжух»
    for t in (1.65, 3.9, 8.2, 10.8, 14.35, 18.35, 24.55, 26.7): put(t, pop(), .5)     # реплики
    for t, n in ((2.75, 'dice-throw-1.m4a'), (9.05, 'dice-throw-2.m4a'), (15.4, 'dice-throw-3.m4a'), (25.52, 'dice-throw-1.m4a')):
        x = load(n)
        if x is not None: put(t, x, .5)
    for k, t in enumerate((4.5, 5.0, 5.5, 6.0, 16.9, 17.4, 27.1, 27.6, 28.1, 28.6)):
        x = load('chip-lay-%d.m4a' % (k % 3 + 1))
        if x is not None: put(t, x, .55)
    put(17.95, thump(.5, 60), .55)                              # проигрыш: стук по столу
    put(19.85, whoosh(.5, 500, 1600, .4), .2)
    put(30.0, whoosh(1.0, 200, 6000, .9), .95); put(30.95, thump(.5, 52), .75); put(30.95, shimmer(.9), .9); put(31.1, chime(2.2), .45)
else:
    put(0.0, whoosh(1.3, 250, 2400, .55), .55)                  # телефон прилетает снизу
    put(1.05, thump(.7, 42), .35)
    put(5.0, whoosh(.9, 300, 1500, .5), .3)                     # наезд на доску
    for i, t in enumerate((5.4, 6.4, 7.4, 8.4, 9.4)):          # отсчёт 5…1
        put(t, tick(1250 if i < 4 else 1500), .55 if i < 4 else .7)
    put(10.4, whoosh(.8, 1500, 400, .4), .3)                    # отъезд, показ ответа
    put(10.45, tap(), .5)
    for t, n in ((10.98, 'chip-lay-1.m4a'), (11.72, 'chip-lay-2.m4a')):   # две шашки ложатся на поля
        x = load(n)
        if x is not None: put(t - .03, x, .75)
    put(13.33, chime(), .9); put(13.33, pop(), .35)             # «Верно!»
    put(13.3, whoosh(.7, 400, 1300, .5), .18)
    put(17.25, whoosh(1.0, 200, 6000, .9), .95)                 # финал: телефон влетает в камеру
    put(18.2, thump(.5, 52), .75); put(18.2, shimmer(.9), .9)
    put(18.35, chime(2.2), .45)
ir = rng.standard_normal(int(.6 * SR)) * np.exp(-np.arange(int(.6 * SR)) / SR / .12) * .03
for c in range(2): out[:, c] += fftconvolve(out[:, c], ir)[:len(out)] * .6
out /= max(1e-9, np.abs(out).max()) / .89
out[-int(.4 * SR):] *= np.linspace(1, 0, int(.4 * SR))[:, None]
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out, -1, 1) * 32767).astype('<i2').tobytes())
print('sfx ok', DUR)
