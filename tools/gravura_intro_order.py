# Порядок «резца» для заставки «Гравюры»: boards/gravura-lid-order.png (825×1050, серый): 0 — не гравировка,
# 1…255 — когда пиксель проступает. Уголки и боковые узоры раскручиваются от центра (первые 28%),
# конь и всадник прорисовываются вдоль линий от головы коня (до 88%), красный меч — последним, от рукояти к острию.
import os, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
sys.path.insert(0, os.path.dirname(__file__))
import render_gravura_lid as L

L.build()
K, LW, LH = L.K, L.LW, L.LH
def down(m): return m.reshape(LH, K, LW, K).mean((1, 3))
T = np.zeros((LH, LW))
yy, xx = np.mgrid[0:LH, 0:LW].astype(float)
rider = sword = None
for name, m, c in L.PARTS:
    md, cd = down(m), c.reshape(LH, K, LW, K, 3).mean((1, 3))
    if name in ('lid-david', 'lid-rider'):
        red = (cd[..., 0] - cd[..., 1] > .12) & (md > .2)
        red = ndi.binary_opening(red, iterations=1); red = ndi.binary_dilation(red, iterations=2) & (md > .05)
        rider = (md > .05) & ~red; sword = red
    else:
        mm = md > .05; ys, xs = np.nonzero(mm); cy, cx = ys.mean(), xs.mean()
        d = np.hypot(yy - cy, xx - cx) * mm; d = d / d.max()
        T = np.where(mm, .02 + .26 * d, T)

def geodesic(mask, seed, gap=7.0, step=2):
    # расстояние вдоль линий: по гравировке шаг стоит 1, через пустое место — gap (фронт перескакивает щели медленно)
    m = mask[::step, ::step]; h, w = m.shape; idx = np.arange(h * w).reshape(h, w)
    cost = np.where(m, 1.0, gap).ravel()
    rows, cols, vals = [], [], []
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        a = idx[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
        b = idx[max(0, dy):h - max(0, -dy) if dy <= 0 else h, max(0, dx):w - max(0, -dx) if dx < 0 else w][:a.shape[0], :a.shape[1]]
        L_ = np.hypot(dy, dx); v = (cost[a.ravel()] + cost[b.ravel()]) / 2 * L_
        rows += [a.ravel(), b.ravel()]; cols += [b.ravel(), a.ravel()]; vals += [v, v]
    G = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(h * w, h * w)).tocsr()
    sy, sx = seed[0] // step, seed[1] // step
    d = dijkstra(G, indices=idx[sy, sx]).reshape(h, w)
    return ndi.zoom(d, step, order=1)[:mask.shape[0], :mask.shape[1]]

ys, xs = np.nonzero(rider)
seed = (ys[np.argmax(xs)], xs.max())                       # самая правая точка — морда коня
gd = geodesic(rider, seed); r = gd[rider]; lo, hi = np.percentile(r, 0), np.percentile(r, 99.5)
T = np.where(rider, .30 + .58 * np.clip((gd - lo) / (hi - lo), 0, 1), T)
ys, xs = np.nonzero(sword); hilt = (ys[np.argmin(xs)], xs.min())   # клинок поднят вправо-вверх: рукоять слева
ds = np.hypot(yy - hilt[0], xx - hilt[1]); dv = ds[sword]
T = np.where(sword, .90 + .10 * (ds - dv.min()) / (dv.max() - dv.min()), T)
ink = T > 0
out = np.where(ink, 1 + np.round(np.clip(T, 0, 1) * 254), 0).astype(np.uint8)
ROOT = os.path.join(os.path.dirname(__file__), '..')
Image.fromarray(out).save(os.path.join(ROOT, 'boards', 'gravura-lid-order.png'), optimize=True)
sb = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
print('saved order; ink px', int(ink.sum()), 'sword bbox', sb)
