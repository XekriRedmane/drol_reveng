#!/usr/bin/env python3
"""Render the contents of a disk track as font characters.

Usage:
    python .claude/scripts/render_track_font.py TRACK [OFFSET] [OUTPUT_FILE]

TRACK: track number in decimal or $hex
OFFSET: byte offset into the track to start rendering (decimal or $hex, default 0)
OUTPUT_FILE: defaults to output/track_XX_font.png

Loads the track using the empirically-determined sector-to-page
mapping, then interprets the data from OFFSET onward as font
characters (32 bytes each) and renders them using the Apple II
hi-res color artifact algorithm.
"""
from __future__ import annotations

import sys
from PIL import Image

DISK_FILE = 'Ali Baba and the Forty Thieves (4am and san inc crack).dsk'
MAIN_BIN = 'main.bin'
MAIN_BIN_BASE = 0x0500

# Sector-to-page mapping: physical sector N -> page (15 - N).
# This was determined empirically by matching raw disk sectors
# against the known-good reference binary (main.bin).
SECTOR_TO_PAGE = [15 - i for i in range(16)]

# Apple II hi-res artifact colors
COLORS: dict[str, tuple[int, int, int]] = {
    '.': (0, 0, 0),
    'G': (0, 255, 0),
    'V': (128, 0, 255),
    'O': (255, 128, 0),
    'B': (0, 128, 255),
    'W': (255, 255, 255),
}


def load_track(disk: bytes, track: int) -> bytearray:
    """Load one track using the sector-to-page mapping."""
    data = bytearray(4096)
    for phys in range(16):
        page_offset = SECTOR_TO_PAGE[phys]
        offset = (track * 16 + phys) * 256
        data[page_offset * 256:(page_offset + 1) * 256] = disk[offset:offset + 256]
    return data


def get_char_pixels(d: bytes) -> list[list[str]]:
    """Get 14x16 colored pixel array for one 32-byte font character."""
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


def render_track_font(track: int, byte_offset: int, output_file: str) -> None:
    disk = open(DISK_FILE, 'rb').read()
    data = load_track(disk, track)
    data = data[byte_offset:]

    num_chars = len(data) // 32
    base_addr = 0x4000 + (track - 0x07) * 0x1000 if 0x07 <= track <= 0x0C else track * 0x1000
    base_addr += byte_offset

    SCALE = 3
    CHAR_W, CHAR_H = 14, 16
    GRID_COLS = 16
    GRID_ROWS = (num_chars + GRID_COLS - 1) // GRID_COLS
    PAD = 2
    cell_w = CHAR_W * SCALE + PAD
    cell_h = CHAR_H * SCALE + PAD
    img_w = GRID_COLS * cell_w
    img_h = GRID_ROWS * cell_h
    img = Image.new('RGB', (img_w, img_h), (20, 20, 20))

    for ci in range(num_chars):
        gr = ci // GRID_COLS
        gc = ci % GRID_COLS
        pixels = get_char_pixels(data[ci * 32:(ci + 1) * 32])
        for y in range(CHAR_H):
            for x in range(CHAR_W):
                color = COLORS.get(pixels[y][x], (0, 0, 0))
                px = gc * cell_w + x * SCALE
                py = gr * cell_h + y * SCALE
                for sy in range(SCALE):
                    for sx in range(SCALE):
                        img.putpixel((px + sx, py + sy), color)

    img.save(output_file)
    print(f"Track ${track:02X} -> memory ${base_addr:04X}-${base_addr + 0xFFF:04X}")
    print(f"Saved {output_file} ({img_w}x{img_h}, {num_chars} characters)")


def parse_number(s: str) -> int:
    """Parse decimal or $hex/0xhex number."""
    if s.startswith('$'):
        return int(s[1:], 16)
    elif s.startswith('0x') or s.startswith('0X'):
        return int(s, 16)
    else:
        return int(s)


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} TRACK [OFFSET] [OUTPUT_FILE]")
        print(f"  TRACK:  decimal or $hex track number")
        print(f"  OFFSET: byte offset into track (decimal or $hex, default 0)")
        sys.exit(1)

    track = parse_number(sys.argv[1])
    byte_offset = 0
    output_file = f"output/track_{track:02x}_font.png"

    if len(sys.argv) >= 3:
        try:
            byte_offset = parse_number(sys.argv[2])
            if len(sys.argv) >= 4:
                output_file = sys.argv[3]
        except ValueError:
            output_file = sys.argv[2]

    render_track_font(track, byte_offset, output_file)


if __name__ == '__main__':
    main()
