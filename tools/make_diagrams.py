"""
Generator gambar untuk proyek macropad ESP32-S2 Mini + OLED.

Menghasilkan:
  hardware/wiring.png      - peta koneksi 12 tombol + OLED
  hardware/layout.png      - tampak atas (case + layar + keycap)
  hardware/oled_states.png - tampilan layar di 4 kondisi
  hardware/plate_1to1.pdf  - template plate skala 1:1 (300 dpi)
  hardware/plate_1to1.png  - pratinjau template

Jalankan:  python tools/make_diagrams.py
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(ROOT, "hardware")

sys.path.insert(0, os.path.join(ROOT, "firmware"))
import font5x7  # noqa: E402  (font yang sama dengan yang dipakai board)

# ---------------------------------------------------------------- mekanik
PITCH = 19.05
KEY_HOLE = 14.05
MARGIN = 5.0
COLS, ROWS = 4, 3

SCREEN_BAND = 26.0
WIN_W, WIN_H = 24.0, 13.0          # jendela di plate
ACTIVE_W, ACTIVE_H = 21.74, 11.2   # active area OLED 0.96"

PLATE_T = 3.0
WALL = 2.4

PLATE_W = MARGIN * 2 + COLS * PITCH                 # 86.2
PLATE_D = MARGIN * 2 + SCREEN_BAND + ROWS * PITCH   # 93.15
GRID_Y0 = MARGIN + SCREEN_BAND
WIN_CX = PLATE_W / 2
WIN_CY = MARGIN + SCREEN_BAND / 2

CASE_W = PLATE_W + 2 * WALL
CASE_D = PLATE_D + 2 * WALL

# ---------------------------------------------------------------- font OS
FONT_DIR = r"C:\Windows\Fonts"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    for candidate in (name, "segoeui.ttf", "arial.ttf"):
        path = os.path.join(FONT_DIR, candidate)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


bold = lambda s: font("segoeuib.ttf", s)      # noqa: E731
regular = lambda s: font("segoeui.ttf", s)    # noqa: E731
mono = lambda s: font("consola.ttf", s)       # noqa: E731

# ---------------------------------------------------------------- warna
INK = "#0f172a"
MUTED = "#64748b"
BOARD_FILL = "#f8fafc"
BOARD_LINE = "#94a3b8"
PAD_FILL = "#e2e8f0"
PAD_LINE = "#64748b"
KEY_WIRE = "#2563eb"
SWITCH_INK = "#1e293b"
GND = "#475569"
OLED_LINE = "#0d9488"
PWR = "#dc2626"

KEYS = [
    ("K1", "MUTE"), ("K2", "VOL-"), ("K3", "VOL+"), ("K4", "PLAY"),
    ("K5", "PREV"), ("K6", "NEXT"), ("K7", "BRI-"), ("K8", "BRI+"),
    ("K9", "COPY"), ("K10", "PASTE"), ("K11", "UNDO"), ("K12", "NAV"),
]

OLED_ROWS = [
    ("3V3", "VCC", "3.3 V", PWR),
    ("GND", "GND", "0 V", GND),
    ("IO33", "SDA", "data", OLED_LINE),
    ("IO35", "SCL", "clock", OLED_LINE),
]


# ================================================================ MOCK OLED
OLED_FG = (150, 236, 255)
OLED_BG = (7, 11, 15)


def _text(d, s, x, y, color):
    for ch in s:
        glyph = font5x7.FONT.get(ord(ch)) or font5x7.FONT[0x3F]
        for col in range(5):
            bits = glyph[col]
            for row in range(7):
                if bits & (1 << row):
                    d.point((x + col, y + row), fill=color)
        x += font5x7.ADVANCE
    return x


def _box(d, x, y, w, h, color):
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=color)


def _fill(d, x, y, w, h, color):
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=color)


def _face(d, mood):
    """Wajah companion: gambar sama persis dengan ui.py."""
    x0, y0 = 2, 16
    _box(d, x0, y0, 24, 24, OLED_FG)
    for ex in (7, 16):
        if mood == "tidur":
            d.line([ex, 25, ex + 2, 25], fill=OLED_FG)
        elif mood == "senang":
            d.point((ex, 25), fill=OLED_FG)
            d.point((ex + 1, 24), fill=OLED_FG)
            d.point((ex + 2, 25), fill=OLED_FG)
        else:
            _fill(d, ex, 24, 3, 3, OLED_FG)

    if mood == "senang":
        d.line([11, 32, 14, 32], fill=OLED_FG)
        d.point((10, 31), fill=OLED_FG)
        d.point((15, 31), fill=OLED_FG)
        d.point((5, 29), fill=OLED_FG)
        d.point((22, 29), fill=OLED_FG)
    elif mood == "tidur":
        _fill(d, 12, 32, 3, 2, OLED_FG)
    else:
        d.line([10, 32, 15, 32], fill=OLED_FG)


def oled_mock(state: str) -> Image.Image:
    """Satu layar 128x64 sesuai kondisi."""
    cfg = {
        "boot": dict(layer="0 MEDIA", up="0:00", last="--", mood="diam",
                     word="SIAP", idle="IDLE 0S", cnt=0, grid=(), log=()),
        "aktif": dict(layer="0 MEDIA", up="4:07", last="PASTE", mood="senang",
                      word="ASYIK", idle="IDLE 0S", cnt=42,
                      grid=(5, 9), log=("PASTE", "VOL+", "MUTE")),
        "layer1": dict(layer="1 NAV", up="9:31", last="LEFT", mood="senang",
                       word="ASYIK", idle="IDLE 0S", cnt=57,
                       grid=(4, 5, 11), log=("LEFT", "NAV", "PASTE")),
        "tidur": dict(layer="0 MEDIA", up="12:48", last="LEFT", mood="tidur",
                      word="TIDUR", idle="IDLE 3M", cnt=57,
                      grid=(), log=("LEFT", "NAV", "PASTE")),
    }[state]

    img = Image.new("RGB", (128, 64), OLED_BG)
    d = ImageDraw.Draw(img)

    # bar kepala inverted
    _fill(d, 0, 0, 128, 8, OLED_FG)
    _text(d, "L" + cfg["layer"], 2, 0, OLED_BG)
    _text(d, cfg["up"], 128 - len(cfg["up"]) * 6 - 2, 0, OLED_BG)

    _text(d, "LAST: " + cfg["last"], 0, 9, OLED_FG)
    _face(d, cfg["mood"])
    _text(d, cfg["word"], 32, 17, OLED_FG)
    _text(d, cfg["idle"], 32, 25, OLED_FG)
    _text(d, "CNT %d" % cfg["cnt"], 32, 33, OLED_FG)

    for i in range(12):
        x = 4 + (i % 4) * 9
        y = 41 + (i // 4) * 8
        if i in cfg["grid"]:
            _fill(d, x, y, 8, 6, OLED_FG)
        else:
            _box(d, x, y, 8, 6, OLED_FG)

    for row, name in enumerate(cfg["log"]):
        prefix = "> " if row == 0 else "  "
        _text(d, prefix + name, 44, 41 + row * 8, OLED_FG)

    return img


def oled_states():
    """4 kondisi layar berdampingan, dengan keterangan."""
    states = [
        ("boot", "baru menyala"),
        ("aktif", "baru menekan PASTE"),
        ("layer1", "K12 ditahan -> layer NAV"),
        ("tidur", "idle 3 menit"),
    ]
    SCALE = 3
    tile_w, tile_h = 128 * SCALE, 64 * SCALE
    gap = 26
    top = 108
    W = gap + len(states) * (tile_w + gap)
    H = top + tile_h + 62

    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((gap, 20), "TAMPILAN OLED 128×64", font=bold(30), fill=INK)
    d.text((gap, 62), "Empat kondisi: boot, baru dipakai, layer navigasi, dan saat idle.",
           font=regular(16), fill=MUTED)

    for i, (state, caption) in enumerate(states):
        x = gap + i * (tile_w + gap)
        mock = oled_mock(state).resize((tile_w, tile_h), Image.NEAREST)
        d.rectangle([x - 3, top - 3, x + tile_w + 2, top + tile_h + 2],
                    fill="#0b0f14", outline="#334155", width=2)
        img.paste(mock, (x, top))
        d.text((x, top + tile_h + 10), caption, font=regular(16), fill=MUTED)

    return img


# ================================================================ WIRING MAP
def wiring_svg_like():
    W, H = 1700, 1450
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.text((90, 52), "WIRING MAP  —  Macropad ESP32-S2 Mini", font=bold(42), fill=INK)
    d.text(
        (90, 112),
        "12 tombol, 1 pin per tombol (tanpa dioda) + OLED 0.96\" di I2C",
        font=regular(22), fill=MUTED,
    )
    d.text(
        (90, 148),
        "Posisi pin di gambar ini diurutkan agar mudah dibaca, bukan tata letak fisik board — di board asli ikuti label di silkscreen.",
        font=regular(17), fill="#94a3b8",
    )

    bx0, by0, bx1, by1 = 90, 195, 470, 1235
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=18, fill=BOARD_FILL,
                        outline=BOARD_LINE, width=3)
    d.text((280, 232), "ESP32-S2 Mini", font=bold(26), fill=INK, anchor="mm")
    d.text((280, 268), "USB-C  ->  PC", font=regular(17), fill=MUTED, anchor="mm")

    pad_x0, pad_x1 = 470, 548
    wire_x1 = 700
    sw_right = 790
    bus_x = 930

    def pad(y, label):
        d.rounded_rectangle([pad_x0, y - 18, pad_x1, y + 18], radius=7,
                            fill=PAD_FILL, outline=PAD_LINE, width=2)
        d.text(((pad_x0 + pad_x1) / 2, y), label, font=mono(17), fill=INK, anchor="mm")

    # ---- 12 baris tombol
    key_y = [300 + i * 50 for i in range(12)]
    for (name, fn), y in zip(KEYS, key_y):
        pad(y, "IO" + name[1:])
        d.line([pad_x1, y, wire_x1, y], fill=KEY_WIRE, width=3)
        d.line([wire_x1, y - 17, wire_x1, y + 17], fill=SWITCH_INK, width=4)
        d.line([sw_right, y - 17, sw_right, y + 17], fill=SWITCH_INK, width=4)
        d.line([wire_x1 + 5, y + 12, sw_right - 6, y - 15], fill=SWITCH_INK, width=4)
        d.line([sw_right, y, bus_x, y], fill=GND, width=3)
        d.ellipse([bus_x - 5, y - 5, bus_x + 5, y + 5], fill=GND)
        d.text((560, y - 26), name, font=bold(19), fill=INK)
        fw = d.textlength(name, font=bold(19))
        d.text((560 + fw + 8, y - 24), "· " + fn, font=regular(16), fill=MUTED)

    d.line([bus_x, key_y[0], bus_x, 1160], fill=GND, width=4)

    # ---- pemisah bagian OLED
    d.line([115, 890, 445, 890], fill="#cbd5e1", width=2)
    d.text((280, 916), "OLED  128x64", font=bold(18), fill=MUTED, anchor="mm")

    # ---- kotak OLED
    ex0, ex1, ey0, ey1 = wire_x1, 870, 925, 1125
    d.rounded_rectangle([ex0, ey0, ex1, ey1], radius=14, fill="#f0fdfa",
                        outline=OLED_LINE, width=3)
    d.text(((ex0 + ex1) / 2, ey0 - 12), "SSD1306", font=bold(20), fill=OLED_LINE,
           anchor="ms")

    oled_y = [950 + i * 50 for i in range(4)]
    for (pin, pname, note, colour), y in zip(OLED_ROWS, oled_y):
        pad(y, pin)
        d.line([pad_x1, y, ex0, y], fill=colour, width=3)
        d.ellipse([ex0 - 5, y - 5, ex0 + 5, y + 5], fill=colour)
        d.text((ex0 + 16, y), pname, font=bold(17), fill=OLED_LINE, anchor="lm")
        d.text((ex0 + 62, y + 1), note, font=regular(14), fill="#5eead4", anchor="lm")

    # ---- bus GND -> pad
    d.line([bus_x, 1160, pad_x1, 1160], fill=GND, width=4)
    pad(1160, "GND")
    d.text((560, 1130), "bus GND  (semua GND board = jalur yang sama)",
           font=regular(16), fill=GND)

    # ---- legenda
    ly = 1270
    d.text((90, ly), "CARA BACA", font=bold(20), fill=INK)
    d.line([100, ly + 42, 160, ly + 42], fill=KEY_WIRE, width=4)
    d.text((176, ly + 34), "kabel sinyal tombol (pin -> kaki saklar)", font=regular(18), fill=INK)
    d.line([100, ly + 78, 160, ly + 78], fill=GND, width=4)
    d.text((176, ly + 70), "GND (kaki saklar kedua, dan GND OLED)", font=regular(18), fill=INK)
    d.line([100, ly + 114, 160, ly + 114], fill=OLED_LINE, width=4)
    d.text((176, ly + 106), "I2C: SDA + SCL ke OLED (plus 3V3)", font=regular(18), fill=INK)

    d.text((90, 1402), "Detail pin dan urutan tombol ada di  hardware/wiring.md  dan  README.md",
           font=regular(17), fill="#94a3b8")
    return img


# ================================================================ TAMPAK ATAS
def layout_view():
    S = 11.8                    # px per mm (supaya OLED 2x pas)
    margin = 70
    W = int(CASE_W * S) + 2 * margin
    H = int(CASE_D * S) + 2 * margin + 130

    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.text((margin, 34), "TAMPAK ATAS", font=bold(38), fill=INK)
    d.text((margin, 86),
           f"case {CASE_W:.0f} × {CASE_D:.0f} × {2 + 14 + PLATE_T:.0f} mm   ·   "
           f"pitch {PITCH} mm   ·   keycap 1u",
           font=regular(20), fill=MUTED)

    ox, oy = margin, 130

    def X(v):
        return ox + v * S

    def Y(v):
        return oy + v * S

    d.rounded_rectangle([X(0) + 6, Y(0) + 8, X(CASE_W) + 6, Y(CASE_D) + 8],
                        radius=22, fill="#e2e8f0")
    d.rounded_rectangle([X(0), Y(0), X(CASE_W), Y(CASE_D)],
                        radius=22, fill="#f1f5f9", outline="#94a3b8", width=3)
    d.rounded_rectangle([X(WALL), Y(WALL), X(CASE_W - WALL), Y(CASE_D - WALL)],
                        radius=12, outline="#cbd5e1", width=2)

    # jendela layar + isi layar (mock 2x)
    wx0 = WALL + WIN_CX - WIN_W / 2
    wy0 = WALL + WIN_CY - WIN_H / 2
    d.rounded_rectangle([X(wx0), Y(wy0), X(wx0 + WIN_W), Y(wy0 + WIN_H)],
                        radius=4, fill="#0b0f14", outline="#334155", width=2)

    mock = oled_mock("aktif")
    ax0 = WALL + WIN_CX - ACTIVE_W / 2
    ay0 = WALL + WIN_CY - ACTIVE_H / 2
    target = (int(ACTIVE_W * S), int(ACTIVE_H * S))
    img.paste(mock.resize(target, Image.NEAREST), (int(X(ax0)), int(Y(ay0))))

    # keycap 1u
    cap = 18.0
    for r in range(ROWS):
        for c in range(COLS):
            cx = WALL + MARGIN + c * PITCH + PITCH / 2
            cy = WALL + GRID_Y0 + r * PITCH + PITCH / 2
            d.rounded_rectangle(
                [X(cx - cap / 2), Y(cy - cap / 2), X(cx + cap / 2), Y(cy + cap / 2)],
                radius=8, fill="#ffffff", outline="#475569", width=3)
            d.rounded_rectangle(
                [X(cx - cap / 2) + 6, Y(cy - cap / 2) + 6,
                 X(cx + cap / 2) - 6, Y(cy + cap / 2) - 6],
                radius=6, outline="#e2e8f0", width=2)
            label = KEYS[r * COLS + c][1]
            size = 24 if len(label) <= 5 else 19
            d.text((X(cx), Y(cy)), label, font=bold(size), fill=INK, anchor="mm")
            d.text((X(cx - cap / 2) + 9, Y(cy - cap / 2) + 5),
                   f"K{r * COLS + c + 1}", font=mono(14), fill="#94a3b8")

    # celah USB-C di dinding atas
    d.rounded_rectangle([X(CASE_W / 2 - 7), Y(-1), X(CASE_W / 2 + 7), Y(2)],
                        radius=6, fill="#94a3b8")
    d.text((X(CASE_W / 2 + 9), Y(1.2)), "USB-C", font=bold(15), fill=MUTED, anchor="lm")

    d.text((margin, H - 46),
           "case.scad menghasilkan bentuk ini (plate + bak bawah, tanpa sekrup).",
           font=regular(17), fill="#94a3b8")
    return img


# ================================================================ PLATE 1:1
MM = 300 / 25.4   # px per mm pada 300 dpi


def mm(v: float) -> float:
    return v * MM


# dua versi mekanik: MX (19.05 mm) dan tactile 6x6 (15 mm)
VARIANTS = {
    "mx": dict(
        pitch=19.05, hole=14.05, round_hole=False,
        plate_w=PLATE_W, plate_d=PLATE_D,
        title="4x3 MX 19.05 mm", note="pitch 19.05  ·  lubang 14.05 persegi  ·  jendela 24 x 13",
    ),
    "tactile": dict(
        pitch=15.0, hole=7.0, round_hole=True,
        plate_w=70.0, plate_d=81.0,
        title="4x3 TACTILE 15 mm", note="pitch 15  ·  lubang 7 mm bulat  ·  jendela 24 x 13",
    ),
}


def plate_template(kind: str):
    v = VARIANTS[kind]
    plate_w, plate_d = v["plate_w"], v["plate_d"]
    pitch, hole = v["pitch"], v["hole"]
    grid_y0 = MARGIN + SCREEN_BAND
    win_cx = plate_w / 2
    win_cy = MARGIN + SCREEN_BAND / 2

    border = 15.0
    cw = plate_w + border * 2
    ch = plate_d + border * 2
    W, H = int(round(mm(cw))), int(round(mm(ch)))
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    ox, oy = mm(border), mm(border)

    def X(x):
        return ox + mm(x)

    def Y(y):
        return oy + mm(y)

    d.text((mm(3), mm(3.5)), "TEMPLATE PLATE 1:1   ·   " + v["title"] + "   +   jendela OLED",
           font=bold(int(mm(3.2))), fill=INK)
    d.text((mm(3), mm(8.6)),
           "Cetak 100% / actual size - JANGAN 'fit to page'. Cek garis 50 mm di bawah.",
           font=regular(int(mm(2.4))), fill=MUTED)

    d.rectangle([X(0), Y(0), X(plate_w), Y(plate_d)], outline="#334155",
                width=max(2, int(mm(0.35))))

    teal = "#0d9488"
    d.rectangle([X(win_cx - WIN_W / 2), Y(win_cy - WIN_H / 2),
                 X(win_cx + WIN_W / 2), Y(win_cy + WIN_H / 2)],
                outline=teal, width=max(2, int(mm(0.35))))

    # footprint modul OLED (27.3 x 27.3) - garis putus-putus
    mw = 27.3
    x0, y0 = win_cx - mw / 2, win_cy - mw / 2
    step, x = 2.0, 0.0
    dash = max(1, int(mm(0.2)))
    while x < mw:
        xe = x0 + min(x + 1.2, mw)
        d.line([X(x0 + x), Y(y0), X(xe), Y(y0)], fill=teal, width=dash)
        d.line([X(x0 + x), Y(y0 + mw), X(xe), Y(y0 + mw)], fill=teal, width=dash)
        d.line([X(x0), Y(y0 + x), X(x0), Y(y0 + min(x + 1.2, mw))], fill=teal, width=dash)
        d.line([X(x0 + mw), Y(y0 + x), X(x0 + mw), Y(y0 + min(x + 1.2, mw))], fill=teal,
               width=dash)
        x += step

    d.text((X(win_cx), Y(win_cy + WIN_H / 2 - 0.6)), "OLED", font=bold(int(mm(2.0))),
           fill=teal, anchor="md")
    d.text((X(2.2), Y(1.1)),
           "modul OLED 27.3 x 27.3 -> tempel di bawah plate (kaca di tengah jendela)",
           font=regular(int(mm(1.9))), fill=teal)

    purple = "#7c3aed"
    for r in range(ROWS):
        for c in range(COLS):
            cx = MARGIN + c * pitch + pitch / 2
            cy = grid_y0 + r * pitch + pitch / 2
            if v["round_hole"]:
                d.ellipse([X(cx - hole / 2), Y(cy - hole / 2),
                           X(cx + hole / 2), Y(cy + hole / 2)],
                          outline=INK, width=max(2, int(mm(0.3))))
                d.text((X(cx), Y(cy)), f"K{r * COLS + c + 1}",
                       font=mono(int(mm(2.0))), fill=purple, anchor="mm")
            else:
                d.rectangle([X(cx - hole / 2), Y(cy - hole / 2),
                             X(cx + hole / 2), Y(cy + hole / 2)],
                            outline=INK, width=max(2, int(mm(0.3))))
                d.text((X(cx - hole / 2 + 0.6), Y(cy - hole / 2 + 0.5)),
                       f"K{r * COLS + c + 1}", font=mono(int(mm(2.0))), fill=purple)

    cal_y = mm(border + plate_d + 6)
    d.line([X(0), cal_y, X(50), cal_y], fill=INK, width=max(2, int(mm(0.3))))
    for xv in (0, 50):
        d.line([X(xv), cal_y - mm(1.2), X(xv), cal_y + mm(1.2)], fill=INK,
               width=max(2, int(mm(0.3))))
    d.text((X(25), cal_y - mm(4.2)), "50 mm", font=regular(int(mm(2.4))), fill=INK,
           anchor="ma")
    d.text((X(0), cal_y + mm(4.4)), v["note"],
           font=regular(int(mm(2.2))), fill=MUTED)
    return img

def main():
    os.makedirs(HW, exist_ok=True)

    wiring = wiring_svg_like()
    wiring.save(os.path.join(HW, "wiring.png"), optimize=True)

    layout = layout_view()
    layout.save(os.path.join(HW, "layout.png"), optimize=True)

    states = oled_states()
    states.save(os.path.join(HW, "oled_states.png"), optimize=True)

    print("wiring.png         ", wiring.size)
    print("layout.png         ", layout.size)
    print("oled_states.png    ", states.size)

    for kind in ("mx", "tactile"):
        plate = plate_template(kind)
        name = f"plate_{kind}_1to1"
        plate.save(os.path.join(HW, name + ".png"), optimize=True)
        plate.save(os.path.join(HW, name + ".pdf"), "PDF", resolution=300)
        print(f"{name}.png    ", plate.size,
              f"({plate.width / MM:.1f} x {plate.height / MM:.1f} mm)")


if __name__ == "__main__":
    main()
