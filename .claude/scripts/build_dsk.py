#!/usr/bin/env python3
"""Reconstruct the Ali Baba .dsk image from assembled binaries and scene data.

Usage:
    python build_dsk.py [--verify]

Inputs (all in output/ or scenes/):
    output/boot1.bin    — BOOT1 code ($0800-$0CFF, 1280 bytes)
    output/ealdr.bin    — EALDR loader ($A000-$BFFF, 8192 bytes)
    output/main.bin     — main game binary ($0500-$BFFF, 47872 bytes)
    scenes/track_XX.asm — scene/data tracks (raw HEX data per logical sector)

Output:
    output/ali_baba.dsk — reconstructed 143360-byte disk image

With --verify, compares against the original .dsk image and reports diffs.
"""
from __future__ import annotations

import os
from collections.abc import Generator
import re
import sys

DISK_SIZE = 143360  # 35 tracks x 16 sectors x 256 bytes
SECTOR_SIZE = 256
SECTORS_PER_TRACK = 16
TRACK_SIZE = SECTOR_SIZE * SECTORS_PER_TRACK
NUM_TRACKS = 35

# DOS 3.3 sector interleaving: physical sector -> logical sector
DOS_SKEW = [0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15]

# Reverse: logical sector -> physical sector
LOGICAL_TO_PHYS = [0] * 16
for phys, logical in enumerate(DOS_SKEW):
    LOGICAL_TO_PHYS[logical] = phys

# Custom game loader interleave: physical sector -> page offset from base
LOADER_INTERLEAVE = [0xF, 0x8, 0x1, 0x9, 0x2, 0xA, 0x3, 0xB,
                     0x4, 0xC, 0x5, 0xD, 0x6, 0xE, 0x7, 0x0]

# Reverse: page offset -> physical sector
PAGE_TO_PHYS = [0] * 16
for phys, page in enumerate(LOADER_INTERLEAVE):
    PAGE_TO_PHYS[page] = phys

# Main binary layout
MAIN_BASE = 0x0500

# EALDR DXR decryption: needed to re-encrypt $4000-$67FF before writing to disk
def funny_inc_gen(bot: int = 2, top: int = 3) -> Generator[int, None, None]:
    """Yield the EALDR funny_inc key sequence."""
    while True:
        bot += 1
        if bot == top:
            bot = 1
            top += 1
            yield 1
        else:
            yield bot


def dxr_encrypt(data: bytearray, start: int, end: int) -> None:
    """Re-encrypt a region using the DXR XOR sequence (same as decrypt)."""
    keys = funny_inc_gen()
    src = start
    while True:
        key = next(keys)
        if 0 <= src < len(data):
            data[src] ^= key
        src += 2
        if (src >> 8) == (end >> 8):
            break


def write_sector(dsk: bytearray, track: int, logical_sector: int,
                 data: bytes) -> None:
    """Write 256 bytes to a logical sector position in the .dsk image.

    The .dsk format stores sectors in DOS 3.3 logical order, so the file
    offset for logical sector L on track T is simply (T*16 + L) * 256.
    """
    offset = track * TRACK_SIZE + logical_sector * SECTOR_SIZE
    padded = (data + bytes(SECTOR_SIZE))[:SECTOR_SIZE]
    dsk[offset:offset + SECTOR_SIZE] = padded


def write_track_loader(dsk: bytearray, track: int, base_page: int,
                       mem: bytes, mem_base: int) -> None:
    """Write a track using the custom game loader interleave.

    The loader reads physical sectors and maps them to memory pages via
    LOADER_INTERLEAVE.  To reverse this, for each physical sector we
    determine which memory page it provides, then write that data to the
    .dsk at the logical sector position corresponding to that physical sector.
    """
    for phys in range(16):
        page_offset = LOADER_INTERLEAVE[phys]
        logical = DOS_SKEW[phys]
        mem_addr = (base_page + page_offset) * 256
        mem_offset = mem_addr - mem_base
        if 0 <= mem_offset and mem_offset + 256 <= len(mem):
            data = mem[mem_offset:mem_offset + 256]
        else:
            data = bytes(256)
        # .dsk stores sectors in logical order
        offset = track * TRACK_SIZE + logical * SECTOR_SIZE
        dsk[offset:offset + SECTOR_SIZE] = data


