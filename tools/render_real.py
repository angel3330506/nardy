# Доски по образцу настоящих армянских нард ручной работы (Ohanyan, Sunny Armenia): морёный лакированный бук,
# пункты — инкрустация светлым буком с выжженным контуром (капля + две планки буквой V, на конце завитки и капелька),
# у края поля резные арки с точечной насечкой, в центре аревахач в витом жгуте, узорные латунные петли.
# Поверхность дерева — фотографии шпона (tools/tex, CC0), а не нарисованный шум.
import math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(__file__))
from render_boards import (S, W, H, OUT, canvas, to_arr, P, poly, polys, rrect, circle, lines, ptX, is_top, put, shade,
                           sheen, save, arevakhach_masks, arc_pts, spiral, fbm, vnoise)
from PIL import ImageDraw

TEX = os.path.join(os.path.dirname(__file__), 'tex')
_cache = {}


def phototex(name, vertical=False, scale=1.0, off=(0, 0)):
    """Фото шпона на весь холст: зеркальная укладка без швов. vertical — волокна сверху вниз."""
    key = (name, vertical, scale, off)
    if key in _cache: return _cache[key]
    im = np.asarray(Image.open(os.path.join(TEX, name + '.jpg')).convert('RGB'), float) / 255
    if vertical: im = np.rot90(im)
    if scale != 1: im = ndi.zoom(im, (scale, scale, 1), order=1)
    t = np.concatenate([im, im[::-1]], 0); t = np.concatenate([t, t[:, ::-1]], 1)
    reps = (H // t.shape[0] + 2, W // t.shape[1] + 2, 1)
    t = np.tile(t, reps)[off[0]:off[0] + H, off[1]:off[1] + W]
    _cache[key] = t
    return t


def stain(tex, color, k=1.0):
    """Морилка: цвет задаём сами, рисунок волокон берём из фото (яркость относительно средней)."""
    lum = tex.mean(-1); L = lum / lum.mean()
    return np.clip(np.array(color)[None, None] * (L ** k)[..., None], 0, 1)


def outline(m, w=1.0):
    """Выжженный контур вокруг маски инкрустации."""
    d = ndi.grey_dilation(m, size=max(2, int(w * S * 2) + 1))
    return np.clip(d - m, 0, 1)


def point_shapes(x, top, tip_len=218):
    """Узор пункта, как на настоящих досках: капля из арки у края, по бокам планки буквой V,
    на конце планки закручены завитками наружу, за ними капелька. Возвращает (капли, планки-линии, завитки, капельки)."""
    d = 1 if top else -1
    y0 = 40 if top else 660
    Y = lambda t: y0 + d * t
    drop = [(x + 17 * math.cos(a), Y(30) - d * 17 * math.sin(a)) for a in np.linspace(0, math.pi, 30)] + [(x, Y(128))]
    tip = tip_len
    strips = [[(x - 30, Y(16)), (x - 5.5, Y(tip))], [(x + 30, Y(16)), (x + 5.5, Y(tip))]]
    curls = []
    for s in (-1, 1):
        cx, cy = x + s * 9.6, Y(tip + 1)
        a0 = math.atan2(Y(tip) - cy, x + s * 5.5 - cx)
        curls.append([(cx + r * math.cos(a0 - s * d * t), cy + r * math.sin(a0 - s * d * t))
                      for t, r in zip(np.linspace(0, 1.75 * math.pi, 26), np.linspace(4.2, 1.2, 26))])
    oval = (x, Y(tip + 11))
    return drop, strips, curls, oval


def oval_mask(cx, cy, rx, ry):
    im = canvas(); ImageDraw.Draw(im).ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=255)
    return to_arr(im, .6)


def rope_ring(cx, cy, r0, r1, n=44):
    """Витой жгут между радиусами r0..r1: косые валики (высота) и тёмные бороздки."""
    yy, xx = np.mgrid[0:H, 0:W] / S
    r = np.hypot(xx - cx, yy - cy); a = np.arctan2(yy - cy, xx - cx)
    t = (r - r0) / (r1 - r0)
    band = (t > 0) & (t < 1)
    ph = (a / (2 * math.pi) * n + t * 1.2) % 1
    roll = np.sqrt(np.clip(1 - ((ph - .5) * 2) ** 2, 0, 1)) * np.sqrt(np.clip(1 - ((t - .5) * 2) ** 2, 0, 1))
    return band * roll, band


