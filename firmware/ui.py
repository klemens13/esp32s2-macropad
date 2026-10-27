"""Layar status + companion kecil untuk macropad (SSD1306 128x64).

Isi layar:
    baris atas   : layer aktif + waktu sejak board menyala
    baris kedua  : tombol yang terakhir ditekan
    kiri tengah  : wajah companion (berkedip, senang saat dipakai, tidur saat idle)
    kanan tengah : mood, lama idle, jumlah tekanan
    bawah        : peta 4x3 tombol (kotak terisi = sedang ditekan) + 3 tombol terakhir

Modul ini menumpang di main loop KMK lewat Module.after_matrix_scan(), jadi tidak
perlu thread atau timer sendiri. Pengiriman ke OLED dibatasi 1 halaman per putaran
loop supaya pemindaian tombol tidak tertahan.
"""

from supervisor import ticks_ms

from kmk.modules import Module

TICK_MASK = 0x1FFFFFFF   # supervisor.ticks_ms() wrap di 2**29

MOOD_OK = 0
MOOD_HAPPY = 1
MOOD_SLEEP = 2

MOOD_WORDS = ('SIAP', 'ASYIK', 'TIDUR')

IDLE_HAPPY_MS = 900       # di bawah ini wajah senang
IDLE_SLEEP_MS = 60000     # di atas ini companion tidur
BLINK_PERIOD = 4300
BLINK_LEN = 120


def _diff(now, then):
    """Selisih ticks_ms yang tetap benar setelah wrap."""
    return (now - then) & TICK_MASK


