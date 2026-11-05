# Карта теней виноградного навеса: стол с навесом / стол без навеса (рендеры tools/blender_table.py, обычный и NOVINE=1).
# В щелях между досками стола оба рендера почти чёрные, отношение там бессмысленно — такие места заполняем по соседям,
# иначе щели ложились бы тёмными полосами на доску и предметы.
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
a = np.asarray(Image.open('.preview/blender-table.png').convert('RGB')).astype(np.float32).mean(2)
b = np.asarray(Image.open('.preview/blender-table-novine.png').convert('RGB')).astype(np.float32).mean(2)
valid = (b > 55).astype(np.float32)
valid = ndi.binary_erosion(valid, iterations=2).astype(np.float32)          # и края щелей тоже не берём
r = np.clip(a / (b + 1), 0, 1.2)
s = 3.0
num = ndi.gaussian_filter(r * valid, s); den = ndi.gaussian_filter(valid, s)
fill = num / np.maximum(den, 1e-4)
# где рядом совсем нет годных пикселей — берём шире
num2 = ndi.gaussian_filter(r * valid, 12); den2 = ndi.gaussian_filter(valid, 12)
fill = np.where(den > .05, fill, num2 / np.maximum(den2, 1e-4))
out = np.clip(fill, .2, 1)
# щели между досками — горизонтальные полосы: находим их по тёмным строкам рендера и заменяем
# плавной интерполяцией между строками выше и ниже (кромки досок тоже захватываем)
rm = b.mean(1); low = np.nonzero(rm < np.median(rm) * .75)[0]
bands = []
for y in low:
    if bands and y - bands[-1][1] <= 2: bands[-1][1] = y
    else: bands.append([y, y])
for y0, y1 in bands:
    y0 = max(0, y0 - 14); y1 = min(len(rm) - 1, y1 + 14)
    top, bot = out[y0 - 1].copy(), out[y1 + 1].copy()
    for y in range(y0, y1 + 1):
        t = (y - y0 + 1) / (y1 - y0 + 2); out[y] = top * (1 - t) + bot * t
out = ndi.gaussian_filter(out, 1.5)
# тень = чёрный с прозрачностью (1 − освещённость): обычное наложение, без mix-blend-mode
sh = Image.fromarray((out * 255).astype(np.uint8)).resize((1200, 750), Image.LANCZOS); A = 255 - np.asarray(sh)
Image.fromarray(np.dstack([np.zeros_like(A)] * 3 + [A]), 'RGBA').save('boards/leafshade.webp', 'WEBP', quality=85, method=6, alpha_quality=90)
Image.fromarray((out * 255).astype(np.uint8)).resize((960, 600)).save('.preview/leaf-s.png')
print('leafshade ok')