def hinge(alb, h, metal, x, y):
    """Литая бронзовая петля как на настоящих нардах: ось вертикально вдоль стыка половин, по обе стороны —
    фигурные пластины с волнистым краем, литой рельеф (завитки, листья, розетка), винты со шлицем,
    ось-трубка с колпачками. Выпуклое натёрто до блеска, в углублениях тёмная патина."""
    yy, xx = np.mgrid[0:H, 0:W] / S
    plate = np.zeros((H, W)); rel = np.zeros((H, W))
    for s in (-1, 1):
        cx = x + s * 21
        u, v = (xx - cx) / 19, (yy - y) / 27
        r = np.hypot(u, v); a = np.arctan2(u, v)
        edge = 1 + .07 * np.cos(a * 10) + .12 * np.cos(a * 2) ** 2          # фигурный волнистый край
        pm = np.clip((edge - r) * 30, 0, 1) * (s * (xx - x) > 2.5)
        plate = np.maximum(plate, pm)
        # рельеф: бортик по краю, розетка в центре, сверху и снизу завитки с листьями
        border = np.exp(-((edge - r - .07) / .035) ** 2) * pm
        ros = np.zeros((H, W))
        for k in range(8):
            ang = k * math.pi / 4
            ros = np.maximum(ros, np.clip(1 - np.hypot((xx - cx - 3.6 * math.cos(ang)) / 2.2, (yy - y - 3.6 * math.sin(ang)) / 2.2), 0, 1))
        ros = np.maximum(ros, np.clip(1 - np.hypot(xx - cx, yy - y) / 1.8, 0, 1))
        scroll = np.zeros((H, W))
        for sy in (-1, 1):
            sp = spiral(cx + s * 2, y + sy * 14, 6.5, 1.5, (math.pi / 2 if sy > 0 else -math.pi / 2) + s * .6, sy * s)
            scroll = np.maximum(scroll, lines([sp], 1.6, aa=.5))
            leaf = [(cx - s * (6 + 3 * math.sin(math.pi * t)), y + sy * (5 + 7 * t)) for t in np.linspace(0, 1, 10)]
            scroll = np.maximum(scroll, lines([leaf], 1.3, aa=.5))
        screws = np.zeros((H, W))
        for sy in (-9, 9):
            sx = cx + s * 11
            sc = circle(sx, y + sy, 2.6)
            slot = lines([[(sx - 1.9, y + sy - 1.9), (sx + 1.9, y + sy + 1.9)], [(sx - 1.9, y + sy + 1.9), (sx + 1.9, y + sy - 1.9)]], .55, aa=.3)
            screws = np.maximum(screws, sc * (1 - slot * .8))
        rel += pm * (1.2 + border * 1.4 + ros * 1.6 + scroll * 1.4 + screws * 1.8)
    knuckle = np.clip(1 - np.abs(xx - x) / 3.6, 0, 1) * (np.abs(yy - y) < 29)
    seg = (np.abs(((yy - y) / 10.5) % 1 - .5) < .03) * knuckle
    caps = (np.abs(np.abs(yy - y) - 30) < 1.6) * (np.abs(xx - x) < 2.6)
    m = np.clip(np.maximum.reduce([plate, (knuckle > 0).astype(float), caps.astype(float)]), 0, 1)
    rel = rel + np.sqrt(knuckle) * 4.2 - seg * 1.2 + caps * 3.5
    rel = ndi.gaussian_filter(rel, .5)
    # фон пластины в тёмной патине, литой узор и края натёрты до блеска
    orn = np.clip((rel - 1.2 * plate) / 1.6, 0, 1)
    dark, bright = np.array((.30, .22, .11)), np.array((.86, .70, .40))
    col = dark[None, None] * (1 - orn[..., None]) + bright[None, None] * orn[..., None]
    col = np.where((knuckle > 0)[..., None] | caps[..., None], bright * .9, col)
    col = col * (.82 + .3 * fbm(H, W, 40, 40, 9, 2))[..., None]
    alb = put(alb, m, col); metal = np.maximum(metal, m)
    h = h * (1 - m) + m * (25 + rel * 1.1)
    return alb, h, metal


