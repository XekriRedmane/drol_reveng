#!/usr/bin/env python3
"""Decode scene text sectors from the Ali Baba disk image.

Usage:
    python .claude/scripts/decode_scenes.py [SCENE_NUM ...]

With no arguments, lists all scenes. With scene numbers (decimal or $hex),
shows full decoded text for those scenes.

Scene data encoding:
  $00     = space
  $01-$1A = A-Z
  $1B-$24 = 0-9
  $25     = ,   $26 = :   $27 = -   $28 = '
  $2C     = (   $2D = )   $2F = *
  $7D     = reset layout
  $7E     = page break (pause)
  $7F     = end of stream
  $80-$FE = position command (& $7F = row, next byte = col)
"""
from __future__ import annotations

import sys

DISK_FILE = 'Ali Baba and the Forty Thieves (4am and san inc crack).dsk'
SKEW_TABLE = [0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15]
BASE_TRACK = 0x11
BASE_SECTOR = 0x00

CHAR_MAP: dict[int, str] = {0x00: ' '}
for _i in range(1, 27):
    CHAR_MAP[_i] = chr(ord('A') + _i - 1)
for _i in range(10):
    CHAR_MAP[0x1B + _i] = str(_i)
CHAR_MAP[0x25] = ','
CHAR_MAP[0x26] = ':'
CHAR_MAP[0x27] = '-'
CHAR_MAP[0x28] = "'"
CHAR_MAP[0x2C] = '('
CHAR_MAP[0x2D] = ')'
CHAR_MAP[0x2F] = '*'


def read_sector(disk: bytes, track: int, sector: int) -> bytes | None:
    for phys_s in range(16):
        if SKEW_TABLE[phys_s] == sector:
            offset = (track * 16 + phys_s) * 256
            return disk[offset:offset + 256]
    return None


def decode_scene(data: bytes) -> str:
    result: list[str] = []
    i = 0
    while i < len(data):
        b = data[i]
        if b == 0x7F:
            break
        elif b == 0x7E:
            result.append('\n--- PAGE BREAK ---\n')
        elif b == 0x7D:
            result.append('[RESET]')
        elif b >= 0x80:
            row = b & 0x7F
            i += 1
            if i < len(data):
                col = data[i]
                result.append(f'\n  [row {row} col {col}] ')
        elif b in CHAR_MAP:
            result.append(CHAR_MAP[b])
        else:
            result.append(f'[${b:02X}]')
        i += 1
    return ''.join(result).strip()


def main() -> None:
    disk = open(DISK_FILE, 'rb').read()

    args = sys.argv[1:]
    if args:
        scene_nums = []
        for a in args:
            if a.startswith('$') or a.startswith('0x'):
                scene_nums.append(int(a.lstrip('$').lstrip('0x'), 16))
            else:
                scene_nums.append(int(a))
    else:
        scene_nums = list(range(70))

    for scene_num in scene_nums:
        total_sector = BASE_SECTOR + scene_num
        track = BASE_TRACK + total_sector // 13
        sector = total_sector % 13
        data = read_sector(disk, track, sector)
        if data is None:
            print(f'Scene ${scene_num:02X} ({scene_num}): SECTOR READ ERROR')
            continue
        text = decode_scene(data)
        if not text or len(text.strip()) < 3:
            if not args:
                print(f'  ${scene_num:02X} ({scene_num:2d}): (empty)')
            else:
                print(f'Scene ${scene_num:02X} ({scene_num}): (empty)')
        elif args:
            print(f'Scene ${scene_num:02X} ({scene_num}):')
            print(text)
            print()
        else:
            import re
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            preview = ' / '.join(lines[:2])[:90]
            print(f'  ${scene_num:02X} ({scene_num:2d}): {preview}')


if __name__ == '__main__':
    main()
