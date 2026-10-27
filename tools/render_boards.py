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
ARM_FONT = 'C:/Windows/Fonts/sylfaen.ttf'


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
    drops = [teardrop(ptX(i), is_top(i), 270 if is_top(i) else 430, 48) for i in range(24)]
    dm = polys(drops)
    btex = wood(H, W, *BEECH, rings=30, seed=8, vertical=True, contrast=.32, fiber=.12, warp=1.4)
    alb = put(alb, dm, btex)
    edge = np.clip(ndi.gaussian_filter(dm, .9 * S) - ndi.gaussian_filter(dm, .25 * S), 0, 1) + np.clip(dm - ndi.grey_erosion(dm, size=3), 0, 1)
    alb = alb * (1 - np.clip(edge, 0, 1)[..., None] * .55)
    h -= dm * .6
    fl = polys(sum([fleur(ptX(i), (276 if is_top(i) else 424), 1 if is_top(i) else -1) for i in range(24)], []))
    alb = put(alb, fl, btex)
    # аревахач — маркетри: тёмный орех и бук, вокруг тонкий инкрустированный круг
    for cx in (250, 750):
        arevakhach_inlay(alb, h, cx, 350, 64, BEECH, ((.30, .16, .07), (.12, .06, .02)), cx)
        for r0, r1 in ((72, 70.4), (75.5, 74.7)):
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
        x, top = ptX(i), is_top(i); tip = 262 if top else 438; d = 1 if top else -1
        drops.append(teardrop(x, top, tip, 42))
        inner.append(teardrop(x, top, tip - 30 * d, 26, 12) + [teardrop(x, top, tip - 30 * d, 26, 12)[0]])
        cy = 84 if top else 616
        sp = [(x + (7 - t * 5) * math.cos(t * 9), cy + (7 - t * 5) * math.sin(t * 9)) for t in np.linspace(0, 1.2, 50)]
        swirls.append(sp)
        dots.append((x, tip + 16 * d))
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
    # медальон «Арарат»
    disc = circle(250, 350, 66)
    alb = put(alb, disc, btex)
    alb = put(alb, np.clip(circle(250, 350, 66) - circle(250, 350, 63), 0, 1), np.ones((H, W, 3)) * burn)
    alb = put(alb, np.clip(circle(250, 350, 58.5) - circle(250, 350, 57.3), 0, 1) * .8, np.ones((H, W, 3)) * burn)
    mount = poly([(196, 378), (222, 346), (232, 354), (262, 312), (282, 334), (304, 378)])
    shade_m = wood(H, W, (.62, .38, .16), (.42, .22, .08), rings=40, seed=31, contrast=.4)
    alb = put(alb, mount, shade_m)
    snow = polys([[(262, 312), (251, 327), (258, 325), (264, 331), (271, 323), (277, 328), (282, 334)],
                  [(222, 346), (217, 352), (224, 351), (228, 355)]])
    alb = put(alb, snow, btex)
    t1 = text_mask('ԱՐԱՐԱՏ', 250, 398, 15, spacing=2)
    alb = put(alb, t1 * .9, np.ones((H, W, 3)) * burn)
    h -= (eng.max() * 0 + mount * .8 + t1 * 1)
    # медальон с аревахачем и лентой «ՀԱՅԱՍՏԱՆ»
    disc2 = circle(750, 345, 62)
    alb = put(alb, disc2, btex)
    alb = put(alb, np.clip(circle(750, 345, 62) - circle(750, 345, 59), 0, 1), np.ones((H, W, 3)) * burn)
    arevakhach_inlay(alb, h, 750, 345, 48, BIRCH, ((.50, .28, .11), (.30, .15, .05)), 77)
    ribbon = poly(bez((672, 392), (720, 404), (780, 404), (828, 392), 30) + [(836, 410), (824, 418)] +
                  bez((824, 418), (780, 432), (720, 432), (676, 418), 30) + [(664, 410)])
    alb = put(alb, ribbon, btex)
    alb = put(alb, np.clip(ribbon - ndi.grey_erosion(ribbon, size=3), 0, 1), np.ones((H, W, 3)) * burn)
    t2 = text_mask('ՀԱՅԱՍՏԱՆ', 750, 414, 14, spacing=2)
    alb = put(alb, t2 * .9, np.ones((H, W, 3)) * burn)
    h += ribbon * 1.5 - t2
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
    # звёзды под стеклом: белая краска, половины лучей разного тона, тёмные швы
    for cx in (250, 750):
        halves = star_halves(cx, 350, 168, 64, n=6)
        lt = polys([a for a, b in halves]); dk = polys([b for a, b in halves])
        glass = put(glass, lt, np.ones((H, W, 3)) * np.array((.93, .93, .95)))
        glass = put(glass, dk, np.ones((H, W, 3)) * np.array((.74, .75, .79)))
        seams = lines([[(cx, 350), a[1]] for a, b in halves] + [star_poly(cx, 350, 168, 64, 6) + [star_poly(cx, 350, 168, 64, 6)[0]]], 2.2)
        glass = put(glass, seams * .9 * np.maximum(lt, dk), np.ones((H, W, 3)) * .08)
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