class Status(Module):
    def __init__(self, oled, labels, layer_names):
        self.oled = oled
        self.labels = labels
        self.layer_names = layer_names

        self.layer = 0
        self.count = 0
        self.last = '--'
        self.hist = []
        self.pressed = [False] * len(labels[0])

        self.boot_ms = ticks_ms()
        self.last_press = self.boot_ms

        # nilai yang terakhir digambar (biar tidak menggambar ulang tiap loop)
        self._c_layer = None
        self._c_uptime = None
        self._c_last = None
        self._c_mood = None
        self._c_blink = None
        self._c_idle_s = None
        self._c_count = None

        self._dirty_grid = True
        self._dirty_log = True

    # ------------------------------------------------------------------ util
    def _label(self, layer, coord):
        rows = self.labels[layer] if layer < len(self.labels) else self.labels[0]
        if 0 <= coord < len(rows):
            return rows[coord]
        return '--'

    def _layer_name(self, layer):
        if layer < len(self.layer_names):
            return self.layer_names[layer]
        return 'L%d' % layer

    def _current_layer(self, keyboard):
        layer = keyboard.active_layers[0]
        return layer if layer < len(self.labels) else len(self.labels) - 1

    # --------------------------------------------------------------- gambar
    def _draw_header(self, uptime, layer):
        oled = self.oled
        # bar kepala dibuat inverted (putih) supaya kebaca seperti "title bar"
        oled.clear_rect(0, 0, oled.width, 8)
        oled.fill_rect(0, 0, oled.width, 8)
        oled.text('L%d %s' % (layer, self._layer_name(layer)), 2, 0, False)
        oled.text(uptime, oled.width - len(uptime) * 6 - 2, 0, False)

    def _draw_last(self):
        oled = self.oled
        oled.clear_rect(0, 8, oled.width, 8)
        oled.text('LAST: ' + self.last, 0, 9)

    def _draw_face(self, mood, blink):
        oled = self.oled
        oled.clear_rect(2, 16, 24, 24)
        oled.rect(2, 16, 24, 24)

        # mata
        for ex in (7, 16):
            if blink or mood == MOOD_SLEEP:
                oled.hline(ex, 25, 3)
            elif mood == MOOD_HAPPY:
                oled.pixel(ex, 25)
                oled.pixel(ex + 1, 24)
                oled.pixel(ex + 2, 25)
            else:
                oled.fill_rect(ex, 24, 3, 3)

        # mulut (+ pipi kalau senang)
        if mood == MOOD_HAPPY:
            oled.hline(11, 32, 4)
            oled.pixel(10, 31)
            oled.pixel(15, 31)
            oled.pixel(5, 29)
            oled.pixel(22, 29)
        elif mood == MOOD_SLEEP:
            oled.fill_rect(12, 32, 3, 2)
        else:
            oled.hline(10, 32, 6)

    def _draw_info(self, mood, idle_s):
        oled = self.oled
        oled.clear_rect(30, 16, 98, 24)
        oled.text(MOOD_WORDS[mood], 32, 17)
        if idle_s < 60:
            oled.text('IDLE %dS' % idle_s, 32, 25)
        else:
            oled.text('IDLE %dM' % (idle_s // 60), 32, 25)
        oled.text('CNT %d' % self.count, 32, 33)

    def _draw_grid(self):
        oled = self.oled
        oled.clear_rect(2, 40, 40, 24)
        for i in range(len(self.pressed)):
            x = 4 + (i % 4) * 9
            y = 41 + (i // 4) * 8
            if self.pressed[i]:
                oled.fill_rect(x, y, 8, 6)
            else:
                oled.rect(x, y, 8, 6)

    def _draw_log(self):
        oled = self.oled
        oled.clear_rect(44, 40, 84, 24)
        for row in range(3):
            if row < len(self.hist):
                prefix = '> ' if row == 0 else '  '
                oled.text(prefix + self.hist[row], 44, 41 + row * 8)

    # ---------------------------------------------------------------- update
    def redraw(self, keyboard, full=False):
        now = ticks_ms()
        layer = self._current_layer(keyboard)

        idle_ms = _diff(now, self.last_press)
        if idle_ms > IDLE_SLEEP_MS:
            mood = MOOD_SLEEP
        elif idle_ms < IDLE_HAPPY_MS:
            mood = MOOD_HAPPY
        else:
            mood = MOOD_OK

        blink = (mood == MOOD_OK) and ((now % BLINK_PERIOD) < BLINK_LEN)

        uptime_s = _diff(now, self.boot_ms) // 1000
        uptime = '%d:%02d' % (uptime_s // 60, uptime_s % 60)
        idle_s = idle_ms // 1000

        if full or layer != self._c_layer or uptime != self._c_uptime:
            self._c_layer = layer
            self._c_uptime = uptime
            self._draw_header(uptime, layer)

        if full or self.last != self._c_last:
            self._c_last = self.last
            self._draw_last()

        face_changed = full or mood != self._c_mood or blink != self._c_blink
        if face_changed:
            self._c_mood = mood
            self._c_blink = blink
            self._draw_face(mood, blink)

        if (face_changed or idle_s != self._c_idle_s
                or self.count != self._c_count):
            self._c_idle_s = idle_s
            self._c_count = self.count
            self._draw_info(mood, idle_s)

        if full or self._dirty_grid:
            self._dirty_grid = False
            self._draw_grid()

        if full or self._dirty_log:
            self._dirty_log = False
            self._draw_log()

        # maksimal 1 halaman per putaran loop (kecuali saat boot)
        self.oled.flush(None if full else 1)

    # -------------------------------------------------------------- hook KMK
    def during_bootup(self, keyboard):
        self.oled.clear()
        self.redraw(keyboard, full=True)

    def process_key(self, keyboard, key, is_pressed, int_coord):
        if int_coord is not None and 0 <= int_coord < len(self.pressed):
            if is_pressed:
                name = self._label(self._current_layer(keyboard), int_coord)
                self.pressed[int_coord] = True
                self.count += 1
                self.last = name
                self.hist.insert(0, name)
                del self.hist[3:]
                self.last_press = ticks_ms()
                self._dirty_grid = True
                self._dirty_log = True
            else:
                self.pressed[int_coord] = False
                self._dirty_grid = True
        return key

    def after_matrix_scan(self, keyboard):
        self.redraw(keyboard)
