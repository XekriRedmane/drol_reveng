---
name: Drol rescue-children subsystem
description: RESCUE_UPDATE at $6F9C ticks the 20-slot rescue-child entity system; RESCUE_DRAW at $0C98 draws + collides + can spawn hostile projectiles; awards 35 BCD on player pickup
type: project
---

Drol's `RESCUE_UPDATE` at $6F9C is the per-frame tick for the 20-slot "rescue child" entity subsystem --- the small walking figures that appear on the perspective floors and are Drol's actual scoring objective. It is paired with `RESCUE_DRAW` at $0C98 (carved out of the $03A8 HEX blob 2026-04-17) and with `DRAW_ENTITIES` phase 5 at $694E (which draws the perspective-grid marker sprite).

**Why:** Drol's objective is rescuing children, not killing enemies (though both happen). RESCUE_DRAW awards +$0035 BCD on player-collision via `SCORE_ADD`, with NO `DEC $39` (so the collision is not a life-loss event).

**Surprise: RESCUE_DRAW also has a hostile path.** When a rescue child is on the player's floor, has odd row, and a free `$C5,X` projectile slot exists (X $\le$ ZP_PROJ_MAX $31$), the rescue child throws a hostile projectile (direction = its walking direction, X = its screen-X, Y = its row). This is the third gate beyond the two collision tests. So "rescue children" are NOT pure friendlies --- they harass the player on the same floor.

**How to apply:** When RE'ing any routine that touches $0358/$036C/$0380/$03A8 (shared with DRAW_ENTITIES phase 5) or the private tables $0394/$03BC/$03D0/$03E4, consult this summary:

**Slot record (20 slots, indexed by Y in 0..$13):**
- `ENTITY_ACTIVE` ($03A8,Y): state machine byte (see below).
- `ENTITY_FLOOR_COL` ($0358,Y): world-X low (also exit-anim counter and drift-rearm seed).
- `ENTITY_XOFF_IDX` ($036C,Y): world-X high (carry propagates from lo).
- `ENTITY_FLOOR_POS` ($0380,Y): row Y (bobbled by RESCUE_BOBBLE during steps).
- `RESCUE_DIR` ($0394,Y): direction, $01 right / $FF left.
- `RESCUE_ANIM` ($03BC,Y): step anim counter (8..1; 0 = ready for next step).
- `RESCUE_FLOOR` ($03D0,Y): assigned floor index (static per slot).
- `RESCUE_COUNTDOWN` ($03E4,Y): drift rearm countdown (4 every-other-frame ticks).

**State machine on $03A8,Y (RESCUE_UPDATE side):**
- $00: inactive. Try to spawn. PRNG-gate (1/256) AND $4D counter residue == 3 (every 4th slot in pass), OR one-shot player-floor trigger (if RESCUE_FLOOR,Y == $0C and $1F < $10). Direction alternates by slot parity.
- $01..$7F: active walking. Chase AI runs when player on same floor ($0C == $03D0,Y).
- $FE: exit animation. INC $0358,Y, deactivate on wrap to 0.
- other negative: drift countdown. DEC $03E4,Y every 2 frames (gated on $FD bit 0); on 0, reseat floor-col from $34 (ZP_DIFF_THRESH_A) and transition to $FE.

