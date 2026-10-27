"""
Generator font 5x7 untuk OLED (dipakai firmware/font5x7.py).

Alasannya: KMK + CircuitPython tidak butuh library tambahan, jadi font-nya
ikut ditulis sendiri di repo - bukan ambil dari bundle Adafruit.

Jalankan:  python tools/gen_font.py          -> tulis firmware/font5x7.py
           python tools/gen_font.py --show   -> cetak contoh render ke layar
"""

from __future__ import annotations

import argparse
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "firmware", "font5x7.py")

# setiap glyph = 7 baris x 5 kolom, '#' = pixel menyala
GLYPHS: dict[str, tuple[str, ...]] = {
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    "!": ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
    '"': (" # # ", " # # ", "     ", "     ", "     ", "     ", "     "),
    "'": ("  #  ", "  #  ", "     ", "     ", "     ", "     ", "     "),
    "%": ("##  #", "##  #", "   # ", "  #  ", " #   ", "#  ##", "#  ##"),
    "(": ("   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "),
    ")": (" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "),
    "*": ("     ", "# # #", " ### ", "#####", " ### ", "# # #", "     "),
    "+": ("     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "),
    ",": ("     ", "     ", "     ", "     ", "  ## ", "  ## ", " #   "),
    "-": ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    ".": ("     ", "     ", "     ", "     ", "     ", "  ## ", "  ## "),
    "/": ("    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "),
    ":": ("     ", "  ## ", "  ## ", "     ", "  ## ", "  ## ", "     "),
    "<": ("   # ", "  #  ", " #   ", "#    ", " #   ", "  #  ", "   # "),
    "=": ("     ", "     ", "#####", "     ", "#####", "     ", "     "),
    ">": (" #   ", "  #  ", "   # ", "    #", "   # ", "  #  ", " #   "),
    "?": (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    "0": (" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "2": (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": ("#####", "   # ", "  #  ", "   # ", "    #", "#   #", " ### "),
    "4": ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    "5": ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    "6": ("  ## ", " #   ", "#    ", "#### ", "#   #", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "),
    "8": (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    "9": (" ### ", "#   #", "#   #", " ####", "    #", "   # ", " ##  "),
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ### ", "#   #", "#    ", "#    ", "#    ", "#   #", " ### "),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ### ", "#   #", "#    ", "# ###", "#   #", "#   #", " ### "),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": (" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "J": ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "#   #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
}


def to_bytes(art: tuple[str, ...]) -> bytes:
    """7 baris x 5 kolom -> 5 byte (1 byte per kolom, bit0 = baris atas)."""
    if len(art) != 7 or any(len(row) != 5 for row in art):
        raise ValueError(f"glyph harus 7x5: {art}")
    cols = []
    for c in range(5):
        value = 0
        for r in range(7):
            if art[r][c] == "#":
                value |= 1 << r
        cols.append(value)
    return bytes(cols)


def render(text: str) -> str:
    """Render teks jadi ASCII art, untuk dicek mata manusia."""
    lines = []
    for r in range(7):
        row = []
        for ch in text:
            art = GLYPHS.get(ch, GLYPHS["?"])
            row.append(art[r])
            row.append(" ")
        lines.append("".join(row))
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true", help="cetak contoh render")
    args = ap.parse_args()

    if args.show:
        print(render("MACROPAD S2 0123456789"))
        print(render("LAST: PASTE  CNT 42  L0 MEDIA"))
        print(render("SIAP IDLE 12s TIDUR (ZzZ) ???"))
        return

    lines = [
        '"""Font bitmap 5x7 (hanya karakter ini yang tersedia).',
        "",
        "Dibuat otomatis oleh tools/gen_font.py - jangan diedit manual.",
        "Setiap glyph = 5 byte, 1 byte per kolom, bit0 = baris paling atas.",
        '"""',
        "",
        "GLYPH_WIDTH = 5",
        "GLYPH_HEIGHT = 7",
        "ADVANCE = 6  # lebar glyph + 1 px jarak antar huruf",
        "",
        "FONT = {",
    ]
    for ch in sorted(GLYPHS):
        data = to_bytes(GLYPHS[ch])
        hexed = "".join(f"\\x{b:02x}" for b in data)
        lines.append(f"    0x{ord(ch):02X}: b'{hexed}',  # {ch}")
    lines.append("}")
    lines.append("")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print(f"tulis {OUT} ({len(GLYPHS)} glyph)")


if __name__ == "__main__":
    main()
