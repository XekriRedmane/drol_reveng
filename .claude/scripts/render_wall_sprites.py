#!/usr/bin/env python3
"""Render the 7 WALL_L_SPR and 7 WALL_SPR frames from drol.bin.

WALL_L_SPR_DATA occupies $7DA4-$8177 (7 frames x 140 bytes) and
WALL_SPR_DATA occupies $8178-$854B (7 frames x 140 bytes).  Both share
the same column-major 4-column x 35-row format as PILLAR_SPR_DATA: each
source byte paints into the three perspective bands simultaneously via
INTERLACE_BLIT_P1/P2.  WALL_L is drawn at the left edge of the playfield
by REFRESH_LEFT_WALL; WALL is drawn at the right edge by
REFRESH_RIGHT_WALL.

This renderer paints each frame into band 0 of a mock HGR page, crops to
the sprite's footprint, and assembles the 7 frames of each table into
its own grid image.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from render_interlace_blit import render_hgr_page  # noqa: E402
from render_pillar_sprites import (  # noqa: E402
    decode_column_major_sprite,
    render_sprite_to_hgr,
)
from PIL import Image, ImageDraw  # noqa: E402


def render_table(
    drol: bytes, frame_addrs: list[int], title: str, out_path: pathlib.Path,
    scale: int = 2,
) -> None:
    num_cols = 4
    rows = 35
    tile_imgs: list[Image.Image] = []
    for addr in frame_addrs:
        bytegrid = decode_column_major_sprite(
            drol, addr, num_cols, rows, base=0x0100,
        )
        hgr = bytearray(0x2000)
        render_sprite_to_hgr(hgr, 0x2000, bytegrid, x_left=10, y_top=72)
        full = render_hgr_page(bytes(hgr), 0x2000, scale=scale)
        x0 = 10 * 7 * scale
        y0 = 72 * scale
        x1 = x0 + num_cols * 7 * scale
        y1 = y0 + rows * scale
        tile_imgs.append(full.crop((x0, y0, x1, y1)))

    tile_w, tile_h = tile_imgs[0].size
    margin = 10
    label_h = 16
    title_h = 18
    n = len(frame_addrs)
    img_w = margin + n * (tile_w + margin)
    img_h = title_h + label_h + tile_h + margin
    grid_img = Image.new("RGB", (img_w, img_h), (20, 20, 20))
    draw = ImageDraw.Draw(grid_img)
    draw.text((margin, 2), title, fill=(230, 230, 230))
    for i, tile in enumerate(tile_imgs):
        x = margin + i * (tile_w + margin)
        draw.text((x + tile_w // 2 - 12, title_h + 2), f"f{i}", fill=(210, 210, 210))
        grid_img.paste(tile, (x, title_h + label_h))
    grid_img.save(out_path)
    print(f"Wrote {out_path} ({img_w}x{img_h})")


def main() -> None:
    drol = pathlib.Path("reference/drol.bin").read_bytes()
    pathlib.Path("images").mkdir(exist_ok=True)

    wall_l_frames = [0x7DA4, 0x7E30, 0x7EBC, 0x7F48, 0x7FD4, 0x8060, 0x80EC]
    wall_frames = [0x8178, 0x8204, 0x8290, 0x831C, 0x83A8, 0x8434, 0x84C0]

    render_table(
        drol, wall_l_frames,
        "WALL_L_SPR_DATA frames (left wall, drawn by REFRESH_LEFT_WALL)",
        pathlib.Path("images/wall_l_sprites.png"),
    )
    render_table(
        drol, wall_frames,
        "WALL_SPR_DATA frames (right wall, drawn by REFRESH_RIGHT_WALL)",
        pathlib.Path("images/wall_sprites.png"),
    )


if __name__ == "__main__":
    main()
