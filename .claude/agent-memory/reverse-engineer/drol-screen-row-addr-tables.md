---
name: Drol screen-row-address tables
description: Three 192-byte hi-res row base-address tables at $72C0/$7380/$7440 in the persistent-code region, plus 4 bytes of residue at $72BC
type: project
---

The three Apple II hi-res row-base-address tables live adjacent in the
persistent game-code region ($7300-$74FF) and are used by almost every
sprite/refresh routine in the game:

- `SCREEN_ROW_ADDR_HI` at $72C0 — high byte for page 1 rows ($2000-$3FFF)
- `SCREEN_ROW_ADDR_LO` at $7380 — low byte, shared between both pages
- `SCREEN_ROW_ADDR_HI2` at $7440 — high byte for page 2 rows ($4000-$5FFF)

Four stale bytes at $72BC-$72BF (CD D0 A0 A3, high-bit-stripped "MP #")
precede the tables. Not referenced anywhere in the binary; labeled
`SCREEN_TBL_PAD` for cleanliness.

**Why:** Until this RE round, $72BC-$8BFF was a single opaque HEX blob
labeled "Screen address tables and sprite data (6468 bytes)". The three
screen-row tables were referenced by EQU from the three sprite
blitters + several other routines, but the tables themselves lived
inside the blob as unlabeled bytes. Carving them into proper data
chunks turns the blob into a structured, documented region while the
remainder ($7500-$8BFF, 5888 bytes) stays as the HEX blob for later RE.

**How to apply:** The three tables are replacement for Apple II
hi-res row-base math (three-way interleave of Y). When seeing
`LDA ...,X` / `STA ...,X` SMC patches that hit a row-high-byte operand
from one of these tables, the table selection is gated by
`ZP_PAGE_FLAG` (the three main blitters toggle between HI and HI2 on
every `DISPLAY_PAGE_FLIP`). Low bytes always come from
`SCREEN_ROW_ADDR_LO`.
