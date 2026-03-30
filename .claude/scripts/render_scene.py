#!/usr/bin/env python3
"""Render scene(s) from the Ali Baba disk image using the custom font.

Usage:
    python .claude/scripts/render_scene.py [SCENE_NUM ...]
    python .claude/scripts/render_scene.py all

With no arguments or "all", renders all non-empty scenes.
With scene numbers (decimal or $hex), renders those specific scenes.
Output PNGs are saved to output/scene_XX.png.

The scene text font starts at charset 3 (font character 48) in the
custom font at $83A5 in main.bin.  Scene data is read from disk
starting at track $11 sector 0, one 256-byte sector per scene.
"""
from __future__ import annotations

import os
import sys
from PIL import Image

DISK_FILE = 'Ali Baba and the Forty Thieves (4am and san inc crack).dsk'
MAIN_BIN = 'main.bin'
MAIN_BIN_BASE = 0x0500
FONT_ADDR = 0x83A5
SCENE_CHAR_OFFSET = 48  # scene text = charset 3 = font char 48+

# DOS 3.3 sector skew (physical -> logical)
DOS_SKEW = [0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15]

# Scene disk layout
SCENE_BASE_TRACK = 0x11
SCENE_BASE_SECTOR = 0x00
SECTORS_PER_TRACK = 13

# Apple II hi-res artifact colors
COLORS: dict[str, tuple[int, int, int]] = {
    '.': (0, 0, 0),
    'G': (0, 255, 0),
    'V': (128, 0, 255),
    'O': (255, 128, 0),
    'B': (0, 128, 255),
    'W': (255, 255, 255),
}

SCALE = 3
CHAR_W = 14
CHAR_H = 16
GRID_COLS = 20
GRID_ROWS = 12


def read_scene_sector(disk: bytes, scene_num: int) -> bytes | None:
    """Read a scene's 256-byte sector from disk using DOS 3.3 skew."""
    total = SCENE_BASE_SECTOR + scene_num
    track = SCENE_BASE_TRACK + total // SECTORS_PER_TRACK
    sector = total % SECTORS_PER_TRACK
    # Find physical sector for this DOS logical sector
    for phys in range(16):
        if DOS_SKEW[phys] == sector:
            offset = (track * 16 + phys) * 256
            if offset + 256 <= len(disk):
                return disk[offset:offset + 256]
    return None


def get_char_pixels(ref: bytes, font_char_idx: int) -> list[list[str]]:
    """Get 14x16 colored pixel array using Apple II hi-res color algorithm."""
    font_offset = FONT_ADDR - MAIN_BIN_BASE
    d = ref[font_offset + font_char_idx * 32:
            font_offset + (font_char_idx + 1) * 32]
    if len(d) < 32:
        return [['.' for _ in range(14)] for _ in range(16)]

    sprite_data: list[str] = [""] * 16
    for j in range(8):
        sprite_data[j] = f"{d[j]:08b}{d[j+8]:08b}"
    for j in range(8):
        sprite_data[j + 8] = f"{d[j+16]:08b}{d[j+24]:08b}"

    pixel_data: list[list[str]] = []
    for line in sprite_data:
        raw = f"{line[9:16]}{line[1:8]}"
        raw = raw[::-1]
        color_set = line[0]
        color01 = "O" if color_set == "1" else "G"
        color10 = "B" if color_set == "1" else "V"
        pixels = list("..............")
        for i in range(0, 14, 2):
            if raw[i:i + 2] == "01":
                pixels[i + 1] = color01
            elif raw[i:i + 2] == "10":
                pixels[i] = color10
        for i in range(13):
            if raw[i:i + 2] == "11":
                pixels[i:i + 2] = list("WW")
        for i in range(12):
            if raw[i:i + 3] == "010":
                pixels[i + 1] = color10 if ((i + 1) % 2) == 0 else color01
            elif raw[i:i + 3] == "101":
                pixels[i + 1] = color10 if ((i + 1) % 2) == 1 else color01
        pixel_data.append(pixels)
    return pixel_data


