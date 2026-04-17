#!/usr/bin/env python3
"""Render the attract-mode ATTRACT_SPR sprites whose dimensions can be
pulled directly out of ATTRACT_ANIM_4's static code ($1844 in drol.bin).

ATTRACT_ANIM_4 fetches each entity's pointer from ATTRACT_SPR at $B006/$B086
and draws with a fixed height of 8 rows; the width comes from runtime ZP
$F5..$F6 but for the first two entries the stored byte layout is big
enough to use the convention W+1 bytes per row that DRAW_SPRITE expects
(see render_sprite_lib.decode_sprite).  Concretely:

  ATTRACT_SPR[0] @ $B5FD: 104 = 13 * 8 bytes  -> W=12, H=8
  ATTRACT_SPR[1] @ $B665:  24 =  3 * 8 bytes  -> W=2,  H=8

The output image stacks both sprites vertically for the prose around
the level-1 swappable-data chapter.
"""
from __future__ import annotations

import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from render_sprite_lib import render_sprite_image, save_grid


def main() -> None:
    level1 = pathlib.Path('reference/level1.bin').read_bytes()
    spr0 = render_sprite_image(level1, 0xB5FD, 12, 8, scale=6, base=0x0000)
    spr1 = render_sprite_image(level1, 0xB665, 2, 8, scale=6, base=0x0000)
    save_grid(
        'images/attract_spr_renders.png',
        [spr0, spr1],
        labels=[
            'ATTRACT_SPR[0] $B5FD (W=12, H=8)',
            'ATTRACT_SPR[1] $B665 (W=2, H=8)',
        ],
        columns=1,
    )


if __name__ == '__main__':
    main()
