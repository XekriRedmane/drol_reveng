---
name: ATTRACT_SPR2 and adjacent UI sprite labels
description: ATTRACT_SPR2_0..3 carved out of $B571-$B5FC, plus READY_PROMPT_SPR at $B535 and BEAM_SPR_DATA at $B529 now live in standalone labeled chunks
type: project
---

Four attract-mode drifting silhouettes now have data-labels:
  ATTRACT_SPR2_0 at $B571 (42 bytes, W=2 H=14)
  ATTRACT_SPR2_1 at $B59B (42 bytes, W=2 H=14, 10-byte $00 lead-in)
  ATTRACT_SPR2_2 at $B5C5 (28 bytes, W=1 H=14, 8-byte $00 lead-in)
  ATTRACT_SPR2_3 at $B5E1 (28 bytes, W=1 H=14, the stripe-bar)

Consumed by ATTRACT_ANIM_2 ($17E1) via pointer table ATTRACT_SPR2_LO/HI at $B002/$B082.

BEAM_SPR_DATA ($B529, 12 bytes, sprite-table id 0) and READY_PROMPT_SPR
($B535, 60 bytes = W=3 H=15, sprite-table id 1) are the adjacent sub-chunks.
Renderer at .claude/scripts/render_attract_spr2.py.

Why: These addresses were raw $XXXX in prose; lifting them to labels removes
the need for the "at [[$B571]]" style of reference in the attract-mode
title-sprite documentation. Also unlocks the prose rule that forbids raw
addresses when a symbol exists.

How to apply: level1-target only — drol.asm never references these data
addresses directly (it indexes through ATTRACT_SPR2_LO/HI). Future data
labels in the $B500-$BCFF level1 sprite blob should follow the same pattern:
split the monolithic `<<level1 pages 8C-BD tail>>` chunk at label
boundaries with sub-labels and appropriate @ %def lines.
