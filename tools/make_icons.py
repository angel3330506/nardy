# Рисует иконки приложения: воровская звезда на тёмном дереве с золотым кольцом.
import math, os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), '..', 'icons')
S = 2048  # рисуем крупно и уменьшаем — так края гладкие

def star(d, cx, cy, R, r, light, dark, outline=None):
    for k in range(8):
        a = math.radians(-90 + k * 45)
        tip = (cx + R * math.cos(a), cy + R * math.sin(a))
        l = (cx + r * math.cos(a - math.pi / 8), cy + r * math.sin(a - math.pi / 8))
        rr = (cx + r * math.cos(a + math.pi / 8), cy + r * math.sin(a + math.pi / 8))
        d.polygon([(cx, cy), tip, l], fill=light, outline=outline)
        d.polygon([(cx, cy), tip, rr], fill=dark, outline=outline)

def make(scale):
    img = Image.new('RGB', (S, S), (12, 11, 10))
    px = img.load()
    # радиальный фон: тёплое дерево к краям темнеет
    for y in range(0, S, 4):
        for x in range(0, S, 4):
            t = min(1, math.hypot(x - S * .42, y - S * .36) / (S * .8))
            c = (int(62 - 44 * t), int(38 - 27 * t), int(24 - 16 * t))
            for dy in range(4):
                for dx in range(4):
                    px[x + dx, y + dy] = c
    d = ImageDraw.Draw(img)
    c = S / 2
    R = S * .40 * scale
    d.ellipse([c - R, c - R, c + R, c + R], fill=(92, 24, 26), outline=(217, 181, 106), width=int(S * .018 * scale))
    R2 = R * .88
    d.ellipse([c - R2, c - R2, c + R2, c + R2], outline=(190, 150, 80), width=int(S * .005))
    star(d, c, c, R * .80, R * .28, (243, 214, 140), (16, 11, 8), outline=(200, 160, 90))
    return img

for name, size, scale in [('icon-512.png', 512, 1), ('icon-192.png', 192, 1),
                          ('apple-touch-icon.png', 180, 1), ('icon-maskable-512.png', 512, .82)]:
    make(scale).resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name), optimize=True)
    print('ok', name)