def load_track_asm(filename: str) -> list[bytes]:
    """Load a track .asm file, returning 16 sectors of 256 bytes each.

    The file contains HEX directives with sector data in logical order.
    """
    sectors: list[bytearray] = [bytearray(256) for _ in range(16)]
    current_sector = 0

    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line.startswith('; Track') and 'sector' in line:
                m = re.search(r'sector (\d+)', line)
                if m:
                    current_sector = int(m.group(1))
            elif line.startswith('HEX '):
                hex_str = line[4:].strip()
                data = bytes.fromhex(hex_str.replace(' ', ''))
                sectors[current_sector] = bytearray(data[:256])
                if len(data) < 256:
                    sectors[current_sector].extend(bytes(256 - len(data)))

    return [bytes(s) for s in sectors]


def build_disk() -> bytearray:
    """Build the complete .dsk image."""
    dsk = bytearray(DISK_SIZE)

    # --- Track 0: BOOT1 ---
    boot1 = open('output/boot1.bin', 'rb').read()
    # Boot ROM reads physical sectors 0-4 into $0800-$0CFF
    # In .dsk, physical sector N is at offset logical_sector * 256
    # boot1.bin has pages in memory order ($0800, $0900, $0A00, $0B00, $0C00)
    # Write boot1 sectors (physical 0-4 = DOS logical 0,7,14,6,13).
    for page in range(len(boot1) // SECTOR_SIZE):
        phys = page
        logical = DOS_SKEW[phys]
        data = boot1[page * 256:(page + 1) * 256]
        write_sector(dsk, 0, logical, data)

    # Physical sectors 5-7 contain residual disk format data (not loaded
    # during boot — sector count byte is $05).  Each sector is mostly $FF
    # fill with the physical sector number as a trailing signature.
    TRACK0_EXTRA: dict[int, bytes] = {
        5: (  # DOS logical 5: all $FF except last 3 bytes = $0D $0D $FF
            bytes([0xFF] * 253 + [0x0D, 0x0D, 0xFF])),
        6: (  # DOS logical 12: sparse format data
            bytes.fromhex(
                'd300000000000000000000000000000000000000000000000000000000000000'
                '0000000000000000ff0000000000000000000000000000000000000000000000'
                'bf00000000000000000000000000000000000000000000000000000000000000'
                '0000000000000000ff0000000000000000000000000000000000000000000000'
                '0000000000000000000000000000000000000000000000000000000000000000'
                '0000000000000000000000000000000000000000000000000000000000000000'
                '0000000000000000000000000000000000000000000000000000000000000000'
                '0000000000000000000000000000000000000000000000000000000000000e0e')),
        7: (  # DOS logical 4: $0F + $FF fill, last byte $0F
            bytes([0x0F] + [0xFF] * 254 + [0x0F])),
    }
    for phys, data in TRACK0_EXTRA.items():
        logical = DOS_SKEW[phys]
        write_sector(dsk, 0, logical, data)

    # --- Tracks 1-2: EALDR ---
    ealdr = open('output/ealdr.bin', 'rb').read()
    # EALDR loaded with custom loader interleave, base pages $A0 and $B0
    ealdr_base = 0xA000
    write_track_loader(dsk, 1, 0xA0, ealdr, ealdr_base)
    write_track_loader(dsk, 2, 0xB0, ealdr, ealdr_base)

    # --- Tracks 5: fill pattern data ---
    if os.path.exists('scenes/track_05.asm'):
        sectors = load_track_asm('scenes/track_05.asm')
        for logical in range(16):
            write_sector(dsk, 5, logical, sectors[logical])

    # --- Tracks 7-16: main program (pre-relocation, pre-encryption) ---
    main_bin = open('output/main.bin', 'rb').read()

    # We need to reverse the game_init relocation and DXR encryption.
    # extract_main.py does: load from disk -> DXR decrypt -> relocate
    # We need: un-relocate -> DXR encrypt -> write to disk

    mem = bytearray(len(main_bin))
    mem[:] = main_bin

    # Reverse game_init relocation:
    # Original: copy $2000-$32FF <- $9600-$A8FF, copy $3300-$3FFF <- $B300-$BFFF
    # (then clear $2000-$3FFF, but we need the data back there)
    src_hrcg = 0x9600 - MAIN_BASE
    dst_hrcg = 0x2000 - MAIN_BASE
    mem[dst_hrcg:dst_hrcg + 0x1300] = mem[src_hrcg:src_hrcg + 0x1300]

    src_disk = 0xB300 - MAIN_BASE
    dst_disk = 0x3300 - MAIN_BASE
    mem[dst_disk:dst_disk + 0x0D00] = mem[src_disk:src_disk + 0x0D00]

    # Now $0500-$07FF needs to come from EALDR $A300-$A5FF (not from main.bin)
    # The EALDR copies $A300-$A5FF -> $0500-$07FF during boot.
    # For the disk image, $0500-$07FF is part of what EALDR provides,
    # and shouldn't appear in the Group 2/3 tracks.
    # Actually, $0500-$07FF is loaded by the EALDR copy, not from tracks.
    # Group 3 loads tracks $0D-$10 into $0800-$3FFF.
    # Group 2 loads tracks $07-$0C into $4000-$95FF.
    # $0500-$07FF isn't loaded from any track - it comes from EALDR.
    # $9600-$BFFF also aren't loaded from tracks - they come from relocation.

    # DXR re-encrypt $4000-$67FF
    dxr_encrypt(mem, 0x4000 - MAIN_BASE, 0x6800 - MAIN_BASE)

    # Group 2: tracks $07-$0C -> $4000-$95FF
    GROUP2 = [(0x07, 0x40), (0x08, 0x50), (0x09, 0x60),
              (0x0A, 0x70), (0x0B, 0x80), (0x0C, 0x86)]
    for track, base_page in GROUP2:
        write_track_loader(dsk, track, base_page, bytes(mem), MAIN_BASE)

    # Group 3: tracks $0D-$10 -> $0800-$3FFF
    GROUP3 = [(0x0D, 0x08), (0x0E, 0x10), (0x0F, 0x20), (0x10, 0x30)]
    for track, base_page in GROUP3:
        write_track_loader(dsk, track, base_page, bytes(mem), MAIN_BASE)

    # --- Tracks $11-$1F: scene data ---
    for track in range(0x11, 0x20):
        filename = f'scenes/track_{track:02x}.asm'
        if os.path.exists(filename):
            sectors = load_track_asm(filename)
            for logical in range(16):
                write_sector(dsk, track, logical, sectors[logical])

    return dsk


def verify(dsk: bytearray) -> int:
    """Compare against original disk image, return number of differing bytes."""
    orig_file = 'Ali Baba and the Forty Thieves (4am and san inc crack).dsk'
    if not os.path.exists(orig_file):
        print(f"  Original disk image not found: {orig_file}")
        return -1

    orig = open(orig_file, 'rb').read()
    diffs = 0
    first_diffs: list[str] = []

    for track in range(NUM_TRACKS):
        track_diffs = 0
        for sector in range(SECTORS_PER_TRACK):
            offset = track * TRACK_SIZE + sector * SECTOR_SIZE
            for i in range(SECTOR_SIZE):
                if dsk[offset + i] != orig[offset + i]:
                    track_diffs += 1
                    diffs += 1
                    if len(first_diffs) < 20:
                        first_diffs.append(
                            f"    ${offset+i:05X} (T${track:02X} S{sector:02d} +${i:02X}): "
                            f"got ${dsk[offset+i]:02X}, expected ${orig[offset+i]:02X}")
        if track_diffs > 0:
            print(f"  Track ${track:02X}: {track_diffs} byte diffs")

    if diffs == 0:
        print("  Perfect match!")
    else:
        print(f"\n  Total: {diffs} differing bytes")
        if first_diffs:
            print("  First diffs:")
            for d in first_diffs:
                print(d)

    return diffs


def main() -> None:
    print("Building Ali Baba .dsk image...")
    dsk = build_disk()

    output = 'output/ali_baba.dsk'
    with open(output, 'wb') as f:
        f.write(dsk)
    print(f"Wrote {len(dsk)} bytes to {output}")

    if '--verify' in sys.argv:
        print("\nVerifying against original:")
        verify(dsk)


if __name__ == '__main__':
    main()
