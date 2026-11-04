# Рабочий стол iOS 27 для ролика из настоящих материалов: официальные тёмные обои iOS 27 (1320×2868)
# и иконки, вырезанные со скриншотов iPhone (1184×2576). Подписи — по-русски.
# Выход: home.png (без значка «Нарды»), newic.png (значок «Нарды» с подписью), icons/*.png, pos.json
import json, os, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = sys.argv[1]                     # папка: iOS27_Default_Dark.png, h1.jpg, h2.jpg, icon-512.png
OUT = sys.argv[2]; os.makedirs(os.path.join(OUT, 'icons'), exist_ok=True)
W, H = 1320, 2868; K = W / 1184     # скриншоты 1184 px в ширину
FONT = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
FONT_SB = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
DIM = np.array([.956, .894, .893])  # рабочий стол iOS чуть затемняет обои (измерено по скриншоту)

h1 = np.asarray(Image.open(os.path.join(D, 'h1.jpg')).convert('RGB'))
h2 = np.asarray(Image.open(os.path.join(D, 'h2.jpg')).convert('RGB'))
# рабочий стол iOS затемняет обои неравномерно (сильнее внизу, у дока) — снимаем карту затемнения со скриншота
# по местам, где нет значков, и сглаживаем; потом переносим на обои в полном разрешении
w0 = np.asarray(Image.open(os.path.join(D, 'iOS27_Default_Dark.png')).convert('RGB')).astype(float)
ws = cv2.resize(w0, (1184, 2576), interpolation=cv2.INTER_AREA)
free = np.ones((2576, 1184), np.float32)
free[:150] = 0                                                        # статус-бар
for r in range(6):
    for c in range(4): free[int(265 + 295.4 * r) - 12:int(265 + 295.4 * r) + 250, [89, 361, 634, 906][c] - 30:[89, 361, 634, 906][c] + 220] = 0
free[2060:] = 0                                                       # капсула «Поиск» и док
free[263:751] = 0                                                     # виджеты на 1-м скриншоте
gain = []
for ch in range(3):
    num = cv2.GaussianBlur(h1[..., ch].astype(np.float32) * free, (0, 0), 70)
    den = cv2.GaussianBlur(ws[..., ch].astype(np.float32) * free, (0, 0), 70) + 1e-3
    gain.append(np.clip(num / den, .5, 1.2))
gain = np.dstack(gain)
# внизу (под доком) карту продолжаем последней строкой, где она ещё надёжна
gain[2060:] = gain[2059]
wall = w0 * cv2.resize(gain, (W, H), interpolation=cv2.INTER_LINEAR)

# сетка значков на скриншоте (1184 px): x начала столбцов, y начала строк, размер
GX = [89, 361, 634, 906]; GY = [265 + 295.4 * r for r in range(6)]; S = 190
DX = [108, 367, 627, 887]; DY = 2277

def squircle(n, s, p=5.0):
    """Маска значка iOS (суперэллипс), со сглаживанием."""
    ss = 4; t = (np.arange(n * ss) + .5) / (n * ss) * 2 - 1
    X, Y = np.meshgrid(t, t); m = (np.abs(X) ** p + np.abs(Y) ** p) <= 1
    return m.reshape(n, ss, n, ss).mean((1, 3))

def grab(img, x, y, name, fix=None):
    x, y = int(round(x)), int(round(y))
    c = img[y:y + S, x:x + S].copy()
    if fix: c = fix(c)
    big = Image.fromarray(c).resize((round(S * K), round(S * K)), Image.LANCZOS)
    a = (squircle(big.width, big.width) * 255).astype(np.uint8)
    im = big.convert('RGBA'); im.putalpha(Image.fromarray(a))
    im.save(os.path.join(OUT, 'icons', name + '.png')); return im

def cal_fix(c):
    """«Thu» → «Чт» на значке Календаря."""
    im = Image.fromarray(c); d = ImageDraw.Draw(im)
    top = c[10:70, 20:170].reshape(-1, 3); bg = tuple(int(v) for v in np.median(c[8:14, 30:160].reshape(-1, 3), 0))
    red = tuple(int(v) for v in top[np.argmax(top[:, 0].astype(int) - top[:, 1].astype(int))])
    d.rectangle((25, 14, 165, 66), fill=bg)
    f = ImageFont.truetype(FONT_SB, 40); w = d.textlength('Чт', font=f); d.text(((S - w) / 2, 17), 'Чт', font=f, fill=red)
    return np.asarray(im)

