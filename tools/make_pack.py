"""VFX texture + flipbook pack generator (Solar Verdict v2).

All maps are white RGB with the shape in alpha (tint in Roblox with Color/ImageColor3),
except where noted. Every map uses noise breakup so nothing reads as a clean vector shape.
Run: python3 tools/make_pack.py  -> writes textures/solar_v2/*.png
"""
import os
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "..", "textures", "solar_v2")
os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(7)


# ---------------------------------------------------------------- noise helpers
def _lattice(shape, seed):
    return np.random.default_rng(seed).random(shape)


def value_noise(x, y, period=None, seed=0):
    """Smooth 2D value noise. x,y float arrays. period -> tile in both axes."""
    size = 256
    g = _lattice((size, size), seed)
    xi, yi = np.floor(x).astype(int), np.floor(y).astype(int)
    xf, yf = x - xi, y - yi
    px = period[0] if period else size
    py = period[1] if period else size
    x0, x1 = xi % px % size, (xi + 1) % px % size
    y0, y1 = yi % py % size, (yi + 1) % py % size
    u = xf * xf * (3 - 2 * xf)
    v = yf * yf * (3 - 2 * yf)
    a = g[y0, x0] * (1 - u) + g[y0, x1] * u
    b = g[y1, x0] * (1 - u) + g[y1, x1] * u
    return a * (1 - v) + b * v


def fbm(x, y, octaves=5, period=None, seed=0, lac=2.0, gain=0.5):
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        p = (period[0] * lac ** o, period[1] * lac ** o) if period else None
        p = (int(round(p[0])), int(round(p[1]))) if p else None
        total = total + amp * value_noise(x * lac ** o, y * lac ** o, p, seed + o * 17)
        norm += amp
        amp *= gain
    return total / norm


def grid(n):
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)
    u = (x + 0.5) / n * 2 - 1
    v = (y + 0.5) / n * 2 - 1
    return u, v


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def save_alpha(name, alpha, rgb=None):
    alpha = np.clip(alpha, 0, 1)
    h, w = alpha.shape
    if rgb is None:
        rgb = np.ones((h, w, 3))
    img = np.dstack([np.clip(rgb, 0, 1), alpha])
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, name), optimize=True)
    print("wrote", name)


def atlas(frames, cols):
    n = frames[0].shape[0]
    rows = int(np.ceil(len(frames) / cols))
    out = np.zeros((rows * n, cols * n) + frames[0].shape[2:])
    for i, f in enumerate(frames):
        r, c = divmod(i, cols)
        out[r * n:(r + 1) * n, c * n:(c + 1) * n] = f
    return out


# ---------------------------------------------------------------- flipbooks
def flame_flipbook():
    """8x8, 64 frames @128px: a flame tongue that licks up, splits and burns away.
    RGB carries a hot-core ramp (white core -> warm edge), so ParticleEmitter Color can stay light."""
    n, frames_a, frames_rgb = 128, [], []
    u, v = grid(n)
    for f in range(64):
        t = f / 63
        yb = (1 - v) / 2  # 0 at the bottom of the frame, 1 at the top
        rise = t * 2.4
        # sideways sway that grows toward the tip, advected upward over time
        sway = (fbm(u * 1.5 + 11, yb * 2.5 - rise, 4, seed=3) - 0.5) * 0.9 * yb
        uu = u + sway
        width = 0.5 * np.sin(np.pi * np.clip(yb * 0.85 + 0.12, 0, 1)) ** 0.7 * (1 - yb) ** 0.35 * (1 - 0.3 * t) + 0.02
        body = 1 - smooth(width * 0.35, width, np.abs(uu))
        body *= smooth(0.04, 0.2, yb) * (1 - smooth(0.9, 1.0, yb))
        # licking tongues: noise scrolling upward, threshold rises with height and age
        tongue = fbm(uu * 4.0, yb * 5.5 - rise * 2.2, 5, seed=21)
        thresh = 0.12 + yb ** 1.2 * 0.7 + t * 0.35
        a = body * smooth(thresh - 0.08, thresh + 0.12, tongue + body * 0.3)
        a *= 1 - smooth(0.75, 1.0, t)
        heat = np.clip(a * 1.2 * (1 - yb * 0.5), 0, 1)
        rgb = np.dstack([np.ones_like(heat), 0.62 + 0.38 * heat, 0.3 + 0.7 * heat ** 2])
        frames_a.append(a)
        frames_rgb.append(rgb)
    save_alpha("flame_8x8.png", atlas(frames_a, 8), atlas(frames_rgb, 8))


