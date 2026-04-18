---
name: Drol sprite pointer tables region ($7500-$76FF)
description: 512-byte 16-bit-pointer table region split into 37 sub-tables (LO/HI halves) referenced from DRAW_SPRITE callers
type: project
---

The [[$7500]]--[[$76FF]] region is a sprite-pointer-table block with 37 parallel LO/HI sub-tables, now properly labeled.

**Layout:**
- `$7500-$75FF` (`SPRITE_POINTER_TABLES_LO`): 37 sub-tables + $00 pad at $75FF.
- `$7600-$76FF` (`SPRITE_POINTER_TABLES_HI`): mirror layout with high bytes + $00 pad at $76FF.
- `$7700-$8BFF` (`SPRITE_PIXEL_DATA`): 5376 bytes of actual sprite pixel data referenced by the persistent pointers.

**Sub-table count per subsystem:**
- Playfield chrome (pillar/floor/wall/hit): 6 tables, 7-11 entries each
- Player body (idle + active + grid A/B): 4 tables, 7-10 entries
- Special slot (4 poses + 2 grid frames + peek): 7 tables
- Companion (6 poses + 1 grid): 7 tables, 7-8 entries
- Enemy-C tail + puffs (C/B/peek, 1 each): 4 tables
- Floor enemies (4 slots × 7 frames): 4 tables
- Entity grid: 1 table (7 entries)
- Rescue (2 dirs × 2 phases): 4 tables
- Projectile (right-moving only, 8 entries): 1 table

**Why:** Round RE'd the single HEX blob and split into labeled chunks; 74 EQUs (low+high per table) removed in favor of proper labels inside the three new data chunks. The persistent pointer-table region is now navigable in the PDF; the 5376-byte pixel data chunk is kept as raw HEX because per-frame rendering requires per-subsystem W/H knowledge (future round).

**How to apply:**
- When RE'ing or naming new sprite-related code, reference the existing LO/HI label pairs; they are the canonical names.
- The left-moving projectile table `PROJ_SPR_L_LO/HI` at `$AFD3/$B053` lives in the SWAPPABLE level-data region, not drol.bin.
- Per-level variable sprites (grid body / floor-enemy / companion / rescue / special body) have their pointers in drol.bin but pixel data in the swappable `$8C00-$BDFF` range; each level can change art without rewriting pointers.
- Rendering per-frame: a future round should iterate each LO/HI pair, pull W/H from the specific DRAW_SPRITE caller, and emit one PNG per frame.