ICONS = [  # (скриншот, строка, столбец, имя, подпись)
    (h2, 0, 0, 'weather', 'Погода'), (h1, 2, 0, 'calendar', 'Календарь'), (h1, 2, 1, 'mail', 'Почта'), (h1, 2, 2, 'maps', 'Карты'),
    (h1, 4, 3, 'photos', 'Фото'), (h1, 4, 2, 'camera', 'Камера'), (h1, 3, 3, 'clock', 'Часы'), (h1, 3, 0, 'notes', 'Заметки'),
    (h1, 3, 1, 'reminders', 'Напоминания'), (h1, 3, 2, 'settings', 'Настройки'), (h1, 4, 1, 'appstore', 'App Store'), (h1, 4, 0, 'wallet', 'Wallet'),
    (h1, 5, 0, 'health', 'Здоровье'), (h2, 0, 1, 'files', 'Файлы'), (h2, 0, 2, 'findmy', 'Локатор'), (h2, 0, 3, 'shortcuts', 'Команды'),
    (h2, 1, 0, 'calculator', 'Калькулятор'), (h2, 1, 1, 'contacts', 'Контакты'), (h2, 1, 3, 'passwords', 'Пароли'), (h1, 2, 3, 'stocks', 'Акции'),
    (h2, 2, 1, 'voicememos', 'Диктофон'), (h2, 2, 2, 'compass', 'Компас'), (h2, 2, 0, 'magnifier', 'Лупа'),
]
home = Image.fromarray(np.clip(wall, 0, 255).astype(np.uint8)).convert('RGBA')
# размер подписи — как на скриншоте: «Calendar» шириной ~150 px при 1184
f_lab = ImageFont.truetype(FONT, 10)
probe = ImageDraw.Draw(home)
for sz in np.arange(28, 46, .5):
    f_lab = ImageFont.truetype(FONT, sz)
    if probe.textlength('Calendar', font=f_lab) >= 150 * K: break
LAB_DY = 224 * K   # центр подписи ниже верха значка

def label(img, cx, cy, text):
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w = d.textlength(text, font=f_lab); bb = f_lab.getbbox('Аа')
    y = cy - (bb[1] + bb[3]) / 2
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    ds.text((cx - w / 2, y + 2), text, font=f_lab, fill=(0, 0, 0, 120)); sh = sh.filter(ImageFilter.GaussianBlur(3))
    d.text((cx - w / 2, y), text, font=f_lab, fill=(255, 255, 255, 255))
    img.alpha_composite(sh); img.alpha_composite(lay)

pos = {'icon': S * K / 3}
for i, (src, r, c, name, lab) in enumerate(ICONS):
    ic = grab(src, GX[c], GY[r], name, cal_fix if name == 'calendar' else None)
    rr, cc = divmod(i, 4); x, y = GX[cc] * K, GY[rr] * K
    home.alpha_composite(ic, (round(x), round(y))); label(home, x + S * K / 2, y + LAB_DY, lab)

# док: настоящий кусок со скриншота, бейджи «1» и «14» убираем (inpaint)
dy0, dy1 = 2190, 2520
dock = h1[dy0:dy1].copy()
hsv = cv2.cvtColor(dock, cv2.COLOR_RGB2HSV)
red = ((hsv[..., 0] < 8) | (hsv[..., 0] > 172)) & (hsv[..., 1] > 110) & (hsv[..., 2] > 120)
num, lab_, st, _ = cv2.connectedComponentsWithStats(red.astype(np.uint8))
mask = np.zeros(red.shape, np.uint8)
for k in range(1, num):
    x, y, w, h, a = st[k]
    if a > 400 and y < DY - dy0 + 10:                      # только бейджи у верхнего края значков (не стрелка Safari)
        cv2.ellipse(mask, (x + w // 2, y + h // 2), (w // 2 + 7, h // 2 + 7), 0, 0, 360, 255, -1)
# Бейдж закрывает угол значка и стекло дока. Восстанавливаем так:
#  - стекло — по соседнему стеклу (значки на время закрыты, чтобы зелёный не растёкся);
#  - значок — зеркально относительно его точного центра (левый верхний угол такой же, глиф туда не заходит);
#  - всё это вклеиваем с мягким переходом, чтобы не было шва.
sq = (squircle(S, S) > .02).astype(np.uint8)
icons_m = np.zeros(mask.shape, np.uint8)
for x0 in DX: icons_m[DY - dy0:DY - dy0 + S, x0:x0 + S] = sq * 255
icons_m = cv2.dilate(icons_m, np.ones((7, 7), np.uint8))
glass = cv2.inpaint(dock, cv2.bitwise_or(mask, icons_m), 11, cv2.INPAINT_TELEA).astype(np.float32)
synth = dock.astype(np.float32).copy()
hh, ww = mask.shape; YY, XX = np.mgrid[0:hh, 0:ww]
for cx2 in (403, 921):                     # удвоенные центры «Телефона» (201.5) и «Сообщений» (460.5), измерено по зелёному
    cx = cx2 / 2; cy = 2373 - dy0; half = 94.0
    u = (XX - cx) / half; v = (YY - cy) / half
    alpha = np.clip(((1 - (np.abs(u) ** 5 + np.abs(v) ** 5)) * 60), 0, 1)        # мягкая маска значка
    xm = np.clip(cx2 - XX, 0, ww - 1)
    mir = dock[YY, xm].astype(np.float32)
    if cx2 == 403:
        # у «Телефона» трубка несимметрична: внутри угла берём фон из центрального столбца той же строки,
        # зеркало — только для кромки значка (там блик рамки, трубки нет)
        f = np.abs(u) ** 5 + np.abs(v) ** 5
        rowfill = dock[:, int(cx)].astype(np.float32)[YY]
        tt = np.clip((f - .55) / .25, 0, 1)[..., None]
        mir = tt * mir + (1 - tt) * rowfill
    zone = (np.abs(XX - cx) < 140) & (np.abs(YY - cy) < 140)
    syn = alpha[..., None] * mir + (1 - alpha[..., None]) * glass
    synth[zone] = syn[zone]
synth[(mask > 0) & ~((XX < 560))] = glass[(mask > 0) & ~((XX < 560))]
wgt = cv2.GaussianBlur(cv2.dilate(mask, np.ones((31, 31), np.uint8)).astype(np.float32) / 255, (0, 0), 7)
wgt = np.maximum(wgt, (mask > 0).astype(np.float32))[..., None]
clean = np.clip(wgt * synth + (1 - wgt) * dock, 0, 255).astype(np.uint8)
for x0, name in zip(DX, ['phone', 'messages', 'safari', 'music']):
    grab(clean, x0, DY - dy0, name)
def capsule_mask(w, h, x0, y0, x1, y1, r, feather=1.5):
    m = np.zeros((h, w), np.float32)
    cv2.rectangle(m, (int(x0 + r), int(y0)), (int(x1 - r), int(y1)), 1, -1); cv2.rectangle(m, (int(x0), int(y0 + r)), (int(x1), int(y1 - r)), 1, -1)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)): cv2.circle(m, (int(cx), int(cy)), int(r), 1, -1)
    return cv2.GaussianBlur(m, (0, 0), feather)
