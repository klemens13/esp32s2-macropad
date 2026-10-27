"""Driver OLED SSD1306 128x64 lewat I2C - tanpa library tambahan.

Ditulis khusus untuk proyek ini supaya firmware cukup: CircuitPython + KMK.
Tidak butuh adafruit_ssd1306 / adafruit_display_text / bundle Adafruit.

Cara pakai:
    import busio, board
    from ssd1306 import SSD1306
    oled = SSD1306(busio.I2C(board.SCL, board.SDA, frequency=400000))
    oled.text('HALO', 0, 0)
    oled.flush()
"""

import font5x7


class SSD1306:
    def __init__(self, i2c, addr=0x3C, width=128, height=64, contrast=0xCF):
        self.i2c = i2c
        self.addr = addr
        self.width = width
        self.height = height
        self.pages = height // 8
        self.contrast = contrast

        self.buf = bytearray(width * self.pages)
        self.dirty = set()

        # buffer kirim, dialokasikan sekali supaya tidak bikin fragmentasi heap
        self._tx_cmd = bytearray(9)
        self._tx_cmd[0] = 0x00
        self._tx_data = bytearray(1 + width)
        self._tx_data[0] = 0x40

        self._init_display()

    # ---------------------------------------------------------------- internal
    def _cmd(self, *cmds):
        buf = self._tx_cmd
        buf[0] = 0x00
        for i, c in enumerate(cmds):
            buf[1 + i] = c
        self.i2c.writeto(self.addr, buf[: 1 + len(cmds)])

    def _init_display(self):
        self._cmd(0xAE)                    # display off
        self._cmd(0xD5, 0x80)              # clock divide
        self._cmd(0xA8, self.height - 1)   # multiplex
        self._cmd(0xD3, 0x00)              # display offset
        self._cmd(0x40)                    # start line 0
        self._cmd(0x8D, 0x14)              # charge pump on
        self._cmd(0x20, 0x02)              # page addressing mode
        self._cmd(0xA1)                    # segment remap
        self._cmd(0xC8)                    # COM scan dec
        self._cmd(0xDA, 0x12)              # COM pins
        self._cmd(0x81, self.contrast)     # contrast
        self._cmd(0xD9, 0xF1)              # pre-charge
        self._cmd(0xDB, 0x40)              # VCOMH
        self._cmd(0xA4)                    # resume from RAM
        self._cmd(0xA6)                    # normal (tidak inverted)
        self._cmd(0x2E)                    # scroll off
        self._cmd(0xAF)                    # display on

    # ------------------------------------------------------------------ gambar
    def clear(self, value=0):
        for i in range(len(self.buf)):
            self.buf[i] = value
        self.dirty = set(range(self.pages))

    def pixel(self, x, y, on=True):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y >> 3) * self.width + x
            bit = 1 << (y & 7)
            if on:
                self.buf[i] |= bit
            else:
                self.buf[i] &= ~bit
            self.dirty.add(y >> 3)

    def hline(self, x, y, w, on=True):
        for i in range(w):
            self.pixel(x + i, y, on)

    def vline(self, x, y, h, on=True):
        for i in range(h):
            self.pixel(x, y + i, on)

    def rect(self, x, y, w, h, on=True):
        self.hline(x, y, w, on)
        self.hline(x, y + h - 1, w, on)
        self.vline(x, y, h, on)
        self.vline(x + w - 1, y, h, on)

    def fill_rect(self, x, y, w, h, on=True):
        for j in range(h):
            self.hline(x, y + j, w, on)

    def clear_rect(self, x, y, w, h):
        self.fill_rect(x, y, w, h, False)

    def text(self, s, x, y, on=True):
        """Tulis teks 5x7. Huruf yang tidak tersedia diganti '?'."""
        for ch in s:
            glyph = font5x7.FONT.get(ord(ch))
            if glyph is None:
                glyph = font5x7.FONT[0x3F]
            for col in range(5):
                bits = glyph[col]
                for row in range(7):
                    if bits & (1 << row):
                        self.pixel(x + col, y + row, on)
            x += font5x7.ADVANCE
        return x

    def text_right(self, s, y, on=True):
        """Teks rata kanan."""
        self.text(s, self.width - len(s) * font5x7.ADVANCE, y, on)

    # ------------------------------------------------------------------ kirim
    def flush(self, max_pages=None):
        """Kirim halaman yang berubah. max_pages membatasi jumlah per panggilan."""
        if not self.dirty:
            return 0

        pages = sorted(self.dirty)
        if max_pages is not None:
            pages = pages[:max_pages]

        for page in pages:
            self._cmd(0xB0 | page, 0x00, 0x10)
            start = page * self.width
            self._tx_data[1:] = self.buf[start:start + self.width]
            self.i2c.writeto(self.addr, self._tx_data)
            self.dirty.discard(page)

        return len(pages)
