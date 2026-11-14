# Эскизы нового центра доски «Гранат»: три варианта (A — реалистичная инкрустация, B — орнамент-розетка,
# C — разрез граната на доске из красного дерева). python3 tools/pom_sketch.py → .preview/pom-sketch.png
import math, os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(__file__))
import render_real as RR
from render_real import _paint, outline, circle, poly, H, W, S

def burn(alb, m, k=.8, w=.8): return alb * (1 - np.clip(outline(m, w), 0, 1)[..., None] * k)
def shade(alb, m, f): return alb * (1 - m[..., None] * (1 - f)[..., None])   # затемнить (песочное тонирование)
YY, XX = np.mgrid[0:H, 0:W] / S

def leaf(x, y, ang, L=34, wd=11):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    up = [(x + ca * t * L - sa * math.sin(math.pi * t ** .8) * wd, y + sa * t * L + ca * math.sin(math.pi * t ** .8) * wd) for t in np.linspace(0, 1, 18)]
    dn = [(x + ca * t * L + sa * math.sin(math.pi * t ** .8) * wd, y + sa * t * L - ca * math.sin(math.pi * t ** .8) * wd) for t in np.linspace(1, 0, 18)]
    full = poly(up + dn); half = poly(up + [(x + ca * L, y + sa * L), (x, y)])
    vein = poly([(x, y), (x + ca * L * .92 - sa * .7, y + sa * L * .92 + ca * .7), (x + ca * L * .92 + sa * .7, y + sa * L * .92 - ca * .7)])
    return full, half, vein

def seeds_in(alb, h, m, cx, cy, R, r=3.4, seed=1, n=None):
    """гранатовые зёрна в маске m: красные капли с бликом, плотно"""
    rng = np.random.default_rng(seed); pts = []
    for _ in range(9000):
        if n and len(pts) >= n: break
        rr, aa = R * math.sqrt(rng.random()), rng.random() * 2 * math.pi
        x, y = cx + rr * math.cos(aa), cy + rr * math.sin(aa)
        if m[int(y * S) % H, int(x * S) % W] < .6: continue
        if all((x - px) ** 2 + (y - py) ** 2 > (2.05 * r) ** 2 for px, py in pts): pts.append((x, y))
    sd = np.zeros((H, W)); hl = np.zeros((H, W))
    for x, y in pts:
        sd = np.maximum(sd, circle(x, y, r)); hl = np.maximum(hl, circle(x - r * .35, y - r * .35, r * .32))
    alb = _paint(alb, sd, (0, 0, 1)); alb = burn(alb, sd, .55, .45)
    d = np.clip(np.hypot(*np.gradient(ndi.gaussian_filter(sd, S))) , 0, 1)
    alb = _paint(alb, hl * sd * .75, (0, 1, 0))
    h += sd * .45
    return alb, h

