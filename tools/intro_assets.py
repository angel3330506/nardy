# Ассеты заставки: крышка нард без Аревахача (boards/lid-plain.webp) и белый Аревахач, вырезанный из крышки (boards/intro-rev-w.webp).
# Волокна ореха идут вертикально, поэтому круг закрашиваем по столбцам зеркальным отражением дерева сверху/снизу.
from PIL import Image, ImageFilter
import numpy as np
from scipy.ndimage import gaussian_filter1d
L = Image.open('boards/lid.webp').convert('RGBA'); A = np.asarray(L).astype(float)
H, W = A.shape[:2]; cx, cy, R = 413, 525, 276
yy, xx = np.mgrid[0:H, 0:W]; d = np.hypot(xx - cx, yy - cy)
out = A.copy(); TOP, BOT = 100, 950
def pp(y, a, b):                     # пинг-понг отражение внутрь отрезка [a,b]
    n = b - a; t = np.mod(y - a, 2 * n); return np.where(t < n, a + t, b - (t - n)).astype(int)
for x in range(cx - R - 2, cx + R + 3):
    h = np.sqrt(max(0, R * R - (x - cx) ** 2)) + 3
    if h <= 3: continue
    y0, y1 = int(cy - h), int(cy + h) + 1
    ys = np.arange(y0, y1)
    up = pp(2 * y0 - ys, TOP, y0)          # отражение верхнего дерева
    dn = pp(2 * y1 - ys, y1, BOT)          # отражение нижнего
    w = np.clip((ys - (cy - 30)) / 60, 0, 1)[:, None]
    raw = A[up, x, :3] * (1 - w) + A[dn, x, :3] * w
    # яркость: низкие частоты столбца — плавно от дерева над кругом к дереву под ним (без ступеньки посередине)
    xs = slice(max(0, x - 6), x + 7)
    tv = A[y0 - 14:y0, xs, :3].mean((0, 1)); bv = A[y1:y1 + 14, xs, :3].mean((0, 1))
    k = ((ys - y0) / max(1, y1 - y0))[:, None]
    low = np.stack([gaussian_filter1d(raw[:, c], 30, mode='nearest') for c in range(3)], -1)
    out[y0:y1, x, :3] = raw - low + tv * (1 - k) + bv * k
# мягкий край
m = np.clip((R + 2 - d) / 4, 0, 1)[..., None]
res = A * (1 - m) + out * m
img = Image.fromarray(res.clip(0, 255).astype(np.uint8))
img.save('boards/lid-plain.webp', quality=86, method=6)
# белый и золотой Аревахач в высоком разрешении: рисуем заново по той же геометрии, что на крышке (tools/render_real.py:
# аревахач n=12 R=128 band=.02, жгут 145…168 n=80, кольца 137…139.5 и 173…175.5 — в единицах крышки 550×700),
# а не вырезаем из картинки крышки (там знак ~530 px — на экране телефона он выходил мутным).
# Кадр: ±181.3 единицы вокруг центра (как прежний вырез 544 px из lid.webp), сплошной диск до r=177.3.
import math
from scipy.ndimage import gaussian_filter as gf, zoom
N = 1024; U = 181.33; k = N / (2 * U)                      # пикселей на единицу
yy, xx = (np.mgrid[0:N, 0:N] + .5) / k - U
r = np.hypot(xx, yy); ang = np.arctan2(yy, xx)
aa = lambda v: np.clip(.5 + v * k, 0, 1)                 # сглаживание края в 1 пиксель
R = 128.; n = 12; w = R * .02 * (.35 + .65 * np.clip(r / R, 0, 1))
ds = [np.hypot(xx - R / 2 * math.cos(math.radians(-90 + j * 30)), yy - R / 2 * math.sin(math.radians(-90 + j * 30))) - R / 2 for j in range(n)]
petals = np.max([aa(-ds[j] - w) * aa(ds[(j + 1) % n] - w) for j in range(n)], axis=0)
t = (r - 145) / 23; band = aa(r - 145) * aa(168 - r)
ph = (ang / (2 * math.pi) * 80 + t * 1.2) % 1
roll = np.sqrt(np.clip(1 - ((ph - .5) * 2) ** 2, 0, 1)) * np.sqrt(np.clip(1 - ((t - .5) * 2) ** 2, 0, 1))
rope = band * np.clip((roll - .22) * 7, 0, 1)              # светлые валики жгута с чёткими тёмными бороздками
rings = aa(r - 137) * aa(139.5 - r) + aa(r - 173) * aa(175.5 - r)
light = np.clip(petals + rope + rings, 0, 1)
disc = aa(177.3 - r)
relief = np.where(band > .5, .62 + .38 * roll, 1.0)       # объём жгута
# белый: светлое дерево инкрустации; между линиями — настоящее дерево крышки (увеличенный вырез), чтобы приземление было незаметным
S2 = 272; crop = A[cy - S2:cy + S2, cx - S2:cx + S2, :3]
wood = np.stack([zoom(crop[..., c], N / (2 * S2), order=1) for c in range(3)], -1)[:N, :N]
lumc = crop.mean(-1); cream = crop[lumc > 215].mean(0)
w_img = np.zeros((N, N, 4)); w_img[..., :3] = wood * (1 - light[..., None]) + (cream * relief[..., None]) * light[..., None]; w_img[..., 3] = disc * 255
Image.fromarray(np.clip(w_img, 0, 255).astype(np.uint8)).save('boards/intro-rev-w.webp', quality=92, method=6)
# золотой: тёплый градиент (светлее к центру-верху), объём жгута, просветы — почти чёрное дерево
g = np.clip(1 - np.hypot(xx / U + .25, yy / U + .3) * .55, 0, 1)[..., None]
c0 = np.array([196, 134, 38.]); c1 = np.array([255, 224, 130.])
gold_c = (c0 + (c1 - c0) * g) * relief[..., None]
dark = np.array([28., 17., 9.])
gi = np.zeros((N, N, 4)); gi[..., :3] = gold_c * light[..., None] + dark * (1 - light[..., None]); gi[..., 3] = disc * 255
Image.fromarray(np.clip(gi, 0, 255).astype(np.uint8)).save('boards/intro-rev.webp', quality=92, method=6)
print('ok', N)
