# Рендер досок и шашек: процедурное дерево, карта высот для резьбы и инкрустации, освещение.
# Результат: boards/<skin>.webp (фон доски 2200x1400) и boards/ck-<name>.png (спрайты шашек).
# Геометрия совпадает с index.html (viewBox 1100x700).
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'boards')
os.makedirs(OUT, exist_ok=True)
S = 2
W, H = 1100 * S, 700 * S
ARM_FONT = next((f for f in ('C:/Windows/Fonts/sylfaen.ttf', '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf')
                 if os.path.exists(f)), 'sylfaen.ttf')


# ---------- шум и дерево ----------
def vnoise(h, w, cy, cx, seed):
    cy, cx = max(1, int(cy)), max(1, int(cx))
    r = np.random.default_rng(seed).random((cy + 3, cx + 3))
    z = ndi.zoom(r, (h / cy, w / cx), order=3, mode='reflect')
    oy, ox = int(h / cy), int(w / cx)
    return z[oy:oy + h, ox:ox + w]


def fbm(h, w, cy, cx, seed, octaves=4):
    out = np.zeros((h, w)); amp = 1.0; tot = 0
    for i in range(octaves):
        out += vnoise(h, w, cy * 2 ** i, cx * 2 ** i, seed + 17 * i) * amp
        tot += amp; amp *= 0.5
    return out / tot


def wood(h, w, light, dark, rings=10, seed=1, vertical=False, contrast=.7, fiber=.14, warp=2.2):
    """Альбедо дерева. Волокна идут вдоль x (или вдоль y при vertical)."""
    if vertical:
        return wood(w, h, light, dark, rings, seed, False, contrast, fiber, warp).transpose(1, 0, 2)
    # Доска тангенциального распила: годовые кольца бревна, срезанные плоскостью, дают «арки» и «пламя».
    y = np.linspace(-.5, .5, h)[:, None] * np.ones((1, w))
    z = .09 + .3 * vnoise(h, w, 1, 2.5, seed + 9)          # глубина среза медленно меняется вдоль доски
    yc = (vnoise(h, w, 1, 1.5, seed + 10) - .5) * .5        # смещение сердцевины
    wp = fbm(h, w, 4, 2, seed, 3)
    wp2 = fbm(h, w, 30, 4, seed + 1, 2)
    rr = np.sqrt((y - yc) ** 2 + z ** 2)
    t = rr * rings * 2.2 + wp * warp * .45 + wp2 * .12
    f = t - np.floor(t)
    late = np.clip((f - .5) / .5, 0, 1) ** 2.2 + np.clip((.08 - f) / .08, 0, 1) * .6   # тёмная поздняя древесина с резкой границей
    fib = vnoise(h, w, h / 1.6, 7, seed + 2)
    fib2 = vnoise(h, w, h / 5, 20, seed + 4)
    pores = np.clip((vnoise(h, w, h / 1.4, w / 9, seed + 5) - .72) / .28, 0, 1)
    tone = fbm(h, w, 2, 3, seed + 3, 2)
    v = late * contrast + (fib - .5) * fiber + (fib2 - .5) * fiber * .9 + pores * .35 + (tone - .5) * .22
    v = np.clip(v, 0, 1)[..., None]
    L, D = np.array(light)[None, None], np.array(dark)[None, None]
    return L * (1 - v) + D * v


def felt(h, w, base, seed):
    n = vnoise(h, w, h / 1.3, w / 1.3, seed) * .5 + vnoise(h, w, h / 4, w / 4, seed + 1) * .3 + fbm(h, w, 6, 9, seed + 2, 2) * .4
    n = (n - n.mean())
    return np.clip(np.array(base)[None, None] * (1 + n[..., None] * .55), 0, 1)


# ---------- маски ----------
def canvas():
    return Image.new('L', (W, H), 0)


def to_arr(img, aa=.7):
    a = np.asarray(img, dtype=float) / 255
    return ndi.gaussian_filter(a, aa) if aa else a


def P(pts):
    return [(x * S, y * S) for x, y in pts]


def poly(pts, aa=.7):
    im = canvas(); ImageDraw.Draw(im).polygon(P(pts), fill=255); return to_arr(im, aa)


def polys(list_of_pts, aa=.7):
    im = canvas(); d = ImageDraw.Draw(im)
    for pts in list_of_pts: d.polygon(P(pts), fill=255)
    return to_arr(im, aa)


def rrect(x0, y0, x1, y1, r, aa=.7):
    im = canvas(); ImageDraw.Draw(im).rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], r * S, fill=255); return to_arr(im, aa)


def circle(cx, cy, r, aa=.7):
    im = canvas(); ImageDraw.Draw(im).ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=255); return to_arr(im, aa)


def lines(segs, width, aa=.6):
    im = canvas(); d = ImageDraw.Draw(im)
    for pts in segs: d.line(P(pts), fill=255, width=max(1, int(width * S)), joint='curve')
    return to_arr(im, aa)


def text_mask(txt, cx, cy, size, font=ARM_FONT, spacing=0):
    im = canvas(); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(font, int(size * S))
    if spacing:
        widths = [d.textlength(ch, font=f) for ch in txt]
        total = sum(widths) + spacing * S * (len(txt) - 1)
        x = cx * S - total / 2
        for ch, wd in zip(txt, widths):
            d.text((x, cy * S), ch, font=f, fill=255, anchor='lm'); x += wd + spacing * S
    else:
        d.text((cx * S, cy * S), txt, font=f, fill=255, anchor='mm')
    return to_arr(im, .5)


