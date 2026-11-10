# Доска «Гравюра» — по настоящим нардам из белого акрила с гравировкой (фото пользователя):
# белое поле, пункты — тонкие гравированные линии буквой V с растительным узором внутри и «пламенем» на вершине,
# у основания пунктов — прозрачные арки, в центре половин — ромб с птицами и цветком, по краям — узорные вставки.
# Сам узор вырезан из выпрямленного фото (tools/tex/uzor/*.png, чёрное = гравировка) и уложен по сетке игры.
# Результат: .preview/layers-gravura.npz для tools/blender_generic.py.
import os, sys, math
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(__file__))
from render_boards import S, W, H, rrect, circle, lines, ptX, is_top, fbm, poly

ROOT = os.path.join(os.path.dirname(__file__), '..')
UZ = os.path.join(os.path.dirname(__file__), 'tex', 'uzor')


def ink(name, trim=False):
    m = np.asarray(Image.open(os.path.join(UZ, name + '.png')).convert('L'), float) / 255   # 1 — гравировка
    if trim:                                                   # убрать соринки с фото и обрезать по самому рисунку
        lab, n = ndi.label(m > .25); sz = ndi.sum(np.ones_like(m), lab, range(1, n + 1))
        keep = np.isin(lab, 1 + np.nonzero(sz >= .04 * sz.max())[0]); m = m * ndi.binary_dilation(keep, iterations=2)
        ys, xs = np.nonzero(m > .25); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        # по ширине — так, чтобы «центр тяжести» узора лёг на ось пункта (завитки на фото несимметричны)
        cx = (m.sum(0) * np.arange(m.shape[1])).sum() / m.sum(); half = int(max(cx, m.shape[1] - cx)) + 1
        pad = np.zeros((m.shape[0], 2 * half)); o = int(round(half - cx)); pad[:, o:o + m.shape[1]] = m; m = pad
    return m


def stamp(dst, src, x0, y0, sc, flipv=False, fliph=False):
    """вклеить маску src (2 px на ед. фото) в масштабе sc с левым верхним углом (x0,y0) в единицах доски"""
    if flipv: src = src[::-1]
    if fliph: src = src[:, ::-1]
    z = ndi.zoom(src, sc * S / 2, order=1)
    X, Y = int(round(x0 * S)), int(round(y0 * S)); h, w = z.shape
    a = dst[Y:Y + h, X:X + w]; a[...] = np.maximum(a, np.clip(z[:a.shape[0], :a.shape[1]], 0, 1))


