#!/usr/bin/env python3
"""Render the 10 DIGIT_TILE sprites (0-9) into a single labelled grid.

POST_FRAME ($10CF in drol.bin) and DISPLAY_UPDATE ($10AB) draw score/
timer digits by looking up a sprite pointer from DIGIT_TILE_LO / _HI
indexed by X (0..9), storing it into SMC_TILE_SRC_LO/HI, and calling
DRAW_SPRITE_OPAQUE with ZP_SPRITE_W=1 and ZP_SPRITE_H=6 -- i.e. each
glyph is W+1 = 2 bytes per row x 6 rows = 12 bytes.

All ten pointers live in the level-1 swappable bank at $B4B1..$B529,
contiguous and 12-byte-aligned.
"""

from __future__ import annotations

import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from render_sprite_lib import render_sprite_image, save_grid


def main() -> None:
    level1 = pathlib.Path('reference/level1.bin').read_bytes()
    # DIGIT_TILE_LO / HI pointer tables resolve to:
    # digit 0: $B4B1, digit 1: $B4BD, digit 2: $B4C9, digit 3: $B4D5,
    # digit 4: $B4E1, digit 5: $B4ED, digit 6: $B4F9, digit 7: $B505,
    # digit 8: $B511, digit 9: $B51D.  (Step = 12 bytes = (W+1)*H.)
    digit_addrs = [0xB4B1 + i * 12 for i in range(10)]
    sprites = [
        render_sprite_image(level1, addr, w_param=1, height_rows=6, scale=16, base=0x0000)
        for addr in digit_addrs
    ]
    labels = [f'{i}' for i in range(10)]
    save_grid(
        'images/digit_tiles.png',
        sprites,
        labels=labels,
        columns=10,
    )


if __name__ == '__main__':
    main()
