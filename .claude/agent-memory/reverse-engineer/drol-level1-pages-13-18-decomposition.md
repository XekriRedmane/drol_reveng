---
name: level1 pages 13-18 decomposition
description: $1300-$18FF swappable region split into 15 L1_-prefixed sub-chunks mirroring drol's 14 routines
type: project
---

The `<<level1 pages 13-18>>` raw HEX blob ($1300-$18FF, 1536 bytes) was
decomposed into 15 labelled sub-chunks mirroring drol's routine
decomposition:

- L1_BEAM_TARGET_DRAW_TAIL ($1300-$1309, 10 bytes) — tail of BEAM_TARGET_DRAW
- L1_BEAM_UPDATE ($130A-$13A3, 154 bytes)
- L1_GAME_START_INIT ($13A4-$13D5, 50 bytes)
- L1_ENEMY_A_ADVANCE ($13D6-$1422, 77 bytes)
- L1_ENEMY_A_DRAW ($1423-$1535, 275 bytes)
- L1_ENEMY_B_ADVANCE ($1536-$1590, 91 bytes)
- L1_ENEMY_B_DRAW ($1591-$1645, 181 bytes)
- L1_ENEMY_C_ADVANCE ($1646-$16AB, 102 bytes)
- L1_ENEMY_C_DRAW ($16AC-$17A5, 250 bytes)
- L1_ATTRACT_ANIM_1 ($17A6-$17E0, 59 bytes)
- L1_ATTRACT_ANIM_2 ($17E1-$1812, 50 bytes)
- L1_ATTRACT_ANIM_3 ($1813-$1843, 49 bytes)
- L1_ATTRACT_ANIM_4 ($1844-$1889, 70 bytes)
- L1_FLOOR_BASE_ROW_PAD ($188A-$188E, 5 bytes)
- L1_FLOOR_BASE_ROW_HEAD ($188F-$18FF, 113 bytes)

**Why:** level1.bin's $1300-$18FF span is byte-identical to drol.bin's
same window. Previously emitted as a single 1536-byte HEX blob; now
mirrors drol's decomposition with L1_-prefix labels.

**How to apply:** Two level1 swappable-window boundary artifacts: (1)
L1_BEAM_TARGET_DRAW_TAIL is only 10 bytes — the routine's real entry at
$1297 sits in the persistent drol.bin window ($0100-$12FF); (2)
L1_FLOOR_BASE_ROW_HEAD is only the first 113 of 256 entries — the tail
143 bytes ($1900-$198E) live in persistent pages 19-1F.

Pitfall during generation: `<<level1 pages 13-18>>` chunk name kept but
was ambiguous; replaced with per-label chunk names in the collection
chunk (`<<level1 beam target draw tail>>`, `<<level1 beam update>>`,
etc.) listed in ORG address order between `<<level1 lvl init input
data>>` and `<<level1 gap 2>>`.
