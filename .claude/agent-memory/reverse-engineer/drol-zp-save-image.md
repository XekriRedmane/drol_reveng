---
name: Drol ZP_SAVE at $5700 is the full cold-start zero-page image
description: 256-byte buffer at $5700 in loader.bin seeds every ZP variable on boot AND doubles as save/restore backing during level swaps
type: project
---

ZP_SAVE at $5700-$57FF (loader.bin) is not just a scratch save area — it is the canonical on-disk image of the whole zero page at cold start. FIRST_BOOT copies it byte-by-byte into $00-$FF before `JMP (ZP_GAME_ENTRY)` hands off to the attract loop. The same buffer is then reused as save/restore backing across level loads via SAVE_ZP (ZP -> $5700) and SEEK_AND_RESTORE_ZP ($5700 -> ZP).

Notable seeds visible in the cold-start image:
- $00 = $80 (ZP_PAGE_FLAG, b7 set skips first frame flip)
- $06 = $30 (ZP_PLAYER_COL starting column)
- $1E = $01 (ZP_HIT_FLAG = gameplay active, NOT intro — intro state is re-seeded at level start)
- $1F = $09 (ZP_ANIM_COUNTER)
- $36/$37 = $30/$C0 (ZP_SFX_CLICK = $C030 = SW_SPEAKER; the $C0 high byte is the game's "ZP $37" invariant)
- $4A = $6B (ZP_PLAYER_Y perspective-table index)
- $4E/$4F = $A3/$72 (ZP_GAME_ENTRY = $72A3 = START_ATTRACT — this is WHY boot lands in attract)
- $52/$53 = $61/$C0 (ZP_INPUT_1 = $C061 = SW_PUSH_BTN0)
- $54/$55 = $62/$C0 (ZP_INPUT_2 = $C062 = SW_PUSH_BTN1)
- $5E = $04 (ZP_LIVES_BCD = four lives)
- $D4/$DC/$E0 = $01 each (enemy A/B/C initially active)
- $F8 = $D0 (ZP_BEAM_TICK idle)

Why this matters:
- INIT_LEVEL_STATE (called at each level start) overwrites ZP $01-$B4 from LVL_INIT_ENTITY/SPRITE/INPUT (in the swappable level region $029A-$02FF), so most of ZP_SAVE's content is stale after the first level load. But $00, $20-$22 (high score), $36-$38 (sound), $4E/$4F (game entry), $5E (lives), $5F (PRNG), etc. are only ever set by the initial ZP_SAVE restore.
- The $5E = $04 "four lives" default is also visible in LVL_INIT_INPUT as offset 7 ($02E2+7 = $02E9 = $04), so per-level state matches the cold-start value.

**Why:** Understanding ZP_SAVE as the cold-start table explains why e.g. START_ATTRACT is the first code to run (it's the JMP indirect target from $4E/$4F), and why ZP_SFX_CLICK+1 ($37) silently equals $C0 without any code ever writing it (see drol-zp-37-assumption.md — $37's value comes from ZP_SAVE offset $37, not a runtime store).

**How to apply:** When reading any ZP load in the game, check ZP_SAVE first for the cold-start value before assuming a runtime initializer exists. When a ZP byte is "never written," it was written once by FIRST_BOOT's $5700 copy.
