# Надписи ролика «Задача дня» (PNG 1080×1920 с прозрачностью): верхняя и нижняя полосы над/под телефоном, отсчёт, финальная карточка.
import os, sys, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
OUT = sys.argv[1]; F = sys.argv[2]            # папка вывода, папка со шрифтами (Forum.ttf, Onest.ttf)
NARDY = sys.argv[3] if len(sys.argv) > 3 else '/home/user/nardy'
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
GOLD, GOLD2, CREAM = (246, 220, 150), (214, 166, 72), (243, 234, 214)
from fontTools.ttLib import TTFont
_cm = {}
def font(name, size):
    f = ImageFont.truetype(os.path.join(F, name), size); f._cmap = _cm.setdefault(name, TTFont(os.path.join(F, name)).getBestCmap())
    f._fb = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', int(size * .8)); return f
def runs(l, fnt):                                              # куски строки: свой шрифт или запасной (стрелки)
    out = []
    for ch in l:
        f = fnt if ord(ch) in fnt._cmap or ch == ' ' else fnt._fb
        if out and out[-1][1] is f: out[-1][0] += ch
        else: out.append([ch, f])
    return out
def tlen(d, l, fnt): return sum(d.textlength(t, font=f) for t, f in runs(l, fnt))
def draw_line(d, x, y, l, fnt, fill):
    base = fnt.getmetrics()[0]
    for t, f in runs(l, fnt):
        d.text((x, y + base - f.getmetrics()[0] + (fnt.size * .06 if f is not fnt else 0)), t, font=f, fill=fill); x += d.textlength(t, font=f)
def text_layer(lines, y, fnt, fill, spacing=1.12, shadow=14, grad=False):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    hs = [fnt.getbbox(l)[3] - fnt.getbbox(l)[1] for l in lines]; lh = max(hs) * spacing; yy = y
    mask = Image.new('L', (W, H), 0); md = ImageDraw.Draw(mask)
    for l in lines:
        w = tlen(d, l, fnt); draw_line(md, (W - w) / 2, yy, l, fnt, 255); yy += lh
    col = Image.new('RGBA', (W, H), fill + (255,))
    if grad:                                                   # золото: сверху светлее
        g = Image.linear_gradient('L').resize((W, H)); col = Image.composite(Image.new('RGBA', (W, H), GOLD2 + (255,)), Image.new('RGBA', (W, H), GOLD + (255,)), g)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(mask.filter(ImageFilter.GaussianBlur(shadow)).point(lambda v: min(255, int(v * 1.6))))
    out = Image.alpha_composite(im, sh); col.putalpha(mask); return Image.alpha_composite(out, col)
def save(name, *layers):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for l in layers: im = Image.alpha_composite(im, l)
    im.save(os.path.join(OUT, name + '.png'))
FT, FB = font('Forum.ttf', 118), font('Onest.ttf', 50)
save('t1', text_layer(['90% не найдут', 'лучший ход'], 300, FT, GOLD, grad=True),
           text_layer(['Задача дня · Нарды'], 1480, FB, CREAM))
save('t2', text_layer(['Выпало 4–6.', 'Как сходишь?'], 300, FT, GOLD, grad=True),
           text_layer(['Пиши ответ', 'в комментариях ↓'], 1380, font('OnestB.ttf', 58), CREAM))
save('t3', text_layer(['Ответ:'], 300, FT, GOLD, grad=True), text_layer(['12 → 16,  15 → 21'], 470, font('Forum.ttf', 96), CREAM))
save('t4', text_layer(['Перекрыл сопернику', 'почти все ходы'], 300, font('Forum.ttf', 100), GOLD, grad=True),
           text_layer(['Новая задача — каждый день'], 1480, FB, CREAM))
# отсчёт 5…1 — кольцо с цифрой под надписью
for n in range(1, 6):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx, cy, r = W // 2, 1580, 70
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(20, 12, 8, 170), outline=GOLD + (255,), width=6)
    f2 = font('Forum.ttf', 110); w = d.textlength(str(n), font=f2); bb = f2.getbbox(str(n))
    d.text((cx - w / 2, cy - (bb[3] + bb[1]) / 2), str(n), font=f2, fill=GOLD + (255,))
    im.save(os.path.join(OUT, f'n{n}.png'))
# финальная карточка: тёмный фон, золотой Аревахач, название, где играть
end = Image.new('RGBA', (W, H), (14, 9, 6, 255))
glow = Image.new('L', (W, H), 0); ImageDraw.Draw(glow).ellipse((W/2 - 420, 520 - 420, W/2 + 420, 520 + 420), fill=120)
end = Image.alpha_composite(end, Image.merge('RGBA', [Image.new('L', (W, H), c) for c in (120, 80, 30)] + [glow.filter(ImageFilter.GaussianBlur(160))]))
rev = Image.open(os.path.join(NARDY, 'boards', 'intro-rev.webp')).convert('RGBA').resize((560, 560), Image.LANCZOS)
end.alpha_composite(rev, ((W - 560) // 2, 520 - 280))
for l in (text_layer(['Нарды'], 880, font('Forum.ttf', 170), GOLD, grad=True),
          text_layer(['Длинные и короткие · задача дня', 'соседи по двору из Еревана'], 1110, font('Onest.ttf', 46), CREAM),
          text_layer(['Бесплатно в RuStore'], 1380, font('OnestB.ttf', 64), GOLD),
          text_layer(['angel3330506.github.io/nardy'], 1480, font('Onest.ttf', 40), (200, 186, 160))):
    end = Image.alpha_composite(end, l)
end.save(os.path.join(OUT, 'end.png'))
print('cards ok')
