---
name: level1 pages 75-7A decomposition
description: $7500-$7AFF in level1.asm now split into 10 L1_-prefixed sub-chunks mirroring drol.bin's pointer tables + PILLAR_SPR frames + HIT_SPR_NEG head
type: project
---

The raw-HEX `<<level1 pages 75-7A>>` chunk ($7500-$7AFF, 1536 bytes) was
byte-identical to the corresponding drol.bin range and now decomposes to:

- `L1_SPRITE_POINTER_TABLES_LO` at $7500 (256 bytes; mirror of drol's
  37-subtable LO half + null pad)
- `L1_SPRITE_POINTER_TABLES_HI` at $7600 (256 bytes; HI half)
- `L1_PILLAR_SPR_DATA_0..6` at $7700-$7AD3 (7 × 140 bytes)
- `L1_HIT_SPR_NEG_DATA_0` at $7AD4 (40 bytes)
- `L1_HIT_SPR_NEG_DATA_1_HEAD` at $7AFC (4 bytes - partial, remaining 36
  bytes fall into drol.bin's persistent $7B00-$7B23 range)

**Why:** labels remain `L1_`-prefixed to avoid symbol clashes with the
authoritative drol symbols at the same runtime addresses. Pattern
matches the earlier `L1_LVL_INIT_*` decomposition of page 02.

**How to apply:** when writing future memory notes about swappable vs
persistent regions, the boundary cut at $7AFC is a real in-game artifact
(the last 4 bytes of a 40-byte sprite frame sit in the swappable window,
the rest in persistent). Not a disassembly mistake.

**Gotcha:** decomposing this level1 HEX blob does NOT require duplicating
all 37 pointer-table sub-labels. The L1_SPRITE_POINTER_TABLES_LO /
SPRITE_POINTER_TABLES_HI labels just wrap the 256-byte halves with a
comment cross-referencing the drol-side decomposition, keeping symbol
churn proportional to value.
