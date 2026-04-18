---
name: Drol level-state init blocks at $029A-$02FF
description: INIT_LEVEL_STATE ($11B8) copies 4 per-level buffers from $029A-$02FF in swappable page-02 data into ZP
type: project
---

The four level-state init source buffers live contiguously at $029A-$02FF in the
swappable per-level region (loaded from track-5+ sector 0 by the level loader).
Every level has a distinct payload, so identical ZP destinations end up
parameterized per level.

Labels introduced:

- `LVL_INIT_HIT_Y  = $029A` (2 bytes) -> `ZP_HIT_Y_OFFSET/$42`, `ZP_HIT_Y_SPAN/$43` - floor-enemy Y-window
- `LVL_INIT_ENTITY = $029C` (25 bytes) -> `ZP_ENTITY_BLOCK/$D4-$EC` - entity slot params
- `LVL_INIT_SPRITE = $02B5` (45 bytes) -> `ZP_SPRITE_BLOCK/$88-$B4` - sprite/collision state
- `LVL_INIT_INPUT  = $02E2` (30 bytes) -> `ZP_INPUT_BLOCK/$01-$1E` - input/direction state

**Why:** these buffers sit inside the raw-HEX `<<level1 page 02>>` chunk (a 256-byte
blob not yet structurally decoded). Adding labels at those addresses in the level
data would require splitting the HEX chunk; the labels are therefore defined as
EQUs inside the drol-code `<<init level state defines>>` chunk and resolve via
forward reference when drol.asm assembles.

**How to apply:** when RE'ing other levels' page-02 data or the level-transition
flow, use these EQU names; when eventually splitting level1 page 02 into labelled
sub-chunks, convert the EQUs to real labels in the level1 data.
