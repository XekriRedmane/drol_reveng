---
name: TIMER_FRAME_LO/HI read MAIN_LOOP code as fake data
description: DISPLAY_UPDATE's $6800/$6900 sprite-pointer tables are actually code bytes from MAIN_LOOP, giving a glitchy random-looking timer animation
type: project
---

DISPLAY_UPDATE at $10AB does `LDX ZP_ANIM_COUNTER / LDA TIMER_FRAME_HI,X / AND #$7F / STA SMC_TILE_SRC_HI / LDA TIMER_FRAME_LO,X / STA SMC_TILE_SRC_LO / JSR DRAW_SPRITE_OPAQUE` with TIMER_FRAME_LO=$6800 and TIMER_FRAME_HI=$6900. But $6800-$69FF is live MAIN_LOOP code (main loop runs $67CB-$683B). X is PRNG state = arbitrary 8-bit value. So it's reading random code bytes as sprite pointers.

**Why:** The "animated timer element" is just garbage visualization - the game is deliberately using code bytes as pseudo-random sprite data. No dedicated animation table exists.

**How to apply:** Don't try to "find" the timer frame data - the memory region is shared with MAIN_LOOP code. When RE'ing code in $6800-$69FF area, annotate that bytes serve dual purpose: executable code AND lookup source for DISPLAY_UPDATE.
