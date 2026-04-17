#!/usr/bin/env python3
"""Render the player sprite families (idle + active) to PNG grids.

DRAW_PLAYER at $64DF (main.nw) indexes two pointer tables by
ZP_PLAYER_STANCE ($03..$09 = top..bottom floor):
    PLAYER_SPR_IDLE_LO/HI   at $7527/$7627 — idle body sprites (3 x $13)
    PLAYER_SPR_ACTIVE_LO/HI at $7531/$7631 — active body sprites (3 x $14)

Both pointer tables dereference into $8500-$8ABF (inside drol.bin, persistent).
Entry 3 is top floor; entry 9 is bottom floor (seven used entries, 3..9).

Writes:
    images/player_sprites_idle.png    — 7 stances side-by-side
    images/player_sprites_active.png  — 7 stances side-by-side
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from render_sprite_lib import render_sprite_image, save_grid  # noqa: E402

DROL = pathlib.Path("reference/drol.bin")
DROL_BASE = 0x0100


def read_ptr(data: bytes, lo_addr: int, hi_addr: int, idx: int) -> int:
    lo = data[lo_addr - DROL_BASE + idx]
    hi = data[hi_addr - DROL_BASE + idx]
    return (hi << 8) | lo


def main() -> None:
    data = DROL.read_bytes()
    pathlib.Path("images").mkdir(exist_ok=True)

    # Stance indices 3..9 are the valid floor positions.
    stances = list(range(3, 10))

    # Idle: W=3 (4 bytes/row), H=$13=19. Table at $7527/$7627.
    idle_sprites = []
    idle_labels = []
    for s in stances:
        ptr = read_ptr(data, 0x7527, 0x7627, s)
        img = render_sprite_image(data, ptr, w_param=3, height_rows=0x13,
                                  scale=5, base=DROL_BASE)
        idle_sprites.append(img)
        idle_labels.append(f"idx {s}  ${ptr:04X}")
    save_grid("images/player_sprites_idle.png", idle_sprites, idle_labels)

    # Active: W=3 (4 bytes/row), H=$14=20. Table at $7531/$7631.
    active_sprites = []
    active_labels = []
    for s in stances:
        ptr = read_ptr(data, 0x7531, 0x7631, s)
        img = render_sprite_image(data, ptr, w_param=3, height_rows=0x14,
                                  scale=5, base=DROL_BASE)
        active_sprites.append(img)
        active_labels.append(f"idx {s}  ${ptr:04X}")
    save_grid("images/player_sprites_active.png", active_sprites,
              active_labels)


if __name__ == "__main__":
    main()
