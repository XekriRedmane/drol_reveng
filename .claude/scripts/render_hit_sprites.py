#!/usr/bin/env python3
"""Render the HIT_SPR_POS / HIT_SPR_NEG sprite families.

REFRESH_HIT_ENTITIES at $631D (main.nw) draws the 12-slot
ENTITY_HIT_STATE table with a sprite picked from one of two
7-frame pointer tables, keyed on the per-slot facing bit:

    HIT_SPR_POS_LO/HI  at $7524/$7624 -> sprites in drol.bin
                       ($8AC0, $8AE8, $8B10, $8B38, $8B60, $8B88, $8BB0)
    HIT_SPR_NEG_LO/HI  at $750E/$760E -> sprites split between
                       drol.bin and level1.bin
                       ($7AD4, $7AFC, $7B24, $7B4C, $7B74, $7B9C, $7BC4)

Each frame is W=7 / H=5 (ZP_SPRITE_W=$07, ZP_SPRITE_H=$05), so 8 bytes
per row x 5 rows = 40 bytes ($28) per frame -- matching the stride in
the pointer tables.  DRAW_SPRITE_OPAQUE is the blitter (no zero-skip,
simple opaque STA), so no transparency is simulated.

HIT_SPR_NEG frame 0 lives at the tail of the swappable level-1 region
($7AD4-$7AFB) while frames 1..6 live in the persistent game-code
region ($7AFC-$7BEB, which is inside drol.bin's $7B00-$8BFF bank).
HIT_SPR_POS is entirely in drol.bin at $8AC0-$8BD7.  Both tables are
rendered here from drol.bin -- drol.bin has the full set.

Writes:
    images/hit_sprites_pos.png  -- 7 frames of the positive-facing sprite
    images/hit_sprites_neg.png  -- 7 frames of the negative-facing sprite
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from render_sprite_lib import render_sprite_image, save_grid  # noqa: E402

DROL = pathlib.Path("reference/drol.bin")
DROL_BASE = 0x0100


def main() -> None:
    data = DROL.read_bytes()
    pathlib.Path("images").mkdir(exist_ok=True)

    w = 7   # ZP_SPRITE_W; bytes/row = W+1 = 8
    h = 5   # ZP_SPRITE_H

    # HIT_SPR_POS frames at $8AC0..$8BB0 (stride $28).
    pos_ptrs = [0x8AC0 + i * 0x28 for i in range(7)]
    pos_imgs = [
        render_sprite_image(data, p, w_param=w, height_rows=h,
                            scale=6, base=DROL_BASE)
        for p in pos_ptrs
    ]
    pos_lbls = [f"frame {i}  ${p:04X}" for i, p in enumerate(pos_ptrs)]
    save_grid("images/hit_sprites_pos.png", pos_imgs, pos_lbls)

    # HIT_SPR_NEG frames at $7AD4..$7BC4 (stride $28).  Frame 0 is in
    # the level-1 swappable region but drol.bin carries a copy; frames
    # 1..6 live in the persistent $7B00-$8BFF bank.
    neg_ptrs = [0x7AD4 + i * 0x28 for i in range(7)]
    neg_imgs = [
        render_sprite_image(data, p, w_param=w, height_rows=h,
                            scale=6, base=DROL_BASE)
        for p in neg_ptrs
    ]
    neg_lbls = [f"frame {i}  ${p:04X}" for i, p in enumerate(neg_ptrs)]
    save_grid("images/hit_sprites_neg.png", neg_imgs, neg_lbls)


if __name__ == "__main__":
    main()