**RESCUE_DRAW side ($0C98) per-slot dispatch:**
- $00: skip.
- +ve (active): compute screen-X residue $AF, draw body (sprite tables $75DB/$75E2/$75E9/$75F0 + $76DB/$76E2/$76E9/$76F0; pick by RESCUE_DIR sign and RESCUE_ANIM in {0,7,8} = end-step h=$1A vs mid-step h=$1C), then run 3 collision/spawn checks.
- $FE: skip (invisible during exit).
- other -ve (drift): play descending click ($0213,X pitch via SND_DELAY_DOWN), patch SMC_SPRITE_MASK_OP $65B7 to $29 (AND #imm flicker), draw body, then SKIP collision (drift is invulnerable). Restore $65B7 to $24 on exit.

**Collision/spawn block (ONLY for +ve active state, $0DAB-$0E50):**
1. **Floor-enemy overlap** ($0DAB-$0DEF): walk 4-slot $9B,X table; if any enemy at same X (within 10 px) and Y (within $42/$43 band), clear $9B,X, set ENTITY_ACTIVE,Y=$FF (drift), RESCUE_COUNTDOWN,Y=$04, +$0035 BCD via SCORE_ADD ($121A). Both die.
2. **Player pickup** ($0DF0-$0E11): screen-X in [$40, $50) AND ZP_PLAYER_COL ($06) within [entity_row-$12, entity_row+$19]: set ZP_HIT_FLAG ($1E)=$FF, JMP into shared reward path at $0DD8. NO `DEC $39` --- not a life-loss.
3. **Hostile projectile spawn** ($0E13-$0E50): if entity row is odd AND RESCUE_FLOOR,Y == ZP_PLAYER_FLOOR_CUR ($0C) AND first empty $C5,X slot found (X iterates $31 down to 0): seed $C5,X=RESCUE_DIR, $CD,X=row, $C9,X=screen-X. Play $0D-pitch SND_DELAY_DOWN (X=$0A) click. Projectile then handled by HAZARD_CHECK on subsequent frames.

**Spawn parameters (RESCUE_UPDATE side):**
- +dir spawn: world-X = $003E (left edge), RESCUE_DIR = $01.
- -dir spawn: world-X = $035C (right edge), RESCUE_DIR = $FF.
- Row = FLOOR_THRESH[RESCUE_FLOOR] - 7.

**One-shot BIT/JMP opcode patch at $705F:**
- Disk-image byte = $2C (BIT). First time the player-floor trigger fires in a pass, patched to $4C (JMP) so subsequent floor-matching slots fall through to .slot_next. Restored to $2C at the pass exit (after DEY BPL loop falls through).

**Private slot-iteration counter $4D (`ZP_RESCUE_SPAWN_CTR`):**
- Incremented once per processed slot in RESCUE_UPDATE; NEVER cleared anywhere in the game. Free-running mod-256 counter. Read only by RESCUE_UPDATE (both spawn paths depend on its low 1 or 2 bits).

**Meet-player chase AI ($713F-$719C):**
- Computes entity's screen-X = FLOOR_BASE_ROW[$0358,Y] + $B9[$036C,Y] (mapped via byte-domain perspective table).
- Compares against ZP_PLAYER_Y ($4A); flips direction (+/-1) to walk toward player.
- If direction is already correct, takes one step; if wrong, flips direction and stalls the anim counter to $08 for one step-cycle.

**RESCUE_BOBBLE ($BD) 7-byte signed delta table:**
- bit 7 = sign (0 ascend, 1 descend); bits 0..6 = |delta|.
- Indexed by the current anim counter (1..7). Produces the child's characteristic bobbing vertical motion while walking.
- Lives in the $88..$B4 staging-copy buffer; initial values copied from $02DF..$02E5 by INIT_LEVEL_STATE.

**RESCUE_DRAW pre-compute helper at $0D8C (`RESCUE_DRAW_PERSPECTIVE_CACHE`):**
- Caches `PERSPECTIVE_XOFF_LO[ZP_PLAYER_Y] - ZP_SPRITE_XREF` into ZP_PERSP_OFFSET_LO/HI ($0F/$10) once per call; each per-slot loop subtracts from ENTITY_FLOOR_COL/XOFF_IDX to derive the entity's screen-X residue $AF.

**Drift-state pitch table `RESCUE_DRIFT_PITCH` at $0213:**
- 4-entry table indexed by RESCUE_COUNTDOWN (1..4); plays 4 descending tones during the 4-frame drift countdown after a hit/pickup.
