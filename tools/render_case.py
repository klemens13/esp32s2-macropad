r"""
Render case macropad jadi PNG - tanpa OpenGL, tanpa OpenSCAD GUI.

Alur:
  1. OpenSCAD mengekspor STL (lihat README / langkah di bawah)
  2. Script ini memuat STL, menyusun scene (tray + plate + keycap + layar),
     lalu merasterisasi dengan z-buffer numpy.

Prasyarat (sekali saja):
  openscad -o %TEMP%\mx_tray.stl  -D "PART=\"tray\""  hardware/case_mx.scad
  (atau pakai tools/render_case.ps1 yang mengurus semuanya)

Jalankan:  python tools/render_case.py
"""

from __future__ import annotations

import glob
import os
import struct

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(ROOT, "hardware")
STL_DIR = os.path.join(os.environ.get("TEMP", "."), "mp_stl")

SS = 3                     # supersampling
BG_TOP = np.array([246, 248, 250], dtype=np.float64)
BG_BOT = np.array([214, 223, 232], dtype=np.float64)

# warna material
COL_PLATE = np.array([228, 231, 235], dtype=np.float64)
COL_TRAY = np.array([205, 211, 219], dtype=np.float64)
COL_KEY = np.array([250, 250, 248], dtype=np.float64)
COL_KEY_ACTIVE = np.array([ 96, 165, 250], dtype=np.float64)
COL_SCREEN = np.array([ 11,  15,  20], dtype=np.float64)


# --------------------------------------------------------------------- STL
def load_stl(path: str) -> np.ndarray:
    raw = open(path, "rb").read()
    if raw[:5] == b"solid" and b"facet" in raw[:400]:
        txt = raw.decode("ascii", "ignore")
        verts = np.array(
            [list(map(float, m)) for m in
             __import__("re").findall(r"vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)", txt)],
            dtype=np.float64,
        )
        return verts.reshape(-1, 3, 3)

    n = struct.unpack("<I", raw[80:84])[0]
    data = np.frombuffer(raw, dtype=np.uint8, count=n * 50, offset=84)
    data = data.reshape(n, 50)[:, 12:48].copy().view("<f4").reshape(n, 3, 3)
    return data.astype(np.float64)


# ---------------------------------------------------------------- primitif
def _quad(a, b, c, d):
    return [(a, b, c), (a, c, d)]


def box(cx, cy, cz, sx, sy, sz):
    """Balok, (cx,cy,cz) = titik tengah alas."""
    x0, x1 = cx - sx / 2, cx + sx / 2
    y0, y1 = cy - sy / 2, cy + sy / 2
    z0, z1 = cz, cz + sz
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    t = []
    t += _quad(p[4], p[5], p[6], p[7])      # atas
    t += _quad(p[0], p[3], p[2], p[1])      # bawah
    t += _quad(p[0], p[1], p[5], p[4])
    t += _quad(p[1], p[2], p[6], p[5])
    t += _quad(p[2], p[3], p[7], p[6])
    t += _quad(p[3], p[0], p[4], p[7])
    return t


def frustum(cx, cy, cz, s_bot, s_top, h):
    """Keycap: alas lebih lebar dari atas."""
    b = s_bot / 2
    t = s_top / 2
    p = [(cx - b, cy - b, cz), (cx + b, cy - b, cz), (cx + b, cy + b, cz), (cx - b, cy + b, cz),
         (cx - t, cy - t, cz + h), (cx + t, cy - t, cz + h),
         (cx + t, cy + t, cz + h), (cx - t, cy + t, cz + h)]
    tri = []
    tri += _quad(p[4], p[5], p[6], p[7])
    tri += _quad(p[0], p[3], p[2], p[1])
    tri += _quad(p[0], p[1], p[5], p[4])
    tri += _quad(p[1], p[2], p[6], p[5])
    tri += _quad(p[2], p[3], p[7], p[6])
    tri += _quad(p[3], p[0], p[4], p[7])
    return tri


