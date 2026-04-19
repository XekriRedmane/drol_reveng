---
name: Drol LEVEL_TRANSITION mirrors digit strip into BOTH pages
description: $116C high-score routine copies page-1 left-HUD digits into right-HUD on BOTH page 1 and page 2 (not just page 2 as old prose suggested)
type: project
---

LEVEL_TRANSITION at $116C is the level-complete high-score check. When the current BCD score exceeds the stored high score, it copies the new score and then mirrors six rows of the left HUD digit strip into the right HUD area — but not just to page 2 as the old prose claimed. It writes to BOTH page 1 and page 2.

Three 16-bit ZP scratch pointer pairs (only touched by this routine, no other callers):
- `ZP_HISCORE_SRC` = $23 — read pointer, page 1 row+$01 (left HUD strip, cols 1-10)
- `ZP_HISCORE_DST1` = $25 — write pointer, page 1 row+$1E (right HUD strip on page 1)
- `ZP_HISCORE_DST2` = $27 — write pointer, page 2 row+$1E (right HUD strip on page 2)

The inner loop `LDA (ZP_HISCORE_SRC),Y; STA (ZP_HISCORE_DST1),Y; STA (ZP_HISCORE_DST2),Y` is two stores per load — this is what made the prose misleading: it isn't "copy page 1 to page 2", it's "copy page 1's left HUD to the right HUD on BOTH pages".

**Why:** The effect is that once a new high score is set, the right-side HUD permanently displays it regardless of the hi-res display page selected by the flip. The left-side HUD continues to show the running score (updated each frame by POST_FRAME), so after a new high, the left is running-score and the right is the frozen-new-high on both pages.

**How to apply:**
- When reading any code around $23-$28 ZP, that's LEVEL_TRANSITION scratch and nothing else uses it.
- The old comments in the routine labelled `$23/$24` as "Dest pointer A" — that was backwards. $23 is source, $25/$27 are both destinations.
- Row range $0C..$11 ($0C, $0D, $0E, $0F, $10, $11) = six rows at the top of the hi-res area matching where POST_FRAME draws the digit sprites.
- SCREEN_ROW_ADDR_LO is shared between pages 1 and 2 (same row-base low byte); only HI differs.