def is_empty_scene(data: bytes) -> bool:
    """Check if scene data is empty (all zeros or no content before $7F)."""
    for b in data:
        if b == 0x7F:
            return True
        if b != 0x00:
            return False
    return True


def render_scene(ref: bytes, disk: bytes, scene_num: int, output_base: str) -> int:
    """Render one scene to PNG(s). Returns number of pages rendered.

    If the scene has page breaks ($7E), each page is saved as a
    separate file: output_base.png, output_base_p2.png, etc.
    """
    scene_data = read_scene_sector(disk, scene_num)
    if scene_data is None:
        return 0
    if is_empty_scene(scene_data):
        return 0

    img_w = GRID_COLS * CHAR_W * SCALE
    img_h = GRID_ROWS * CHAR_H * SCALE

    def new_page() -> Image.Image:
        return Image.new('RGB', (img_w, img_h), (0, 0, 0))

    def draw_char(img: Image.Image, scene_char_idx: int, col: int, row: int) -> None:
        if scene_char_idx == 0:
            return
        font_idx = SCENE_CHAR_OFFSET + scene_char_idx
        pixels = get_char_pixels(ref, font_idx)
        px_base = col * CHAR_W * SCALE
        py_base = row * CHAR_H * SCALE
        for y in range(CHAR_H):
            for x in range(CHAR_W):
                color = COLORS.get(pixels[y][x], (0, 0, 0))
                if color != (0, 0, 0):
                    for sy in range(SCALE):
                        for sx in range(SCALE):
                            ix = px_base + x * SCALE + sx
                            iy = py_base + y * SCALE + sy
                            if 0 <= ix < img_w and 0 <= iy < img_h:
                                img.putpixel((ix, iy), color)

    pages: list[Image.Image] = []
    img = new_page()
    col = 2
    row = 0
    left_margin = 2
    right_margin = 18

    i = 0
    while i < len(scene_data):
        b = scene_data[i]
        if b == 0x7F:
            break
        elif b == 0x7E:
            # Page break: save current page and start a new one
            pages.append(img)
            img = new_page()
            col = left_margin
            row = 0
        elif b == 0x7D:
            left_margin = 0
            right_margin = 20
        elif b >= 0x80:
            row = b & 0x7F
            i += 1
            if i < len(scene_data):
                col = scene_data[i]
        else:
            draw_char(img, b, col, row)
            col += 1
            if col >= right_margin:
                col = left_margin
                row += 1
        i += 1

    pages.append(img)

    # Save pages
    # Strip .png extension from output_base if present
    if output_base.endswith('.png'):
        base = output_base[:-4]
    else:
        base = output_base

    for page_num, page_img in enumerate(pages):
        if len(pages) == 1:
            filename = f"{base}.png"
        else:
            filename = f"{base}_p{page_num + 1}.png"
        page_img.save(filename)

    return len(pages)


def parse_number(s: str) -> int:
    if s.startswith('$'):
        return int(s[1:], 16)
    elif s.startswith('0x') or s.startswith('0X'):
        return int(s, 16)
    else:
        return int(s)


def main() -> None:
    ref = open(MAIN_BIN, 'rb').read()
    disk = open(DISK_FILE, 'rb').read()
    os.makedirs('output', exist_ok=True)

    args = sys.argv[1:]
    if not args or args == ['all']:
        scene_nums = list(range(70))
    else:
        scene_nums = [parse_number(a) for a in args]

    rendered = 0
    total_pages = 0
    for scene_num in scene_nums:
        output_base = f"output/scene_{scene_num:02x}.png"
        pages = render_scene(ref, disk, scene_num, output_base)
        if pages > 0:
            suffix = f" ({pages} pages)" if pages > 1 else ""
            print(f"  Scene ${scene_num:02X} ({scene_num:2d}) -> output/scene_{scene_num:02x}*.png{suffix}")
            rendered += 1
            total_pages += pages

    print(f"\nRendered {rendered} scenes ({total_pages} pages total).")


if __name__ == '__main__':
    main()