def cylinder(cx, cy, cz, d, h, seg=20):
    r = d / 2
    ang = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    tri = []
    for i in range(seg):
        a0, a1 = ang[i], ang[(i + 1) % seg]
        x0, y0 = cx + r * np.cos(a0), cy + r * np.sin(a0)
        x1, y1 = cx + r * np.cos(a1), cy + r * np.sin(a1)
        tri.append(((cx, cy, cz + h), (x0, y0, cz + h), (x1, y1, cz + h)))
        tri.append(((cx, cy, cz), (x1, y1, cz), (x0, y0, cz)))
        tri += _quad((x0, y0, cz), (x1, y1, cz), (x1, y1, cz + h), (x0, y0, cz + h))
    return tri


def plane(cx, cy, cz, sx, sy):
    hx, hy = sx / 2, sy / 2
    return _quad((cx - hx, cy - hy, cz), (cx + hx, cy - hy, cz),
                 (cx + hx, cy + hy, cz), (cx - hx, cy + hy, cz))


# ------------------------------------------------------------------ scene
KEY_LABELS_GRID = [(c, r) for r in range(3) for c in range(4)]


def build_scene(kind: str):
    """Susun tray + plate + keycap + layar dalam koordinat dunia (mm)."""
    stl_tray = os.path.join(STL_DIR, f"{kind}_tray.stl")
    stl_plate = os.path.join(STL_DIR, f"{kind}_plate.stl")
    tray = load_stl(stl_tray)
    plate = load_stl(stl_plate)

    if kind == "mx":
        plate_w, plate_d, plate_t = 86.2, 93.15, 3.0
        total_h = 19.0
        pitch, margin, band = 19.05, 5.0, 26.0
        cap_h, cap_bot, cap_top = 7.5, 18.0, 15.0
    else:
        plate_w, plate_d, plate_t = 70.0, 81.0, 3.0
        total_h = 11.2
        pitch, margin, band = 15.0, 5.0, 26.0
        cap_h, cap_bot, cap_top = 4.5, 7.0, 7.0

    def centered(tris):
        """Geser mesh supaya pusat XY-nya di (0,0) - jangan pakai ukuran part lain."""
        pts = tris.reshape(-1, 3)
        cx = (pts[:, 0].min() + pts[:, 0].max()) / 2
        cy = (pts[:, 1].min() + pts[:, 1].max()) / 2
        return tris - np.array([cx, cy, 0.0])

    tray = centered(tray)
    plate = centered(plate)

    ox, oy = -plate_w / 2, -plate_d / 2
    plate_z = total_h - plate_t

    parts = []
    parts.append((tray, COL_TRAY))
    # +0.05 mm: hindari z-fighting dengan bibir tray (permukaannya koplanar)
    parts.append((plate + np.array([0, 0, plate_z + 0.05]), COL_PLATE))

    # keycap: satu menyala (K10) supaya ada aksen
    lit = 9
    idx = 0
    for (c, r) in KEY_LABELS_GRID:
        cx = ox + margin + c * pitch + pitch / 2
        cy = oy + margin + band + r * pitch + pitch / 2
        if kind == "mx":
            tris = frustum(cx, cy, total_h + 0.4, cap_bot, cap_top, cap_h)
        else:
            tris = cylinder(cx, cy, total_h + 0.2, cap_bot, cap_h)
        parts.append((np.array(tris), COL_KEY_ACTIVE if idx == lit else COL_KEY))
        idx += 1

    # layar OLED (jendela 24x13, active area 21.7x11.2)
    win_cx = ox + plate_w / 2
    win_cy = oy + margin + band / 2
    parts.append((np.array(plane(win_cx, win_cy, total_h - 0.4, 21.7, 11.2)), COL_SCREEN))

    return parts, (plate_w, plate_d, total_h)