def arc_text_mask(txt, cx, cy, radius, size, font=ARM_FONT, spacing=1.0, bottom=True):
    """Надпись по дуге внутри круга: буквы стоят «головой» к центру, середина строки — внизу (или вверху)."""
    im = canvas()
    f = ImageFont.truetype(font, int(size * S * 3))
    d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
    widths = [d0.textlength(ch, font=f) / (3 * S) + spacing for ch in txt]
    total = sum(widths) - spacing
    ang = math.degrees(total / radius)
    a = 90 + ang / 2 if bottom else -90 - ang / 2
    for ch, wd in zip(txt, widths):
        mid = a - math.degrees((wd - spacing) / 2 / radius) * (1 if bottom else -1)
        n = int(size * S * 3 * 1.8)
        g = Image.new('L', (n, n), 0)
        ImageDraw.Draw(g).text((n / 2, n / 2), ch, font=f, fill=255, anchor='mm')
        g = g.rotate(-(mid - 90) if bottom else -(mid + 90), resample=Image.BICUBIC)
        g = g.resize((n // 3, n // 3), Image.LANCZOS)
        px = (cx + radius * math.cos(math.radians(mid))) * S - n // 6
        py = (cy + radius * math.sin(math.radians(mid))) * S - n // 6
        layer = Image.new('L', im.size, 0); layer.paste(g, (int(round(px)), int(round(py))))
        im = Image.fromarray(np.maximum(np.asarray(im), np.asarray(layer)))
        a -= math.degrees(wd / radius) * (1 if bottom else -1)
    return to_arr(im, .4)


# ---------- геометрия ----------
def ptX(i):
    if i < 12: return 925 - 70 * i if i < 6 else 425 - 70 * (i - 6)
    j = i - 12; return 75 + 70 * j if j < 6 else 575 + 70 * (j - 6)


def is_top(i): return i >= 12


def bez(p0, p1, p2, p3, n=24):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = map(np.array, (p0, p1, p2, p3))
    pts = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
    return [tuple(p) for p in pts]


def wavy_rect(x0, y0, x1, y1, amp, nx, ny, corner=0):
    pts = []
    def edge(ax, ay, bx, by, n, ox, oy):
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            sx, sy = ax + (bx - ax) * t0, ay + (by - ay) * t0
            ex, ey = ax + (bx - ax) * t1, ay + (by - ay) * t1
            s = (-.6 if i % 2 else 1) * amp
            pts.extend(bez((sx, sy), (sx + (ex - sx) * .2 + ox * s, sy + (ey - sy) * .2 + oy * s),
                           (sx + (ex - sx) * .8 + ox * s, sy + (ey - sy) * .8 + oy * s), (ex, ey))[:-1])
    edge(x0, y0, x1, y0, nx, 0, -1); edge(x1, y0, x1, y1, ny, 1, 0)
    edge(x1, y1, x0, y1, nx, 0, 1); edge(x0, y1, x0, y0, ny, -1, 0)
    return pts


def arc_pts(cx, cy, r, a0, a1, n=40):
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]


def teardrop(x, top, tip, w, inset=0):
    r = w / 2
    if top:
        cy = 40 + r + 6 + inset
        return arc_pts(x, cy, r, 180, 360) + [(x, tip)]
    cy = 660 - r - 6 - inset
    return arc_pts(x, cy, r, 180, 0) + [(x, tip)]


def triangle(x, top, base_y, tip, half):
    return [(x - half, base_y), (x + half, base_y), (x, tip)]


def star_halves(cx, cy, R, r, n=8, rot=-90):
    """Для каждого луча — две половины (левая, правая)."""
    out = []; step = 360 / n; half = math.pi / n
    for k in range(n):
        a = math.radians(rot + k * step)
        tip = (cx + R * math.cos(a), cy + R * math.sin(a))
        lv = (cx + r * math.cos(a - half), cy + r * math.sin(a - half))
        rv = (cx + r * math.cos(a + half), cy + r * math.sin(a + half))
        out.append(([(cx, cy), tip, lv], [(cx, cy), tip, rv]))
    return out


def star_poly(cx, cy, R, r, n=8, rot=-90):
    pts = []
    for k in range(n):
        a = math.radians(rot + k * 360 / n); b = a + math.pi / n
        pts += [(cx + R * math.cos(a), cy + R * math.sin(a)), (cx + r * math.cos(b), cy + r * math.sin(b))]
    return pts


def arevakhach_masks(cx, cy, R, n=8, band=.085, rot=-90):
    """Аревахач по классическому построению: 8 кругов радиуса R/2 через центр.
    Лопасть k — серп между кругом k и соседним кругом k+1; тёмные полосы — границы кругов.
    Возвращает (окно-срез, маска всего знака, список масок лопастей, углы лопастей) в локальном окне."""
    pad = 4
    x0, x1 = int((cx - R - pad) * S), int((cx + R + pad) * S)
    y0, y1 = int((cy - R - pad) * S), int((cy + R + pad) * S)
    yy, xx = np.mgrid[y0:y1, x0:x1] / S
    r = np.hypot(xx - cx, yy - cy)
    w = R * band * (.35 + .65 * np.clip(r / R, 0, 1))        # полоса тоньше к центру, как на эскизе
    ds = []
    for k in range(n):
        a = math.radians(rot + k * 360 / n)
        ccx, ccy = cx + R / 2 * math.cos(a), cy + R / 2 * math.sin(a)
        ds.append(np.hypot(xx - ccx, yy - ccy) - R / 2)
    aa = lambda v: np.clip(.5 + v * S, 0, 1)
    union = np.max([aa(-d) for d in ds], axis=0)
    petals = [aa(-ds[k] - w) * aa(ds[(k + 1) % n] - w) for k in range(n)]
    angles = [rot + k * 360 / n + 360 / n / 2 for k in range(n)]
    return (slice(y0, y1), slice(x0, x1)), union, petals, angles


def arevakhach_inlay(alb, h, cx, cy, R, light, dark, seed, gloss=None):
    """Маркетри: знак из тёмного ореха, лопасти — светлое дерево, волокна каждой лопасти вдоль неё."""
    sl, union, petals, angles = arevakhach_masks(cx, cy, R)
    hh, ww = union.shape
    big = int(max(hh, ww) * 1.5)
    dtex = wood(hh, ww, *dark, rings=18, seed=seed, contrast=.45, fiber=.12)
    base = wood(big, big, *light, rings=16, seed=seed + 1, contrast=.3, fiber=.1, warp=1.2)
    a = alb[sl]
    a = a * (1 - union[..., None]) + dtex * union[..., None]
    for k, pm in enumerate(petals):
        rt = ndi.rotate(base, angles[k] + 90, axes=(0, 1), reshape=False, order=1, mode='reflect')
        oy, ox = (big - hh) // 2, (big - ww) // 2
        tex = rt[oy:oy + hh, ox:ox + ww] * (.94 + .1 * (k % 2))   # соседние лопасти чуть различаются тоном
        a = a * (1 - pm[..., None]) + tex * pm[..., None]
        glue = np.clip(pm - ndi.grey_erosion(pm, size=3), 0, 1)
        a = a * (1 - glue[..., None] * .35)
    alb[sl] = a
    lit = np.max(petals, axis=0)
    h[sl] = h[sl] - union * .4 + lit * .25                    # лопасти чуть выше полос: живой рельеф маркетри
    return union


# ---------- резьба в медальонах ----------
class Relief:
    """Резьба по дереву: карта высот на сетке втрое плотнее доски. Рисунок задаётся в квадрате ±R условных единиц
    (y вниз) и ложится на доску в масштабе sc. Точки слегка дрожат, как при ручной работе."""
    def __init__(self, R, seed, sc=1.0):
        self.R = R; self.sc = sc; self.n = int(2 * R * sc * S) * 3; self.k = self.n / (2 * R)
        self.h = np.zeros((self.n, self.n))
        self.rng = np.random.default_rng(seed)
        y, x = (np.mgrid[0:self.n, 0:self.n] + .5) / self.k - R
        self.x, self.y = x, y

    def _pts(self, pts, jit=.12):
        return [((px + self.R) * self.k + self.rng.normal(0, jit * self.k), (py + self.R) * self.k + self.rng.normal(0, jit * self.k)) for px, py in pts]

    def _img(self, draw):
        im = Image.new('L', (self.n, self.n), 0); draw(ImageDraw.Draw(im))
        return np.asarray(im, float) / 255

    def poly(self, *polys, jit=.12):
        return self._img(lambda d: [d.polygon(self._pts(p, jit), fill=255) for p in polys])

    def lines(self, segs, w, jit=.06):
        return self._img(lambda d: [d.line(self._pts(p, jit), fill=255, width=max(1, int(w * self.k)), joint='curve') for p in segs])

    def disc(self, cx, cy, r, ry=None):
        ry = r if ry is None else ry
        return ((self.x - cx) / r) ** 2 + ((self.y - cy) / ry) ** 2 < 1

    def dist(self, m):
        return ndi.distance_transform_edt(m > .5) / self.k

    def carve(self, m, edge, inner, bevel, p=.6):
        """Внутри маски высота идёт от edge у контура к inner вглубь на ширине bevel (скруглённый срез ножа)."""
        m = m > .5
        prof = edge + (inner - edge) * np.clip(self.dist(m) / bevel, 0, 1) ** p
        self.h = np.where(m, prof, self.h)

    def raise_(self, m, base, height, bevel=.8, p=.6):
        self.carve(m, base, base + height, bevel, p)

    def result(self):
        """Высоты в разрешении доски: 0 — поверхность поля, рельеф выше, выборки ниже."""
        h = self.h + 7.5 + (fbm(self.n, self.n, 60, 60, int(self.rng.integers(1e6)), 2) - .5) * .25 * (self.h > -7.4)   # следы стамески
        h = h.reshape(self.n // 3, 3, self.n // 3, 3).mean((1, 3))
        return h * self.sc


def spiral(cx, cy, r0, turns, a0, cw=1, n=80):
    t = np.linspace(0, 1, n)
    a = a0 + cw * t * turns * 2 * math.pi
    r = r0 * (1 - .82 * t)
    return [(cx + rr * math.cos(aa), cy + rr * math.sin(aa)) for rr, aa in zip(r, a)]


def rosette(rv, cx, cy, r, petals, base, height, seed=0):
    """Розетка: выпуклые лепестки-капли вокруг шишечки."""
    pl = []
    for k in range(petals):
        a = 2 * math.pi * k / petals
        c, s_ = math.cos(a), math.sin(a)
        w = math.pi * r / petals * .85
        pts = [(cx + .32 * r * c - w * .35 * s_, cy + .32 * r * s_ + w * .35 * c)]
        pts += [(cx + (.32 * r + (r * .66) * t) * c - w * math.sin(math.pi * (.15 + .85 * t)) * .5 * s_ * (1.2 - .5 * t),
                 cy + (.32 * r + (r * .66) * t) * s_ + w * math.sin(math.pi * (.15 + .85 * t)) * .5 * c * (1.2 - .5 * t)) for t in np.linspace(0, 1, 9)]
        pts += [(cx + .32 * r * c + w * .35 * s_, cy + .32 * r * s_ - w * .35 * c)]
        pl.append(pts)
    rv.carve(rv.disc(cx, cy, r), base - .3, base - .9, .5)
    for p in pl: rv.raise_(rv.poly(p, jit=.05), base - .6, height, .55, .5)
    rv.raise_(rv.disc(cx, cy, r * .3), base, height * 1.25, r * .25, .5)


def weave(x, y, P, w, ang=45):
    """Плетёнка из двух систем лент с переплетением «над-под»: высота 0..1."""
    a = math.radians(ang)
    u = (x * math.cos(a) + y * math.sin(a)) / P; v = (-x * math.sin(a) + y * math.cos(a)) / P
    fu, fv = u % 1 - .5, v % 1 - .5
    r1 = np.sqrt(np.clip(1 - (fu / w) ** 2, 0, 1)); r2 = np.sqrt(np.clip(1 - (fv / w) ** 2, 0, 1))
    over = (np.floor(u) + np.floor(v)) % 2 == 0
    # на перекрёстке верхняя лента целая, нижняя ныряет под неё с зазором
    h1 = r1 + np.where(over, .35, -.35) * (r2 > 0); h2 = r2 + np.where(over, -.35, .35) * (r1 > 0)
    gap1 = (r1 > 0) & (np.abs(fv) > w) & (np.abs(fv) < w + .06) & ~over
    gap2 = (r2 > 0) & (np.abs(fu) > w) & (np.abs(fu) < w + .06) & over
    hgt = np.maximum(np.where(r1 > 0, h1, 0), np.where(r2 > 0, h2, 0))
    return np.clip(hgt - (gap1 | gap2) * .8, 0, None)


def khachkar(R=58, seed=11, sc=1.0):
    """Хачкар по образцу классической плиты: карниз с нишей и крестиком, широкая рамка-плетёнка,
    в выбранном поле крест на «крыльях» с концами-завитками, под ним пара больших волют-побегов,
    колесо-розетка и плетёный фриз; плита стоит на резном постаменте."""
    rv = Relief(R, seed, sc)
    x, y = rv.x, rv.y
    rv.h[:] = -7.5                                            # уровень поля доски
    X1, Y0, Y1 = 28.5, -49.5, 37.5                            # плита
    slab = rv.poly([(-X1, Y0 + 5), (X1, Y0 + 5), (X1, Y1), (-X1, Y1)])
    rv.raise_(slab, -7.5, 7.5, .9, .5)
    # карниз-навершие: выступающая полка с нишей посередине
    top = rv.poly([(-X1 - 1.2, Y0), (X1 + 1.2, Y0), (X1 + 1.2, Y0 + 5.5), (-X1 - 1.2, Y0 + 5.5)])
    rv.raise_(top, -7.5, 8.6, .8, .5)
    rv.h -= rv.lines([[(-X1 - 1.2, Y0 + 1.4), (X1 + 1.2, Y0 + 1.4)]], .3) * .6
    band = weave(x, y, 2.2, .26, 45) * (top > .5) * ((y > Y0 + 2) & (y < Y0 + 5.2) & (np.abs(x) > 4.5))
    rv.h -= (top > .5) * ((y > Y0 + 2) & (y < Y0 + 5.2) & (np.abs(x) > 4.5)) * 1.4
    rv.h += band * 1.1
    niche = [(-3.6, Y0 + 5.4), (-3.6, Y0 + 3.2)] + arc_pts(0, Y0 + 3.2, 3.6, 180, 360, 16) + [(3.6, Y0 + 5.4)]
    rv.carve(rv.poly(niche), 1.1, -1.4, .4)
    rv.raise_(rv.lines([[(0, Y0 + 1.6), (0, Y0 + 5.0)], [(-1.4, Y0 + 2.9), (1.4, Y0 + 2.9)]], .55), -1.4, 1.6, .25)
    # рамка: широкая плетёнка из мелких квадратных узлов
    B = 8.2
    fx0, fx1, fy0, fy1 = -X1 + B, X1 - B, Y0 + 5.5 + B * .8, Y1 - 6.5
    frame = (slab > .5) & ~((np.abs(x) < fx1) & (y > fy0) & (y < fy1)) & (y > Y0 + 5.5)
    rv.h = np.where(frame, -1.6 + weave(x, y, 2.75, .24, 45) * 1.9, rv.h)
    cells = (np.abs((x / 3.9) % 1 - .5) > .46) | (np.abs((y / 3.9) % 1 - .5) > .46)
    rv.h -= frame * cells * .5
    # нижний фриз плиты: волнистая плетёнка
    fr = (slab > .5) & (y >= fy1) & (y < Y1 - 1.2) & (np.abs(x) < fx1 + B)
    s1 = np.sin(x / 2.4 * math.pi) * 1.6 + (fy1 + Y1 - 1.2) / 2; s2 = -np.sin(x / 2.4 * math.pi) * 1.6 + (fy1 + Y1 - 1.2) / 2
    w1 = np.sqrt(np.clip(1 - ((y - s1) / .75) ** 2, 0, 1)); w2 = np.sqrt(np.clip(1 - ((y - s2) / .75) ** 2, 0, 1))
    top1 = (np.floor(x / 2.4) % 2) == 0
    rv.h = np.where(fr, -2.2 + np.maximum(w1 + .3 * top1 * (w2 > 0), w2 + .3 * ~top1 * (w1 > 0)) * 2.2, rv.h)
    # поле — выбрано гладко
    field = rv.poly([(-fx1, fy0), (fx1, fy0), (fx1, fy1), (-fx1, fy1)])
    rv.carve(field, 0, -4.4, .6)
    F = -4.4
    # крест: центр перекрестья, ветви расширяются к концам и заканчиваются парой завитков с трилистником
    cx, cy = 0, -19
    def arm(dx, dy, L, w0, w1):
        px_, py_ = -dy, dx
        e = (cx + dx * L, cy + dy * L); b0 = (cx + dx * 2.5, cy + dy * 2.5)
        return [(b0[0] + px_ * w0 / 2, b0[1] + py_ * w0 / 2), (e[0] + px_ * w1 / 2, e[1] + py_ * w1 / 2),
                (e[0] - dx * 1.6, e[1] - dy * 1.6),
                (e[0] - px_ * w1 / 2, e[1] - py_ * w1 / 2), (b0[0] - px_ * w0 / 2, b0[1] - py_ * w0 / 2)], e, (px_, py_), (dx, dy)
    arms = [arm(0, -1, 15.5, 4.0, 7.2), arm(-1, 0, 13.5, 4.0, 7.2), arm(1, 0, 13.5, 4.0, 7.2), arm(0, 1, 18, 4.0, 5.4)]
    cross = rv.poly(*[a[0] for a in arms]) + rv.disc(cx, cy, 3.2)
    curls = []
    for poly_, e, (px_, py_), (dx, dy) in arms[:3]:
        for s2 in (-1, 1):
            c0 = (e[0] + px_ * s2 * 3.9 - dx * .6, e[1] + py_ * s2 * 3.9 - dy * .6)
            a0 = math.atan2(-dy, -dx)
            curls.append(spiral(c0[0], c0[1], 2.6, 1.3, a0 + s2 * .3, cw=s2 * (1 if dx + dy > 0 else -1) * (-1 if dy else 1)))
        cross = cross + rv.disc(e[0] + dx * 1.2, e[1] + dy * 1.2, 1.3)          # шишечка-трилистник на конце
    cross = np.clip(cross, 0, 1)
    # «крылья»: листья, отходящие от перекрестья вниз-в стороны
    wings = []
    for sgn in (-1, 1):
        wings.append([(sgn * 2.2, cy + 3.5)] + [(sgn * (2.2 + 9 * t), cy + 3.5 + 6 * t ** 1.4 - 2.4 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 14)]
                     + [(sgn * (2.2 + 9 * t), cy + 3.5 + 6 * t ** 1.4 + .6 * math.sin(math.pi * t)) for t in np.linspace(1, 0, 14)])
    rv.raise_(rv.poly(*wings, jit=.05), F, 2.4, .6, .5)
    for sgn in (-1, 1):
        rv.h -= rv.lines([[(sgn * (2.2 + 9 * t), cy + 3.5 + 6 * t ** 1.4 - .9 * math.sin(math.pi * t)) for t in np.linspace(.1, .9, 10)]], .3) * .7
    # большие волюты под крестом: от подножия расходятся и закручиваются внутрь
    for sgn in (-1, 1):
        stem = [(sgn * 1.2, cy + 17.5), (sgn * 5, cy + 19.5), (sgn * 10.5, cy + 21), (sgn * 14.5, cy + 25), (sgn * 14.6, cy + 30.5)]
        vol = spiral(sgn * 9.4, cy + 30.4, 5.2, 1.4, 0 if sgn > 0 else math.pi, cw=sgn)
        rv.raise_(rv.lines([stem, vol], 2.3), F, 3.0, .9, .5)
        rv.h -= rv.lines([vol[:60]], .4) * .9
        # пальметта внутри волюты и бутон сверху
        for k, (lx, ly) in enumerate(((5.2, cy + 25.5), (3.6, cy + 28.5))):
            rv.raise_(rv.disc(sgn * lx, ly, 1.3, 2.2), F, 1.8, .6, .5)
        rv.raise_(rv.lines(curls, 1.25), F, 2.6, .6, .5)
    # узлы-розетки в верхних углах поля
    for sgn in (-1, 1):
        kx_, ky_ = sgn * 13.2, fy0 + 6.2
        rv.carve(rv.disc(kx_, ky_, 4.6), F, F + 1.6, .6, .5)
        rv.h = np.where(rv.disc(kx_, ky_, 4.0), F + .4 + weave(x - kx_, y - ky_, 2.0, .25, 45) * 1.6, rv.h)
        rv.h -= (np.abs(np.hypot(x - kx_, y - ky_) - 4.2) < .25) * .6
    # колесо-розетка под волютами
    wcx, wcy = 0, cy + 38.5
    rv.carve(rv.disc(wcx, wcy, 6.6), F, F + 2.4, .7, .5)
    rv.h -= (np.abs(np.hypot(x - wcx, y - wcy) - 5.3) < .3) * .8
    for k in range(8):
        a = k * math.pi / 4
        rv.h -= rv.lines([[(wcx + 1.6 * math.cos(a), wcy + 1.6 * math.sin(a)), (wcx + 4.9 * math.cos(a + .5), wcy + 4.9 * math.sin(a + .5))]], .35) * .8
    rv.raise_(rv.disc(wcx, wcy, 1.5), F + 2.4, .8, .6, .5)
    # сам крест поверх всего: выпуклый, с врезанной двойной линией по контуру
    rv.raise_(cross, F, 4.4, .9, .55)
    inner = ndi.binary_erosion(cross > .5, iterations=int(.9 * rv.k)) & ~ndi.binary_erosion(cross > .5, iterations=int(1.25 * rv.k))
    rv.h -= inner * .9
    rv.h = np.where(rv.disc(cx, cy, 2.2), rv.h + .6, rv.h)
    # постамент: широкий блок с плетёнкой и профилированными полками
    ped = rv.poly([(-35, Y1), (35, Y1), (35, Y1 + 11), (-35, Y1 + 11)])
    rv.raise_(ped, -7.5, 6.4, .8, .5)
    inn = (ped > .5) & (y > Y1 + 2) & (y < Y1 + 9.2) & (np.abs(x) < 33)
    rv.h = np.where(inn, -3.6 + weave(x, y, 3.4, .22, 30) * 1.7, rv.h)
    rv.h -= rv.lines([[(-35, Y1 + 1.2), (35, Y1 + 1.2)], [(-35, Y1 + 10), (35, Y1 + 10)]], .3) * .5
    return rv


# ---------- Гарни в три четверти: 3D-модель → барельеф ----------
def _hs_box(x0, x1, y0, y1, z0, z1):
    """Выпуклое тело как набор полупространств n·p <= c."""
    return [((1, 0, 0), x1), ((-1, 0, 0), -x0), ((0, 1, 0), y1), ((0, -1, 0), -y0), ((0, 0, 1), z1), ((0, 0, -1), -z0)]


def garni_relief(wu, hu, sc=1.0, yaw=-38, pitch=-4, seed=12):
    """Храм Гарни (6×8 ионических колонн на высоком подиуме, лестница с фасада) в ракурсе три четверти:
    фасад слева, длинный бок уходит вправо. Глубина сжата в барельеф: ближний угол выше, дальний ниже.
    Возвращает высоты (0 — поле) размером (hu*S, wu*S) — окно wu×hu единиц доски."""
    ss = 2
    Wp, Hp = int(wu * S * ss), int(hu * S * ss)
    a, p = math.radians(yaw), math.radians(pitch)
    cdir = np.array((math.sin(a) * math.cos(p), math.sin(p), -math.cos(a) * math.cos(p)))   # к камере: спереди-сбоку, чуть снизу, как с площадки перед храмом
    d = -cdir
    right = np.cross(d, (0, 1, 0)); right /= np.linalg.norm(right)
    up = np.cross(right, d)
    prims = []                                                # (тип, данные, метка)
    W_, L_ = 14.0, 20.0
    prims.append(('cvx', _hs_box(0, W_, 0, 2.8, 0, L_), 'podium'))
    prims.append(('cvx', _hs_box(-.15, W_ + .15, 2.55, 2.8, -.15, L_ + .15), 'cap'))           # карниз подиума
    for k in range(9):                                        # лестница во всю ширину между щеками
        z0 = -4.6 + k * .5; prims.append(('cvx', _hs_box(1.7, W_ - 1.7, 0, (k + 1) * 2.8 / 9, z0, 0), 'step'))
    for x0 in (0, W_ - 1.7):
        prims.append(('cvx', _hs_box(x0, x0 + 1.7, 0, 2.1, -4.6, 0), 'cheek'))
        prims.append(('cvx', _hs_box(x0 - .1, x0 + 1.8, 2.1, 2.45, -4.7, -3.0), 'cap'))
    prims.append(('cvx', _hs_box(3.0, W_ - 3.0, 2.8, 9.4, 3.6, 17.0), 'cella'))
    cols = []
    xs = np.linspace(1.0, W_ - 1.0, 6); zs = np.linspace(1.0, L_ - 1.0, 8)
    for x in xs: cols += [(x, 1.0), (x, L_ - 1.0)]
    for z in zs[1:-1]: cols += [(1.0, z), (W_ - 1.0, z)]
    for (cx, cz) in cols:
        prims.append(('cyl', (cx, cz, .5, 3.15, 9.0), 'col'))
        prims.append(('cyl', (cx, cz, .66, 2.8, 3.15), 'base'))
        prims.append(('cvx', _hs_box(cx - .66, cx + .66, 9.0, 9.4, cz - .66, cz + .66), 'capital'))
    prims.append(('cvx', _hs_box(.35, W_ - .35, 9.4, 11.0, .35, L_ - .35), 'ent'))
    prims.append(('cvx', _hs_box(.1, W_ + -.1, 11.0, 11.45, .1, L_ - .1), 'corn'))
    ridge = 2.6
    roof = [((0, 0, 1), L_ - .1), ((0, 0, -1), -.1), ((0, -1, 0), -11.45),
            ((ridge / (W_ / 2 - .1), 1, 0), 11.45 + ridge + ridge / (W_ / 2 - .1) * W_ / 2),
            ((-ridge / (W_ / 2 - .1), 1, 0), 11.45 + ridge - ridge / (W_ / 2 - .1) * W_ / 2)]
    prims.append(('cvx', roof, 'roof'))
    # проекция: границы кадра по вершинам подиума, лестницы и кровли
    pts = np.array([(x, y, z) for x in (-.2, W_ + .2) for y in (0, 11.45) for z in (-4.7, L_)] + [(W_ / 2, 11.45 + ridge, z) for z in (0, L_)])
    px_, py_ = pts @ right, pts @ up
    cx0, cy0 = (px_.min() + px_.max()) / 2, (py_.min() + py_.max()) / 2
    scale = min(Wp / (px_.max() - px_.min()), Hp / (py_.max() - py_.min())) * .98
    J, I = np.meshgrid(np.arange(Wp) + .5, np.arange(Hp) + .5)
    sx_ = (J - Wp / 2) / scale + cx0; sy_ = -(I - Hp / 2) / scale + cy0
    O = sx_[..., None] * right + sy_[..., None] * up - d * 200
    T = np.full((Hp, Wp), np.inf); LAB = np.full((Hp, Wp), '', dtype=object); NRM = np.zeros((Hp, Wp, 3))
    def bbox(corners):
        c = np.array(corners); u_, v_ = c @ right, c @ up
        j0 = int(max(0, (u_.min() - cx0) * scale + Wp / 2 - 2)); j1 = int(min(Wp, (u_.max() - cx0) * scale + Wp / 2 + 2))
        i0 = int(max(0, -(v_.max() - cy0) * scale + Hp / 2 - 2)); i1 = int(min(Hp, -(v_.min() - cy0) * scale + Hp / 2 + 2))
        return slice(i0, i1), slice(j0, j1)
    for kind, g, lab in prims:
        if kind == 'cvx':
            # вершины для рамки — грубо по полупространствам осей
            lim = {tuple(n): c for n, c in g}
            xs_ = (-lim.get((-1, 0, 0), 1) if (-1, 0, 0) in lim else -1, lim.get((1, 0, 0), W_ + 1))
            corners = [(x, y, z) for x in (-1 if lab == 'roof' else xs_[0], W_ + 1 if lab == 'roof' else xs_[1])
                       for y in (-lim.get((0, -1, 0), 0), lim.get((0, 1, 0), 11.45 + ridge)) for z in (-lim[(0, 0, -1)], lim[(0, 0, 1)])]
            sl = bbox(corners)
            o = O[sl]; t0 = np.full(o.shape[:2], -np.inf); t1 = np.full(o.shape[:2], np.inf); n0 = np.zeros(o.shape)
            for n, c in g:
                n = np.array(n, float); dn = d @ n; on = o @ n
                if abs(dn) < 1e-9:
                    bad = on > c; t0[bad] = np.inf; continue
                t = (c - on) / dn
                if dn < 0:
                    upd = t > t0; t0 = np.where(upd, t, t0); n0[upd] = n / np.linalg.norm(n)
                else:
                    t1 = np.minimum(t1, t)
            hit = (t0 <= t1) & np.isfinite(t0)
        else:
            cx, cz, r, y0_, y1_ = g
            sl = bbox([(cx + ox, y, cz + oz) for ox in (-r, r) for oz in (-r, r) for y in (y0_, y1_)])
            o = O[sl]
            ox_, oz_ = o[..., 0] - cx, o[..., 2] - cz
            A = d[0] ** 2 + d[2] ** 2; B = 2 * (ox_ * d[0] + oz_ * d[2]); C = ox_ ** 2 + oz_ ** 2 - r * r
            disc = B * B - 4 * A * C
            t0 = (-B - np.sqrt(np.clip(disc, 0, None))) / (2 * A)
            yy = o[..., 1] + t0 * d[1]
            hit = (disc > 0) & (yy >= y0_) & (yy <= y1_)
            P = o + t0[..., None] * d
            n0 = np.dstack([P[..., 0] - cx, np.zeros_like(yy), P[..., 2] - cz]) / r
        Ts = T[sl]; better = hit & (t0 < Ts)
        Ts[better] = t0[better]; LAB[sl][better] = lab; NRM[sl][better] = n0[better]
    hitm = np.isfinite(T)
    P = O + np.where(hitm, T, 0)[..., None] * d
    X, Y, Z = P[..., 0], P[..., 1], P[..., 2]
    det = np.zeros((Hp, Wp))                                  # резные детали: + выступ, − углубление (в метрах модели)
    isl = lambda *ls: np.isin(LAB, ls)
    nz, nx = NRM[..., 2], NRM[..., 0]
    along = np.where(np.abs(nz) > .5, X, Z)
    # кладка подиума и щёк: ряды и вертикальные швы вперевязку
    m = isl('podium', 'cheek', 'cella') & (np.abs(NRM[..., 1]) < .5)
    rowh = np.where(LAB == 'cella', .55, .7)
    row = np.floor(Y / rowh)
    joint = (np.abs((Y / rowh) % 1) < .07) | (np.abs(((along + (row % 2) * .7) / 1.4) % 1) < .035)
    det -= m * joint * .07
    # дверной проём в целле
    door = (LAB == 'cella') & (nz < -.5) & (np.abs(X - W_ / 2) < 1.25) & (Y < 7.6)
    det -= door * .9
    # колонны: каннелюры и стыки барабанов
    m = LAB == 'col'
    th = np.arctan2(NRM[..., 2], NRM[..., 0])
    det -= m * ((np.cos(th * 12) * .5 + .5) ** 4 * .045 + (np.abs((Y - 3.15) / 1.17 % 1) < .03) * .05)
    # антаблемент: три полосы архитрава, фриз с розетками, зубчики
    m = isl('ent') & (np.abs(NRM[..., 1]) < .5)
    det += m * ((Y > 9.75) * .04 + (Y > 10.05) * .04)
    det += m * (Y > 10.3) * (Y < 10.75) * (np.hypot((along % .9) - .45, Y - 10.52) < .16) * .05
    det += m * (Y > 10.8) * ((along % .32) < .17) * .07
    det -= m * (np.abs(Y - 10.27) < .03) * .05
    # фронтон: тимпан утоплен, по скатам выпуклый карниз
    m = (LAB == 'roof') & (nz < -.5)
    inset = (Y > 11.75) & (Y < 11.45 + ridge * (1 - np.abs(X - W_ / 2) / (W_ / 2 - .1)) - .32)
    det -= m * inset * .25
    # кровля: ряды черепицы по скату
    m = (LAB == 'roof') & (nz > -.5)
    det -= m * (np.abs((Z / .55) % 1) < .12) * .05
    det += isl('cap', 'capital') * .05
    # барельеф по-скульпторски: берём наклоны глубины (в пикселях), скачки на контурах обрезаем до небольшой ступеньки,
    # остальное слегка сжимаем и снова интегрируем (уравнение Пуассона через DCT) — грани сохраняют наклон к свету
    t = np.where(hitm, T - det, np.nan) * scale
    tb = np.where(hitm, t, np.nanmax(t) + 40)
    gx = np.diff(tb, axis=1, append=tb[:, -1:]); gy = np.diff(tb, axis=0, append=tb[-1:, :])
    edge = ~(hitm & np.roll(hitm, -1, 1)); gx = np.where(edge, 0, gx)
    edge = ~(hitm & np.roll(hitm, -1, 0)); gy = np.where(edge, 0, gy)
    cap = 1.6
    cmp = lambda g: np.sign(g) * np.minimum(np.abs(g), cap) / (1 + .25 * np.minimum(np.abs(g), cap))
    gx, gy = -cmp(gx), -cmp(gy)                               # ближе к зрителю — выше
    div = np.diff(gx, axis=1, prepend=0) + np.diff(gy, axis=0, prepend=0)
    from scipy.fft import dctn, idctn
    Dv = dctn(div, norm='ortho')
    ky = np.cos(np.pi * np.arange(Hp) / Hp)[:, None]; kx = np.cos(np.pi * np.arange(Wp) / Wp)[None, :]
    den = 2 * kx + 2 * ky - 4; den[0, 0] = 1
    Hs = Dv / den; Hs[0, 0] = 0
    rel = idctn(Hs, norm='ortho')
    # общий перепад (дальний угол против ближнего) сильно ужимаем, местные наклоны граней оставляем
    mf = hitm.astype(float)
    low = ndi.gaussian_filter(rel * mf, 30) / np.maximum(ndi.gaussian_filter(mf, 30), 1e-3)
    rel = rel - .92 * low
    rel = rel - np.percentile(rel[hitm], 2)
    h = np.where(hitm, 2.0 + np.clip(rel, 0, None) * .45, 0) * sc
    hh = h.reshape(Hp // ss, ss, Wp // ss, ss).mean((1, 3))
    return hh


def fleur(x, y, d):
    c = [(x, y), (x + 5, y + 12 * d), (x, y + 24 * d), (x - 5, y + 12 * d)]
    l = [(x - 3, y + 10 * d), (x - 14, y + 4 * d), (x - 9, y + 15 * d)]
    r = [(x + 3, y + 10 * d), (x + 14, y + 4 * d), (x + 9, y + 15 * d)]
    return [c, l, r]


def field_with_bays(x0, bay_r=28, bay_depth=16):
    """Поле половины доски с резными арками у основания каждого пункта."""
    m = rrect(x0, 40 + bay_depth, x0 + 420, 660 - bay_depth, 6, aa=0)
    im = canvas(); d = ImageDraw.Draw(im)
    for k in range(6):
        cx = x0 + 35 + 70 * k
        for cy in (40 + bay_depth, 660 - bay_depth):
            d.ellipse([(cx - bay_r) * S, (cy - bay_depth) * S, (cx + bay_r) * S, (cy + bay_depth) * S], fill=255)
    m = np.maximum(m, to_arr(im, 0))
    return ndi.gaussian_filter(m, .7)


# ---------- освещение ----------
LIGHT = np.array([-.42, -.62, .66]); LIGHT /= np.linalg.norm(LIGHT)
HALF = LIGHT + np.array([0, 0, 1.0]); HALF /= np.linalg.norm(HALF)


def normals(h, k=1.0):
    gy, gx = np.gradient(h * k)
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    return n / np.linalg.norm(n, axis=2, keepdims=True)


def shade(alb, h, gloss, metal=None, exp=40, cast=1.0):
    """alb HxWx3, h высота в пикселях, gloss 0..1 — сила лака, metal — маска металла."""
    n = normals(h)
    flat = LIGHT[2]
    diff = np.clip((n @ LIGHT) / flat, 0, 1.6)
    spec = np.clip(n @ HALF, 0, 1) ** exp
    broad = np.clip(n @ HALF, 0, 1) ** 6
    # мягкая тень от возвышений (свет сверху-слева, тень вниз-вправо)
    sh = ndi.gaussian_filter(np.clip(ndi.shift(h, (9, 7), order=1, mode='nearest') - h, 0, 40), 6)
    shadow = 1 - np.clip(sh / 22, 0, .55) * cast
    ao = 1 - np.clip((ndi.gaussian_filter(h, 12) - h) / 30, 0, .35)
    lit = alb * (.32 + .68 * diff[..., None]) * (shadow * ao)[..., None]
    g = gloss[..., None] if np.ndim(gloss) else gloss
    out = lit + g * (spec[..., None] * .55 + broad[..., None] * .06)
    if metal is not None:
        m = metal[..., None]
        mlit = alb * (.18 + 1.05 * diff[..., None] ** 1.4) * (shadow * ao)[..., None] + alb * spec[..., None] * 1.3
        out = out * (1 - m) + mlit * m
    return np.clip(out, 0, 1)


def sheen(h, w, strength=.07, angle=.35, width=.18, pos=.42):
    """Отражение окна в лаке: широкая мягкая диагональная полоса."""
    y, x = np.mgrid[0:h, 0:w]
    t = (x / w * math.cos(angle) + y / h * math.sin(angle))
    band = np.exp(-((t - pos) / width) ** 2) * strength + np.exp(-((t - pos - .22) / (width * .45)) ** 2) * strength * .5
    return band[..., None]


def put(alb, m, tex):
    m3 = m[..., None]
    return alb * (1 - m3) + tex * m3


def save(name, rgb, alpha):
    a = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), 'RGB')
    im.putalpha(Image.fromarray(a, 'L'))
    im.save(os.path.join(OUT, name + '.webp'), 'WEBP', quality=88, method=6)
    im.resize((W // 4, H // 4), Image.LANCZOS).save(os.path.join(OUT, name + '-thumb.webp'), 'WEBP', quality=82)
    print('saved', name)


# ---------- общие детали ----------
def carved_frame(outline_pts, amp_h=26):
    """Маска и высота рамки: скруглённый край и тонкий резной желобок по контуру."""
    m = poly(outline_pts, aa=.8)
    d = ndi.distance_transform_edt(m > .5) / S
    h = amp_h * np.clip(d / 16, 0, 1) ** .6
    h -= 5 * np.exp(-((d - 24) / 2.6) ** 2)
    return m, h


def bowl(mask, depth, soft=12):
    d = ndi.distance_transform_edt(mask > .5) / S
    return depth * (1 - np.exp(-d / soft)) * mask


def hinge_layer(alb, h, metal, metal_col):
    for y in (118, 522):
        m = rrect(482, y, 518, y + 60, 4)
        alb = put(alb, m, np.ones((H, W, 3)) * np.array(metal_col))
        d = ndi.distance_transform_edt(m > .5) / S
        h = h + m * (6 + 2 * np.clip(d / 3, 0, 1))
        metal = np.maximum(metal, m)
        for yy in (y + 12, y + 48):
            for xx in (490, 510):
                sm = circle(xx, yy, 3.2)
                h = h - sm * 2.5
                ring = np.clip(circle(xx, yy, 3.2) - circle(xx, yy, 1.4), 0, 1)
                alb = put(alb, sm * .5, np.zeros((H, W, 3)) + .12)
        knuckle = rrect(497, y - 2, 503, y + 62, 3)
        h = h + knuckle * 3
    return alb, h, metal


# ---------- доски ----------
WALNUT = ((.56, .34, .17), (.27, .14, .06))
BEECH = ((.96, .84, .64), (.82, .62, .40))
PINE = ((.82, .58, .29), (.47, .27, .09))
BIRCH = ((.97, .87, .66), (.86, .70, .46))


def board_ararat():
    alb = wood(H, W, *WALNUT, rings=22, seed=3, contrast=.55)
    outline = wavy_rect(10, 10, 1090, 690, 11, 7, 3)
    fm, h = carved_frame(outline)
    gloss = np.full((H, W), .55)
    # поля — углублённые, со своим рисунком волокон
    fields = np.maximum(field_with_bays(40), field_with_bays(540))
    falb = wood(H, W, (.62, .38, .19), (.30, .16, .07), rings=14, seed=5, vertical=True, contrast=.6)
    alb = put(alb, fields, falb)
    h -= ndi.gaussian_filter(fields, 2.2 * S) * 16
    # бортик-фаска вокруг поля
    rim = np.clip(ndi.gaussian_filter(fields, 4 * S) - fields, 0, 1)
    alb = alb * (1 - rim[..., None] * .35)
    # пункты-капли из бука
    # длинные только крайние пункты каждой шестёрки, средние короче — посередине место под крупный аревахач
    tip_of = lambda i: (270 if is_top(i) else 430) if i % 6 in (0, 5) else (200 if is_top(i) else 500)
    drops = [teardrop(ptX(i), is_top(i), tip_of(i), 48) for i in range(24)]
    dm = polys(drops)
    btex = wood(H, W, *BEECH, rings=30, seed=8, vertical=True, contrast=.32, fiber=.12, warp=1.4)
    alb = put(alb, dm, btex)
    edge = np.clip(ndi.gaussian_filter(dm, .9 * S) - ndi.gaussian_filter(dm, .25 * S), 0, 1) + np.clip(dm - ndi.grey_erosion(dm, size=3), 0, 1)
    alb = alb * (1 - np.clip(edge, 0, 1)[..., None] * .55)
    h -= dm * .6
    fl = polys(sum([fleur(ptX(i), tip_of(i) + (6 if is_top(i) else -6), 1 if is_top(i) else -1) for i in range(24)], []))
    alb = put(alb, fl, btex)
    # аревахач — маркетри: тёмный орех и бук, вокруг тонкий инкрустированный круг
    for cx in (250, 750):
        arevakhach_inlay(alb, h, cx, 350, 112, BEECH, ((.30, .16, .07), (.12, .06, .02)), cx)
        for r0, r1 in ((124, 121.4), (129.5, 128.2)):
            ring = np.clip(circle(cx, 350, r0) - circle(cx, 350, r1), 0, 1)
            alb = put(alb, ring, btex)
            h -= ring * .3
    # стык половин и петли
    gap = rrect(497.5, 30, 502.5, 670, 2)
    h -= gap * 14
    alb = alb * (1 - gap[..., None] * .6)
    metal = np.zeros((H, W))
    alb, h, metal = hinge_layer(alb, h, metal, (.78, .60, .30))
    # лотки
    for y0 in (40, 360):
        tm = rrect(1016, y0, 1086, y0 + 300, 35)
        h -= bowl(tm, 20)
        alb = alb * (1 - tm[..., None] * .12)
    rgb = shade(alb, h, gloss, metal)
    rgb = rgb + sheen(H, W, .05) * fm[..., None]
    save('ararat', rgb, fm)


def board_yerevan():
    alb = wood(H, W, *PINE, rings=12, seed=21, contrast=.85, fiber=.18, warp=2.8)
    outline = wavy_rect(10, 10, 1090, 690, 13, 7, 3)
    fm, h = carved_frame(outline, 24)
    gloss = np.full((H, W), .5)
    fields = np.maximum(field_with_bays(40, 30, 14), field_with_bays(540, 30, 14))
    falb = wood(H, W, (.74, .50, .24), (.40, .22, .07), rings=7, seed=25, vertical=True, contrast=.9, fiber=.2, warp=3.2)
    alb = put(alb, fields, falb)
    h -= ndi.gaussian_filter(fields, 2 * S) * 14
    rim = np.clip(ndi.gaussian_filter(fields, 4 * S) - fields, 0, 1)
    alb = alb * (1 - rim[..., None] * .35)
    btex = wood(H, W, *BIRCH, rings=30, seed=28, vertical=True, contrast=.3, fiber=.08, warp=1)
    burn = np.array((.42, .22, .08))
    drops, inner, swirls, dots = [], [], [], []
    for i in range(24):
        # длинные только крайние пункты каждой шестёрки, средние короче — посередине место под крупную резьбу
        x, top = ptX(i), is_top(i); edge_pt = i % 6 in (0, 5); d = 1 if top else -1
        tip = (262 if top else 438) if edge_pt else (196 if top else 504)
        drops.append(teardrop(x, top, tip, 42))
        inner.append(teardrop(x, top, tip - 30 * d, 26, 12) + [teardrop(x, top, tip - 30 * d, 26, 12)[0]])
        cy = 84 if top else 616
        sp = [(x + (7 - t * 5) * math.cos(t * 9), cy + (7 - t * 5) * math.sin(t * 9)) for t in np.linspace(0, 1.2, 50)]
        swirls.append(sp)
        if edge_pt and x < 500: dots.append((x, tip + 16 * d))   # у коротких пунктов и у Гарни точек нет: там резьба
        if i % 6 != 5: dots.append((x + (35 if top else -35), 66 if top else 634))
    dm = polys(drops)
    alb = put(alb, dm, btex)
    edge = np.clip(dm - ndi.grey_erosion(dm, size=3), 0, 1)
    alb = alb * (1 - edge[..., None] * .5)
    eng = np.maximum(lines(inner, 1.4), lines(swirls, 1.3)) * dm
    alb = put(alb, eng * .85, np.ones((H, W, 3)) * burn)
    h -= eng * 1.2
    dmask = np.zeros((H, W))
    for (x, y) in dots: dmask = np.maximum(dmask, circle(x, y, 4.5))
    alb = put(alb, dmask, btex)
    # резьба прямо по полю, во всю высоту средней полосы: слева хачкар, справа храм Гарни в три четверти
    for cx, make in ((250, lambda: khachkar(sc=3.0).result()), (750, lambda: garni_relief(392, 214, 1.5))):
        hl = make()
        nh, nw = hl.shape; y0, x0 = int(round(350 * S - nh / 2)), int(round(cx * S - nw / 2))
        win = (slice(y0, y0 + nh), slice(x0, x0 + nw))
        hl = hl * (1 - dm[win])                               # пункты-вставки лежат поверх резьбы
        h[win] += hl
        # патина: в выборках и бороздах дерево темнее, как у морёной резьбы
        cav = np.clip((ndi.gaussian_filter(hl, 5) - hl) / 3.5, 0, 1) + np.clip(-hl / 6, 0, 1)
        pw = np.clip(cav, 0, 1)[..., None] * .5
        alb[win] = alb[win] * (1 - pw) + np.array((.34, .19, .07)) * pw
    gap = rrect(497.5, 30, 502.5, 670, 2)
    h -= gap * 14
    alb = alb * (1 - gap[..., None] * .6)
    metal = np.zeros((H, W))
    alb, h, metal = hinge_layer(alb, h, metal, (.80, .64, .34))
    for y0 in (40, 360):
        tm = rrect(1016, y0, 1086, y0 + 300, 35)
        h -= bowl(tm, 20)
    cup = circle(1051, 350, 10)
    h -= bowl(cup, 8, 5)
    rgb = shade(alb, h, gloss, metal)
    rgb = rgb + sheen(H, W, .05) * fm[..., None]
    save('yerevan', rgb, fm)


def board_glass():
    alb = wood(H, W, (.40, .37, .43), (.22, .20, .26), rings=14, seed=41, contrast=.55, fiber=.16)
    outline = wavy_rect(10, 10, 1090, 690, 12, 7, 3)
    fm, h = carved_frame(outline, 22)
    gloss = np.full((H, W), .25)
    fields = np.maximum(field_with_bays(40, 27, 15), field_with_bays(540, 27, 15))
    glass = np.ones((H, W, 3)) * np.array((.045, .05, .06))
    # под стеклом — тёмный камень и две воровские звезды: восемь равных лучей,
    # у каждого луча одна половина залита белой краской, вторая — только тонкий контур
    stone = np.array((.10, .10, .11)) * (.75 + .5 * fbm(H, W, 40, 60, 43, 5)[..., None])
    glass = put(glass, fields, stone)
    for cx in (250, 750):
        R, r = 172, 52
        halves = star_halves(cx, 350, R, r, n=8)
        lt = polys([b for a, b in halves])
        chalk = np.array((.90, .90, .92)) * (.86 + .22 * fbm(H, W, 120, 180, 44 + cx, 3)[..., None])
        glass = put(glass, lt, chalk)
        sp = star_poly(cx, 350, R, r, 8)
        outline = lines([sp + [sp[0]]] + [[(cx, 350), a[1]] for a, b in halves], 2.0)
        glass = put(glass, outline * .9, np.ones((H, W, 3)) * np.array((.84, .84, .87)))
    # тонкие матовые контуры пунктов
    tri = []
    for i in range(24):
        x, top = ptX(i), is_top(i)
        b = 58 if top else 642; tip = 290 if top else 410
        t = triangle(x, top, b, tip, 27); tri.append(t + [t[0]])
    tl = lines(tri, 1.3)
    glass = glass + tl[..., None] * .22
    alb = put(alb, fields, glass)
    h -= ndi.gaussian_filter(fields, 1.2 * S) * 10
    gloss = gloss * (1 - fields) + fields * 1.0
    gap = rrect(497.5, 30, 502.5, 670, 2)
    h -= gap * 14
    alb = alb * (1 - gap[..., None] * .6)
    metal = np.zeros((H, W))
    alb, h, metal = hinge_layer(alb, h, metal, (.75, .75, .78))
    for y0 in (40, 360):
        tm = rrect(1016, y0, 1086, y0 + 300, 12)
        h -= bowl(tm, 18, 8)
        alb = put(alb, tm * .85, np.ones((H, W, 3)) * np.array((.05, .05, .06)))
        gloss = np.maximum(gloss, tm)
    rgb = shade(alb, h, gloss, metal, exp=80)
    # отражения в стекле
    refl = sheen(H, W, .16, .55, .12, .38) + sheen(H, W, .05, .55, .3, .7)
    rgb = rgb + refl * fields[..., None]
    rgb = rgb + sheen(H, W, .03) * (fm * (1 - fields))[..., None]
    save('glass', rgb, fm)


def board_night():
    # рамка — тёмный лакированный орех
    alb = wood(H, W, (.25, .14, .08), (.09, .05, .025), rings=18, seed=61, contrast=.6, fiber=.1)
    fm = rrect(0, 0, 1000, 700, 24, aa=.8)
    tray = rrect(1010, 0, 1100, 700, 20, aa=.8)
    allm = np.maximum(fm, tray)
    d = ndi.distance_transform_edt(allm > .5) / S
    h = 24 * np.clip(d / 14, 0, 1) ** .6
    gloss = np.full((H, W), .8)
    fields = np.maximum(rrect(40, 40, 460, 660, 4), rrect(540, 40, 960, 660, 4))
    fl = felt(H, W, (.075, .17, .115), 63)
    vign = np.exp(-(((np.mgrid[0:H, 0:W][1] % (500 * S)) / S - 250) ** 2 / 2e5 + ((np.mgrid[0:H, 0:W][0] / S - 350) ** 2) / 3e5))
    fl = fl * (.7 + .4 * vign[..., None])
    alb = put(alb, fields, fl)
    h -= ndi.gaussian_filter(fields, 1.4 * S) * 12
    h += fields * (vnoise(H, W, H / 1.5, W / 1.5, 64) - .5) * .6
    gloss = gloss * (1 - fields) + fields * .02
    # пункты — кожа: бордовая и костяная, золотой кант
    red, bone = [], []
    for i in range(24):
        x, top = ptX(i), is_top(i)
        t = [(x - 33, 40), (x + 33, 40), (x, 296)] if top else [(x - 33, 660), (x + 33, 660), (x, 404)]
        (red if i % 2 == 0 else bone).append(t)
    rm, bm = polys(red), polys(bone)
    leather_r = felt(H, W, (.46, .09, .10), 65) * .9 + .05 * np.array((.3, 0, 0))
    leather_b = felt(H, W, (.88, .82, .68), 66)
    alb = put(alb, rm, leather_r); alb = put(alb, bm, np.clip(leather_b, 0, 1))
    pts = np.maximum(rm, bm)
    h += pts * 1.5
    gloss = gloss * (1 - pts) + pts * .25
    gold = np.array((.86, .66, .30))
    kant = np.clip(pts - ndi.grey_erosion(pts, size=4), 0, 1)
    metal = kant.copy()
    alb = put(alb, kant, np.ones((H, W, 3)) * gold)
    # золотая инкрустация по краю поля
    inl = np.clip(rrect(26, 26, 974, 674, 10) - rrect(29, 29, 971, 671, 8), 0, 1)
    alb = put(alb, inl, np.ones((H, W, 3)) * gold); metal = np.maximum(metal, inl)
    # планка
    bar = rrect(460, 28, 540, 672, 0)
    alb = put(alb, bar, wood(H, W, (.25, .14, .08), (.09, .05, .025), rings=24, seed=67, vertical=True, contrast=.6))
    h = h * (1 - bar) + bar * 24
    bl = rrect(499.2, 40, 500.8, 660, 0)
    alb = put(alb, bl, np.ones((H, W, 3)) * gold); metal = np.maximum(metal, bl)
    # гранёные золотые воровские звёзды: высота из расстояния до контура
    def gold_star(cx, cy, R, r, base):
        nonlocal alb, h, metal
        sm = poly(star_poly(cx, cy, R, r, 8))
        dist = ndi.distance_transform_edt(sm > .5) / S
        alb = put(alb, sm, np.ones((H, W, 3)) * gold)
        metal = np.maximum(metal, sm)
        return sm * (base + dist * 1.1)
    dd = np.zeros((H, W))
    disc = circle(500, 350, 34)
    alb = put(alb, disc, np.ones((H, W, 3)) * np.array((.06, .04, .03)))
    ring = np.clip(circle(500, 350, 34) - circle(500, 350, 31.5), 0, 1)
    alb = put(alb, ring, np.ones((H, W, 3)) * gold); metal = np.maximum(metal, ring)
    dd = np.maximum(dd, gold_star(500, 350, 28, 10, 2))
    for y in (150, 550): dd = np.maximum(dd, gold_star(500, y, 15, 5.5, 1.5))
    dd = np.maximum(dd, gold_star(250, 350, 42, 15, 2))
    cr = np.clip(circle(250, 350, 48) - circle(250, 350, 46.5), 0, 1)
    alb = put(alb, cr * .8, np.ones((H, W, 3)) * gold); metal = np.maximum(metal, cr)
    for (x, y) in ((20, 20), (980, 20), (20, 680), (980, 680)): dd = np.maximum(dd, gold_star(x, y, 13, 4.8, 1))
    dd = np.maximum(dd, gold_star(1055, 350, 12, 4.4, 1))
    h = h + dd
    for y0 in (40, 360):
        tm = rrect(1020, y0, 1090, y0 + 300, 8)
        h -= bowl(tm, 16, 6)
        alb = put(alb, tm, felt(H, W, (.06, .045, .035), 70 + y0))
        gloss = gloss * (1 - tm) + tm * .02
        tr = np.clip(rrect(1019, y0 - 1, 1091, y0 + 301, 9) - tm, 0, 1)
        alb = put(alb, tr * .8, np.ones((H, W, 3)) * gold); metal = np.maximum(metal, tr)
    rgb = shade(alb, h, gloss, metal, exp=60)
    rgb = rgb + sheen(H, W, .07) * ((allm) * (1 - fields))[..., None]
    save('night', rgb, allm)


# ---------- шашки ----------
def checker_sprite(name, kind):
    N = 4 * 64  # рисуем с запасом и уменьшаем
    R = N * 30 / 64
    y, x = np.mgrid[0:N, 0:N] - (N - 1) / 2
    r = np.hypot(x, y) / R
    inside = np.clip((1 - r) * R / 1.2, 0, 1)
    dome = np.sqrt(np.clip(1 - r ** 2, 0, 1)) * R * .18
    bevel = np.clip((1 - r) / .08, 0, 1) ** .5 * R * .12
    h = np.minimum(dome + R * .06, bevel + R * .02)
    def groove(rad, depth, wdt): return -np.exp(-((r - rad) / wdt) ** 2) * depth * R
    if kind in ('beech', 'walnut'):
        cols = BEECH if kind == 'beech' else ((.50, .30, .15), (.22, .11, .04))
        alb = wood(N, N, *cols, rings=6, seed=91 if kind == 'beech' else 92, contrast=.5, fiber=.12)
        h = h + groove(.78, .035, .025) + groove(.55, .03, .02) + groove(.3, .025, .018)
        gl, ex = .6, 30
    else:
        base = (.94, .90, .80) if kind == 'ivory' else (.10, .10, .115)
        alb = np.ones((N, N, 3)) * np.array(base)
        alb = alb * (1 + (vnoise(N, N, 6, 6, 93) - .5)[..., None] * .06)
        # воровская звезда-инкрустация
        sp = star_halves(0, 0, R * .55, R * .2, 8)
        def pm(pts):
            im = Image.new('L', (N, N), 0)
            ImageDraw.Draw(im).polygon([(px + (N - 1) / 2, py + (N - 1) / 2) for px, py in pts], fill=255)
            return ndi.gaussian_filter(np.asarray(im, float) / 255, 1)
        lt = sum(pm(a) for a, b in sp); dk = sum(pm(b) for a, b in sp)
        c1, c2 = ((.98, .95, .88), (.12, .10, .09)) if kind == 'ivory' else ((.90, .88, .84), (.02, .02, .025))
        alb = alb * (1 - lt[..., None]) + np.array(c1) * lt[..., None]
        alb = alb * (1 - dk[..., None]) + np.array(c2) * dk[..., None]
        ringc = (.69, .54, .24) if kind == 'ivory' else (.6, .6, .64)
        ringm = np.exp(-((r - .77) / .02) ** 2)
        alb = alb * (1 - ringm[..., None]) + np.array(ringc) * ringm[..., None]
        h = h + groove(.77, .02, .02) - (lt + dk) * R * .01
        gl, ex = 1.0, 70
    gy, gx = np.gradient(h)
    n = np.dstack([-gx, -gy, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    diff = np.clip((n @ LIGHT) / LIGHT[2], 0, 1.6)
    spec = np.clip(n @ HALF, 0, 1) ** ex
    rgb = alb * (.3 + .7 * diff[..., None]) + gl * spec[..., None] * .6
    rgb = np.clip(rgb, 0, 1)
    im = Image.fromarray((rgb * 255).astype(np.uint8), 'RGB')
    im.putalpha(Image.fromarray((inside * 255).astype(np.uint8), 'L'))
    im.resize((128, 128), Image.LANCZOS).save(os.path.join(OUT, f'ck-{name}.png'), optimize=True)
    print('saved ck', name)


if __name__ == '__main__':
    which = sys.argv[1:] or ['ararat', 'yerevan', 'glass', 'night', 'checkers']
    for w_ in which:
        if w_ == 'checkers':
            for k in ('ivory', 'onyx', 'beech', 'walnut'): checker_sprite(k, k)
        else:
            globals()['board_' + w_]()