def smoke_flipbook():
    """8x8 billowing puff that expands and erodes. Lit from the top (baked soft shading)."""
    n, fa, frgb = 128, [], []
    u, v = grid(n)
    for f in range(64):
        t = f / 63
        scale = 0.72 + 0.26 * t
        r = np.sqrt(u * u + v * v) / scale
        billow = fbm(u * 2.6 / scale + 5, v * 2.6 / scale + t * 0.8, 5, seed=41)
        shape = 1 - smooth(0.45, 1.0, r + (billow - 0.5) * 0.9)
        erode = 0.05 + 0.75 * t ** 1.3
        a = shape * smooth(erode, erode + 0.35, billow * 0.8 + shape * 0.45)
        a *= 0.95 - 0.35 * t
        light = np.clip(0.55 + 0.45 * (-v) * 0.8 + (billow - 0.5) * 0.6, 0.25, 1)
        frgb.append(np.dstack([light, light, light]))
        fa.append(a)
    save_alpha("smoke_8x8.png", atlas(fa, 8), atlas(frgb, 8))


def electric_flipbook():
    """4x4 (256px frames): forked arcs crawling across the frame, each frame new."""
    n, frames = 256, []
    rng = np.random.default_rng(99)
    for f in range(16):
        field = np.zeros((n, n))

        def bolt(p0, p1, w, depth):
            pts = [np.array(p0, float)]
            steps = 14
            d = np.array(p1, float) - np.array(p0, float)
            perp = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
            for i in range(1, steps):
                tt = i / steps
                off = rng.normal() * np.linalg.norm(d) * 0.07 * np.sin(tt * np.pi)
                pts.append(np.array(p0) + d * tt + perp * off)
            pts.append(np.array(p1, float))
            for i in range(len(pts) - 1):
                stroke(field, pts[i], pts[i + 1], w * (1 - i / len(pts) * 0.6))
                if depth < 2 and rng.random() < 0.18:
                    ang = np.arctan2(d[1], d[0]) + rng.uniform(-1.1, 1.1)
                    L = np.linalg.norm(d) * rng.uniform(0.2, 0.4)
                    bolt(pts[i], pts[i] + np.array([np.cos(ang), np.sin(ang)]) * L, w * 0.55, depth + 1)

        for _ in range(rng.integers(1, 3)):
            a0 = rng.uniform(0, 2 * np.pi)
            p0 = np.array([n / 2, n / 2]) + np.array([np.cos(a0), np.sin(a0)]) * n * 0.46
            p1 = np.array([n / 2, n / 2]) - np.array([np.cos(a0), np.sin(a0)]) * n * 0.46 + rng.normal(size=2) * 20
            bolt(p0, p1, rng.uniform(2.2, 3.2), 0)
        glow = blur(field, 6) * 0.55
        frames.append(np.clip(field + glow, 0, 1))
    save_alpha("electric_4x4.png", atlas(frames, 4))


def stroke(field, a, b, w):
    n = field.shape[0]
    x0, y0 = a
    x1, y1 = b
    minx, maxx = int(max(0, min(x0, x1) - w - 2)), int(min(n - 1, max(x0, x1) + w + 2))
    miny, maxy = int(max(0, min(y0, y1) - w - 2)), int(min(n - 1, max(y0, y1) + w + 2))
    if minx > maxx or miny > maxy:
        return
    yy, xx = np.mgrid[miny:maxy + 1, minx:maxx + 1] + 0.5
    dx, dy = x1 - x0, y1 - y0
    L2 = max(dx * dx + dy * dy, 1e-6)
    t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / L2, 0, 1)
    d = np.hypot(xx - x0 - dx * t, yy - y0 - dy * t)
    c = np.clip(w - d + 0.5, 0, 1)
    sub = field[miny:maxy + 1, minx:maxx + 1]
    np.maximum(sub, c, out=sub)


def blur(img, r):
    from PIL import ImageFilter
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), float) / 255


# ---------------------------------------------------------------- single maps
def beam_scroll():
    """512x128 horizontally tileable energy streaks for Beams (TextureMode Wrap + TextureSpeed)."""
    w, h = 512, 128
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    fx = x / w * 8
    fy = y / h * 2
    streak = fbm(fx, fy * 6, 5, period=(8, 12), seed=55)
    streak = smooth(0.45, 0.8, streak)
    vv = (y + 0.5) / h * 2 - 1
    core = np.exp(-vv * vv * 10)
    edge = np.exp(-vv * vv * 3)
    a = np.clip(core * 0.8 + streak * edge * 0.9, 0, 1)
    save_alpha("beam_scroll.png", a)


