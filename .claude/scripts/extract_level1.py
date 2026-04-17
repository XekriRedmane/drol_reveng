#!/usr/bin/env python3
"""Extract level-1 swappable data from drol.dsk.

Reverse-engineered from the loader's READ_SECTORS ($5148) and
PAGE_TABLE_RELOAD ($5440) in main.nw.

The Drol loader has two phase tables. First boot (LDR_PHASE=$FF) reads tracks
1-4 with PAGE_TABLE offset $00 (the persistent game code/data). Subsequent
"reload" phases (0..3) read five tracks each with PAGE_TABLE_RELOAD (offset
$40), starting at track 5, 10, 15, or 20 respectively — these are the four
level data sets.

PAGE_TABLE_RELOAD (first 80 entries, terminated by $00):
    track 5:  02 13 14 15 16 17 18 67 68 69 6A 6B 6C 6D 6E 6F
    track 6:  70 71 72 75 76 77 78 79 7A 8C 8D 8E 8F 90 91 92
    track 7:  93 94 95 96 97 98 99 9A 9B 9C 9D 9E 9F A0 A1 A2
    track 8:  A3 A4 A5 A6 A7 A8 A9 AA AB AC AD AE AF B0 B1 B2
    track 9:  B3 B4 B5 B6 B7 B8 B9 BA BB BC BD 00 (terminator)

Each entry i maps physical sector i of the current track to the specified
destination page. Reading physical sector P from the .dsk file:
    dsk_offset = track * 4096 + DOS_SKEW[P] * 256
per the Drol convention that RWTS encodes physical sector numbers in the
address field (see CLAUDE.md).

Output: reference/level1.bin covering the level-1 swappable memory pages
$0200, $1300-$18FF, $6700-$72FF, $7500-$7AFF, $8C00-$BDFF. Non-level pages
are left as $00. The binary is a flat image base $0000-$BDFF (48640 bytes);
addresses not covered by level data remain $00.

Phases 1-3 (tracks 10/15/20) load the same set of destination pages; this
script does phase 0 only, which is what the game loads first (per the
FIRST_BOOT documentation at $5524: "Phase 2 loads level data from track 5").
"""

from __future__ import annotations

import pathlib
import sys

DSK = pathlib.Path("drol.dsk")
OUT = pathlib.Path("reference/level1.bin")

# DOS 3.3 physical-to-logical sector skew (from CLAUDE.md).
DOS_SKEW = [0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15]

# PAGE_TABLE_RELOAD at $5440, as documented in main.nw (<<page table>>).
# First 80 entries span 5 tracks (16 sectors each). Terminator $00 excluded.
PAGE_TABLE_RELOAD = [
    # track 5 sectors 0-15
    0x02, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x67,
    0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F,
    # track 6
    0x70, 0x71, 0x72, 0x75, 0x76, 0x77, 0x78, 0x79,
    0x7A, 0x8C, 0x8D, 0x8E, 0x8F, 0x90, 0x91, 0x92,
    # track 7
    0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A,
    0x9B, 0x9C, 0x9D, 0x9E, 0x9F, 0xA0, 0xA1, 0xA2,
    # track 8
    0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA,
    0xAB, 0xAC, 0xAD, 0xAE, 0xAF, 0xB0, 0xB1, 0xB2,
    # track 9 (11 entries, then $00 terminator)
    0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA,
    0xBB, 0xBC, 0xBD,
]

START_TRACK = 5   # Phase 0 start track.
BYTES_PER_SECTOR = 256
SECTORS_PER_TRACK = 16


def main() -> None:
    if not DSK.exists():
        print(f"ERROR: {DSK} not found", file=sys.stderr)
        sys.exit(1)
    disk = DSK.read_bytes()

    # Image ends at $BDFF (last page loaded is $BD). We size it to $BE00.
    image_size = 0xBE00
    image = bytearray(image_size)

    idx = 0  # index into PAGE_TABLE_RELOAD
    for track_offset in range(5):  # tracks 5..9
        track = START_TRACK + track_offset
        # Consume at most 16 sectors' worth of entries for this track.
        sector = 0
        while sector < SECTORS_PER_TRACK and idx < len(PAGE_TABLE_RELOAD):
            dest_page = PAGE_TABLE_RELOAD[idx]
            # Read physical sector `sector` of this track from the .dsk.
            logical = DOS_SKEW[sector]
            dsk_off = track * 4096 + logical * BYTES_PER_SECTOR
            sector_bytes = disk[dsk_off:dsk_off + BYTES_PER_SECTOR]
            if len(sector_bytes) != BYTES_PER_SECTOR:
                print(f"ERROR: short read at track {track} phys sec {sector}",
                      file=sys.stderr)
                sys.exit(1)
            dest_addr = dest_page * 0x100
            image[dest_addr:dest_addr + BYTES_PER_SECTOR] = sector_bytes
            sector += 1
            idx += 1

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(image)
    print(f"Wrote {OUT} ({len(image)} bytes, pages $00-${(image_size-1)>>8:02X}).")
    print(f"Loaded 79 sectors from tracks 5-9 into level-specific pages.")


if __name__ == "__main__":
    main()