def board_arevakhach(layers=False):
    """layers=True — вместо картинки вернуть слои для 3D-рендера (tools/blender_board.py): высоты, маски дерева и металла.
    Тогда «основное дерево» = (1,0,0), «светлый бук» = (0,1,0): после всех затемнений R и G — доли и тон каждого."""
    STAIN = (.30, .165, .075)                                 # «орех» на буке, как на фото
    base = phototex('cherry_veneer', vertical=True)
    alb = stain(base, STAIN, 1.6)
    # морилка темнее к краям доски и в углублениях
    yy, xx = np.mgrid[0:H, 0:W] / S
    edge = np.minimum.reduce([xx, 1100 - xx, yy, 700 - yy])
    alb = alb * (.78 + .22 * np.clip(edge / 70, 0, 1))[..., None]
    alb = alb * (.88 + .24 * fbm(H, W, 2, 3, 5, 3))[..., None]      # морилка легла неровно, как на настоящей доске
    light = stain(phototex('cherry_veneer', vertical=True, off=(400, 900)), (.86, .66, .45), 1.1)   # натуральный бук
    light_h = stain(phototex('cherry_veneer', off=(300, 200)), (.86, .66, .45), 1.1)
    if layers:
        alb = np.zeros((H, W, 3)); alb[..., 0] = 1
        alb = alb * (.80 + .20 * np.clip(edge / 70, 0, 1))[..., None]
        light = np.zeros((H, W, 3)); light[..., 1] = 1; light_h = light
    # корпус: прямой, скруглённые углы, профилированный край
    body = rrect(0, 0, 1100, 700, 18, aa=.8)
    d = ndi.distance_transform_edt(body > .5) / S
    h = 26 * np.clip(d / 12, 0, 1) ** .55 - 4 * np.exp(-((d - 16) / 2) ** 2)
    gloss = np.full((H, W), .8)
    # поля чуть утоплены, по краю — уступ
    fields = np.maximum(rrect(30, 30, 470, 670, 8), rrect(530, 30, 970, 670, 8))
    h -= ndi.gaussian_filter(fields, 1.2 * S) * 5
    alb = alb * (1 - outline(fields, 1.2)[..., None] * .45)
    # стык половин
    gap = rrect(497, 20, 503, 680, 2); h -= gap * 14; alb = alb * (1 - gap[..., None] * .7)
    # лотки — продольные желоба в раме справа
    for y0 in (40, 360):
        tm = rrect(1022, y0, 1088, y0 + 300, 30)
        dd = ndi.distance_transform_edt(tm > .5) / S
        h -= tm * 16 * (1 - np.exp(-dd / 10))
        alb = alb * (1 - tm[..., None] * .12)
    # резной бордюр у края поля: приподнятая полоса с точечной насечкой; под каждым пунктом в ней вырезана арка,
    # скруглённая к краю и плавно уходящая в поле — в её скруглении лежит голова капли
    band = np.zeros((H, W))
    for x0 in (30, 530):
        band = np.maximum(band, rrect(x0 + 3, 33, x0 + 437, 68, 3, aa=.5) + rrect(x0 + 3, 632, x0 + 437, 667, 3, aa=.5))
    band = np.clip(band, 0, 1)
    holes = np.zeros((H, W)); bays = np.zeros((H, W)); bayd = np.zeros((H, W))
    for i in range(24):
        x, top = ptX(i), is_top(i); dy = 1 if top else -1; y0 = 40 if top else 660
        u = [(x + 27 * math.cos(a), y0 + dy * (14 - 13 * math.sin(a))) for a in np.linspace(math.pi, 0, 30)]
        arch = u + [(x + 27, y0 + dy * 34), (x + 20, y0 + dy * 58), (x - 20, y0 + dy * 58), (x - 27, y0 + dy * 34)]
        m = poly(arch); bays = np.maximum(bays, m)
        prof = np.clip(1 - (dy * (np.mgrid[0:H, 0:W][0] / S - y0) - 14) / 44, 0, 1) * m   # глубже у края, мельче к полю
        bayd = np.maximum(bayd, prof)
        if i % 6 != 5: holes = np.maximum(holes, circle(x + 35 * (1 if top else -1), y0 + dy * 16, 2.6))
    band = band * (1 - bays)
    stip = ndi.gaussian_filter(((vnoise(H, W, H / 1.3, W / 1.3, 7) > .6) * band).astype(float), .7)
    h += band * 1.8 - stip * 1.0
    alb = alb * (1 - stip[..., None] * .3)
    db = ndi.distance_transform_edt(bays > .5) / S
    h -= 10 * bayd * (1 - np.exp(-db / 5))
    alb = alb * (1 - (bayd * .25)[..., None])
    h -= holes * 3; alb = alb * (1 - holes[..., None] * .55)
    # пункты: инкрустация из светлого бука, выжженный контур
    drops, strips, curls, ovals = [], [], [], np.zeros((H, W))
    for i in range(24):
        dr, st, cu, ov = point_shapes(ptX(i), is_top(i), 218 if i % 6 in (0, 5) else 150)   # длинные только крайние
        drops.append(dr); strips += st; curls += cu
        ovals = np.maximum(ovals, oval_mask(ov[0], ov[1], 4.6, 7.2))
    dm = polys(drops)
    sm = np.maximum(lines(strips, 4.6, aa=.35), lines(curls, 3.4, aa=.35))
    inl = np.clip(np.maximum(np.maximum(dm, sm), ovals), 0, 1)
    alb = put(alb, sm, light)
    alb = put(alb, np.maximum(dm, ovals), light_h)
    burn = outline(inl, .9)
    alb = alb * (1 - burn[..., None] * .8)
    # аревахач в центре половины: лопасти — светлый бук, между ними тонкие тёмные линии; вокруг витой жгут
    for cx in (250, 750):
        sl, union, petals, angles = arevakhach_masks(cx, 350, 99, n=12, band=.02)
        a = alb[sl]
        for k, pm in enumerate(petals):
            tex = (light if k % 2 else light_h)[sl] * (.96 + .06 * (k % 2))
            a = a * (1 - pm[..., None]) + tex * pm[..., None]
        alb[sl] = a
        lit = np.max(petals, axis=0)
        h[sl] -= np.clip(union - lit, 0, 1) * .6
        rope, rb = rope_ring(cx, 350, 112, 131, n=64)
        alb = put(alb, rb * .85, light)
        groove = rb * (1 - np.clip(rope * 1.6, 0, 1))
        alb = alb * (1 - groove[..., None] * .75)
        h += rope * 1.2
        for r0, r1 in ((105.6, 107.8), (135.5, 137.8)):
            ring = np.clip(circle(cx, 350, r1) - circle(cx, 350, r0), 0, 1)
            alb = put(alb, ring, light); h -= ring * .2
    # латунные петли
    metal = np.zeros((H, W))
    for y in (110, 590):
        alb, h, metal = hinge(alb, h, metal, 500, y)
    if layers:
        return dict(h=h, body=body, metal=metal, alb=alb)
    rgb = shade(alb, h, gloss, metal, exp=70)
    rgb = rgb + sheen(H, W, .06, .4, .2, .35) * body[..., None]
    save('ararat', rgb, body)



