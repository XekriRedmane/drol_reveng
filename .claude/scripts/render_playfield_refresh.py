#!/usr/bin/env python3
"""Render the sprite-pointer tables consumed by the three playfield-refresh
routines (REFRESH_RIGHT_WALL at $61F0, REFRESH_LEFT_WALL at $626A,
REFRESH_PILLARS at $62E2).

Each of the three routines loads a 16-bit sprite pointer from a pair of
level-data tables at $75NN (low) / $76NN (high) indexed by $4C (the
walking-animation / X-reference slot, normally $02..$07).  The pointer
addresses a column-major sprite that INTERLACE_BLIT paints into the
3-band perspective playfield.

Entry format (per INTERLACE_BLIT_P1 docs in main.nw):
  - Column-major, rightmost column first
  - 35 bytes per column
  - Width N columns -> N * 35 bytes total
  - Byte 0 = column (N-1), byte 35 = column (N-2), ..., byte (N-1)*35 = column 0

Observed widths:
  - PILLAR (entries 0..7 step by $8C = 140 bytes = 4 columns of 35):
    $7700, $778C, $7818, $78A4, $7930, $79BC, $7A48, $7AD4 - 4-col sprites
  - PILLAR entries 8..12 step by $28 = 40 bytes = 1 col of 35 + padding,
    or possibly 1-column narrow sprites.

We render the first 8 entries of each table as 4-column sprites painted
to band 0 only (rows 72-106, single-band, 35 rows tall).  The image is a
3-row grid (one row per table) of 8 tiles each.
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
    """Read a column-major sprite as a 2D grid of bytes [row][col].

    The on-disk layout is: byte (N-1-c)*rows + r holds the byte for (row r,
    column c) — rightmost column first.
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
    """Paint a decoded row-major grid of bytes into band 0 of an HGR page.

    x_left is the leftmost screen column (grid[r][0] lands there).
    y_top is the top scanline.
    """
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
    level1 = pathlib.Path("reference/level1.bin").read_bytes()
    pathlib.Path("images").mkdir(exist_ok=True)

    # Enumerate the three pointer tables (first 8 entries each, which are
    # the full-width 4-column sprites).
    tables = [
        ("PILLAR", 0x7500, 0x7600),
        ("WALL_L", 0x7519, 0x7619),
        ("WALL_R", 0x7520, 0x7620),
    ]
    # ZP $4C cycles through $02..$07 during player movement (six animation
    # frames) and is held at $02 idle.  Render those 6 frames --- PILLAR
    # entries 2..7 (with entry 7 at the stride boundary) plus the
    # corresponding wall-table entries.
    frame_indices = list(range(2, 8))
    num_cols = 4
    rows = 35

    # Determine which binary each sprite lives in (drol.bin covers up to
    # $8BFF; level1.bin covers $8C00+ and overlap).
    def load_sprite(addr: int) -> list[list[int]]:
        if addr < 0x8C00:
            return decode_column_major_sprite(drol, addr, num_cols, rows, base=0x0100)
        return decode_column_major_sprite(level1, addr, num_cols, rows, base=0x0000)

    # Render each sprite as its own small 4-col x 35-row tile painted to an
    # isolated page 1 frame (band 0 only), then assemble into a grid.
    per_tile_w_px = num_cols * 7 * 2  # scale=2 applied later
    per_tile_h_px = rows * 2
    grid_cols = len(frame_indices)
    grid_rows = len(tables)
    label_h = 18
    tile_margin = 8

    tile_imgs: list[list[Image.Image]] = []
    for (name, lo_base, hi_base) in tables:
        row_imgs: list[Image.Image] = []
        for i in frame_indices:
            lo_off = lo_base - 0x0100 + i
            hi_off = hi_base - 0x0100 + i
            sprite_addr = (drol[hi_off] << 8) | drol[lo_off]
            bytegrid = load_sprite(sprite_addr)
            # Paint into a minimal HGR at fixed (col=10, row=72) and crop.
            hgr = bytearray(0x2000)
            render_sprite_to_hgr(hgr, 0x2000, bytegrid, x_left=10, y_top=72)
            full = render_hgr_page(bytes(hgr), 0x2000, scale=2)
            # Crop to sprite footprint.
            x0 = 10 * 7 * 2
            y0 = 72 * 2
            x1 = x0 + num_cols * 7 * 2
            y1 = y0 + rows * 2
            cropped = full.crop((x0, y0, x1, y1))
            row_imgs.append(cropped)
        tile_imgs.append(row_imgs)

    # Compose the grid image.
    tile_w, tile_h = tile_imgs[0][0].size
    header_w = 96  # space for table name
    img_w = header_w + grid_cols * (tile_w + tile_margin) + tile_margin
    img_h = label_h + grid_rows * (tile_h + label_h + tile_margin) + tile_margin
    grid = Image.new("RGB", (img_w, img_h), (24, 24, 24))
    draw = ImageDraw.Draw(grid)

    # Column headers (frame index, as stored in ZP $4C).
    for c, frame_idx in enumerate(frame_indices):
        x = header_w + c * (tile_w + tile_margin) + tile_margin // 2
        draw.text((x + tile_w // 2 - 8, 2), f"${frame_idx:02X}", fill=(200, 200, 200))

    # Rows: table name + sprites.
    for r, (name, _lo, _hi) in enumerate(tables):
        y = label_h + r * (tile_h + label_h + tile_margin) + label_h // 2
        draw.text((4, y + tile_h // 2 - 6), name, fill=(230, 230, 230))
        for c in range(grid_cols):
            x = header_w + c * (tile_w + tile_margin) + tile_margin // 2
            grid.paste(tile_imgs[r][c], (x, y))

    out = pathlib.Path("images/playfield_refresh_sprites.png")
    grid.save(out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
