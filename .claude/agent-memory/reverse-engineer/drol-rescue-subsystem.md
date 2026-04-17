---
name: Drol rescue-children subsystem
description: RESCUE_UPDATE at $6F9C ticks the 20-slot rescue-child entity system; sibling draw+collision at $0C98 awards 35 BCD on player pickup
type: project
---

Drol's `RESCUE_UPDATE` at $6F9C is the per-frame tick for the 20-slot "rescue child" entity subsystem --- the small walking figures that appear on the perspective floors and are Drol's actual scoring objective. It is paired with a sibling draw-plus-collision routine at `$0C98` (still inside the $03A8..$0C97 HEX blob) and with `DRAW_ENTITIES` phase 5 at $694E (which draws the perspective-grid marker sprite).

**Why:** Drol's objective is rescuing children, not killing enemies (though both happen). The rescue subsystem is what triggers the score-per-rescue reward; identifying it as "rescue" was confirmed by the sibling draw at $0C98 awarding +$0035 BCD on player-collision via `SCORE_ADD`, with NO `DEC $39` (so the collision is not a life-loss event).

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

**State machine on $03A8,Y:**
- $00: inactive. Try to spawn. PRNG-gate (1/256) AND $4D counter residue == 3 (every 4th slot in pass), OR one-shot player-floor trigger (if RESCUE_FLOOR,Y == $0C and $1F < $10). Direction alternates by slot parity.
- $01..$7F: active walking. Chase AI runs when player on same floor ($0C == $03D0,Y).
- $FE: exit animation. INC $0358,Y, deactivate on wrap to 0.
- other negative: drift countdown. DEC $03E4,Y every 2 frames (gated on $FD bit 0); on 0, reseat floor-col from $34 (ZP_DIFF_THRESH_A) and transition to $FE.

**Spawn parameters:**
- +dir spawn: world-X = $003E (left edge), RESCUE_DIR = $01.
- -dir spawn: world-X = $035C (right edge), RESCUE_DIR = $FF.
- Row = FLOOR_THRESH[RESCUE_FLOOR] - 7.

**Pickup logic (in sibling draw at $0C98):**
- Tested AFTER the 4-slot floor-enemy collision check (same $9B/$9F/$A3 table enemy-C uses).
- Player-catch hit-box: screen-X in [$40, $50) AND floor_pos in [player_col-$19, player_col+$12].
- On pickup: writes `$FF` to `ZP_HIT_FLAG` $1E, transitions slot to drift ($FF), rearm countdown = 4, awards +$0035 BCD (35 decimal) via `SCORE_ADD`. No DEC $39.

**Floor-enemy kill (incidental, in sibling draw):**
- Entity overlapping an active floor-enemy slot (index X 0..3): clears `$9B,X`, same +$0035 BCD reward, same drift transition. Both die together.

**One-shot BIT/JMP opcode patch at $705F:**
- Disk-image byte = $2C (BIT). First time the player-floor trigger fires in a pass, patched to $4C (JMP) so subsequent floor-matching slots fall through to .slot_next. Restored to $2C at the pass exit (after DEY BPL loop falls through).

**Private slot-iteration counter $4D:**
- Named `ZP_RESCUE_SPAWN_CTR`. Incremented once per processed slot; NEVER cleared anywhere in the game. Free-running mod-256 counter. Read only by this routine (both spawn paths depend on its low 1 or 2 bits). Not used by any other routine in drol.bin.

**Meet-player chase AI ($713F-$719C):**
- Computes entity's screen-X = FLOOR_BASE_ROW[$0358,Y] + $B9[$036C,Y] (mapped via byte-domain perspective table).
- Compares against ZP_PLAYER_Y ($4A); flips direction (+/-1) to walk toward player.
- If direction is already correct, takes one step; if wrong, flips direction and stalls the anim counter to $08 for one step-cycle.

**RESCUE_BOBBLE ($BD) 7-byte signed delta table:**
- bit 7 = sign (0 ascend, 1 descend); bits 0..6 = |delta|.
- Indexed by the current anim counter (1..7). Produces the child's characteristic bobbing vertical motion while walking.
- Lives in the $88..$B4 staging-copy buffer; initial values copied from $02DF..$02E5 by INIT_LEVEL_STATE.
