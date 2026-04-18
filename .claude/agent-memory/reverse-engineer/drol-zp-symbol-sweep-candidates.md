---
name: Drol ZP-symbol sweep candidates
description: Zero-page addresses that have EQU symbols but are still referenced raw in code - useful target list for style-sweep rounds
type: project
---

Raw ZP references that have defined EQU symbols are an ongoing style-sweep opportunity. Periodically grep for `^\s+(LDA|STA|...)\s+\$[0-9A-F]{2}\b` and cross-reference against EQU defs in main.nw.

**Why:** Document quality — CLAUDE.md rules say ZP addresses in code "must use symbolic EQU names". After a big RE round, the code often still has raw `$XX` from the initial disassembly pass, especially in routines that were fully annotated but where the reader didn't walk through replacing every operand.

**How to apply:**
- Run `grep -nE "^\s+(LDA|STA|CMP|LDX|LDY|STX|STY|INC|DEC|EOR|ORA|AND|ADC|SBC|BIT)\s+\$[0-9A-Fa-f]{2}\b" main.nw | grep -v ",X\|,Y"` for unindexed, then `| grep ",X\|,Y"` for indexed.
- Cross-reference the address against `grep -nE "ZP_[A-Z_]+\s*=\s*\$XX\b"` to see if a symbol exists.
- When a ZP address has multiple aliases (e.g. `$0B` = both ZP_TEMP_A and ZP_ASC_FLOOR), prefer the alias from the most contextually relevant defines chunk.
- Remaining raw ZP refs as of this sweep are mostly in RWTS/loader pointer scratch ($A0-$A3), high-score copy scratch ($23-$28), and division scratch ($CE/$DA/$DB/$E6/$E7) — all in tight single-routine scopes with no existing EQU, so they stay raw.
- Dead-code scratch uses (ROW_COPY_CLICK_RANDOM using $56) may read "wrong" if symbolized (e.g. ZP_SPRITE_W for a pitch counter) — leave such cases raw.
