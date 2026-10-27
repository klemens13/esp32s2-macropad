// =============================================================================
//  case_mx.scad - VERSI MX (switch mekanikal, 12 x 14x14 mm)
//  Case macropad 4x3 + OLED 0.96" untuk ESP32-S2 Mini.
//  Satuan: milimeter.  Parameter di bawah ini juga dipakai di
//  hardware/plate_mx_1to1.pdf dan tools/make_diagrams.py - jaga tetap sama.
//
//  Versi tactile ada di case_tactile.scad (lebih tipis, lubang 7 mm).
//
//  CARA PAKAI (OpenSCAD):
//    1. buka file ini
//    2. ubah PART di bawah ini, lalu Render (F6) dan Export STL
//         PART = "plate"  -> plate atas (tempat switch + jendela OLED)
//         PART = "tray"   -> bak bawah
//         PART = "both"   -> pratinjau, keduanya sekaligus
//
//  CATATAN: desain ini titik awal dan belum diuji cetak oleh pembuat file.
//  Cetak plate dulu (kira-kira 1 jam), coba pasang 1 switch, baru cetak tray.
//  Kalau switch terlalu longgar/ketat, ubah key_hole (14.05 -> 13.95 / 14.15).
// =============================================================================

PART = "both";          // "plate" | "tray" | "both"

// ---------------------------------------------------------------- parameter
pitch     = 19.05;      // jarak antar titik tengah switch (MX)
key_hole  = 14.05;      // lubang switch
margin    = 5.0;        // tepi plate -> lubang switch pertama

cols      = 4;
rows      = 3;

SCREEN_BAND = 26.0;     // tinggi area OLED di atas grid tombol
screen_win_w = 24.0;    // jendela layar (active area OLED 0.96" = 21.7 x 11.2)
screen_win_h = 13.0;

plate_t   = 3.0;        // tebal plate
wall      = 2.4;        // tebal dinding
floor_t   = 2.0;        // tebal dasar
inner_h   = 14.0;       // ruang di bawah plate (modul OLED ~4 mm + kabel)
lip_w     = 2.0;        // lebar bibir penopang plate
lip_t     = 1.2;        // tebal bibir
slack     = 0.3;        // kelonggaran cetak

usb_w     = 14.0;       // celah USB-C di dinding depan
usb_h     = 7.0;

$fn = 60;

// ---------------------------------------------------------------- turunan
plate_w = margin * 2 + cols * pitch;                 // 86.2
plate_d = margin * 2 + SCREEN_BAND + rows * pitch;   // 93.15

grid_y0 = margin + SCREEN_BAND;                      // awal baris tombol
win_cx  = plate_w / 2;
win_cy  = margin + SCREEN_BAND / 2;                  // tengah area layar

int_w = plate_w + slack;
int_d = plate_d + slack;

out_w = plate_w + 2 * wall;
out_d = plate_d + 2 * wall;
total_h = floor_t + inner_h + plate_t;

// =============================================================================
//  PLATE (atas)
// =============================================================================
module plate() {
    difference() {
        cube([plate_w, plate_d, plate_t]);

        // lubang 12 switch
        for (r = [0 : rows - 1], c = [0 : cols - 1]) {
            x = margin + c * pitch + (pitch - key_hole) / 2;
            y = grid_y0 + r * pitch + (pitch - key_hole) / 2;
            translate([x, y, -1])
                cube([key_hole, key_hole, plate_t + 2]);
        }

        // jendela OLED: modul ditempel di bawah plate, kaca menghadap jendela
        translate([win_cx - screen_win_w / 2, win_cy - screen_win_h / 2, -1])
            cube([screen_win_w, screen_win_h, plate_t + 2]);

        // chamfer tipis di sisi atas lubang switch (biar switch mudah masuk)
        for (r = [0 : rows - 1], c = [0 : cols - 1]) {
            x = margin + c * pitch + pitch / 2;
            y = grid_y0 + r * pitch + pitch / 2;
            translate([x, y, plate_t - 0.01])
                cube([key_hole + 0.8, key_hole + 0.8, 0.6], center = true);
        }
    }
}

// =============================================================================
//  TRAY (bawah)
// =============================================================================
module tray() {
    x0 = (out_w - int_w) / 2;
    y0 = (out_d - int_d) / 2;
    difference() {
        cube([out_w, out_d, total_h]);

        // 1. rongga bawah (sampai bawah bibir)
        translate([x0, y0, floor_t])
            cube([int_w, int_d, inner_h - lip_t]);

        // 2. bukaan di dalam bibir -> hanya menyisakan bibir selebar lip_w
        translate([x0 + lip_w, y0 + lip_w, floor_t + inner_h - lip_t])
            cube([int_w - 2 * lip_w, int_d - 2 * lip_w, lip_t + 0.01]);

        // 3. dudukan plate: plate masuk dari atas dan berhenti di bibir
        translate([x0, y0, floor_t + inner_h])
            cube([int_w, int_d, plate_t + 2]);

        // celah USB-C di dinding depan (-Y)
        translate([out_w / 2 - usb_w / 2, -1, floor_t])
            cube([usb_w, wall + 2, usb_h]);

        // celah buka plate di dinding belakang (+Y), untuk ujung kuku/spudger
        translate([out_w / 2 - 10, out_d - wall - 1.0, total_h - 1.4])
            cube([20, wall + 2, 1.4]);
    }
}

// =============================================================================
//  RENDER
// =============================================================================
if (PART == "plate") {
    plate();
} else if (PART == "tray") {
    tray();
} else {
    plate();
    translate([0, 0, total_h + 6]) plate();
    translate([out_w + 12, 0, 0]) tray();
}
