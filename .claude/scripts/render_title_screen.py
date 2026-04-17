#!/usr/bin/env python3
"""Render the post-GAME_INIT hi-res page 1 as a PNG.

Simulates Drol's title-screen unpacker at $4013: it walks 37 records of
the form [dest_lo, dest_hi, 40 bytes] starting at $4100, terminated by
$FF. Each record writes its 40 bytes (in reverse, since the unpacker
counts Y from $27 down to 0) to the hi-res page-1 address.

Rendered output: images/title_screen.png (280x192 scaled 3x).

The unpacker only fills 37 specific scanlines (rows 0-32 and 188-191);
all other rows are rendered as black here, matching what the hi-res
framebuffer looks like before any other init code touches it.
"""

from __future__ import annotations

import pathlib
from PIL import Image

DROL_BIN = pathlib.Path("reference/drol.bin")
DROL_BASE = 0x0100
TITLE_DATA_ADDR = 0x4100

HIRES_BASE = 0x2000
HIRES_SIZE = 0x2000  # $2000-$3FFF

SCALE = 3
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
# Palette 0 (bit 7 = 0): green / violet
COLOR_GREEN = (0, 255, 0)
COLOR_VIOLET = (180, 0, 255)
# Palette 1 (bit 7 = 1): orange / blue
COLOR_ORANGE = (255, 128, 0)
COLOR_BLUE = (0, 128, 255)


def hires_row_address(y: int) -> int:
    """Apple II hi-res page-1 address for scanline y (0-191)."""
    return HIRES_BASE + (y & 7) * 0x400 + ((y >> 3) & 7) * 0x80 + (y >> 6) * 0x28


def unpack_title_screen(drol: bytes) -> bytearray:
    """Run the GAME_INIT unpack on a blank framebuffer and return it."""
    fb = bytearray(HIRES_SIZE)
    ptr = TITLE_DATA_ADDR - DROL_BASE  # offset into drol.bin
    records = 0
    while True:
        lo = drol[ptr]
        if lo == 0xFF:
            break
        ptr += 1
        hi = drol[ptr]
        ptr += 1
        dest = (hi << 8) | lo
        # Unpacker stores 40 bytes with Y from $27 down to 0, so
        # the first stream byte goes to column 39 and the last to
        # column 0 — data is reversed relative to display order.
        data = drol[ptr:ptr + 40][::-1]
        ptr += 40
        fb_off = dest - HIRES_BASE
        fb[fb_off:fb_off + 40] = data
        records += 1
    print(f"Unpacked {records} records, {ptr - (TITLE_DATA_ADDR - DROL_BASE)} bytes consumed.")
    return fb


def render_row(row_bytes: bytes) -> list[tuple[int, int, int]]:
    """Decode 40 bytes of hi-res data to 280 RGB pixels.

    Each byte = 7 pixels (bit 0 leftmost). Bit 7 is the palette bit:
      0 -> green/violet, 1 -> orange/blue.
    Adjacent on-bits render as white (NTSC artifact). Isolated on-bits
    get a color based on column parity and palette.
    """
    raw: list[tuple[bool, int]] = []
    for b in row_bytes:
        palette = (b >> 7) & 1
        for i in range(7):
            raw.append((bool((b >> i) & 1), palette))

    even_color = [COLOR_VIOLET, COLOR_BLUE]
    odd_color = [COLOR_GREEN, COLOR_ORANGE]

    pixels: list[tuple[int, int, int]] = [COLOR_BLACK] * 280
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
    drol = DROL_BIN.read_bytes()
    fb = unpack_title_screen(drol)

    img = Image.new("RGB", (280 * SCALE, 192 * SCALE), COLOR_BLACK)
    for y in range(192):
        addr = hires_row_address(y)
        off = addr - HIRES_BASE
        row_bytes = bytes(fb[off:off + 40])
        pixels = render_row(row_bytes)
        for x, color in enumerate(pixels):
            if color == COLOR_BLACK:
                continue
            for sy in range(SCALE):
                for sx in range(SCALE):
                    img.putpixel((x * SCALE + sx, y * SCALE + sy), color)

    out = pathlib.Path("images/title_screen.png")
    out.parent.mkdir(exist_ok=True)
    img.save(out)
    print(f"Wrote {out} ({280 * SCALE}x{192 * SCALE}).")


if __name__ == "__main__":
    main()
