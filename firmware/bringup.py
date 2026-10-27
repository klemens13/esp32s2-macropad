# =============================================================================
#  bringup.py - TES HARDWARE (tanpa KMK, tanpa keymap)
#
#  Gunakan file ini PERTAMA KALI setelah menyolder, untuk memastikan:
#    1. CircuitPython jalan dan bisa mengetik sebagai keyboard (tes HID),
#    2. setiap tombol terbaca di pin yang benar,
#    3. OLED terdeteksi di bus I2C dan bisa menampilkan teks.
#
#  Cara pakai:
#    - copy file ini ke drive CIRCUITPY dengan nama  code.py
#      (timpa code.py yang lama), ATAU jalankan  tools\deploy.ps1 -Bringup
#    - buka REPL / serial console (lihat README bagian "Melihat output")
#    - tekan tombol satu per satu, nama tombol akan muncul di layar
#
#  Kalau semua sudah benar, kembalikan code.py versi keymap (tools\deploy.ps1).
# =============================================================================

import time

import busio
import digitalio
import usb_hid

import kb
from ssd1306 import SSD1306

KEY_NAMES = ('K1', 'K2', 'K3', 'K4', 'K5', 'K6',
             'K7', 'K8', 'K9', 'K10', 'K11', 'K12')


def build_inputs():
    """Siapkan semua pin tombol sebagai input pull-up (tombol ke GND)."""
    inputs = []
    for name, pin in zip(KEY_NAMES, kb.KEY_PINS):
        io = digitalio.DigitalInOut(pin)
        io.switch_to_input(pull=digitalio.Pull.UP)
        inputs.append((name, io))
    return inputs


def test_oled():
    """Scan I2C, lalu tampilkan teks percobaan kalau OLED ditemukan."""
    if not kb.USE_OLED:
        print('OLED: dilewati (USE_OLED = False)')
        return None

    try:
        i2c = busio.I2C(kb.OLED_SCL, kb.OLED_SDA, frequency=kb.OLED_FREQ)
        while not i2c.try_lock():
            pass
        found = i2c.scan()
        i2c.unlock()
    except Exception as err:
        print('I2C gagal dipakai:', err)
        return None

    print('I2C scan   :', [hex(a) for a in found])
    if not found:
        print('  !! tidak ada perangkat I2C. Cek kabel SDA/SCL/VCC/GND,')
        print('     dan pastikan OLED diberi 3V3 (bukan 5V).')
        return None

    addr = None
    for candidate in (kb.OLED_ADDR, 0x3D, 0x3C):
        if candidate in found:
            addr = candidate
            break
    if addr is None:
        print('  !! ada perangkat I2C tapi bukan di 0x3C/0x3D.')
        return None

    try:
        oled = SSD1306(i2c, addr)
        oled.clear()
        oled.text('OLED OK', 0, 0)
        oled.text('SSD1306 128X64', 0, 8)
        oled.rect(0, 40, 128, 22)
        oled.text('TES LAYAR', 6, 47)
        oled.flush()
        print('  -> OLED di', hex(addr), ': layar harus menampilkan teks.')
        return oled
    except Exception as err:
        print('  !! OLED tidak bisa dipakai:', err)
        return None


def hid_keyboard():
    """Cari perangkat HID keyboard bawaan CircuitPython."""
    for dev in usb_hid.devices:
        try:
            if dev.usage_page == 0x01 and dev.usage == 0x06:
                return dev
        except AttributeError:
            continue
    return None


def type_text(text):
    """Kirim ketikan mentah lewat report keyboard 8 byte (tanpa library)."""
    dev = hid_keyboard()
    if dev is None:
        print('!! HID keyboard tidak ditemukan. USB hanya untuk daya?')
        return False

    codes = {'h': 0x0B, 'a': 0x04, 'i': 0x0C}
    for ch in text:
        dev.send_report(bytes([0, 0, codes[ch], 0, 0, 0, 0, 0]))
        time.sleep(0.03)
        dev.send_report(bytes(8))          # lepas tombol
        time.sleep(0.06)
    return True


inputs = build_inputs()
print()
print('=== BRINGUP MACROPAD S2 MINI ===')
print('pin tombol dipantau :', len(inputs))

test_oled()

print()
print('kalau di bawah ini sudah ada tombol yang terbaca DITEKAN,')
print('berarti ada kabel yang short ke GND.')

for i in range(3, 0, -1):
    print('tes HID (mengetik "hai") dalam', i, 'detik - klik dulu ke editor teks...')
    time.sleep(1)
print('mengetik...')
if type_text('hai'):
    print('selesai. Kalau "hai" muncul di komputer, HID OK.')

print()
print('Sekarang tekan tombol satu per satu. Perubahan akan dicetak di bawah.')
print('(Ctrl+C di REPL untuk berhenti)')
print()

last = None
while True:
    pressed = tuple(name for name, io in inputs if not io.value)
    if pressed != last:
        if pressed:
            print('DITEKAN :', ' '.join(pressed))
        else:
            print('DITEKAN : - (semua lepas)')
        last = pressed
    time.sleep(0.01)
