# Слои для 3D-рендера шашек и граней кубика (tools/blender_pieces.py): высоты и цвет на сетке N×N.
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(__file__))
from render_boards import star_halves, vnoise
TEX = os.path.join(os.path.dirname(__file__), 'tex')
N = 512


def checker(kind):
    y, x = np.mgrid[0:N, 0:N] - (N - 1) / 2
    R = N * .47; r = np.hypot(x, y) / R
    alpha = np.clip((1 - r) * R / 1.5, 0, 1)
    # точёный профиль: борт со скруглённой кромкой, верх чуть выпуклый
    h = np.minimum(np.sqrt(np.clip(1 - r ** 2, 0, 1)) * .05 + .16, np.clip((1 - r) / .09, 0, 1) ** .5 * .2)
    g = lambda rad, d, w: -np.exp(-((r - rad) / w) ** 2) * d
    if kind in ('beech', 'walnut'):
        im = np.asarray(Image.open(os.path.join(TEX, 'white_maple_veneer.jpg' if kind == 'beech' else 'walnut_veneer.jpg')).convert('RGB').resize((N, N)), float) / 255
        col = np.array((.80, .60, .40)) if kind == 'beech' else np.array((.30, .18, .09))
        lum = im.mean(-1); alb = col * (lum / lum.mean())[..., None] ** 1.6
        h = h + g(.80, .018, .012) + g(.60, .015, .01) + g(.38, .012, .009) + g(.16, .01, .008)
        alb = alb * (1 - (np.exp(-((r - .8) / .013) ** 2) + np.exp(-((r - .6) / .011) ** 2) + np.exp(-((r - .38) / .01) ** 2))[..., None] * .35)
        gloss = 1.0
    else:
        base = (.93, .89, .80) if kind == 'ivory' else (.035, .035, .04)
        alb = np.ones((N, N, 3)) * np.array(base) * (1 + (vnoise(N, N, 6, 6, 93) - .5)[..., None] * .05)
        sp = star_halves(0, 0, R * .55, R * .2, 8)
        def pm(pts):
            im = Image.new('L', (N, N), 0)
            ImageDraw.Draw(im).polygon([(px + (N - 1) / 2, py + (N - 1) / 2) for px, py in pts], fill=255)
            return ndi.gaussian_filter(np.asarray(im, float) / 255, 1)
        lt = sum(pm(a) for a, b in sp); dk = sum(pm(b) for a, b in sp)
        c1, c2 = ((.98, .95, .88), (.10, .08, .07)) if kind == 'ivory' else ((.88, .86, .82), (.01, .01, .012))
        alb = alb * (1 - lt[..., None]) + np.array(c1) * lt[..., None]
        alb = alb * (1 - dk[..., None]) + np.array(c2) * dk[..., None]
        ring = np.exp(-((r - .77) / .015) ** 2)
        alb = alb * (1 - ring[..., None]) + np.array((.69, .54, .24) if kind == 'ivory' else (.6, .6, .64)) * ring[..., None]
        h = h + g(.77, .012, .012) - (lt + dk) * .004
        gloss = 1.0
    return dict(h=h, alb=alb, alpha=alpha, gloss=np.full((N, N), gloss), metal=np.zeros((N, N)))


PIPS = {1: [4], 2: [0, 8], 3: [0, 4, 8], 4: [0, 2, 6, 8], 5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8]}


def die_face(v, mat='bone'):
    """Грань кубика сверху: скруглённые рёбра (суперэллипс), лунки-точки, закрашенные чёрным (единица — красным).
    mat: bone — кость, wood — светлый клён с выжженными точками, amber — тёмный янтарь с золотыми точками."""
    y, x = (np.mgrid[0:N, 0:N] + .5) / N * 2 - 1
    q = (np.abs(x) ** 6 + np.abs(y) ** 6) ** (1 / 6)
    alpha = np.clip((1 - q) * N / 3, 0, 1)
    h = np.sqrt(np.clip(1 - np.clip((q - .78) / .22, 0, 1) ** 2, 0, 1)) * .25
    if mat == 'wood':
        im = np.asarray(Image.open(os.path.join(TEX, 'white_maple_veneer.jpg')).convert('RGB').resize((N, N)), float) / 255
        lum = im.mean(-1); alb = np.array((.82, .64, .42)) * (lum / lum.mean())[..., None] ** 1.4
    elif mat == 'amber':
        rng = np.random.default_rng(v)
        cloud = ndi.gaussian_filter(rng.random((N, N)), 30); cloud = (cloud - cloud.min()) / (np.ptp(cloud) + 1e-6)
        alb = np.array((.55, .22, .03)) * (.7 + .6 * cloud)[..., None]
    else:
        alb = np.ones((N, N, 3)) * np.array((.90, .86, .76))
    pipcol = {'bone': ((.55, .05, .05), (.03, .025, .02)), 'wood': ((.30, .08, .03), (.12, .06, .03)), 'amber': ((.95, .78, .40), (.95, .78, .40))}[mat]
    pr = .2 if v == 1 else .15
    metal = np.zeros((N, N))
    for k in PIPS[v]:
        cx, cy = (k % 3 - 1) * .5, (k // 3 - 1) * .5
        d = np.hypot(x - cx, y - cy) / pr
        cup = np.clip(1 - d, 0, 1)
        h -= np.sqrt(np.clip(1 - d ** 2, 0, 1)) * .09            # высверленная лунка
        paint = np.clip((.92 - d) * 25, 0, 1)
        alb = alb * (1 - paint[..., None]) + np.array(pipcol[0] if v == 1 else pipcol[1]) * paint[..., None]
        if mat == 'amber': metal = np.maximum(metal, paint)   # золотые точки
    return dict(h=h, alb=alb, alpha=alpha, gloss=np.full((N, N), .6), metal=metal, mat=np.array(['bone', 'wood', 'amber'].index(mat)))


if __name__ == '__main__':
    out = os.path.join(os.path.dirname(__file__), '..', '.preview')
    for k in ('ivory', 'onyx', 'beech', 'walnut'):
        np.savez_compressed(os.path.join(out, f'piece-ck-{k}.npz'), **checker(k))
    for mat in ('bone', 'wood', 'amber'):
        for v in range(1, 7):
            np.savez_compressed(os.path.join(out, f'piece-die-{mat}-{v}.npz'), **die_face(v, mat))
    print('saved pieces')
