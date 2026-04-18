---
name: Drol TEXT_STRIP_SRC dither buffer
description: 40-byte column-indexed playfield dither source at $0300 used by CLEAR_PAGE1/2 and INTERLACE_RESTORE_P1/2
type: project
---

TEXT_STRIP_SRC ($0300-$0327) is a 40-byte column-indexed buffer holding alternating `$55`/`$2A` dot-pattern bytes. On Apple II hi-res, the pair reads as a uniform 1-dot-on/1-dot-off gray dither. Four routines broadcast these bytes across the playfield's 3-band perspective background:
- CLEAR_PAGE1/CLEAR_PAGE2 `.text_loop` paint the bottom-text-area 12 interlaced rows ($3028-$3D50 / $5028-$5D50).
- INTERLACE_RESTORE_P1/P2 paint a 105-row 3-band stripe through INTERLACE_FILL_P1/P2 (rows 72-106/112-146/152-186).

**Why:** the buffer lives inside the larger $02C6-$03A7 game-data blob, loaded once from disk via STAGE_VECTORS -> VECTOR_PAGE at boot. No STA in any shipped routine writes to it — read-only data.

**How to apply:** when RE'ing refresh/clear code that reads `$0300,X`, it's the column-indexed dither source, not a "text buffer" despite the early drafts calling it that. Don't confuse with ROW_COPY_BUFFER at $024C-$0273 which uses different bytes ($3E/$57/$6A/... pattern) consumed only by SCREEN_ROW_COPY during title wipe.