def checker_real(name, texname, color, k):
    """Точёная шашка: фото шпона, тонированное морилкой, концентрические бороздки, лак."""
    N = 4 * 64; R = N * 30 / 64
    y, x = np.mgrid[0:N, 0:N] - (N - 1) / 2
    r = np.hypot(x, y) / R
    inside = np.clip((1 - r) * R / 1.2, 0, 1)
    im = np.asarray(Image.open(os.path.join(TEX, texname + '.jpg')).convert('RGB').resize((N * 2, N * 2)), float) / 255
    o = {'beech': 150, 'walnut': 230}.get(name, 0)   # разные места шпона — у шашек разный рисунок
    tex = im[o // 2:o // 2 + N, o:o + N]
    alb = stain(tex, color, k)
    dome = np.sqrt(np.clip(1 - r ** 2, 0, 1)) * R * .10
    bevel = np.clip((1 - r) / .1, 0, 1) ** .5 * R * .12
    h = np.minimum(dome + R * .07, bevel + R * .02)
    def groove(rad, depth, wdt): return -np.exp(-((r - rad) / wdt) ** 2) * depth * R
    h = h + groove(.82, .03, .018) + groove(.62, .025, .015) + groove(.38, .02, .013) + groove(.16, .015, .012)
    # в бороздках лак темнее
    g = np.exp(-((r - .82) / .02) ** 2) + np.exp(-((r - .62) / .017) ** 2) + np.exp(-((r - .38) / .015) ** 2)
    alb = alb * (1 - np.clip(g, 0, 1)[..., None] * .35)
    LIGHT = np.array([-.42, -.62, .66]); LIGHT /= np.linalg.norm(LIGHT)
    HALF = LIGHT + np.array([0, 0, 1.0]); HALF /= np.linalg.norm(HALF)
    gy, gx = np.gradient(h)
    n = np.dstack([-gx, -gy, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    diff = np.clip((n @ LIGHT) / LIGHT[2], 0, 1.6)
    spec = np.clip(n @ HALF, 0, 1) ** 50
    rgb = np.clip(alb * (.32 + .68 * diff[..., None]) + spec[..., None] * .5, 0, 1)
    out = Image.fromarray((rgb * 255).astype(np.uint8), 'RGB')
    out.putalpha(Image.fromarray((inside * 255).astype(np.uint8), 'L'))
    out.resize((128, 128), Image.LANCZOS).save(os.path.join(OUT, f'ck-{name}.png'), optimize=True)
    print('saved ck', name)


if __name__ == '__main__':
    if sys.argv[1:] == ['layers']:
        L = board_arevakhach(layers=True)
        np.savez_compressed(os.path.join(os.path.dirname(__file__), '..', '.preview', 'layers-ararat.npz'),
                            **{k: v.astype(np.float32) for k, v in L.items()})
        sys.exit(print('saved layers'))
    which = sys.argv[1:] or ['arevakhach', 'checkers']
    if 'arevakhach' in which: board_arevakhach()
    if 'checkers' in which:
        checker_real('beech', 'cherry_veneer', (.86, .68, .47), 1.2)
        checker_real('walnut', 'cherry_veneer', (.30, .165, .075), 1.6)
