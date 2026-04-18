---
name: Drol perspective-grid sprite-pointer tables
description: Six sprite-pointer table pairs at $7542-$75DB / $7642-$76DB drive DRAW_ENTITIES phases 2-5 (small perspective-grid sprites)
type: project
---

The six `*_GRID_SPR_*` pointer-table pairs live inside the swappable
level-1 region at $7500-$76FF. They are distinct from DRAW_PLAYER's big
centre-screen tables (`PLAYER_SPR_IDLE`/`ACTIVE` at $7527/$7531) --- the
`_GRID_` tables drive the small perspective-grid sprites rendered by
`DRAW_ENTITIES` at $683C.

Labels introduced (all defined as EQUs inside `<<draw entities defines>>`):

- `PLAYER_GRID_SPR_A_LO/HI   = $7542/$7642` (16 entries, frame A)
- `PLAYER_GRID_SPR_B_LO/HI   = $7552/$7652` (16 entries, frame B)
- `SPECIAL_GRID_SPR_A_LO/HI  = $7594/$7694` (7 entries, frame A)
- `SPECIAL_GRID_SPR_B_LO/HI  = $759B/$769B` (7 entries, frame B)
- `COMPANION_GRID_SPR_LO/HI  = $75CC/$76CC` (8 entries, no animation)
- `ENTITY_GRID_SPR_LO/HI     = $75D4/$76D4` (25 entries, shared by 20 slots)

Frame A/B toggles on bit 2 of `$FD` (frame counter). All pointers resolve
to $8Bxx-$AFxx (per-level sprite-bitmap sheet, also in the swappable
$8C00-$BDFF region).

**Why:** these ranges sit inside the raw-HEX `<<level1 pages 75-7A>>`
chunk (a 1536-byte blob); labeling requires either splitting that chunk
or defining forward-reference EQUs in drol code. Same approach as
`LVL_INIT_*` at $029A-$02FF from the prior session.

**How to apply:** when RE'ing other levels' $7500-$76FF data or when
eventually splitting `<<level1 pages 75-7A>>` into labelled sub-chunks,
use these EQU names; convert the EQUs into real labels in level1 data
once the chunk is broken up.

**Watch out:** comments inside code chunks may NOT contain `<<name>>`
noweb chunk-reference syntax --- weave.py will expand them and corrupt
the tangled output. Initial draft had `(see <<level1 pages 75-7A>>)` in
a comment which caused the ORG ordering error
"INITIAL CODE SEGMENT 0100 vs current org: 7b00".
