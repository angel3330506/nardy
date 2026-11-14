# Скриншоты для магазинов: подпись сверху + кадр игры (shots.js) на фоне ореха.
# python frames.py <папка кадров> <iphone|ipad|rustore> <папка результата> [en]
import sys, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
SRC, DEV, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; EN = len(sys.argv) > 4 and sys.argv[4] == 'en'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
F = lambda n, s: ImageFont.truetype(os.path.join(ROOT, 'tools', 'fonts', n), s)
CAP = {   # сцена: (заголовок, подзаголовок)
 '1-menu':    (('Нарды — как во дворе', 'с компьютером, вдвоём или с другом по ссылке'), ('Backgammon, Yerevan style', 'vs computer, two on one phone, or a friend by link')),
 '2-board':   (('Резные доски', 'длинные и короткие нарды'), ('Hand-carved boards', 'long and short backgammon')),
 '3-gravura': (('Доска «Гравюра»', 'белый акрил и гравировка, как у настоящих'), ('The “Engraving” board', 'white acrylic and engraving, like the real thing')),
 '4-short':   (('Шесть соседей за столом', 'от новичка Арама до варпета Гургена'), ('Six neighbours at the table', 'from rookie Aram to master Gurgen')),
 '5-puzzle':  (('Задача дня', 'найдите лучший ход — каждый день новый'), ('Daily puzzle', 'find the best move — a new one every day')),
 '6-mars':    (('Марс и кокс', 'со всеми почестями'), ('Mars and koks', 'with full honours')),
}
os.makedirs(OUT, exist_ok=True)
plank = Image.open(os.path.join(ROOT, 'boards', 'walnut-plank.webp')).convert('RGB')
for name, caps in CAP.items():
    p = os.path.join(SRC, name + '.png')
    if not os.path.exists(p): continue
    shot = Image.open(p).convert('RGB'); W, H = shot.size
    bg = plank.resize((W, H)).filter(ImageFilter.GaussianBlur(W / 160)); bg = ImageEnhance.Brightness(bg).enhance(.42)
    vg = Image.new('L', (W, H), 0); ImageDraw.Draw(vg).ellipse((-W * .25, -H * .35, W * 1.25, H * 1.25), fill=255)
    bg = Image.composite(bg, Image.new('RGB', (W, H), (14, 8, 4)), vg.filter(ImageFilter.GaussianBlur(W / 12)))
    title, sub = caps[1] if EN else caps[0]
    cap_h = int(H * (.2 if W / H > 1.6 else .17))
    sc = min((H - cap_h - H * .06) / H, (W * .94) / W); sw, sh = int(W * sc), int(H * sc)
    x0, y0 = (W - sw) // 2, cap_h + int((H - cap_h - sh) * .35)
    r = int(sw * .025)
    m = Image.new('L', (sw, sh), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, sw - 1, sh - 1), r, fill=255)
    sd = Image.new('L', (W, H), 0); ImageDraw.Draw(sd).rounded_rectangle((x0, y0 + sh * .02, x0 + sw, y0 + sh * 1.02), r, fill=200)
    bg = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), bg, sd.filter(ImageFilter.GaussianBlur(W / 70)))
    bg.paste(shot.resize((sw, sh), Image.LANCZOS), (x0, y0), m)
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((x0 - 2, y0 - 2, x0 + sw + 1, y0 + sh + 1), r + 2, outline=(201, 160, 90), width=max(2, W // 900))
    ft, fs = F('Forum.ttf', int(cap_h * .42)), F('Onest.ttf', int(cap_h * .17))
    ty = int(cap_h * .44)
    tm = Image.new('L', (W, H), 0); ImageDraw.Draw(tm).text((W / 2, ty), title, font=ft, fill=255, anchor='mm')
    grad = Image.linear_gradient('L').resize((W, int(cap_h * .5)))
    g = Image.new('RGB', (W, H), (226, 184, 96)); top = Image.new('RGB', (W, H), (255, 241, 196))
    gm = Image.new('L', (W, H), 0); gm.paste(grad.transpose(Image.FLIP_TOP_BOTTOM), (0, int(ty - cap_h * .25)))
    goldfill = Image.composite(top, g, gm)
    sh_ = tm.filter(ImageFilter.GaussianBlur(cap_h * .03)); bg = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), bg, sh_.point(lambda v: v * .7))
    bg = Image.composite(goldfill, bg, tm); d = ImageDraw.Draw(bg)
    d.text((W / 2, int(cap_h * .8)), sub, font=fs, fill=(233, 214, 176), anchor='mm')
    bg.save(os.path.join(OUT, name + '.jpg'), quality=93)
print('frames ok', DEV, 'en' if EN else 'ru')
