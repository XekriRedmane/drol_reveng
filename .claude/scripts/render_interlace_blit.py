#!/usr/bin/env python3
"""Render INTERLACE_BLIT_P1/P2 blit demonstration.

INTERLACE_BLIT is a 3-band perspective floor-sprite blitter.  It consumes a
column-major sprite (35 bytes per column, rightmost column first) and
paints it into three horizontal bands of hi-res page 1 (or page 2) at
rows 72-106, 112-146, 152-186 — the three "perspective stripes" of the
Drol playfield.  Each source byte simultaneously lands in all three bands
at the same relative row, so the painted content appears as a triple
ghost floor-element.

The demo emulates the blit into a 280x192 hi-res page, then renders the
page with the standard Apple II hi-res palette decoder.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from render_sprite_lib import (  # noqa: E402
    COLOR_BLACK, COLOR_WHITE, COLOR_VIOLET, COLOR_GREEN, COLOR_ORANGE,
    COLOR_BLUE,
)
from PIL import Image


def apple_hgr_row_addr(y: int) -> int:
    """Return the hi-res page-1 byte address of the first byte of row y."""
    return 0x2000 + (y & 7) * 0x400 + ((y >> 3) & 7) * 0x80 + (y >> 6) * 0x28


def interlace_blit_sim(
    hgr: bytearray, page_base: int, source: bytes, x_start: int, x_end: int,
) -> None:
    """Simulate STRIPE_COPY_{PAGE1,PAGE2}.

    page_base is 0x2000 (page 1) or 0x4000 (page 2).
    source is the column-major sprite bytes (rightmost column first, 35
    rows per column).
    x_start is the inclusive starting (right) screen column; x_end is the
    exclusive left terminator (paint stops when X == x_end).
    """
    # Mirror the row-group sequence used by STRIPE_COPY: 35 rows that
    # hit all three bands (72+k, 112+k, 152+k) for k = 0..34.
    row_seq = [72 + k for k in range(35)]
    y_src = 0
    x = x_start
    while True:
        if x >= 40:
            # Prologue guard: skip painting this column but advance source by 35.
            y_src += 35
        else:
            for k in range(35):
                byte = source[y_src]
                y_src += 1
                for band_dr in (0, 40, 80):
                    row = row_seq[k] + band_dr
                    addr = (
                        page_base + (row & 7) * 0x400
                        + ((row >> 3) & 7) * 0x80 + (row >> 6) * 0x28 + x
                    )
                    hgr[addr - page_base] = byte
        x -= 1
        if x == x_end:
            return


def render_hgr_page(hgr: bytes, page_base: int, scale: int = 2) -> Image.Image:
    """Render a 8 KiB hi-res page as a 280x192 RGB image with NTSC palette."""
    # Decode each row into 7-bit-per-byte pixel stream, then colorize using
    # Apple II NTSC artefact rules (palette bit + column parity).
    width = 280
    height = 192
    pixels: list[list[tuple[int, int, int]]] = []
    for y in range(height):
        row_off = apple_hgr_row_addr(y) - 0x2000
        row_bytes = hgr[row_off:row_off + 40]
        # Build per-bit on/palette arrays.
        bits = []  # list of (on, palette)
        for b in row_bytes:
            palette = (b >> 7) & 1
            for i in range(7):
                on = bool((b >> i) & 1)
                bits.append((on, palette))
        # Colorize.
        row_pixels = []
        for col, (on, palette) in enumerate(bits):
            if not on:
                row_pixels.append(COLOR_BLACK)
                continue
            # Two adjacent on-bits blend to white.
            prev_on = bits[col - 1][0] if col > 0 else False
            next_on = bits[col + 1][0] if col + 1 < len(bits) else False
            if prev_on or next_on:
                row_pixels.append(COLOR_WHITE)
                continue
            # Isolated bit: color = palette + column parity.
            # palette 0: even col -> violet, odd -> green
            # palette 1: even col -> blue,   odd -> orange
            if palette == 0:
                row_pixels.append(COLOR_VIOLET if (col & 1) == 0 else COLOR_GREEN)
            else:
                row_pixels.append(COLOR_BLUE if (col & 1) == 0 else COLOR_ORANGE)
        pixels.append(row_pixels)

    img = Image.new("RGB", (width * scale, height * scale))
    for y in range(height):
        for x in range(width):
            c = pixels[y][x]
            for dy in range(scale):
                for dx in range(scale):
                    img.putpixel((x * scale + dx, y * scale + dy), c)
    return img


def main() -> None:
    drol = pathlib.Path("reference/drol.bin").read_bytes()
    lvl = pathlib.Path("reference/level1.bin").read_bytes()
    pathlib.Path("images").mkdir(exist_ok=True)

    # Pick a 4-column (140-byte) sprite from the pointer table at
    # $7500/$7600 — entries 0..7 step by $8C (=140 bytes) and point into
    # level data (reference/level1.bin). Entry 0 = $7700.
    # Wait: $7700 is in the drol.bin range. Let me check both.
    # From $7520,Y lookup: entries 32..39 step by $8C (= 140 bytes). Entry
    # 32 = $8178 (in level1.bin).
    # Let me use entry 0 directly: $7700. That's in drol.bin (persistent).
    # Render a demo for entry 0 at center of screen.

    sprite_addr_0 = 0x7700
    sprite_src = drol[sprite_addr_0 - 0x0100:sprite_addr_0 - 0x0100 + 140]

    # Blit centered: x_start=19, sprite is 4 cols wide so x_end = 19-4 = 15
    hgr = bytearray(0x2000)
    interlace_blit_sim(hgr, 0x2000, sprite_src, x_start=19, x_end=15)
    img = render_hgr_page(bytes(hgr), 0x2000, scale=2)
    img.save("images/interlace_blit_demo_sprite7700.png")
    print("Wrote images/interlace_blit_demo_sprite7700.png")

    # Also render the sprite "source" itself (without the 3-band multiply)
    # so the reader can see the raw artwork alongside the band-painted
    # version.  Blit just into band 0 (rows 72-106) at the same column range
    # with x_start=19 x_end=15, but by hand — strip the band_dr triplication.
    hgr2 = bytearray(0x2000)
    y_src = 0
    x = 19
    while x > 15:
        for k in range(35):
            row = 72 + k  # band 0 only
            addr = apple_hgr_row_addr(row) - 0x2000 + x
            hgr2[addr] = sprite_src[y_src]
            y_src += 1
        x -= 1
    img2 = render_hgr_page(bytes(hgr2), 0x2000, scale=2)
    img2.save("images/interlace_blit_demo_singleband.png")
    print("Wrote images/interlace_blit_demo_singleband.png")


if __name__ == "__main__":
    main()
