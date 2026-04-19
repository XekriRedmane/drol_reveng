---
name: ENEMY_C_TAIL unused frames 7-8
description: ENEMY_C_TAIL_LO ships 9 pointer entries but ENEMY_C_DRAW only indexes 0..6; frames 7-8 are residue
type: project
---

ENEMY_C_TAIL_LO / ENEMY_C_TAIL_HI at $755A / $765A in drol.bin have nine pointer entries ($8C10 $8C1E $8C2C $8C3A $8C48 $8C56 $8C64 $8C72 $8C79), but ENEMY_C_DRAW indexes the table with X = PROJ_FRAME_IDX which only ranges 0..6. Frames 7 and 8 (at $8C72 and $8C79, 7 bytes and 14 bytes respectively) are never reached at runtime. They are kept as labelled residue (ENEMY_C_TAIL_DATA_7 / ENEMY_C_TAIL_DATA_8) because the high-byte side of the pointer table explicitly lists their page bytes — the pointers are live data even if unused.

**Why:** Pattern matches FLOOR_SPR_LO which has 11 entries and also labels all 11 FLOOR_SPR_DATA_* frames despite only some being indexed. Consistent "label every pointer target, even unreached" approach prevents future rounds from treating these bytes as a different decomposition.

**How to apply:** When decomposing level1 sprite-pixel-data regions, check the LO/HI pointer table entry count against the draw routine's actual index range. Extra entries beyond the used range still get labelled chunks.
