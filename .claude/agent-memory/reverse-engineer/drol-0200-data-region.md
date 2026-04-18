---
name: Drol $0200 data region layout
description: Sub-table breakdown of the $0200-$02B6 initial-data chunk with overlapping SFX pitch tables
type: project
---

The $0200-$02B6 initial-data region (183 bytes) is a densely packed concatenation of pitch tables, tracer runtime state, jingle, and a wipe pattern. Several pitch tables OVERLAP:

- LEVEL_DATA_BASE $0200-$0212 (19 bytes) - ZP_INTRO_COUNTDOWN[0..$12]
- RESCUE_DRIFT_PITCH $0213-$0217 (5 bytes)
- SND_PITCH_TBL_SPECIAL $0218-$0223 (12 bytes)
- SND_PITCH_TBL_SPECIAL_B $021F-$0223 (5 bytes, TAIL OVERLAP of SPECIAL)
- SND_PITCH_TBL_C $0224-$022B (8 bytes)
- SND_PITCH_TBL_A $0229-$0230 (8 bytes, OVERLAPS last 3 of C)
- SND_PITCH_TBL_B $0231-$0236 (6 bytes), then 5x $FF pad
- TRACER_STATE $0237-$023B (5 slots, disk=$FF inactive)
- TRACER_ROW $023C-$0240 (5 slots, disk=$00)
- BEAM_JINGLE $0241-$024B (11 bytes)
- ROW_COPY_BUFFER $024C-$0273 (40 bytes)
- $0274-$02B6 - miscellaneous seeds, not yet per-consumer decomposed

**Why:** The overlapping pitch tables mean a change to one can side-effect another; never alter individual bytes without checking which tables span that offset.

**How to apply:** When a subsystem RE uncovers a new pitch sequence in the $0200-$024B range, check this map first - may be an existing named table with a different consumer, not a new one.
