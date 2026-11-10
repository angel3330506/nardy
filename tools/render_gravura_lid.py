# Крышка нард «Гравюра» для главного меню — по фото настоящей крышки: белый акрил, в центре всадник на коне
# (гравировка, клинок и пламя — красным), в углах и посередине длинных краёв — узорные уголки.
# Части вырезаны из выпрямленного фото (tools/tex/uzor/lid-*.png: цвет штриха + прозрачность), масштаб как на фото.
# Результат: .preview/layers-gravura-lid.npz для tools/blender_generic.py (крышка 825×1050, как boards/lid.webp).
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(__file__))
from render_boards import fbm

ROOT = os.path.join(os.path.dirname(__file__), '..'); UZ = os.path.join(os.path.dirname(__file__), 'tex', 'uzor')
K = 2; LW, LH = 825, 1050; W, H = LW * K, LH * K
PH = .825                                                  # фото крышки 1000 px шириной = 825 px крышки в игре


def part(name):
    a = np.asarray(Image.open(os.path.join(UZ, name + '.png')).convert('RGBA'), float) / 255
    return a[..., :3], a[..., 3]


def put(alb, ink, name, cx, cy, fh=False, fv=False):
    c, m = part(name)
    if fh: c, m = c[:, ::-1], m[:, ::-1]
    if fv: c, m = c[::-1], m[::-1]
    z = PH * K
    c = ndi.zoom(c, (z, z, 1), order=1); m = np.clip(ndi.zoom(m, z, order=1), 0, 1)
    h, w = m.shape; x0, y0 = int(cx * K - w / 2), int(cy * K - h / 2)
    alb[y0:y0 + h, x0:x0 + w] = alb[y0:y0 + h, x0:x0 + w] * (1 - m[..., None]) + alb[y0:y0 + h, x0:x0 + w] * c * m[..., None]
    ink[y0:y0 + h, x0:x0 + w] = np.maximum(ink[y0:y0 + h, x0:x0 + w], m)


def build():
    yy, xx = np.mgrid[0:H, 0:W] / K
    r = 26; dx = np.maximum(0, np.maximum(r - xx, xx - (LW - r))); dy = np.maximum(0, np.maximum(r - yy, yy - (LH - r)))
    body = np.clip((r - np.hypot(dx, dy)) * K / 1.5, 0, 1)
    d = ndi.distance_transform_edt(body > .5) / K
    h = 22 * np.clip(d / 14, 0, 1) ** .6                      # скруглённая кромка крышки
    alb = np.ones((H, W, 3)) * np.array((.84, .83, .80)) * (.975 + .05 * fbm(H, W, 3, 4, 31, 3))[..., None]
    ink = np.zeros((H, W))
    put(alb, ink, 'lid-rider', LW / 2, LH * .45)
    cw, chh = 160 * PH / 2, 180 * PH / 2
    for fh in (False, True):
        for fv in (False, True):
            put(alb, ink, 'lid-corner', (LW - 40 * PH - cw) if fh else (40 * PH + cw), (LH - 50 * PH - chh) if fv else (50 * PH + chh), fh, fv)
        put(alb, ink, 'lid-side', (LW - 45 * PH - 40 * PH) if fh else (45 * PH + 40 * PH), LH * .51, fh)
    h = h - ink * .4
    return dict(h=h, alb=np.clip(alb, 0, 1), gloss=np.full((H, W), .4), metal=np.zeros((H, W)), alpha=body)


if __name__ == '__main__':
    out = build()
    np.savez_compressed(os.path.join(ROOT, '.preview', 'layers-gravura-lid.npz'), **{k: np.asarray(v, np.float32) for k, v in out.items()})
    Image.fromarray((out['alb'] * 255).astype(np.uint8)).resize((LW // 2, LH // 2)).save(os.path.join(ROOT, '.preview', 'gravura-lid-alb.png'))
    print('saved layers gravura-lid')