def paste(src_rgb, box, mask_box, radius):
    x0, y0, x1, y1 = box
    im = Image.fromarray(src_rgb).resize((round((x1 - x0) * K), round((y1 - y0) * K)), Image.LANCZOS).convert('RGBA')
    mx0, my0, mx1, my1 = [(v - o) * K for v, o in zip(mask_box, (x0, y0, x0, y0))]
    a = capsule_mask(im.width, im.height, mx0, my0, mx1, my1, radius * K)
    im.putalpha(Image.fromarray((a * 255).astype(np.uint8))); home.alpha_composite(im, (round(x0 * K), round(y0 * K)))
paste(clean, (0, dy0, 1184, dy1), (48, 2217, 1136, 2527), 100)

# «Поиск» вместо «Search»: берём настоящую капсулу, стираем надпись, пишем по-русски
sx0, sy0, sx1, sy1 = 470, 2070, 714, 2162
pill = h1[sy0:sy1, sx0:sx1].copy()
g = pill.mean(2); tm = np.zeros(g.shape, np.uint8); tm[(g > 120)] = 255; tm[:, :78] = 0
tm = cv2.dilate(tm, np.ones((5, 5), np.uint8))
pill = cv2.inpaint(pill, tm, 7, cv2.INPAINT_TELEA)
pim = Image.fromarray(pill).resize((round((sx1 - sx0) * K), round((sy1 - sy0) * K)), Image.LANCZOS).convert('RGBA')
dp = ImageDraw.Draw(pim); fs = ImageFont.truetype(FONT, 34 * K)
col = tuple(int(v) for v in np.percentile(h1[sy0:sy1, sx0 + 90:sx1 - 20].reshape(-1, 3), 99.5, axis=0)) + (255,)
bb = fs.getbbox('Поиск'); dp.text((round(100 * K), pim.height / 2 - (bb[1] + bb[3]) / 2), 'Поиск', font=fs, fill=col)
a = capsule_mask(pim.width, pim.height, (477 - sx0) * K, (2073 - sy0) * K, (707 - sx0) * K, (2160 - sy0) * K, 43 * K)
pim.putalpha(Image.fromarray((a * 255).astype(np.uint8))); home.alpha_composite(pim, (round(sx0 * K), round(sy0 * K)))
home.convert('RGB').save(os.path.join(OUT, 'home.png'))

# значок «Нарды»: веб-приложение — квадратная иконка сайта под маской iOS, с лёгким бликом по краю
nd = Image.open(os.path.join(D, 'icon-512.png')).convert('RGB').resize((round(S * K), round(S * K)), Image.LANCZOS).convert('RGBA')
n = nd.width; m = squircle(n, n)
rim = np.clip(m - squircle(n, n, 5.0) * 0, 0, 1)
nd.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
cell = Image.new('RGBA', (round(272 * K), round(272 * K)), (0, 0, 0, 0))
ox = (cell.width - n) // 2; cell.alpha_composite(nd, (ox, 0)); label(cell, cell.width / 2, LAB_DY, 'Нарды')
cell.save(os.path.join(OUT, 'newic.png'))
r5, c3 = 5, 3
pos.update(newic=dict(x=(GX[c3] * K - ox) / 3, y=GY[r5] * K / 3, w=cell.width / 3, h=cell.height / 3, cx=(GX[c3] + S / 2) * K / 3, cy=(GY[r5] + S / 2) * K / 3))
json.dump(pos, open(os.path.join(OUT, 'pos.json'), 'w'))
print('ok', pos)
