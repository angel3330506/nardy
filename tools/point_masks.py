# Подсветка пунктов: для каждой доски — светящийся силуэт её собственного рисунка пункта (верхний пункт; нижний — зеркально).
# Результат: boards/pt-<доска>-<long|short>.png — окно 80×330 единиц доски (x: ptX−40…ptX+40, y: 40…370), 2 px на единицу.
import os, sys, math
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(__file__))
import render_boards as rb
from render_boards import S, ptX, polys, lines, teardrop
import render_real as rr

OUT = os.path.join(os.path.dirname(__file__), '..', 'boards')
I_LONG, I_SHORT = 12, 13                                     # верхние пункты: длинный (край шестёрки) и средний


def shape_inlay(i, tip):
    """«Аревахач», «Гранат», «Севан»: капля + планки буквой V + завитки + капелька (render_real.point_shapes)."""
    dr, st, cu, ov = rr.point_shapes(ptX(i), True, tip)
    m = np.maximum(polys([dr]), np.maximum(lines(st, 4.6, aa=.35), lines(cu, 3.4, aa=.35)))
    return np.maximum(m, rr.oval_mask(ov[0], ov[1], 4.6, 7.2))


SHAPES = {
    'ararat': lambda i, long: shape_inlay(i, 218 if long else 150),
    'pomegranate': lambda i, long: shape_inlay(i, 218 if long else 150),
    'sevan': lambda i, long: shape_inlay(i, 218 if long else 150),
    'yerevan': lambda i, long: polys([teardrop(ptX(i), True, 262 if long else 196, 42)]),
    'night': lambda i, long: polys([[(ptX(i) - 33, 40), (ptX(i) + 33, 40), (ptX(i), 296)]]),
    'glass': lambda i, long: polys([[(ptX(i) - 27, 58), (ptX(i) + 27, 58), (ptX(i), 290)]]),
}


def glow(mask):
    """золотистая заливка формы, светлый контур и мягкий ореол вокруг"""
    m = np.clip(mask, 0, 1)
    edge = np.clip(ndi.grey_dilation(m, size=5) - ndi.grey_erosion(m, size=3), 0, 1)
    halo = ndi.gaussian_filter(ndi.grey_dilation(m, size=11), 9)
    a = np.clip(m * .7 + edge * 1.0 + halo * .75, 0, 1)
    col = np.zeros(m.shape + (3,))
    col[...] = (1.0, .74, .28)                               # тёплое золото — видно и на светлой инкрустации, и на тёмном дереве
    col = col * (1 - edge[..., None]) + np.array((1.0, .92, .62)) * edge[..., None]
    return np.dstack([col, a])


if __name__ == '__main__':
    for skin, fn in SHAPES.items():
        for kind, i in (('long', I_LONG), ('short', I_SHORT)):
            m = fn(i, kind == 'long')
            x0, y0 = int((ptX(i) - 40) * S), int(40 * S)
            win = m[y0:y0 + 330 * S, x0:x0 + 80 * S]
            rgba = glow(win)
            Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, f'pt-{skin}-{kind}.png'), optimize=True)
        print('saved', skin)
