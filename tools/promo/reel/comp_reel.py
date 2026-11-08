# Монтаж ролика «Задача дня»: фон (plate.png) двигается вслед за камерой, сверху телефон (PNG с прозрачностью),
# надписи с плавным появлением, отсчёт, вспышка и финальная карточка; ffmpeg собирает видео со звуком.
# Запуск: python comp_reel.py <папка рендера> <папка надписей> <sfx.wav> <выходной mp4>
import json, os, sys, subprocess, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
R, CARDS, SFX, MP4 = sys.argv[1:5]
D0 = 16.4; PLANE = 40.0; FPS = 30; TOTAL = 21.0
Ff = 50 / 36 * 1920; Fp = 35 / 36 * 3840
HIT = 18.2                                               # телефон влетает в камеру (END + .95 в reel_blender.py)
cache = os.path.join(R, 'plate_bokeh.png')
if not os.path.exists(cache):
    import importlib.util                                 # размытие фона — из comp.py, без запуска его монтажа
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'comp.py')).read().split('cache = ')[0]
    ns = {}; exec(src.replace('R, SFX, MP4 = sys.argv[1:4]', ''), ns); ns['bokeh'](os.path.join(R, 'plate.png')).save(cache)
plate = Image.open(cache).convert('RGB')
cam = {int(f): (x, y, d) for f, x, y, d in json.load(open(os.path.join(R, 'cam.json')))}
lastf = max(cam)
# надписи: (имя, начало, конец); другой ролик — свой план в JSON (TL=файл: {"txt": [...], "hit": .., "total": ..})
TXT = [('t1', .5, 4.8), ('t2', 5.2, 10.35), ('t3', 10.55, 13.15), ('t4', 13.35, 17.15)] + \
      [('n%d' % (5 - i), 5.4 + i, 6.4 + i) for i in range(5)]
if os.environ.get('TL'):
    tl = json.load(open(os.environ['TL'])); TXT = [tuple(x) for x in tl['txt']]; HIT = tl['hit']; TOTAL = tl['total']
cards = {n: Image.open(os.path.join(CARDS, n + '.png')).convert('RGBA') for n in {x[0] for x in TXT} | {'end'}}
def layer(im, a, dy=0, s=1.0):
    if a <= 0: return None
    if s != 1.0:
        w, h = im.size; im2 = im.resize((int(w * s), int(h * s)), Image.BICUBIC); c = Image.new('RGBA', im.size, (0, 0, 0, 0))
        c.alpha_composite(im2, ((w - im2.width) // 2, (h - im2.height) // 2)); im = c
    if dy: c = Image.new('RGBA', im.size, (0, 0, 0, 0)); c.alpha_composite(im, (0, int(dy))); im = c
    if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    return im
def ease(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
os.makedirs(os.path.join(R, 'comp'), exist_ok=True)
LIMIT = int(os.environ.get('LIMIT', 10 ** 6)); ONLY = os.environ.get('ONLY')
frames = range(1, int(TOTAL * FPS) + 1)
if ONLY: frames = [int(v) for v in ONLY.split(',')]
for f in list(frames)[:LIMIT]:
    t = (f - 1) / FPS
    if t < HIT + .2:
        x, y, d = cam[min(f, lastf)]
        a = Fp * (d + PLANE) / (Ff * (D0 + PLANE)); cx, cy = x / 100, -y / 100
        c = 1080 - a * 540 + Fp * cx / (D0 + PLANE); g = 1920 - a * 960 - Fp * cy / (D0 + PLANE)
        bg = plate.transform((1080, 1920), Image.AFFINE, (a, 0, c, 0, a, g), Image.BICUBIC).convert('RGBA')
        ph = os.path.join(R, '%04d.png' % f)
        if os.path.exists(ph): bg.alpha_composite(Image.open(ph))
        for n, t0, t1 in TXT:
            k = min(ease((t - t0) / .35), 1 - ease((t - t1 + .25) / .25)) if t0 <= t <= t1 else 0
            if n[0] == 'q': l = layer(cards[n], k, 0, 1 + .08 * (1 - ease((t - t0) / .3)))        # реплика — мягкий «поп»
            elif n[0] == 'n' and n[1:].isdigit(): l = layer(cards[n], k, 0, 1 + .25 * (1 - ease((t - t0) / .25)))     # цифра «впрыгивает»
            else: l = layer(cards[n], k, 26 * (1 - ease((t - t0) / .45)))                          # надпись всплывает
            if l: bg.alpha_composite(l)
    else:                                                   # финальная карточка: медленный наезд
        k = (t - HIT - .2) / (TOTAL - HIT - .2); s = 1.06 - .06 * ease(k * 1.4)
        bg = Image.new('RGBA', (1080, 1920), (14, 9, 6, 255)); bg.alpha_composite(layer(cards['end'], 1, 0, s))
    im = np.asarray(bg.convert('RGB')).astype(np.float32)
    if HIT - .15 < t < HIT + .45:                          # вспышка: нарастает, пока телефон летит, и гаснет уже на карточке
        w = ease((t - HIT + .15) / .15) if t < HIT else 1 - ease((t - HIT) / .45)
        im = im * (1 - w) + np.array([255, 244, 220], np.float32) * w
    if t < .25: im *= t / .25
    if t > TOTAL - .4: im *= max(0, (TOTAL - t) / .4)
    Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(os.path.join(R, 'comp', '%04d.jpg' % f), quality=95)
if not ONLY:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(R, 'comp', '%04d.jpg'), '-i', SFX,
                    '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', '-movflags', '+faststart', MP4], check=True)
    print('video', MP4)
