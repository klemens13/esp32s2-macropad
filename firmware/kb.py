# =============================================================================
#  kb.py - PETA PERANGKAT KERAS (hardware) macropad ESP32-S2 Mini
#
#  File ini HANYA mengurus "pin mana untuk apa".
#  Isi keymap (tombol jadi apa) ada di code.py.
#
#  Kalau kabelmu tidak sama dengan contoh, cukup ubah tuple di bawah ini.
# =============================================================================

import board

# -----------------------------------------------------------------------------
# 12 tombol, satu kabel per tombol (tidak pakai dioda / matrix).
# Urutan: kiri -> kanan, baris atas dulu, lalu tengah, lalu bawah.
# Urutan ini HARUS sama dengan urutan di keyboard.keymap (code.py).
#
#   K1  K2  K3  K4      baris atas
#   K5  K6  K7  K8      baris tengah
#   K9  K10 K11 K12     baris bawah
#
# Catatan board: IO15 = LED biru bawaan, IO0 = tombol BOOT, IO19/IO20 = USB.
# Jangan dipakai untuk tombol.
# -----------------------------------------------------------------------------
KEY_PINS = (
    board.IO1,  board.IO2,  board.IO3,  board.IO4,    # baris atas   -> K1..K4
    board.IO5,  board.IO6,  board.IO7,  board.IO8,    # baris tengah -> K5..K8
    board.IO9,  board.IO10, board.IO11, board.IO12,   # baris bawah  -> K9..K12
)

# -----------------------------------------------------------------------------
# OLED 0.96" SSD1306 (128x64) di bus I2C bawaan board.
# S2 Mini: SCL = IO35, SDA = IO33. Tidak butuh pin tambahan selain 2 ini.
#
# Tidak punya OLED? Set USE_OLED = False - sisa firmware tetap jalan normal.
# -----------------------------------------------------------------------------
USE_OLED = True
OLED_SCL = board.SCL          # IO35
OLED_SDA = board.SDA          # IO33
OLED_ADDR = 0x3C              # 0x3D kalau modulmu memakai jumper lain
OLED_FREQ = 400000

# Catatan: modul KMK di-import di dalam make_scanner() supaya file ini tetap
# bisa dipakai sendirian oleh bringup.py (tes hardware tanpa KMK).


def make_scanner():
    """Scanner 'satu pin per tombol'.

    value_when_pressed=False  -> tombol disambung ke GND, jadi saat ditekan
                                 pin membaca False.
    pull=True                 -> pakai pull-up internal ESP32-S2 (tidak perlu
                                 resistor tambahan).
    """
    from kmk.scanners.keypad import KeysScanner

    return KeysScanner(
        pins=KEY_PINS,
        value_when_pressed=False,
        pull=True,
        interval=0.005,  # pindai tiap 5 ms (default KMK 20 ms)
    )
