# Поверхность чёрного армянского кофе на картинке-предмете boards/prop-cup.webp: внутри — почти чёрная гладь
# с мягким бликом лампы, у стенки остаётся ободок из рендера (там слой кофе тонкий и просвечивает).
import sys
import numpy as np
from PIL import Image
p = sys.argv[1] if len(sys.argv) > 1 else 'boards/prop-cup.webp'
im = Image.open(p).convert('RGBA'); a = np.asarray(im).astype(np.float32)
CX, CY, R = 513, 1160, 251                      # центр и радиус кофе в картинке (см. blender_table.py: cup centre)
yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
r = np.hypot(xx - CX, yy - CY) / R
base = np.array([7, 4, 3], np.float32)
# лёгкий градиент глубины: к центру чуть темнее, к стенке чуть теплее
surf = base[None, None, :] * (1 + .5 * np.clip(r, 0, 1)[..., None] ** 2)
# мягкий блик лампы сверху-слева: размытое овальное пятно и узкий яркий центр
hx, hy = CX - .38 * R, CY - .34 * R
d = np.hypot((xx - hx) / (.42 * R), (yy - hy) / (.30 * R))
glow = np.exp(-d ** 2 * 2.2) * 58 + np.exp(-d ** 2 * 9) * 70
surf = surf + glow[..., None] * np.array([1, .96, .9], np.float32)
w = np.clip((.93 - r) / .06, 0, 1)[..., None]   # к стенке плавно возвращаемся к рендеру (ободок, мениск)
a[..., :3] = a[..., :3] * (1 - w) + surf * w
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA').save(p, 'WEBP', quality=88, method=6, alpha_quality=90)
print('coffee surface ok')
