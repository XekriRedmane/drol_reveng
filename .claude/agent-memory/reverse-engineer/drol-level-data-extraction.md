---
name: Drol level-1 extraction from drol.dsk
description: Replay loader phase-0 (tracks 5-9) with PAGE_TABLE_RELOAD + DOS skew to reach $8C00-$BDFF sprite data
type: reference
---

drol.bin covers $0100-$8BFF and contains persistent game code + whatever
level happened to be loaded at extract time. Most sprite pointer tables in
drol.bin (at $7527..$76F7) point to sprite data in the **swappable level
region** $8C00-$BDFF (and parts of $9D00+) which is beyond drol.bin.

To reach that data use `.claude/scripts/extract_level1.py`, which replays
the Drol loader's phase-0 track read (tracks 5..9) against `drol.dsk`:

- Uses the documented PAGE_TABLE_RELOAD at $5440 (see main.nw <<page table>>)
- Physical sector P of track T → .dsk offset `T*4096 + DOS_SKEW[P]*256`
  where DOS_SKEW = [0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15] (CLAUDE.md)
- Output: reference/level1.bin, flat 48640-byte image base $0000

The $7500-$7AFF and $1300-$18FF ranges in level1.bin match drol.bin
byte-for-byte (sanity check: drol.bin was built from the same level-1
state), so it's only the additional pages $8C00-$BDFF (and $0200,
$6700-$72FF, $75xx, $8C-$BD) that level1.bin adds.

**Why:** Without level1.bin, sprite renderers can't reach the actual
pixel bytes for enemy/special/companion/rescue/projectile art.

**How to apply:** Pass `base=0x0000` to decode_sprite/render_sprite_image
when reading from level1.bin; `base=0x0100` when reading from drol.bin.
The `render_sprite_tables.py` script shows both patterns.

Phases 1-3 (tracks 10/15/20) load the same destination pages with
different content — would produce level-2/3/4 binaries. Not yet extracted;
the task only needed the level-1 sprite set.