def shock_ring():
    n = 1024
    u, v = grid(n)
    r = np.sqrt(u * u + v * v)
    th = np.arctan2(v, u)
    brk = fbm(np.cos(th) * 3 + 10, np.sin(th) * 3 + r * 4, 5, seed=61)
    band = np.exp(-((r - 0.82) ** 2) * 900)
    wide = np.exp(-((r - 0.78) ** 2) * 60) * smooth(0.4, 0.8, r)
    a = band * smooth(0.3, 0.6, brk) + wide * 0.45 * smooth(0.35, 0.75, brk)
    a *= 1 - smooth(0.96, 1.0, r)
    save_alpha("shock_ring.png", a)


def spark_streak():
    n = 256
    u, v = grid(n)
    a = np.exp(-(v * v) * 900) * (1 - np.abs(u)) ** 1.5 + np.exp(-(u * u + v * v) * 60) * 0.5
    save_alpha("spark_streak.png", a)


def soft_glow():
    n = 256
    u, v = grid(n)
    r = np.sqrt(u * u + v * v)
    a = np.exp(-r * r * 8) * 0.9 + np.exp(-r * r * 60) * 0.5
    a *= 1 - smooth(0.9, 1, r)
    save_alpha("soft_glow.png", a)


def star_glint():
    n = 512
    u, v = grid(n)
    au, av = np.abs(u), np.abs(v)
    rr = np.sqrt(u * u + v * v)
    h = np.exp(-av * av * 2200) * (1 - au) ** 2 + np.exp(-av * av * 18000) * (1 - au) ** 1.1
    vv = np.exp(-au * au * 2200) * (1 - av) ** 2 + np.exp(-au * au * 18000) * (1 - av) ** 1.1
    d1, d2 = np.abs(u - v) * 0.7071, np.abs(u + v) * 0.7071
    diag = (np.exp(-d1 * d1 * 4000) + np.exp(-d2 * d2 * 4000)) * np.clip(1 - rr * 2.2, 0, 1) * 0.5
    a = h + vv + diag + np.exp(-rr * rr * 140) + np.exp(-rr * rr * 12) * 0.2
    save_alpha("star_glint.png", a)


