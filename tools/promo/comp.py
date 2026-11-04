# Монтаж ролика: фон (plate.png, один кадр) двигается вслед за камерой, сверху — кадры телефона (PNG с прозрачностью),
# в конце — вспышка и затемнение; потом ffmpeg собирает видео со звуками.
# Запуск: python comp.py <папка рендера> <sfx.wav> <выходной mp4>
import json, os, sys, subprocess
import numpy as np
from PIL import Image
R, SFX, MP4 = sys.argv[1:4]
D0 = 16.4; PLANE = 40.0                     # как в phone_blender.py: камера при полном виде и глубина стола
Ff = 50 / 36 * 1920; Fp = 35 / 36 * 3840    # фокусные расстояния в пикселях: кадр и фон
def bokeh(path):
    """Размытие «как у объектива»: яркие точки (лампочки гирлянды) становятся мягкими кругами, стол — мягким пятном."""
    import cv2
    im = np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255
    lin = im ** 2.2
    hi = np.zeros_like(lin)
    r = 34; k = np.zeros((2 * r + 1, 2 * r + 1), np.float32); cv2.circle(k, (r, r), r, 1, -1, cv2.LINE_AA); k /= k.sum()
    disc = cv2.filter2D(lin + hi, -1, k)
    soft = cv2.GaussianBlur(disc, (0, 0), 6)
    out = soft / (1 + soft * .25)                             # мягкое сжатие пересветов
    out = np.clip(out * .78, 0, 1) ** (1 / 2.2)
    out = np.clip((out - .04) * 1.12, 0, 1) ** 1.12                     # плотнее и контрастнее, без серой дымки
    yy, xx = np.mgrid[0:out.shape[0], 0:out.shape[1]]; vg = 1 - .38 * (((xx - 1080) / 1300) ** 2 + ((yy - 1920) / 2300) ** 2)
    out = out * np.clip(vg, .45, 1)[..., None]
    # круги боке на месте лампочек гирлянды (те же координаты и тот же генератор случайных чисел, что в phone_blender.py)
    rng = np.random.default_rng(5); Fp_ = 35 / 36 * 3840
    lay = np.zeros(out.shape, np.float32)
    for (y0, z0, sag) in ((19, -16, 4), (-6, -20, 5), (-24, -14, 3.5)):
        for k in range(9):
            u = k / 8; x = -22 + 44 * u; y = y0 + sag * (1 - (2 * u - 1) ** 2) * -1 + rng.uniform(-.6, .6); z = z0 + rng.uniform(-1, 1)
            dz = D0 - z; px = 1080 + Fp_ * x / dz; py = 1920 - Fp_ * y / dz
            rad = 46 + 3.0 * (dz - D0)                                     # чем дальше от фокуса, тем больше круг
            disc_ = np.zeros(out.shape[:2], np.float32); cv2.circle(disc_, (int(px), int(py)), int(rad), 1, -1, cv2.LINE_AA)
            disc_ = cv2.GaussianBlur(disc_, (0, 0), 2.5)
            ring = cv2.GaussianBlur(cv2.circle(np.zeros(out.shape[:2], np.float32), (int(px), int(py)), int(rad - 2), 1, 3, cv2.LINE_AA), (0, 0), 2)
            a_ = disc_ * .42 + ring * .18
            lay += a_[..., None] * np.array([1.0, .74, .42], np.float32)
    for _ in range(26):                                                    # ещё огоньки подальше — мягче и тусклее
        px, py = rng.uniform(0, 2160), rng.uniform(0, 3840); rad = rng.uniform(40, 95); g_ = rng.uniform(.12, .3)
        disc_ = cv2.GaussianBlur(cv2.circle(np.zeros(out.shape[:2], np.float32), (int(px), int(py)), int(rad), 1, -1, cv2.LINE_AA), (0, 0), 3)
        lay += (disc_ * g_)[..., None] * np.array([1.0, rng.uniform(.6, .8), rng.uniform(.3, .5)], np.float32)
    out = 1 - (1 - out) * (1 - np.clip(lay, 0, 1))                      # «экран»: свет складывается мягко
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
cache = os.path.join(R, 'plate_bokeh.png')
if not os.path.exists(cache): bokeh(os.path.join(R, 'plate.png')).save(cache)
plate = Image.open(cache).convert('RGB')
cam = json.load(open(os.path.join(R, 'cam.json')))
os.makedirs(os.path.join(R, 'comp'), exist_ok=True)
LIMIT = int(os.environ.get('LIMIT', 10**6))
for f, x, y, d in cam[:LIMIT]:
    a = Fp * (d + PLANE) / (Ff * (D0 + PLANE))
    cx, cy = x / 100, -y / 100
    c = 1080 - a * 540 + Fp * cx / (D0 + PLANE); g = 1920 - a * 960 - Fp * cy / (D0 + PLANE)
    bg = plate.transform((1080, 1920), Image.AFFINE, (a, 0, c, 0, a, g), Image.BICUBIC).convert('RGBA')
    ph = os.path.join(R, '%04d.png' % f)
    if os.path.exists(ph): bg.alpha_composite(Image.open(ph))
    t = (f - 1) / 30
    im = np.asarray(bg.convert('RGB')).astype(np.float32)
    if t > 15.85:                            # телефон влетел в камеру: вспышка, затем темнота
        k = min(1, (t - 15.85) / .15); w = k if t < 16.0 else max(0, 1 - (t - 16.0) / .15)
        im = im * (1 - w) + 255 * w
        if t >= 16.0: im *= max(0, 1 - (t - 16.0) / .15)
    if t < .25: im *= t / .25                # мягкое начало
    Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(os.path.join(R, 'comp', '%04d.jpg' % f), quality=95)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(R, 'comp', '%04d.jpg'), '-i', SFX,
                '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                '-shortest', '-movflags', '+faststart', MP4], check=True)
print('video', MP4)
