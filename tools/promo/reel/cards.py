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
SET = sys.argv[4] if len(sys.argv) > 4 else 'puzzle'
def bubble(text, y, size=50, maxw=860):                         # реплика соседа: светлое облачко, как в игре, только крупнее
    fnt = font('OnestB.ttf', size); im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    words, lines = text.split(), ['']
    for w_ in words:
        t = (lines[-1] + ' ' + w_).strip()
        if tlen(d, t, fnt) > maxw - 90 and lines[-1]: lines.append(w_)
        else: lines[-1] = t
    lh = size * 1.3; bw = max(tlen(d, l, fnt) for l in lines) + 90; bh = lh * len(lines) + 60; x0 = (W - bw) / 2
    sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rounded_rectangle((x0, y + 14, x0 + bw, y + bh + 14), 40, fill=150)
    im.putalpha(sh.filter(ImageFilter.GaussianBlur(18))); d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0, y, x0 + bw, y + bh), 40, fill=(244, 234, 214, 255))
    d.polygon([(W / 2 - 26, y), (W / 2 + 26, y), (W / 2 + 4, y - 30)], fill=(244, 234, 214, 255))   # хвостик вверх — к телефону
    for i, l in enumerate(lines): draw_line(d, (W - tlen(d, l, fnt)) / 2, y + 30 + i * lh, l, fnt, (58, 34, 20, 255))
    return im
if SET == 'pov':
    FN, FS = font('Forum.ttf', 128), font('Onest.ttf', 48)
    save('intro', text_layer(['POV: играешь в нарды', 'с соседями по двору'], 300, font('Forum.ttf', 96), GOLD, grad=True))
    for k, name, trait in (('aram', 'Арам', 'новичок · радуется каждому дублю'), ('ashot', 'Дядя Ашот', 'никогда никуда не спешит'),
                           ('siran', 'Бабушка Сирануш', 'сначала чай, потом марс'), ('gurgen', 'Варпет Гурген', 'у него всё по плану')):
        save('n_' + k, text_layer([name], 300, FN if len(name) < 12 else font('Forum.ttf', 108), GOLD, grad=True), text_layer([trait], 470, FS, CREAM))
    for k, t in (('q1', 'Давай, кто кого!'), ('q2', 'Ду-шеш! Вот это я понимаю!'), ('q3', 'Садись, сыграем. Не торопись.'), ('q4', 'Думай, думай, я не спешу.'),
                 ('q5', 'Садись, чай остынет.'), ('q6', 'Марс, родной. Иди чай пей.'), ('q7', 'Нарды — это терпение.'), ('q8', 'Так и было задумано.')):
        save(k, bubble('«' + t + '»', 1390))
    save('outro', text_layer(['А ты с кем', 'сыграешь?'], 300, FT if 'FT' in dir() else font('Forum.ttf', 118), GOLD, grad=True),
                  text_layer(['Отметь друга, который', 'играет как бабушка Сирануш ↓'], 1440, font('Onest.ttf', 46), CREAM))
else:
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