def sigil_hd():
    """1024 sigil with engraved double lines and faint noise wear."""
    n = 1024
    u, v = grid(n)
    r = np.sqrt(u * u + v * v)
    th = (np.arctan2(v, u) / (2 * np.pi) + 0.5)
    px = 2 / n
    rng = np.random.default_rng(1337)

    def circ(rad, w):
        return np.clip(1 - np.abs(r - rad) / (w * px) + 0.5, 0, 1)

    a = np.zeros_like(r)
    for rad, w in [(0.975, 3), (0.955, 1.4), (0.93, 1.4), (0.79, 2.2), (0.765, 1.2), (0.56, 2.4), (0.535, 1.2), (0.22, 2), (0.18, 1.2)]:
        a = np.maximum(a, circ(rad, w))
    ticks = ((th * 180) % 1 < 0.14) & (r > 0.935) & (r < 0.955)
    a = np.maximum(a, ticks * 0.9)
    # rune band
    cells = 72
    ci = np.floor(th * cells).astype(int) % cells
    fx = th * cells - np.floor(th * cells)
    fy = (r - 0.8) / 0.12
    pats = rng.integers(0, 8, cells)
    dots = rng.random(cells)
    band = (r > 0.8) & (r < 0.92) & (fx > 0.16) & (fx < 0.84) & (fy > 0.1) & (fy < 0.9)
    p = pats[ci]
    on = ((p % 2 == 0) & (np.abs(fx - 0.5) < 0.07)) | ((p % 3 == 0) & (np.abs(fy - 0.5) < 0.06)) | \
         ((p >= 4) & (np.abs(fy - 0.22) < 0.06)) | (((p == 1) | (p == 5)) & (np.abs((fx - 0.2) - (fy - 0.1) * 0.75) < 0.07)) | \
         ((p == 7) & (np.abs(fy - 0.78) < 0.06)) | ((dots[ci] > 0.78) & (np.hypot(fx - 0.5, fy - 0.5) < 0.1))
    a = np.maximum(a, (band & on) * 1.0)
    # inner rune ring
    cells2 = 44
    ci2 = np.floor(th * cells2).astype(int) % cells2
    fx2 = th * cells2 - np.floor(th * cells2)
    fy2 = (r - 0.58) / 0.16
    p2 = rng.integers(0, 8, cells2)[ci2]
    band2 = (r > 0.58) & (r < 0.74) & (fx2 > 0.25) & (fx2 < 0.75) & (fy2 > 0.15) & (fy2 < 0.85)
    on2 = ((p2 % 2 == 1) & (np.abs(fx2 - 0.5) < 0.05)) | ((p2 >= 3) & (np.abs(fy2 - 0.5) < 0.045)) | \
          ((p2 == 6) & (np.abs(np.hypot(fx2 - 0.5, fy2 - 0.5) - 0.2) < 0.04))
    a = np.maximum(a, (band2 & on2) * 0.95)
    # sun spokes
    spokes = (r > 0.22) & (r < 0.535) & (np.abs((th * 24) % 1 - 0.5) < np.where(np.floor(th * 24) % 2 == 0, 0.045, 0.02) * (1 - (r - 0.22) / 0.4 * 0.6))
    a = np.maximum(a, spokes * 0.75)
    # double hexagram
    for k in range(2):
        for i in range(3):
            a0 = np.radians(90 + k * 60 + i * 120)
            a1 = np.radians(90 + k * 60 + (i + 1) * 120)
            x0, y0, x1, y1 = np.cos(a0) * 0.535, np.sin(a0) * 0.535, np.cos(a1) * 0.535, np.sin(a1) * 0.535
            dx, dy = x1 - x0, y1 - y0
            t = np.clip(((u - x0) * dx + (v - y0) * dy) / (dx * dx + dy * dy), 0, 1)
            d = np.hypot(u - x0 - dx * t, v - y0 - dy * t)
            a = np.maximum(a, np.clip(1 - d / (1.8 * px) + 0.5, 0, 1))
    wear = fbm(u * 6 + 3, v * 6 - 2, 5, seed=5)
    a *= 0.7 + 0.3 * smooth(0.25, 0.6, wear)
    a *= r < 0.99
    save_alpha("sigil_hd.png", a)


def cracks_hd():
    n = 1024
    field = np.zeros((n, n))
    rng = np.random.default_rng(12)

    def branch(x, y, ang, length, w, depth):
        steps = int(rng.integers(5, 9))
        for _ in range(steps):
            seg = length / steps
            ang += rng.uniform(-0.45, 0.45)
            nx, ny = x + np.cos(ang) * seg, y + np.sin(ang) * seg
            stroke(field, (x, y), (nx, ny), w)
            if depth < 3 and rng.random() < 0.38:
                branch(nx, ny, ang + rng.uniform(-1.1, 1.1), length * 0.42, max(0.8, w * 0.55), depth + 1)
            x, y = nx, ny
            w = max(0.8, w * 0.84)

    for i in range(18):
        a = i / 18 * 2 * np.pi + rng.uniform(-0.12, 0.12)
        branch(n / 2 + np.cos(a) * 30, n / 2 + np.sin(a) * 30, a, rng.uniform(320, 500), rng.uniform(4, 7), 0)
    save_alpha("impact_cracks.png", field)


def ground_scorch():
    """Burnt ground decal: dark smudge with glowing ember veins (RGB baked: black + orange veins)."""
    n = 1024
    u, v = grid(n)
    r = np.sqrt(u * u + v * v)
    base = fbm(u * 3 + 4, v * 3 + 1, 6, seed=77)
    a = (1 - smooth(0.45, 1.0, r + (base - 0.5) * 0.6)) * 0.92
    veins = fbm(u * 9, v * 9, 5, seed=88)
    vein = np.exp(-((veins - 0.5) ** 2) * 900) * (1 - smooth(0.2, 0.75, r))
    rgb = np.dstack([vein * 1.0, vein * 0.42, vein * 0.08])
    a = np.clip(a + vein * 0.5, 0, 1)
    save_alpha("ground_scorch.png", a, rgb)


if __name__ == "__main__":
    flame_flipbook()
    smoke_flipbook()
    electric_flipbook()
    beam_scroll()
    shock_ring()
    spark_streak()
    soft_glow()
    star_glint()
    sigil_hd()
    cracks_hd()
    ground_scorch()
