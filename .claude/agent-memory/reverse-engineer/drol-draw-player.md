---
name: Drol DRAW_PLAYER at $64DF
description: Main-loop player sprite renderer; two paths (idle/action) keyed on $02/$03; self-mods its own operands for intro/complete patches
type: project
---

DRAW_PLAYER at $64DF is called from MAIN_LOOP's SMC_RENDER slot ($67EF, toggled $20/$2C for attract). It is NOT called from DRAW_ENTITIES; DRAW_ENTITIES phase-2 draws a different, smaller perspective sprite (tables $7542/$7552 vs DRAW_PLAYER's $7527/$7531).

Why: The main centre-screen player body (column $14, size $03x$13 idle or $03x$14 active) is rendered here. Phase-2 of DRAW_ENTITIES is a small $01x$04 perspective-grid sprite at FLOOR_SCREEN_COL[$4A+$10], which is the player's depth-axis representation. $0E gates phase-2 (intro wait flag), not the main player draw.

How to apply: when tracing player rendering issues, DRAW_PLAYER is the big-sprite path; DRAW_ENTITIES phase-2 is the small-perspective path. The two use distinct sprite-pointer tables and are gated by different ZP flags ($02 for DRAW_PLAYER, $0E for phase-2).

Action-path flicker: for ZP_PLAYER_STANCE == $03 (top floor) or $09 (bottom floor) and ZP_HIT_FLAG > 0, a "teleport flicker" pre-pass uses the routine's own code bytes at $6500/$6600 as a pseudo-random static source (LDA $6500,$FD / LDA $6600,$FD AND $7F), masked through SMC_SPRITE_MASK_OP set to AND #$83 / #$B0.

SMC operands: SMC_SR_HEIGHT ($64F6, the #$13 operand of "LDA #$13") and SMC_SR_YSRC ($64FA, the $06 operand of "LDA $06") are patched by LEVEL_INTRO_TICK during the countdown (shrink + re-point at ZP_INTRO_Y) and reset by LEVEL_COMPLETE ($13 / $06). Prior docs misnamed these "SMC_COLLISION_A/B" — they are not collision params.

ZP: ZP_ACTION_DIR = $02 ($00 idle, $01 ascend, $FF descend — set by INPUT_DO_ASCEND/DESCEND). ZP_PLAYER_STANCE = $03 (clamped $03..$09 by the input handlers — $03 = top floor, $09 = bottom floor).
