---
name: Drol $0274-$0299 dead-residue decomposition
description: 38-byte gap between ROW_COPY_BUFFER and LVL_INIT_HIT_Y split into 4 dead-sub-labels; also LVL_INIT headpiece chunks extracted
type: project
---

$0274-$0299 in drol.bin (38 bytes between ROW_COPY_BUFFER at $024C-$0273 and LVL_INIT_HIT_Y at $029A) is cold-start residue: non-zero pattern in drol.bin, all $00 in level1.bin (phase-0 reload target). No absolute reference in any shipped binary.

Decomposed into four labeled chunks:
- PAGE2_DEAD_ZEROS ($0274, 13 bytes of $00)
- PAGE2_DEAD_DITHER ($0281, 10 bytes D4 82 x5 — hi-res stripe pattern)
- PAGE2_DEAD_SEP ($028B, one $2A byte)
- PAGE2_DEAD_RECORDS ($028C, 14 bytes = two 7-byte records that look like pre-release entity-init payload)

Also extracted LVL_INIT headpiece data out of the row-copy-data blob into their own chunks:
- LVL_INIT_HIT_Y_DATA ($029A)
- LVL_INIT_ENTITY_DATA ($029C)
- LVL_INIT_SPRITE_HEAD ($02B5)

**Why:** The 38-byte dead span had been a "miscellaneous initial data (not yet per-consumer RE'd)" HEX blob for many rounds. Splitting into semantic sub-labels + confirming via level1.bin zeros that the whole span is transient residue gave a cleaner document.

**How to apply:** When a future round needs to reference any byte in $0274-$0299, use the new sub-labels (PAGE2_DEAD_ZEROS/DITHER/SEP/RECORDS). The LVL_INIT_*_DATA chunks are the canonical emitters; the EQUs LVL_INIT_HIT_Y / LVL_INIT_ENTITY / LVL_INIT_SPRITE in init-level-state defines still point at these labels' addresses.
