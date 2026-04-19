#!/usr/bin/env python3
"""Render the four ATTRACT_SPR2 sprites drawn by ATTRACT_ANIM_2.

ATTRACT_ANIM_2 ($17E1 in drol.bin) draws four attract-mode entities whose
pointers live in ATTRACT_SPR2_LO/HI ($B002/$B082 in the level-1 swappable
region).  Width is per-entity from ZP_ATTRACT_ENT_W ($ED,X); height is
computed at runtime as (distance to row $6B, clamped to 14).  The byte
counts on disk reveal the fixed W/H pairs:

  ATTRACT_SPR2[0] @ $B571 --- $2A = 42 bytes = 3*14 -> W=2, H=14
  ATTRACT_SPR2[1] @ $B59B --- $2A = 42 bytes = 3*14 -> W=2, H=14
  ATTRACT_SPR2[2] @ $B5C5 --- $1C = 28 bytes = 2*14 -> W=1, H=14
  ATTRACT_SPR2[3] @ $B5E1 --- $1C = 28 bytes = 2*14 -> W=1, H=14

The four entries are consecutive within the level-1 blob:
    $B571 .. $B59A (42 bytes)   $B59B .. $B5C4 (42 bytes)
    $B5C5 .. $B5E0 (28 bytes)   $B5E1 .. $B5FC (28 bytes)
exactly abutting ATTRACT_SPR[0]=$B5FD.

Output is a single PNG tiling the four sprites with labels for the prose
around the attract-mode title sprites section.
"""
from __future__ import annotations

import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from render_sprite_lib import render_sprite_image, save_grid


def main() -> None:
    level1 = pathlib.Path('reference/level1.bin').read_bytes()
    sprites = [
        render_sprite_image(level1, 0xB571, 2, 14, scale=6, base=0x0000),
        render_sprite_image(level1, 0xB59B, 2, 14, scale=6, base=0x0000),
        render_sprite_image(level1, 0xB5C5, 1, 14, scale=6, base=0x0000),
        render_sprite_image(level1, 0xB5E1, 1, 14, scale=6, base=0x0000),
    ]
    labels = [
        'ATTRACT_SPR2[0] $B571 (W=2, H=14)',
        'ATTRACT_SPR2[1] $B59B (W=2, H=14)',
        'ATTRACT_SPR2[2] $B5C5 (W=1, H=14)',
        'ATTRACT_SPR2[3] $B5E1 (W=1, H=14)',
    ]
    save_grid('images/attract_spr2_renders.png', sprites, labels=labels, columns=4)


if __name__ == '__main__':
    main()
