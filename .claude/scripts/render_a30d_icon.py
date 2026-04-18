#!/usr/bin/env python3
"""Render the PAINT_HUD_ICON source at $A30D (level1) as a PNG.

The routines at $08F6 (page 1) and $097A (page 2) read 112 bytes from
$A30D,Y and paint a 31-row by 16-column icon at rows 1..31 of hi-res
columns 12..27 -- the top-center HUD icon slot.

Source layout: 16 columns (indexed X=$0F..$00, RIGHT-to-LEFT), each with
7 bytes arranged as [b0, b1, b2, b3, b4, b5, b6]. Expanded as:
  rows 1..7   = b0 (b0 repeated 7 times)
  row 8       = b1
  rows 9..15  = b2
  row 16      = b3
  rows 17..23 = b4
  row 24      = b5
  rows 25..31 = b6

Row 0 is NOT painted by these helpers.
"""

from __future__ import annotations

import pathlib
from PIL import Image

LEVEL1_BIN = pathlib.Path("reference/level1.bin")
LEVEL1_BASE = 0x0200
A30D = 0xA30D

SCALE = 6
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_VIOLET = (180, 0, 255)
COLOR_ORANGE = (255, 128, 0)
COLOR_BLUE = (0, 128, 255)


def render_strip(source: bytes) -> list[list[tuple[int, int, int]]]:
    """Produce a 16-col x 31-row pixel grid from 112 source bytes.

    Each column has 7 source bytes; rows 1..31 are painted, row 0 is
    left blank (the strip itself is 31 rows tall). Output is a
    31x(16*7) pixel matrix (since each hi-res byte is 7 pixels wide).
    """
    # layout: source[col*7 + i] where col runs 15..0 (matching
    # the X-decrement order of the painter). X=$0F reads bytes 0..6.
    # Each column's byte list is expanded into 31 row-bytes.
    col_bytes = {}
    for col_iter in range(16):
        # col_iter=0 corresponds to X=$0F, screen col 12+15=27 (hires col 27)
        # col_iter=15 corresponds to X=$00, screen col 12 (hires col 12)
        screen_col = 12 + 15 - col_iter
        strip = source[col_iter * 7:col_iter * 7 + 7]
        row_bytes = [None] * 32  # rows 0..31, row 0 blank
        for r in range(1, 8):
            row_bytes[r] = strip[0]
        row_bytes[8] = strip[1]
        for r in range(9, 16):
            row_bytes[r] = strip[2]
        row_bytes[16] = strip[3]
        for r in range(17, 24):
            row_bytes[r] = strip[4]
        row_bytes[24] = strip[5]
        for r in range(25, 32):
            row_bytes[r] = strip[6]
        col_bytes[screen_col] = row_bytes

    # Build a 280-wide pixel row per row 0..31 (cols outside 12..27
    # stay black).
    image = []
    for row in range(32):
        # Build 40-byte hi-res row (only cols 12..27 filled).
        hires_row = bytearray(40)
        for col in range(12, 28):
            b = col_bytes[col][row]
            if b is not None:
                hires_row[col] = b
        pixels = decode_hires_row(bytes(hires_row))
        image.append(pixels)
    return image


def decode_hires_row(row_bytes: bytes) -> list[tuple[int, int, int]]:
    """40 hi-res bytes -> 280 RGB pixels."""
    raw = []
    for b in row_bytes:
        palette = (b >> 7) & 1
        for i in range(7):
            raw.append((bool((b >> i) & 1), palette))

    even_color = [COLOR_VIOLET, COLOR_BLUE]
    odd_color = [COLOR_GREEN, COLOR_ORANGE]

    pixels = [COLOR_BLACK] * 280
    for i, (on, pal) in enumerate(raw):
        if not on:
            continue
        left_on = i > 0 and raw[i - 1][0]
        right_on = i < 279 and raw[i + 1][0]
        if left_on or right_on:
            pixels[i] = COLOR_WHITE
        else:
            pixels[i] = even_color[pal] if (i % 2 == 0) else odd_color[pal]
    return pixels


def main() -> None:
    level1 = LEVEL1_BIN.read_bytes()
    off = A30D - LEVEL1_BASE
    source = level1[off:off + 112]
    print(f"Read {len(source)} source bytes from $A30D..${A30D + 111:X}.")

    image_rows = render_strip(source)

    # Crop to cols 12..27 (pixels 84..195 inclusive = 112 px wide)
    # 32 rows tall.
    width = 112
    height = 32
    img = Image.new("RGB", (width * SCALE, height * SCALE), COLOR_BLACK)
    for y, row in enumerate(image_rows):
        for x_pix in range(width):
            color = row[84 + x_pix]
            if color == COLOR_BLACK:
                continue
            for sy in range(SCALE):
                for sx in range(SCALE):
                    img.putpixel((x_pix * SCALE + sx, y * SCALE + sy), color)

    out = pathlib.Path("images/hud_icon_a30d.png")
    out.parent.mkdir(exist_ok=True)
    img.save(out)
    print(f"Wrote {out} ({width * SCALE}x{height * SCALE}).")


if __name__ == "__main__":
    main()
