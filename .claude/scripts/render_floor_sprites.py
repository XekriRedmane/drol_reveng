#!/usr/bin/env python3
"""Render the 11 FLOOR_SPR frames ($7BEC-$7DA3 in drol.bin).

REFRESH_FLOOR_LINES at $62CA paints 40 bytes from FLOOR_SPR_LO/HI[Y] onto
four evenly-spaced hi-res rows (67, 107, 147, 187).  Each frame is 40 bytes
= 40 columns x 1 row (since FLOOR_LINES_P1 copies one source byte per
column directly, no DRAW_SPRITE framing).

FLOOR_SPR_LO/HI has 11 entries: pointers $7BEC $7C14 $7C3C $7C64 $7C8C $7CB4
$7CDC $7D04 $7D2C $7D54 $7D7C, stride $28 bytes per frame.

In level1.bin the region is all zero, which means the shipped level-1
overlay blanks the animation table and the routine effectively erases the
four reserved rows each frame.  In drol.bin, however, the region holds a
real 11-frame rolling-stripe pattern: each frame is a byte-shifted rotation
of a 12-byte dotted motif.  The pattern is live data because drol.bin is a
post-load memory snapshot and the loader deposits this default "horizon
stripe" into the region before any level is loaded.  If a hypothetical
level overlay left the bytes non-zero, the four reserved rows would
display this scrolling motif in sync with ZP_WALK_FRAME.

Writes:
    images/floor_sprites.png  -- 11 frames rendered as 40-column horizontal
                                 stripes, with Apple II hi-res palette.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from render_sprite_lib import (  # noqa: E402
    COLOR_BLACK,
    COLOR_BLUE,
    COLOR_GREEN,
    COLOR_ORANGE,
    COLOR_VIOLET,
    COLOR_WHITE,
)
from PIL import Image, ImageDraw  # noqa: E402

DROL = pathlib.Path("reference/drol.bin")
DROL_BASE = 0x0100

FLOOR_SPR_ADDR = 0x7BEC
FRAME_STRIDE = 0x28
NUM_FRAMES = 11
BYTES_PER_ROW = 40
PIXELS_PER_BYTE = 7


def decode_stripe(row_bytes: bytes) -> list[tuple[int, int, int]]:
    """Decode 40 bytes as a left-to-right 280-pixel stripe.

    Unlike DRAW_SPRITE sprites, FLOOR_LINES_P1 copies source byte Y into
    screen column (39 - Y) --- that is, source byte 0 lands at column 39
    and source byte 39 at column 0.  So we reverse the source bytes before
    expanding bits to pixels.
    """
    raw: list[tuple[bool, int]] = []
    for b in reversed(row_bytes):
        palette = (b >> 7) & 1
        for i in range(PIXELS_PER_BYTE):
            on = bool((b >> i) & 1)
            raw.append((on, palette))
    pixels: list[tuple[int, int, int]] = []
    total = len(raw)
    for i, (on, pal) in enumerate(raw):
        if not on:
            pixels.append(COLOR_BLACK)
            continue
        left_on = i > 0 and raw[i - 1][0]
        right_on = i < total - 1 and raw[i + 1][0]
        if left_on or right_on:
            pixels.append(COLOR_WHITE)
        else:
            if pal == 0:
                pixels.append(COLOR_VIOLET if (i % 2 == 0) else COLOR_GREEN)
            else:
                pixels.append(COLOR_BLUE if (i % 2 == 0) else COLOR_ORANGE)
    return pixels


def main() -> None:
    data = DROL.read_bytes()
    pathlib.Path("images").mkdir(exist_ok=True)

    stripe_h_px = 12        # each frame drawn as a 12 px thick band
    scale = 2
    gap = 6
    label_w = 90

    total_w = label_w + BYTES_PER_ROW * PIXELS_PER_BYTE * scale
    total_h = NUM_FRAMES * (stripe_h_px * scale + gap) + gap

    img = Image.new("RGB", (total_w, total_h), (24, 24, 24))
    px = img.load()
    draw = ImageDraw.Draw(img)

    for f in range(NUM_FRAMES):
        addr = FLOOR_SPR_ADDR + f * FRAME_STRIDE
        off = addr - DROL_BASE
        stripe = data[off:off + BYTES_PER_ROW]
        pixels = decode_stripe(stripe)

        y0 = gap + f * (stripe_h_px * scale + gap)
        for x, col in enumerate(pixels):
            if col == COLOR_BLACK:
                continue
            for sy in range(stripe_h_px * scale):
                for sx in range(scale):
                    px[label_w + x * scale + sx, y0 + sy] = col

        draw.text(
            (4, y0 + stripe_h_px * scale // 2 - 6),
            f"f{f}  ${addr:04X}",
            fill=(200, 200, 200),
        )

    out = pathlib.Path("images/floor_sprites.png")
    img.save(out)
    print(f"Wrote {out} ({img.width}x{img.height}).")


if __name__ == "__main__":
    main()
