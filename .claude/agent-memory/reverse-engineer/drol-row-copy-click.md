---
name: Row-copy click and dead wipe-click variants
description: $01B7 ROW_COPY_CLICK emits one SND_DELAY_UP per row during title-wipe; $01C4-$01EE is dead code (PRNG-driven variant that was superseded)
type: project
---

ROW_COPY_CLICK at $01B7 (13 bytes) is the per-row audio hook for the SCREEN_ROW_COPY title wipe. It saves X to ZP $5C, computes pitch = X/4, calls SND_DELAY_UP with pitch in A and duration=4 in X, then restores X. The rising pitch (0-$2F over the 192-row sweep) is the "zipper" whistle that accompanies Drol's screen-fill transitions.

$01C4-$01EE is dead code — no JSR/JMP anywhere in any shipped binary reaches it. Contents:
- $01C4: orphan bare RTS
- $01C5 ROW_COPY_CLICK_RANDOM: rolls PRNG, dispatches on result ($>=$20 → short delay; $10-$1F → 8-click tone loop through SFX_TONE with descending pitch; $<$10 → short delay)
- $01E9 ROW_COPY_CLICK_GATE: pre-gate that only enters RANDOM when ZP_ANIM_COUNTER >= $09

The structure suggests an earlier, richer wipe-click design that was replaced by the plain ascending tone (ROW_COPY_CLICK) but left in place. $01EF has a stray `A9 00` (LDA #$00) followed by stack-page-tail zeros.

Why: The $01B7 chunk was previously a single 259-byte HEX blob labelled SCREEN_ROW_HELPER; promoting it to properly RE'd code clarifies that the shipped wipe uses ONLY the pitch-rising click, not any PRNG-driven variants.

How to apply: When seeing JSR SCREEN_ROW_HELPER in older notes, it now reads JSR ROW_COPY_CLICK. The three dead-code labels exist for documentation completeness but are never executed. The `SND_PITCH_TBL_A/B/C` labels ($0229/$0231/$0224) live inside the initial-data-tables region on page 2 ($0200-$02B6), not inside the code blob.
