---
name: STAGE_VECTORS decomposed into 13 labeled sub-chunks
description: $5D00-$5DEF staging buffer now decomposed matching $0300-$03EF VECTOR_PAGE tables; $5DF0-$5DFF residue separated
type: project
---

STAGE_VECTORS at $5D00 (loader staging buffer copied by FIRST_BOOT to $0300-$03EF) is broken into 13 labeled sub-chunks whose layout mirrors the $0300 destination tables: STAGE_TEXT_STRIP_SRC/HIT_BG_HI/HIT_BG_LO/HIT_BG_BYTE1/HIT_BG_BYTE0/ENTITY_FLOOR_COL/ENTITY_XOFF_IDX/ENTITY_FLOOR_POS/RESCUE_DIR/ENTITY_ACTIVE/RESCUE_ANIM/RESCUE_FLOOR/RESCUE_COUNTDOWN_HEAD + STAGE_VECTORS_RESIDUE ($5DF0-$5DFF) outside copy window.

**Why:** Prose had described these sub-tables but the chunk was a single HEX blob; decomposition makes the twin-relationship to the $0300 tables explicit and navigable in the PDF (every STAGE_* label is a chunk anchor).

**How to apply:** When RE'ing disk-install-image tables that are byte-for-byte duplicates of their runtime destination tables, label the staging copy with STAGE_<table_name> and add per-table sub-labels. Keeps the install image parseable without bloating prose.

**Pitfall learned:** Noweb expands `<<chunk>>` patterns even inside ASM comments. A reference to `<<entity tables 03A8>>` in a comment line caused drol.asm to get an extra ORG $03A8 in the middle of STAGE_VECTORS, breaking assembly. Always spell chunk names prose-style in comments ("entity-tables-03A8 chunk"), never as `<<name>>`.
