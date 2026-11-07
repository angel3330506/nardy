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
# белый и золотой Аревахач: тот же квадрат 544 px, маска — светлая инкрустация. Светлые волокна ореха (тонкие вертикальные
# полоски между кольцами) из маски убираем: порог выше + медианный фильтр по вертикали (полоски в 1–3 px исчезают, края знака остаются)
from scipy.ndimage import median_filter, gaussian_filter as gf
S = 272; crop = A[cy - S:cy + S, cx - S:cx + S]
lum = crop[..., :3].mean(-1)
m = np.clip((lum - 175) / 35, 0, 1)
m = median_filter(m, size=(1, 5))                       # поперёк волокон (они вертикальные) — тонкие линии пропадают
m = np.minimum(m, median_filter(m, size=(3, 3)))
rr = np.hypot(*np.mgrid[-S:S, -S:S]); m *= np.clip((S - rr) / 3, 0, 1)
w = crop.copy(); w[..., 3] = m * 255
Image.fromarray(w.astype(np.uint8)).resize((640, 640), Image.LANCZOS).save('boards/intro-rev-w.webp', quality=90, method=6)
# золотой: тёплый градиент (светлее к центру) с мягкой светотенью от рельефа инкрустации
yy2, xx2 = np.mgrid[-S:S, -S:S] / S
g = np.clip(1 - np.hypot(xx2 + .25, yy2 + .3) * .55, 0, 1)[..., None]
c0 = np.array([196, 134, 38.]); c1 = np.array([255, 224, 130.])
col = c0 + (c1 - c0) * g
shade = gf(lum, 2) / 255; shade = (shade - shade[m > .5].mean()) * .55 + 1
gold = np.zeros((2 * S, 2 * S, 4)); gold[..., :3] = np.clip(col * shade[..., None], 0, 255); gold[..., 3] = m * 255
Image.fromarray(gold.astype(np.uint8)).resize((640, 640), Image.LANCZOS).save('boards/intro-rev.webp', quality=90, method=6)
print('ok')