def build():
    yy, xx = np.mgrid[0:H, 0:W] / S
    body = rrect(0, 0, 1100, 700, 18, aa=.8)
    d = ndi.distance_transform_edt(body > .5) / S
    h = 26 * np.clip(d / 12, 0, 1) ** .55 - 3 * np.exp(-((d - 16) / 2) ** 2)
    # белый акрил: чуть тёплый, с едва заметной неровностью литья
    alb = np.ones((H, W, 3)) * np.array((.84, .83, .80))
    alb = alb * (.975 + .05 * fbm(H, W, 3, 4, 21, 3))[..., None]
    fields = np.maximum(rrect(30, 30, 470, 670, 8), rrect(530, 30, 970, 670, 8))
    h -= ndi.gaussian_filter(fields, 1.2 * S) * 4
    edge = np.clip(ndi.grey_dilation(fields, size=5) - fields, 0, 1)
    alb = alb * (1 - edge[..., None] * .18)
    gap = rrect(497, 20, 503, 680, 2); h -= gap * 14; alb = alb * (1 - gap[..., None] * .55)
    for y0 in (40, 360):                                       # лотки для выброшенных шашек
        tm = rrect(1022, y0, 1088, y0 + 300, 30)
        dd = ndi.distance_transform_edt(tm > .5) / S
        h -= tm * 16 * (1 - np.exp(-dd / 10)); alb = alb * (1 - tm[..., None] * .06)
    # арки у основания пунктов: прозрачный акрил — полукруглые гнёзда, между ними острые «зубцы» бортика
    bayR, bayY = 34, 70
    discs = np.zeros((H, W))
    for i in range(24):
        cy = bayY if is_top(i) else 700 - bayY
        discs = np.maximum(discs, circle(ptX(i), cy, bayR, aa=.6) * ((yy > cy) if is_top(i) else (yy < cy)) + circle(ptX(i), cy, bayR, aa=.6) * 0)
        discs = np.maximum(discs, circle(ptX(i), cy, bayR, aa=.6))
    band = np.zeros((H, W))
    for x0 in (30, 530):
        band = np.maximum(band, rrect(x0, 30, x0 + 440, bayY, 2, aa=.5) + rrect(x0, 700 - bayY, x0 + 440, 670, 2, aa=.5))
    band = np.clip(band, 0, 1) * (1 - discs)                  # зубцы между арками
    h += ndi.gaussian_filter(band, .8 * S) * 3.2
    rim = np.clip(ndi.grey_dilation(band, size=int(3 * S)) - band, 0, 1) * fields
    glass = np.array((.80, .84, .86))                         # кромка прозрачного акрила — холодная, светлая
    alb = alb * (1 - rim[..., None] * .55) + glass * rim[..., None] * .55
    alb = alb * (1 - band[..., None] * .05)
    # гравировка
    INK = np.zeros((H, W))
    TIP = 205                                                  # пункты короче: между ними и ромбом — простор, как на настоящей доске
    segs = []
    for i in range(24):
        x, t = ptX(i), is_top(i)
        Y = (lambda v: v) if t else (lambda v: 700 - v)
        segs += [[(x - 34, Y(bayY - 8)), (x - .6, Y(TIP))], [(x + 34, Y(bayY - 8)), (x + .6, Y(TIP))]]
    INK = np.maximum(INK, lines(segs, 1.25, aa=.45))
    vines = [ink(f'vine{k}', True) for k in range(6)]
    fins = [ink(f'fin{k}', True) for k in range(6)]
    sc = .43
    for i in range(24):
        x, t = ptX(i), is_top(i); k = (i * 5) % 6
        v = vines[k]; vh, vw = v.shape[0] / 2 * sc, v.shape[1] / 2 * sc
        stamp(INK, v, x - vw / 2, (bayY + 8) if t else (700 - bayY - 8 - vh), sc, flipv=not t, fliph=(i % 2 == 1))
        f = fins[(k + 2) % 6]; fh, fw = f.shape[0] / 2 * sc, f.shape[1] / 2 * sc
        stamp(INK, f, x - fw / 2, (TIP - 1) if t else (700 - TIP + 1 - fh), sc, flipv=not t)
    # ромб в центре половины
    dm = ink('diamond'); R = 80
    for cx in (250, 750):
        dsc = 2 * R / (dm.shape[1] / 2)
        stamp(INK, dm, cx - R, 350 - dm.shape[0] / 2 * dsc / 2, dsc)
        INK = np.maximum(INK, lines([[(cx, 350 - R), (cx + R, 350), (cx, 350 + R), (cx - R, 350), (cx, 350 - R)]], 1.15, aa=.45))
    # узорные вставки у длинных краёв поля, как на фото
    side = ink('side'); s2 = ink('side2'); ssc = .52
    for x, m, fl in ((50, side, True), (950, side, False), (450, s2, False), (550, s2, True)):
        hh, ww = m.shape[0] / 2 * ssc, m.shape[1] / 2 * ssc
        stamp(INK, m, x - ww / 2, 350 - hh / 2, ssc, fliph=fl)
    INK = np.clip(INK * fields * (1 - band), 0, 1)
    alb = alb * (1 - INK[..., None] * .93)
    h -= INK * .5
    # петли: маленькие хромированные, как на фото
    metal = np.zeros((H, W))
    for y in (130, 570):
        pl = np.maximum(rrect(486, y - 22, 497, y + 22, 2), rrect(503, y - 22, 514, y + 22, 2))
        kn = rrect(496, y - 24, 504, y + 24, 3)
        m = np.clip(pl + kn, 0, 1)
        alb = alb * (1 - m[..., None]) + np.array((.78, .79, .80)) * m[..., None]
        h = h * (1 - m) + m * (h + 1.5 + kn * 2.5); metal = np.maximum(metal, m)
        for sy in (-12, 12):
            for sx in (491.5, 508.5):
                sc_ = circle(sx, y + sy, 2.2); alb = alb * (1 - sc_[..., None] * .4)
    gloss = np.ones((H, W)) * .4                               # полуматовый: глянцевый белый целиком отражает лампу
    return dict(h=h, alb=np.clip(alb, 0, 1), gloss=gloss, metal=metal, alpha=body)


if __name__ == '__main__':
    out = build()
    np.savez_compressed(os.path.join(ROOT, '.preview', 'layers-gravura.npz'), **{k: np.asarray(v, np.float32) for k, v in out.items()})
    Image.fromarray((np.clip(out['alb'], 0, 1) * 255).astype(np.uint8)).resize((1100, 700)).save(os.path.join(ROOT, '.preview', 'gravura-alb.png'))
    print('saved layers gravura')
