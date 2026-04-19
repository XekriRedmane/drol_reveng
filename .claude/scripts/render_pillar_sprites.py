#!/usr/bin/env python3
"""Render the 7 PILLAR_SPR frames ($7700-$7AD3 in drol.bin).

Each frame is a column-major 4-column, 35-row sprite (140 bytes) consumed
by INTERLACE_BLIT via REFRESH_PILLARS.  The sprite paints into the 3
perspective bands of the hi-res page: rows 72-106 (top), 112-146 (middle),
152-186 (bottom).  Each source byte lands at the same relative row in all
three bands simultaneously, so the visible sprite is 3 vertical copies.

This renderer paints each frame into band 0 only (rows 72-106) at a fixed
screen column, crops, and assembles the 7 frames into a single grid image.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from render_interlace_blit import render_hgr_page  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def decode_column_major_sprite(
    data: bytes, addr: int, num_cols: int, rows: int, base: int = 0x0100,
) -> list[list[int]]:
    """Read a column-major sprite as a 2D byte grid [row][col].

    The on-disk layout is: source byte (N-1-c)*rows + r holds the byte for
    (row r, column c), rightmost column first.
    """
    out = [[0] * num_cols for _ in range(rows)]
    off0 = addr - base
    for c in range(num_cols):
        stream_col = (num_cols - 1) - c
        for r in range(rows):
            out[r][c] = data[off0 + stream_col * rows + r]
    return out


def render_sprite_to_hgr(
    hgr: bytearray, page_base: int, grid: list[list[int]],
    x_left: int, y_top: int,
) -> None:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    for r in range(rows):
        for c in range(cols):
            row = y_top + r
            col = x_left + c
            if col < 0 or col >= 40 or row < 0 or row >= 192:
                continue
            addr = (
                page_base + (row & 7) * 0x400
                + ((row >> 3) & 7) * 0x80 + (row >> 6) * 0x28 + col
            )
            byte = grid[r][c]
            if byte:
                hgr[addr - page_base] = byte


def main() -> None:
    drol = pathlib.Path("reference/drol.bin").read_bytes()
    pathlib.Path("images").mkdir(exist_ok=True)

    # The 7 PILLAR_SPR frame addresses (pointed to by PILLAR_SPR_LO/HI).
    frame_addrs = [0x7700, 0x778C, 0x7818, 0x78A4, 0x7930, 0x79BC, 0x7A48]
    num_cols = 4
    rows = 35
    scale = 2

    tile_imgs: list[Image.Image] = []
    for addr in frame_addrs:
        bytegrid = decode_column_major_sprite(
            drol, addr, num_cols, rows, base=0x0100,
        )
        hgr = bytearray(0x2000)
        # Place at col 10, row 72 (band 0); crop out the footprint.
        render_sprite_to_hgr(hgr, 0x2000, bytegrid, x_left=10, y_top=72)
        full = render_hgr_page(bytes(hgr), 0x2000, scale=scale)
        x0 = 10 * 7 * scale
        y0 = 72 * scale
        x1 = x0 + num_cols * 7 * scale
        y1 = y0 + rows * scale
        tile_imgs.append(full.crop((x0, y0, x1, y1)))

    # Compose grid.
    tile_w, tile_h = tile_imgs[0].size
    margin = 10
    label_h = 16
    n = len(frame_addrs)
    img_w = margin + n * (tile_w + margin)
    img_h = label_h + tile_h + margin
    grid_img = Image.new("RGB", (img_w, img_h), (20, 20, 20))
    draw = ImageDraw.Draw(grid_img)
    for i, tile in enumerate(tile_imgs):
        x = margin + i * (tile_w + margin)
        draw.text((x + tile_w // 2 - 12, 2), f"f{i}", fill=(210, 210, 210))
        grid_img.paste(tile, (x, label_h))

    out = pathlib.Path("images/pillar_sprites.png")
    grid_img.save(out)
    print(f"Wrote {out} ({img_w}x{img_h})")


if __name__ == "__main__":
    main()
