#!/usr/bin/env python3
"""Render PLAYER_GRID_SPR_A and PLAYER_GRID_SPR_B to a PNG grid.

Both tables hold 7 frames of W=3, H=2 perspective-grid sprites consumed by
DRAW_ENTITIES phase 2 to draw the player as a small tile on the depth grid.
The low/high pointer pair SPRITE_POINTER_TABLES_LO/HI at $7500/$7600 names
them PLAYER_GRID_SPR_A_LO/HI (at offsets $5A/$5A, pointing at $8BD8..$8BFF
then $8C00/$8C08) and PLAYER_GRID_SPR_B_LO/HI (at offset $61, pointing at
$8C87..$8CB7). The first five A frames live in persistent drol.bin; frames
A5/A6 and all seven B frames live in the swappable level-1 bank.

Selector: DRAW_ENTITIES picks table A when ZP_FRAME_COUNTER bit 2 is clear
and table B otherwise, giving the on-floor "twinkle" flicker between the
two close-by posture dots.

Writes:
    images/player_grid_sprites.png  — two rows of 7 frames (A, then B)
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from render_sprite_lib import render_sprite_image, save_grid  # noqa: E402

DROL = pathlib.Path("reference/drol.bin")
LVL1 = pathlib.Path("reference/level1.bin")
DROL_BASE = 0x0100
LVL1_BASE = 0x0000


def drol_ptr(data: bytes, lo_addr: int, hi_addr: int, idx: int) -> int:
    lo = data[lo_addr - DROL_BASE + idx]
    hi = data[hi_addr - DROL_BASE + idx]
    return (hi << 8) | lo


def main() -> None:
    drol = DROL.read_bytes()
    lvl = LVL1.read_bytes()
    pathlib.Path("images").mkdir(exist_ok=True)

    # Pointer tables in drol.bin (per output/drol.sym).
    PLAYER_GRID_SPR_A_LO = 0x7542
    PLAYER_GRID_SPR_A_HI = 0x7642
    PLAYER_GRID_SPR_B_LO = 0x7552
    PLAYER_GRID_SPR_B_HI = 0x7652

    frames = []
    labels = []

    for i in range(7):
        ptr = drol_ptr(drol, PLAYER_GRID_SPR_A_LO, PLAYER_GRID_SPR_A_HI, i)
        # Frames 0..4 live in drol.bin ($8BD8..$8BFF); 5..6 in level1 ($8C00..).
        if ptr < 0x8C00:
            img = render_sprite_image(drol, ptr, w_param=3, height_rows=2,
                                       scale=10, base=DROL_BASE)
        else:
            img = render_sprite_image(lvl, ptr, w_param=3, height_rows=2,
                                       scale=10, base=LVL1_BASE)
        frames.append(img)
        labels.append(f"A[{i}] ${ptr:04X}")

    for i in range(7):
        ptr = drol_ptr(drol, PLAYER_GRID_SPR_B_LO, PLAYER_GRID_SPR_B_HI, i)
        # All seven B frames are swappable.
        img = render_sprite_image(lvl, ptr, w_param=3, height_rows=2,
                                   scale=10, base=LVL1_BASE)
        frames.append(img)
        labels.append(f"B[{i}] ${ptr:04X}")

    save_grid("images/player_grid_sprites.png", frames, labels, columns=7)


if __name__ == "__main__":
    main()
