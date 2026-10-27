"""Peta pin per board - DATA SAJA, tanpa import `board`.

Dipisah begini supaya bisa dibaca juga oleh `tools/make_diagrams.py` di
komputer (yang tidak punya modul CircuitPython), sehingga gambar wiring dan
firmware tidak pernah berbeda.

Urutan `keys` = K1..K12: kiri->kanan, baris atas, tengah, bawah.
"""

BOARDS = {
    # ---------------------------------------------------------------- ESP32-S2
    "s2": dict(
        label='ESP32-S2 Mini',
        cp_board='lolin_s2_mini',
        cp_url='https://circuitpython.org/board/lolin_s2_mini/',
        chip='ESP32-S2FN4R2',
        ble=False,
        keys=(
            'IO1', 'IO2', 'IO3', 'IO4',
            'IO5', 'IO6', 'IO7', 'IO8',
            'IO9', 'IO10', 'IO11', 'IO12',
        ),
        sda='IO33',
        scl='IO35',
        note='LED biru di IO15, tombol BOOT di IO0 - jangan dipakai untuk tombol.',
    ),

    # ------------------------------------------------------------ LOLIN S3 Mini
    "s3_mini": dict(
        label='LOLIN S3 Mini',
        cp_board='lolin_s3_mini',
        cp_url='https://circuitpython.org/board/lolin_s3_mini/',
        chip='ESP32-S3FH4R2',
        ble=True,
        keys=(
            'IO1', 'IO2', 'IO3', 'IO4',
            'IO5', 'IO6', 'IO7', 'IO8',
            'IO9', 'IO10', 'IO11', 'IO12',
        ),
        sda='IO35',
        scl='IO36',
        note='I2C bawaan beda dari S2 (SDA=IO35, SCL=IO36). RGB LED di IO47, BOOT di IO0.',
    ),

    # ------------------------------------------------------- S3 Super Mini
    "s3_supermini": dict(
        label='ESP32-S3 Super Mini',
        cp_board='generic_esp32s3_supermini',
        cp_url='https://circuitpython.org/board/generic_esp32s3_supermini/',
        chip='ESP32-S3FH4R2',
        ble=True,
        # hanya pin "aman": tanpa strapping, flash, USB, UART, atau LED
        keys=(
            'IO1', 'IO2', 'IO4', 'IO5',
            'IO6', 'IO7', 'IO8', 'IO15',
            'IO16', 'IO17', 'IO18', 'IO21',
        ),
        sda='IO33',
        scl='IO34',
        note='Hindari IO0 (BOOT), IO43/IO44 (UART), IO48 (RGB LED + LED merah), IO39-IO46 (JTAG/strapping).',
    ),
}

DEFAULT_BOARD = 's2'