def center_A(alb, h, cx, light):
    """реалистичная инкрустация: плод из долек красного дерева с песочным тонированием, веточка с листьями, половинка с зёрнами"""
    cy = 350; fx, fy, R = cx - 12, cy + 12, 50
    body = circle(fx, fy, R)
    crown = poly([(fx - 17, fy - R + 6), (fx - 21, fy - R - 20), (fx - 9, fy - R - 8), (fx, fy - R - 24), (fx + 9, fy - R - 8), (fx + 21, fy - R - 20), (fx + 17, fy - R + 6)])
    fruit = np.clip(body + crown, 0, 1)
    # ветка и листья (светлый клён), за плодом
    br = np.zeros((H, W)); pts = [(fx + 4 + 30 * t - 10 * t * t, fy - R - 16 - 18 * t) for t in np.linspace(0, 1, 30)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        br = np.maximum(br, poly([(x0 - 2.4, y0), (x1 - 2.4, y1), (x1 + 2.4, y1), (x0 + 2.4, y0)]))
    lv, lh, vn = np.zeros((H, W)), np.zeros((H, W)), np.zeros((H, W))
    for (x, y, a, L_) in ((pts[10][0], pts[10][1], -150, 30), (pts[18][0], pts[18][1], -95, 26), (pts[29][0], pts[29][1], -10, 28)):
        f, hf, v = leaf(x, y, a, L_); lv = np.maximum(lv, f); lh = np.maximum(lh, hf); vn = np.maximum(vn, v)
    back = np.clip(br + lv, 0, 1) * (1 - fruit)
    alb = _paint(alb, back, (0, 1, 0)); alb = shade(alb, lh * (1 - fruit), np.full((H, W), .72)); alb = alb * (1 - (vn * (1 - fruit))[..., None] * .7)
    alb = burn(alb, back, .8)
    # плод: 5 долек-меридианов, каждая темнее к правому краю; общий объём — темнее справа снизу
    alb = _paint(alb, fruit, (0, 0, 1))
    u = np.clip((XX - fx) / R, -1, 1); v = np.sqrt(np.clip(1 - ((YY - fy) / R) ** 2, 0.02, 1))
    q = (np.arcsin(np.clip(u / v, -1, 1)) / math.pi + .5) * 5            # номер дольки 0..5 по долготе
    frac = q % 1
    f = (1.0 - .32 * frac ** 1.6) * (1 - .25 * np.clip(((XX - fx) + (YY - fy)) / (1.6 * R), 0, 1))
    alb = shade(alb, body, f)
    seam = body * (np.minimum(frac, 1 - frac) < .035) * (np.abs(u) < .97)
    alb = alb * (1 - seam[..., None] * .55)
    hi = np.exp(-(((XX - fx + R * .38) / (R * .22)) ** 2 + ((YY - fy + R * .4) / (R * .3)) ** 2))
    alb = _paint(alb, body * hi * .45, (0, 1, 0))                                        # блик лака светлым шпоном
    alb = shade(alb, crown * (1 - body), np.full((H, W), .78)); alb = burn(alb, fruit, .85)
    # половинка
    hx, hy, hr = cx + 46, cy + 44, 34
    half = circle(hx, hy, hr); pulp = circle(hx, hy, hr - 6)
    alb = _paint(alb, half * (1 - pulp), (0, 0, 1)); alb = _paint(alb, pulp, (0, 1, 0))
    alb = shade(alb, pulp, .88 + .12 * np.clip((hy - YY) / hr, -1, 1) * .5 + .06)
    memb = np.zeros((H, W))
    for a in (20, 140, 260):
        t = math.radians(a)
        memb = np.maximum(memb, poly([(hx, hy), (hx + math.cos(t) * hr, hy + math.sin(t) * hr), (hx + math.cos(t + .06) * hr, hy + math.sin(t + .06) * hr)]))
    alb, h = seeds_in(alb, h, pulp * (1 - ndi.grey_dilation(memb, size=int(4 * S))), hx, hy, hr - 7, 3.3, seed=cx)
    alb = alb * (1 - memb[..., None] * pulp[..., None] * .35)
    alb = burn(alb, half, .9); alb = burn(alb, pulp, .5, .5)
    d = ndi.distance_transform_edt(body > .5) / S
    h += body * np.clip(d / 22, 0, 1) ** .6 * 1.8 + crown * .8 + half * .9 - pulp * .3 + back * .3
    return alb, h

def center_B(alb, h, cx, light):
    """орнамент-розетка: шесть гранатов по кругу короной наружу, между ними пары листьев, в центре — розетка из зёрен"""
    cy = 350; shapes = np.zeros((H, W)); lv = np.zeros((H, W)); lh = np.zeros((H, W)); fr = np.zeros((H, W))
    vine = np.clip(circle(cx, cy, 45) - circle(cx, cy, 41.5), 0, 1)
    for k in range(6):
        a = math.radians(k * 60 - 90); ca, sa = math.cos(a), math.sin(a)
        px, py = cx + ca * 70, cy + sa * 70
        b = circle(px, py, 17)
        tip = [(px + ca * 14 + (-sa) * s * 7, py + sa * 14 + ca * s * 7) for s in (-1, 1)]
        cr = poly([tip[0], (px + ca * 30 - sa * 8, py + sa * 30 + ca * 8), (px + ca * 24, py + sa * 24), (px + ca * 32, py + sa * 32),
                   (px + ca * 24 + 0, py + sa * 24), (px + ca * 30 + sa * 8, py + sa * 30 - ca * 8), tip[1]])
        fr = np.maximum(fr, np.clip(b + cr, 0, 1))
        st = poly([(cx + ca * 44 - sa * 1.6, cy + sa * 44 + ca * 1.6), (px - ca * 15 - sa * 1.6, py - sa * 15 + ca * 1.6), (px - ca * 15 + sa * 1.6, py - sa * 15 - ca * 1.6), (cx + ca * 44 + sa * 1.6, cy + sa * 44 - ca * 1.6)])
        shapes = np.maximum(shapes, st)
        b2 = math.radians(k * 60 - 60); c2, s2 = math.cos(b2), math.sin(b2)
        lx, ly = cx + c2 * 46, cy + s2 * 46
        for d_ in (-28, 28):
            f, hf, v = leaf(lx, ly, k * 60 - 60 + d_, 30, 9); lv = np.maximum(lv, f); lh = np.maximum(lh, hf)
    light_m = np.clip(vine + shapes + lv, 0, 1) * (1 - fr)
    alb = _paint(alb, light_m, (0, 1, 0)); alb = shade(alb, lh * (1 - fr), np.full((H, W), .74)); alb = burn(alb, light_m, .8)
    alb = _paint(alb, fr, (0, 0, 1))
    for k in range(6):
        a = math.radians(k * 60 - 90); px, py = cx + math.cos(a) * 70, cy + math.sin(a) * 70
        alb = shade(alb, circle(px, py, 17), .72 + .28 * np.clip(1 - np.hypot(XX - px + 6 * math.cos(a + 2.4), YY - py + 6 * math.sin(a + 2.4)) / 22, 0, 1))
    alb = burn(alb, fr, .85)
    core = circle(cx, cy, 26); alb = _paint(alb, core, (0, 1, 0)); alb = burn(alb, core, .8)
    alb, h = seeds_in(alb, h, circle(cx, cy, 23), cx, cy, 22, 3.3, seed=7)
    h += fr * 1.2 + light_m * .3 + core * .3
    return alb, h

def center_C(alb, h, cx, light):
    """поперечный разрез граната крупно: кожура, белые перегородки, шесть камер с зёрнами-рубинами"""
    cy = 350; R = 90
    peel = circle(cx, cy, R); pulp = circle(cx, cy, R - 11)
    alb = _paint(alb, peel, (0, 0, 1)); alb = shade(alb, peel * (1 - pulp), .78 + .22 * np.clip((cy - YY) / R * .5 + .5, 0, 1))
    alb = _paint(alb, pulp, (0, 1, 0))
    ang = np.arctan2(YY - cy, XX - cx); r = np.hypot(XX - cx, YY - cy)
    wob = 6 * np.sin(ang * 3 + r / 18)
    secs = ((ang + math.pi) / (2 * math.pi) * 6 + wob / 60) % 1
    memb = pulp * ((np.minimum(secs, 1 - secs) < .025 + 2.4 / np.maximum(r, 8)) | (r < 14))
    chambers = pulp * (1 - ndi.grey_dilation(memb, size=int(3 * S)))
    alb = shade(alb, chambers, np.full((H, W), .55))             # мякоть между зёрнами — в тени
    alb, h = seeds_in(alb, h, chambers, cx, cy, R - 12, 3.9, seed=3)
    alb = burn(alb, memb, .45, .5)
    alb = burn(alb, peel, .9); alb = burn(alb, pulp, .55, .5)
    h += peel * .6 - pulp * .25
    return alb, h

RR.WOOD_TONE['pomA'] = RR.WOOD_TONE['pomB'] = RR.WOOD_TONE['pomegranate']
RR.WOOD_TONE['pomC'] = ((.44, .13, .08), (.21, .05, .03))     # красное дерево (махагон/падук) вместо ореха
from PIL import Image
crops = []
for nm, fn in (('pomA', center_A), ('pomB', center_B), ('pomC', center_C)):
    RR.to_generic(nm, RR.board_arevakhach(layers=True, center=fn))
    a = np.load(os.path.join(RR.os.path.dirname(RR.__file__), '..', '.preview', f'layers-{nm}.npz'))['alb']
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    crops.append(im.crop((int(250 * S) - int(150 * S), int(350 * S) - int(150 * S), int(250 * S) + int(150 * S), int(350 * S) + int(150 * S))))
w, h_ = crops[0].size
out = Image.new('RGB', (w * 3 + 40, h_), (20, 14, 10))
for i, c in enumerate(crops): out.paste(c, (i * (w + 20), 0))
out.save(os.path.join(os.path.dirname(__file__), '..', '.preview', 'pom-sketch.png'))
print('sketch ok', out.size)
