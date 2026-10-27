// =============================================================================
//  case_tactile.scad - VERSI TACTILE (12 x tombol 6x6 mm)
//  Case macropad 4x3 + OLED 0.96" untuk ESP32-S2 Mini.
//  Satuan: milimeter.  Parameter di bawah ini juga dipakai di
//  hardware/plate_tactile_1to1.pdf dan tools/make_diagrams.py - jaga tetap sama.
//
//  Bedanya dengan versi MX (case_mx.scad):
//    - pitch 15 mm (bukan 19.05), lubang tombol 7 mm (bukan 14 mm)
//    - case jauh lebih pendek: 11 mm (bukan 19 mm)
//    - plate tidak "mencengkeram" switch: tombol disolder ke PCB di bawah,
//      plate hanya menutup dan menahan badan tombol dari atas
//
//  PENTING: ruang di dalam hanya ~6 mm. Solder ESP32-S2 Mini langsung ke PCB
//  (tanpa header female). Kalau mau pakai header, pakai versi MX atau naikkan
//  angka `body_h` / `floor_t` di bawah.
//
//  CARA PAKAI (OpenSCAD):
//    PART = "plate" | "tray" | "both", lalu Render (F6) dan Export STL.
//
//  CATATAN: desain ini titik awal dan belum diuji cetak oleh pembuat file.
//  Cetak plate dulu, pasang 1 tombol, cek tinggi, baru cetak tray.
// =============================================================================

PART = "both";          // "plate" | "tray" | "both"

// ---------------------------------------------------------------- parameter
pitch     = 15.0;       // jarak antar titik tengah tombol
key_hole  = 7.0;        // lubang tombol (badan 6x6, stem 3.5)
margin    = 5.0;        // tepi plate -> lubang pertama

cols      = 4;
rows      = 3;

SCREEN_BAND = 26.0;     // tinggi area OLED di atas grid tombol
screen_win_w = 24.0;
screen_win_h = 13.0;

plate_t   = 3.0;        // tebal plate / tutup
wall      = 2.4;        // tebal dinding
floor_t   = 2.0;        // tebal dasar

pcb_t     = 1.6;        // tebal PCB bolong
body_h    = 4.5;        // tinggi badan tombol 6x6 (di atas PCB)
body_gap  = 0.1;        // kelonggaran antara badan tombol dan plate

lip_w     = 2.0;        // lebar bibir penopang plate
lip_t     = 1.2;        // tebal bibir
slack     = 0.3;        // kelonggaran cetak

usb_w     = 14.0;
usb_h     = 7.0;

$fn = 60;

// ---------------------------------------------------------------- turunan
plate_w = margin * 2 + cols * pitch;                 // 70
plate_d = margin * 2 + SCREEN_BAND + rows * pitch;   // 81

grid_y0  = margin + SCREEN_BAND;
win_cx   = plate_w / 2;
win_cy   = margin + SCREEN_BAND / 2;

// plate bawah = dasar + pcb + badan tombol
lid_z    = floor_t + pcb_t + body_h + body_gap;      // 8.2
inner_h  = lid_z - floor_t;                          // 6.2
total_h  = lid_z + plate_t;                          // 11.2

int_w = plate_w + slack;
int_d = plate_d + slack;

out_w = plate_w + 2 * wall;
out_d = plate_d + 2 * wall;

// =============================================================================
//  PLATE (tutup atas)
// =============================================================================
module plate() {
    difference() {
        cube([plate_w, plate_d, plate_t]);

        // lubang 12 tombol
        for (r = [0 : rows - 1], c = [0 : cols - 1]) {
            x = margin + c * pitch + pitch / 2;
            y = grid_y0 + r * pitch + pitch / 2;
            translate([x, y, -1])
                cylinder(d = key_hole, h = plate_t + 2);
        }

        // jendela OLED
        translate([win_cx - screen_win_w / 2, win_cy - screen_win_h / 2, -1])
            cube([screen_win_w, screen_win_h, plate_t + 2]);
    }
}

// =============================================================================
//  TRAY (bak bawah)
// =============================================================================
module tray() {
    x0 = (out_w - int_w) / 2;
    y0 = (out_d - int_d) / 2;
    difference() {
        cube([out_w, out_d, total_h]);

        // 1. rongga (sampai bawah bibir)
        translate([x0, y0, floor_t])
            cube([int_w, int_d, inner_h - lip_t]);

        // 2. bukaan di dalam bibir
        translate([x0 + lip_w, y0 + lip_w, lid_z - lip_t])
            cube([int_w - 2 * lip_w, int_d - 2 * lip_w, lip_t + 0.01]);

        // 3. dudukan plate
        translate([x0, y0, lid_z])
            cube([int_w, int_d, plate_t + 2]);

        // celah USB-C di dinding depan (-Y)
        translate([out_w / 2 - usb_w / 2, -1, floor_t])
            cube([usb_w, wall + 2, usb_h]);

        // celah buka plate di dinding belakang (+Y)
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
