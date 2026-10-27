# =============================================================================
#  kb.py - PETA PERANGKAT KERAS (hardware) macropad
#
#  Mendukung 3 board:
#     "s2"            ESP32-S2 Mini      (default)
#     "s3_mini"       LOLIN S3 Mini
#     "s3_supermini"  ESP32-S3 Super Mini
#
#  Cara memilih board: ubah BOARD di bawah ini. Kalau tidak mau mengedit file,
#  bisa juga lewat settings.toml di CIRCUITPY:
#     MACROPAD_BOARD = "s3_mini"
#
#  File ini HANYA mengurus "pin mana untuk apa".
#  Isi keymap (tombol jadi apa) ada di code.py.
# =============================================================================

import os

import board

from profiles import BOARDS, DEFAULT_BOARD

BOARD = (os.getenv('MACROPAD_BOARD') or DEFAULT_BOARD).strip().lower()

if BOARD not in BOARDS:
    raise ValueError(
        'MACROPAD_BOARD "%s" tidak dikenal. Pilih: %s'
        % (BOARD, ', '.join(BOARDS))
    )

PROFILE = BOARDS[BOARD]

# -----------------------------------------------------------------------------
# 12 tombol, satu kabel per tombol (tidak pakai dioda / matrix).
# Urutan: kiri -> kanan, baris atas dulu, lalu tengah, lalu bawah.
# Urutan ini HARUS sama dengan urutan di keyboard.keymap (code.py).
#
#   K1  K2  K3  K4      baris atas
#   K5  K6  K7  K8      baris tengah
#   K9  K10 K11 K12     baris bawah
#
# Nama pin per board ada di profiles.py - satu tempat yang juga dipakai oleh
# tools/make_diagrams.py, supaya gambar wiring tidak pernah beda dari firmware.
# -----------------------------------------------------------------------------
KEY_PINS = tuple(getattr(board, name) for name in PROFILE['keys'])

# -----------------------------------------------------------------------------
# OLED 0.96" SSD1306 (128x64) di I2C.
#
# Tidak punya OLED? Set USE_OLED = False - sisa firmware tetap jalan normal.
# -----------------------------------------------------------------------------
USE_OLED = True
OLED_SDA = getattr(board, PROFILE['sda'])
OLED_SCL = getattr(board, PROFILE['scl'])
OLED_ADDR = 0x3C              # 0x3D kalau modulmu memakai jumper lain
OLED_FREQ = 400000

# Catatan: modul KMK di-import di dalam make_scanner() supaya file ini tetap
# bisa dipakai sendirian oleh bringup.py (tes hardware tanpa KMK).


def make_scanner():
    """Scanner 'satu pin per tombol'.

    value_when_pressed=False  -> tombol disambung ke GND, jadi saat ditekan
                                 pin membaca False.
    pull=True                 -> pakai pull-up internal ESP32 (tidak perlu
                                 resistor tambahan).
    """
    from kmk.scanners.keypad import KeysScanner

    return KeysScanner(
        pins=KEY_PINS,
        value_when_pressed=False,
        pull=True,
        interval=0.005,  # pindai tiap 5 ms (default KMK 20 ms)
    )
