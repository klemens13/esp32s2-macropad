# =============================================================================
#  code.py - KEYMAP macropad ESP32-S2 Mini (12 tombol + OLED status)
#
#  Dijalankan otomatis oleh CircuitPython saat board dihidupkan.
#  Konfigurasi pin ada di kb.py, gambar layar ada di ui.py.
#  Ubah isi file ini untuk mengganti fungsi tombol, lalu simpan; board akan
#  restart sendiri dan keymap baru langsung aktif.
#
#  Tata letak fisik:
#
#     +------------------------------------+
#     |            OLED 128x64             |   <- status + companion
#     +---------+---------+---------+------+
#     |  MUTE   |  VOL-   |  VOL+   | PLAY |
#     +---------+---------+---------+------+
#     |  PREV   |  NEXT   |  BRI-   | BRI+ |
#     +---------+---------+---------+------+
#     |  COPY   |  PASTE  |  UNDO   | NAV  |
#     +---------+---------+---------+------+
#
#  NAV = tahan K12 untuk masuk layer navigasi (HOME/END/panah/PGUP/PGDN/DEL).
# =============================================================================

import busio

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.modules.layers import Layers
from kmk.extensions.media_keys import MediaKeys

import kb
import ui
from ssd1306 import SSD1306

# -----------------------------------------------------------------------------
# Keyboard + scanner
# -----------------------------------------------------------------------------
keyboard = KMKKeyboard()
keyboard.matrix = kb.make_scanner()

# -----------------------------------------------------------------------------
# Modul & extension
#   MediaKeys() WAJIB dibuat SEBELUM KC.MUTE / KC.VOLU / KC.MNXT / KC.BRIU
#   dipakai - extension inilah yang mendaftarkan keycode tersebut.
# -----------------------------------------------------------------------------
media = MediaKeys()
layers = Layers()

keyboard.modules = [layers]
keyboard.extensions = [media]

# -----------------------------------------------------------------------------
# Keymap
#   _______ = tembus ke layer di bawahnya (transparan)
#   KC.MO(1) = tahan tombol ini untuk pindah ke layer 1 (navigasi)
#
#   12 tombol = urutan yang sama dengan KEY_PINS di kb.py.
#   Tiap baris kode di bawah = satu baris fisik tombol.
# -----------------------------------------------------------------------------
_______ = KC.TRNS

keyboard.keymap = [
    # ---------------------------------------------------------- Layer 0: media
    [
        # K1        K2          K3          K4
        KC.MUTE,    KC.VOLD,    KC.VOLU,    KC.MPLY,
        # K5        K6          K7          K8
        KC.MPRV,    KC.MNXT,    KC.BRIU,    KC.BRID,
        # K9        K10         K11         K12
        KC.LCTRL(KC.C), KC.LCTRL(KC.V), KC.LCTRL(KC.Z), KC.MO(1),
    ],

    # ------------------------------------------------ Layer 1: navigasi/edit
    #   K12 tidak dipakai di layer ini: selama K12 ditahan, posisinya sudah
    #   "terpakai" oleh KC.MO(1), jadi isinya dibiarkan tembus.
    [
        # K1        K2          K3          K4
        _______,    KC.HOME,    KC.UP,      KC.END,
        # K5        K6          K7          K8
        _______,    KC.LEFT,    KC.DOWN,    KC.RIGHT,
        # K9        K10         K11         K12
        KC.PGUP,    KC.PGDN,    KC.DEL,     _______,
    ],
]

# -----------------------------------------------------------------------------
# Label yang tampil di OLED. Samakan dengan keymap di atas kalau kamu mengubahnya.
#   label[0] = layer 0 (media), label[1] = layer 1 (navigasi)
#   Tulis singkat (maks 6 huruf) dan huruf besar semua - font OLED hanya
#   punya huruf besar + angka + sedikit simbol.
# -----------------------------------------------------------------------------
LABELS = [
    ['MUTE', 'VOL-', 'VOL+', 'PLAY',
     'PREV', 'NEXT', 'BRI-', 'BRI+',
     'COPY', 'PASTE', 'UNDO', 'NAV'],
    ['MUTE', 'HOME', 'UP', 'END',
     'PREV', 'LEFT', 'DOWN', 'RIGHT',
     'PGUP', 'PGDN', 'DEL', 'NAV'],
]

LAYER_NAMES = ['MEDIA', 'NAV']

# -----------------------------------------------------------------------------
# OLED (opsional)
#   Kalau OLED tidak terpasang / tidak terdeteksi, macropad tetap jalan sebagai
#   keyboard biasa; pesannya muncul di REPL.
# -----------------------------------------------------------------------------
if kb.USE_OLED:
    try:
        i2c = busio.I2C(kb.OLED_SCL, kb.OLED_SDA, frequency=kb.OLED_FREQ)

        while not i2c.try_lock():
            pass
        found = i2c.scan()
        i2c.unlock()

        addr = None
        for candidate in (kb.OLED_ADDR, 0x3D, 0x3C):
            if candidate in found:
                addr = candidate
                break

        if addr is None:
            print('OLED tidak terdeteksi. Alamat I2C yang menjawab:', found)
        else:
            oled = SSD1306(i2c, addr)
            keyboard.modules.append(ui.Status(oled, LABELS, LAYER_NAMES))
            print('OLED OK di alamat', hex(addr))
    except Exception as err:          # jangan sampai keyboard ikut mati
        print('OLED gagal dipakai:', err)

# -----------------------------------------------------------------------------
# Mulai.  Baris ini harus ada di paling bawah.
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    keyboard.go()
