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


def bay(i, r, d):
    """Полукруглая «арка» у основания пункта (render_boards.field_with_bays): эллипс r×d с центром на линии поля."""
    cx, cy = ptX(i), 40 + d
    return polys([[(cx + r * math.cos(a), cy + d * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 64, endpoint=False)]])
def with_bay(i, m, r, d, base):
    """Арка + полоса от неё до основания рисунка: подсвечивается всё «гнездо» пункта, а не только сам рисунок."""
    band = polys([[(ptX(i) - r * .96, 40 + d), (ptX(i) + r * .96, 40 + d), (ptX(i) + r * .8, base), (ptX(i) - r * .8, base)]])
    return np.maximum(m, np.maximum(bay(i, r, d), band))


SHAPES = {
    'ararat': lambda i, long: with_bay(i, shape_inlay(i, 218 if long else 150), 28, 16, 62),
    'pomegranate': lambda i, long: with_bay(i, shape_inlay(i, 218 if long else 150), 28, 16, 62),
    'sevan': lambda i, long: with_bay(i, shape_inlay(i, 218 if long else 150), 28, 16, 62),
    'yerevan': lambda i, long: with_bay(i, polys([teardrop(ptX(i), True, 262 if long else 196, 42)]), 30, 14, 58),
    'night': lambda i, long: polys([[(ptX(i) - 33, 40), (ptX(i) + 33, 40), (ptX(i), 296)]]),
    'gravura': lambda i, long: np.maximum(bay(i, 34, 30), polys([[(ptX(i) - 34, 62), (ptX(i) + 34, 62), (ptX(i), 240)]])),
    'glass': lambda i, long: with_bay(i, polys([[(ptX(i) - 27, 58), (ptX(i) + 27, 58), (ptX(i), 290)]]), 27, 15, 58),
}


GLOW_COL = {'gravura': (.86, .60, .18)}                 # на белой доске белое свечение не видно — золотистое


def glow(mask, col_=(1.0, .97, .9)):
    """мягкое свечение формы: без обводки и резких краёв — заливка с размытой кромкой и плавный ореол вокруг"""
    m = np.clip(mask, 0, 1)
    fill = ndi.gaussian_filter(m, 2.2)                      # кромка размыта — граница не читается
    halo = ndi.gaussian_filter(ndi.grey_dilation(m, size=9), 8)
    a = np.clip(fill * .6 + halo * .34, 0, .8)            # полупрозрачно: рисунок доски просвечивает
    col = np.zeros(m.shape + (3,)); col[...] = col_
    return np.dstack([col, a])


if __name__ == '__main__':
    for skin, fn in SHAPES.items():
        if sys.argv[1:] and skin not in sys.argv[1:]: continue
        for kind, i in (('long', I_LONG), ('short', I_SHORT)):
            m = fn(i, kind == 'long')
            x0, y0 = int((ptX(i) - 40) * S), int(40 * S)
            win = m[y0:y0 + 330 * S, x0:x0 + 80 * S]
            rgba = glow(win, GLOW_COL.get(skin, (1.0, .97, .9)))
            Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, f'pt-{skin}-{kind}.png'), optimize=True)
        print('saved', skin)
