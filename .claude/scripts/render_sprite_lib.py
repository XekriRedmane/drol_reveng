#!/usr/bin/env python3
"""Shared sprite decoding for Drol sprite-table render scripts.

DRAW_SPRITE (main.nw, $656F) blits a rectangle described by:
    ZP_SPRITE_W ($56) — width parameter; actual bytes per row = W + 1
    ZP_SPRITE_H ($57) — height in rows
    ZP_SPRITE_Y ($5B) — starting screen row (top of sprite)
    ZP_SPRITE_X ($5D) — starting column; the sprite's RIGHT edge

The "+1" quirk is because the inner byte loop uses
    STA ZP_SPRITE_ROW_REMAIN  ; initial value = W
.col_loop:
    ... (draw one byte) ...
    DEC ZP_SPRITE_ROW_REMAIN
    BPL .col_loop             ; loop while counter >= 0
which means the loop body runs while ROW_REMAIN takes values W, W-1, ..., 0
before the BPL fails at -1 — that is W+1 byte iterations per row. All
callers in main.nw pass values like W=2 for projectiles (3 bytes/row),
W=3 for the player (4 bytes/row), W=6 for the SPECIAL body (7 bytes/row).

Layout: row-major. For each row r (r=0..H-1, top down), the actual bytes
per row is (W+1), and sprite[r*(W+1) + 0] is placed at screen column
ZP_SPRITE_X, sprite[r*(W+1) + 1] at column X-1, ...
sprite[r*(W+1) + W] at column X-W. That is, the first byte of each row is
the rightmost byte on screen.

Each byte holds 7 pixels: bit 0 = leftmost pixel of that byte, bit 6 =
rightmost pixel of that byte, bit 7 = palette bit (0 = violet/green,
1 = blue/orange). The display maps a 7-bit byte to a 7-pixel-wide slice of
the hi-res scanline, with horizontal order bit0..bit6 from left to right.

In our decoder we always render sprites as an abstract grid: left-to-right
bit order within a byte, with "rightmost byte first" corrected by reversing
the bytes of each row when laying them out so the resulting image has the
leftmost column of the sprite on the left.

Colour model: Apple II hi-res with NTSC artefacts. An isolated on-bit is
coloured by its column parity and the palette bit of its host byte; two or
more adjacent on-bits render as white. We use this to give sprites their
recognisable Drol palette look (cyan/orange player, etc.).

The renderer is transparent: byte 0 means "don't draw this pixel slice",
matching DRAW_SPRITE's `BEQ .col_skip` on zero source bytes.
"""

from __future__ import annotations

import pathlib
from typing import Sequence

from PIL import Image, ImageDraw

# Apple II hi-res palette (approximate NTSC artefacts).
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_VIOLET = (180, 0, 255)
COLOR_ORANGE = (255, 128, 0)
COLOR_BLUE = (0, 128, 255)
COLOR_TRANSPARENT = (32, 32, 32)  # grey backdrop for transparent cells


def read_level_bytes(path: str | pathlib.Path) -> bytes:
    """Load a flat Drol binary (base $0000 for level1, $0100 for drol.bin)."""
    return pathlib.Path(path).read_bytes()


