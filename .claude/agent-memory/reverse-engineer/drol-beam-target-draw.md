---
name: Drol BEAM_TARGET_DRAW at $1297
description: Beam trail sprite draw + 4-slot enemy collision; hit band is col (23,25] and Y-delta (0,3]; +$0100 BCD on hit
type: project
---

$1297 BEAM_TARGET_DRAW is one of three sub-handlers called from BEAM_UPDATE ($130A). Renders a 2-wide variable-height trail sprite (clamped to 4 rows max) at column $24, row BEAM_Y using BEAM_SPR ($B529) — sprite id 0 of the SPRITE_TABLE family. Then walks a 4-slot enemy table (ZP_ENEMY_FLAG/COL/Y at $9B/$9F/$A3) and hit-tests each active slot.

Hit criteria (AND):
- `PROJ_SCREEN_COL[ZP_ENEMY_COL,X]` in `($23, $25]` — i.e. col in {$24, $25} (one column of slop either side of the beam's sprite column $24).
- `ZP_ENEMY_Y,X` in `(BEAM_Y, BEAM_Y+3]` — a 3-row band immediately below the beam's current top row.

On hit: ZP_ENEMY_FLAG,X <- $00; BEAM_STATE <- $00; ZP_BEAM_SND_CTR <- $0A (arms 10-note jingle in BEAM_TARGET_TICK); SCORE += $0100 BCD via SCORE_ADD. Bails out of the slot loop via RTS on first hit (doesn't check remaining slots).

**Why:** Earlier prose at $1297 got the column-range direction wrong (claimed `[$23, $25)` which is closed-open; actually open-closed `($23, $25]`). Traced the CMP/BCC/BCS pair carefully: `#$25 CMP col; BCC skip` means skip when col > $25, and `#$23 CMP col; BCS skip` means skip when col <= $23, so the accept range is col in $24..$25. Save this if RE'ing neighboring collision code that uses the same `#$imm CMP abs,Y` idiom.

**How to apply:** When the player enters a score bracket that flips ZP_PROJ_GATE (via DIFFICULTY_UPDATE at $719D) to $01, BEAM_UPDATE runs this routine each frame — any collision with one of the 4 tracked enemy slots at the narrow column band clears the slot and awards 100 BCD. The 4 slots are distinct from FLOOR_ENEMY's 4 slots; ZP_ENEMY_FLAG ($9B) aliases with KEY_ESC in the input dispatcher for different subsystems.
