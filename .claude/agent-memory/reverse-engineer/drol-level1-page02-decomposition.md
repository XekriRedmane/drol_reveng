---
name: Level-1 page 02 decomposition
description: <<level1 page 02>> HEX blob decomposed into 11 L1_-prefixed sub-chunks mirroring drol's $0200-$02FF split
type: project
---

Level-1 page $0200-$02FF is byte-identical to drol.bin's page $0200-$02FF.
Previously it lived in level1.asm as a single 256-byte `<<level1 page 02>>` HEX
blob; now it's 11 labeled sub-chunks (`L1_LEVEL_INTRO_TONES`,
`L1_RESCUE_DRIFT_PITCH`, `L1_SND_PITCH_TBL_SPECIAL/C/A_TAIL/B`, `L1_TRACER_STATE`,
`L1_TRACER_ROW`, `L1_BEAM_JINGLE`, `L1_ROW_COPY_BUFFER`, `L1_PAGE2_DEAD_ZEROS`,
`L1_PAGE2_DEAD_DITHER`, `L1_PAGE2_DEAD_SEP`, `L1_PAGE2_DEAD_RECORDS`,
`L1_LVL_INIT_HIT_Y_DATA`, `L1_LVL_INIT_ENTITY_DATA`, `L1_LVL_INIT_SPRITE_HEAD`,
`L1_LVL_INIT_ENTITY_HIT_STATE`, `L1_LVL_INIT_SPRITE_TAIL_DATA`,
`L1_LVL_INIT_INPUT_DATA`) that mirror the drol decomposition.

**Why:** level1.asm assembles standalone, so it needs its own label scope; but
since it carries the same bytes as drol at the same ORG, mirroring the drol
chunk structure with an `L1_` prefix gives symmetric navigation without
colliding against drol symbols in the cross-target defines.

**How to apply:** when further decomposing level1.asm HEX blobs (e.g.
`<<level1 pages 13-18>>`, `<<level1 pages 67-72>>`, `<<level1 pages 75-7A>>`,
`<<level1 pages 8C-BD>>`), use the same `L1_` prefix policy and mirror
whatever drol decomposition exists at the shared address. The bytes are
identical across the shared persistent pages ($0200, $1300-$18FF,
$6700-$72FF, $7500-$7AFF); only $8C00-$BDFF is level-1-unique content.
