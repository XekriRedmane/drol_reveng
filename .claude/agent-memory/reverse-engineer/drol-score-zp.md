---
name: Drol BCD score at $D1/$D2/$D3
description: BCD score bytes live at $D1/$D2/$D3 — named ZP_SCORE_HI/MID/LO. Labels previously in main.nw used "ZP_ENTITY_D*" which was a misguess.
type: project
---

The 3-byte BCD score lives at `$D1` (high), `$D2` (mid), `$D3` (low) — labelled
`ZP_SCORE_HI` / `ZP_SCORE_MID` / `ZP_SCORE_LO`.  Confirmed by three
independent routines: `SCORE_ADD` at $121A (BCD add), `POST_FRAME` at $10CF
(digit display: D1 lo-nibble drawn at col 2, D2 hi-nibble at col 4, D2 lo at
col 6, D3 hi at col 8, D3 lo at col $0A), and `LEVEL_TRANSITION` at $116C
(BCD compare against high-score bytes at $20/$21/$22).  High nibble of $D1
is never displayed, so the on-screen score is 5 digits (max 99999).

`DIFFICULTY_UPDATE` ($719D) builds a tier index from `(D1_lo << 4) | (D2_hi >> 4)`
and thresholds it against $04/$10/$18 — effectively bracketing scores
<4000 / 4000--9999 / 10000--17999 / 18000+.

**Why:** Previous RE had these bytes mis-labelled as `ZP_ENTITY_D1/D2/D3`.
The rename is done in main.nw as of 2026-04-17.

**How to apply:** When a ZP read hits $D1, $D2, or $D3, expect score context,
not entity state.  The score appears in BCD mode (`SED`) in SCORE_ADD and
LEVEL_TRANSITION.
