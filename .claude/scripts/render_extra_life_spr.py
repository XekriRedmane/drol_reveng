#!/usr/bin/env python3
"""Render the EXTRA_LIFE_SPR ticked once per extra-life during the
LIFE_LOST_HANDLER animation loop.

LIFE_LOST_HANDLER ($7208 in drol.bin) sets SPRITE_PTR = $B67D with
ZP_SPRITE_W = $06 and ZP_SPRITE_H = $0E before calling DRAW_SPRITE
-- so the sprite is W+1 = 7 bytes per row x 14 rows = 98 bytes,
living in the level-1 swappable data region (reference/level1.bin).

The sprite is the "player glyph" displayed once per remaining
extra life while the game-over sequence animates them away.
"""
from __future__ import annotations

import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from render_sprite_lib import render_sprite_image, save_grid


def main() -> None:
    level1 = pathlib.Path('reference/level1.bin').read_bytes()
    spr = render_sprite_image(level1, 0xB67D, 6, 14, scale=8, base=0x0000)
    save_grid(
        'images/extra_life_spr.png',
        [spr],
        labels=['EXTRA_LIFE_SPR $B67D (W=6, H=14)'],
        columns=1,
    )


if __name__ == '__main__':
    main()