# ----------------------------------------------------------------- render
def render(parts, size_hint, out_path, az=38.0, el=30.0, width=1500, height=1150):
    W, H = width * SS, height * SS

    # semua titik -> cari pusat & skala
    pts = np.concatenate([p.reshape(-1, 3) for p, _ in parts])
    center = (pts.min(axis=0) + pts.max(axis=0)) / 2
    radius = np.linalg.norm(pts.max(axis=0) - pts.min(axis=0)) / 2

    a, e = np.radians(az), np.radians(el)
    fwd = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), -np.sin(e)])
    right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)

    scale = (min(W, H) * 0.62) / radius

    zbuf = np.full((H, W), 1e9, dtype=np.float64)
    img = np.zeros((H, W, 3), dtype=np.float64)

    # lampu
    lights = [
        (np.array([-0.45, -0.55, 0.70]), 0.55),
        (np.array([0.55, -0.25, 0.35]), 0.28),
        (np.array([0.10, 0.75, 0.30]), 0.16),
    ]
    for l, _ in lights:
        l /= np.linalg.norm(l)
    ambient = 0.30

    for tris, color in parts:
        d = tris.reshape(-1, 3) - center
        u = d @ right
        v = d @ up
        zc = d @ fwd

        sx = (W / 2 + u * scale).reshape(-1, 3)
        sy = (H / 2 - v * scale).reshape(-1, 3)
        sz = zc.reshape(-1, 3)

        # normal per segitiga (dunia)
        tri = tris.reshape(-1, 3, 3)
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        ln = np.linalg.norm(n, axis=1, keepdims=True)
        ln[ln == 0] = 1
        n = n / ln

        shade = np.full(len(n), ambient)
        for l, k in lights:
            shade += k * np.clip(n @ l, 0, None)
        shade = np.clip(shade, 0.22, 1.06)

        for i in range(len(sx)):
            x1, y1 = sx[i, 1] - sx[i, 0], sy[i, 1] - sy[i, 0]
            x2, y2 = sx[i, 2] - sx[i, 0], sy[i, 2] - sy[i, 0]
            den = x1 * y2 - x2 * y1
            if abs(den) < 1e-9:
                continue

            minx = int(max(0, np.floor(sx[i].min())))
            maxx = int(min(W - 1, np.ceil(sx[i].max())))
            miny = int(max(0, np.floor(sy[i].min())))
            maxy = int(min(H - 1, np.ceil(sy[i].max())))
            if minx > maxx or miny > maxy:
                continue

            px = np.arange(minx, maxx + 1) + 0.5
            py = np.arange(miny, maxy + 1) + 0.5
            gx, gy = np.meshgrid(px - sx[i, 0], py - sy[i, 0])

            w1 = (gx * y2 - x2 * gy) / den
            w2 = (x1 * gy - gx * y1) / den
            w0 = 1.0 - w1 - w2
            mask = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not mask.any():
                continue

            z = w0 * sz[i, 0] + w1 * sz[i, 1] + w2 * sz[i, 2]
            sub = zbuf[miny:maxy + 1, minx:maxx + 1]
            better = mask & (z < sub)
            if not better.any():
                continue
            sub[better] = z[better]
            img[miny:maxy + 1, minx:maxx + 1][better] = color * shade[i]

    # latar gradien + bayangan kontak
    yy = np.linspace(0, 1, H)[:, None, None]
    bg = BG_TOP * (1 - yy) + BG_BOT * yy
    bg = np.broadcast_to(bg, (H, W, 3)).copy()

    filled = (zbuf < 1e8).astype(np.float64)
    shadow = Image.fromarray((filled * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28 * SS))
    sh = np.asarray(shadow, dtype=np.float64)[..., None] / 255.0
    shift = np.roll(sh, int(18 * SS), axis=0)
    bg = bg * (1 - 0.35 * shift)

    comp = np.where(filled[..., None] > 0, img, bg)
    comp = np.clip(comp, 0, 255).astype(np.uint8)

    out = Image.fromarray(comp).resize((width, height), Image.LANCZOS)
    out.save(out_path, optimize=True)
    return out


def main():
    os.makedirs(HW, exist_ok=True)
    for kind, name in (("mx", "render_mx.png"), ("tactile", "render_tactile.png")):
        parts, size = build_scene(kind)
        img = render(parts, size, os.path.join(HW, name))
        print(f"{name:20s} {img.size}")


if __name__ == "__main__":
    main()