def decode_sprite(
    data: bytes, addr: int, w_param: int, height_rows: int,
    base: int = 0x0000,
) -> list[list[tuple[int, int, int]]]:
    """Decode a sprite from a flat binary, returning a 2D grid of RGB pixels.

    The input w_param is DRAW_SPRITE's ZP_SPRITE_W value; the actual bytes
    per row is w_param + 1 (see module docstring). Returns a list of rows,
    each a list of ((w_param+1)*7) RGB tuples. Transparent source bytes
    (value 0) render as black (matching DRAW_SPRITE's BEQ .col_skip
    transparency). Within a byte, pixels are laid out left-to-right (bit 0
    -> leftmost), and each row is laid out with the LEFTMOST byte on the
    left (DRAW_SPRITE stores rightmost-first, so we reverse the row bytes).
    """
    bytes_per_row = w_param + 1
    pixels_per_byte = 7
    row_pixels = bytes_per_row * pixels_per_byte

    # Materialise raw (on_bit, palette) pairs for every pixel in the sprite.
    rows: list[list[tuple[bool, int, bool]]] = []
    for r in range(height_rows):
        off = addr - base + r * bytes_per_row
        row_bytes = data[off:off + bytes_per_row]
        # Reverse so sprite[r*W + 0] (rightmost byte) ends up on the right.
        row_bytes = row_bytes[::-1]
        # (on, palette, transparent_byte)
        raw: list[tuple[bool, int, bool]] = []
        for b in row_bytes:
            transparent_byte = (b == 0)
            palette = (b >> 7) & 1
            for i in range(pixels_per_byte):
                on = bool((b >> i) & 1)
                raw.append((on, palette, transparent_byte))
        rows.append(raw)

    # Now resolve colours using NTSC-style adjacency.
    out: list[list[tuple[int, int, int]]] = []
    for r_idx, raw in enumerate(rows):
        row_colors: list[tuple[int, int, int]] = [COLOR_BLACK] * row_pixels
        for i, (on, pal, _trans) in enumerate(raw):
            if not on:
                # Even for transparent source bytes, show backdrop.
                row_colors[i] = COLOR_BLACK
                continue
            left_on = i > 0 and raw[i - 1][0]
            right_on = i < row_pixels - 1 and raw[i + 1][0]
            if left_on or right_on:
                row_colors[i] = COLOR_WHITE
            else:
                if pal == 0:
                    row_colors[i] = COLOR_VIOLET if (i % 2 == 0) else COLOR_GREEN
                else:
                    row_colors[i] = COLOR_BLUE if (i % 2 == 0) else COLOR_ORANGE
        out.append(row_colors)

    return out


def render_sprite_image(
    data: bytes, addr: int, w_param: int, height_rows: int,
    scale: int = 6, base: int = 0x0000,
    border_color: tuple[int, int, int] = (60, 60, 60),
) -> Image.Image:
    """Render a single sprite to a scaled PIL image with a thin border.

    w_param is DRAW_SPRITE's ZP_SPRITE_W value (actual bytes per row is
    w_param + 1; see decode_sprite docstring).
    """
    grid = decode_sprite(data, addr, w_param, height_rows, base=base)
    w = (w_param + 1) * 7
    h = height_rows
    img = Image.new("RGB", (w * scale, h * scale), COLOR_BLACK)
    px = img.load()
    for y, row in enumerate(grid):
        for x, col in enumerate(row):
            if col == COLOR_BLACK:
                continue
            for sy in range(scale):
                for sx in range(scale):
                    px[x * scale + sx, y * scale + sy] = col
    # Add a 1-px frame so adjacent sprites in a grid are distinguishable.
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, img.width - 1, img.height - 1), outline=border_color)
    return img


def compose_sprite_grid(
    sprites: Sequence[Image.Image],
    labels: Sequence[str] | None = None,
    columns: int = 0,
    padding: int = 12,
    label_height: int = 18,
    background: tuple[int, int, int] = (24, 24, 24),
) -> Image.Image:
    """Tile sprite images into a single labelled grid image.

    If columns is 0 or <= len(sprites), lay them out in a single row.
    Otherwise wrap to multiple rows. All cells are sized to the max sprite
    dimensions so non-uniform sprite sizes still line up.
    """
    if not sprites:
        raise ValueError("no sprites to compose")
    if columns <= 0:
        columns = len(sprites)
    rows_cnt = (len(sprites) + columns - 1) // columns
    cell_w = max(s.width for s in sprites)
    cell_h = max(s.height for s in sprites)
    total_w = columns * cell_w + (columns + 1) * padding
    total_h = rows_cnt * (cell_h + label_height) + (rows_cnt + 1) * padding
    out = Image.new("RGB", (total_w, total_h), background)
    draw = ImageDraw.Draw(out)
    for i, spr in enumerate(sprites):
        c = i % columns
        r = i // columns
        x = padding + c * (cell_w + padding) + (cell_w - spr.width) // 2
        y = padding + r * (cell_h + label_height + padding)
        out.paste(spr, (x, y))
        if labels and i < len(labels):
            lbl = labels[i]
            lx = padding + c * (cell_w + padding) + cell_w // 2
            ly = y + spr.height + 2
            # Centre the label under the cell.
            tw = draw.textlength(lbl)
            draw.text((lx - tw // 2, ly), lbl, fill=(200, 200, 200))
    return out


def save_grid(
    out_path: str | pathlib.Path,
    sprites: Sequence[Image.Image],
    labels: Sequence[str] | None = None,
    columns: int = 0,
) -> None:
    img = compose_sprite_grid(sprites, labels=labels, columns=columns)
    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"Wrote {out_path} ({img.width}x{img.height}).")
