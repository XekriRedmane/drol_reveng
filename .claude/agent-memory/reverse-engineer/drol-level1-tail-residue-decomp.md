---
name: LEVEL1_TAIL_RESIDUE decomposition
description: $BD89-$BD9F 23-byte level1 residue split into HEAD (orphan TSX/DEY/BNE) + FINALISE (dead RWTS-nibble-reader fragment, twin of STAGE_RESIDUE_DEAD .finalise)
type: project
---

The 23 bytes at `$BD89-$BD9F` between `BRODERBUND_LOGO_SPR_DATA` and `GAME_OVER` are **not** sprite padding. They are two labelled residue chunks:

- `LEVEL1_TAIL_RESIDUE_HEAD` (`$BD89-$BD8C`, 4 bytes): orphan `TSX / DEY / BNE $BD87`. The BNE target lands inside `BRODERBUND_LOGO_SPR_DATA` so the branch is incoherent; leftover from a pre-release build where the logo sprite lived elsewhere.
- `LEVEL1_TAIL_RESIDUE_FINALISE` (`$BD8D-$BD9F`, 19 bytes): dead RWTS-nibble-reader fragment that is a near twin of `STAGE_RESIDUE_DEAD`'s `.finalise` section at `$5E8D`. Both use the same ZP pointers (`ZP_DEAD_SECHDR=$48`, `ZP_DEAD_FLAGS=$47`), call `NIBBLE_READER_OVL ($BE5A)`, and branch on the returned flags to a restart-skip entry (`$BDAB` here vs `$5EAB` there).

**Why:** The shared ZP aliases and the shared `JSR $BE5A` call are strong evidence that this code is from the same pre-release loader layout as `STAGE_RESIDUE_DEAD`. The branches target `$BDAB`, which in the shipped layout lands inside `GAME_OVER` at a nonsensical instruction; no live code path reaches this range.

**How to apply:** When touching level1 sprite-data decomposition at the `$B5xx`/`$BDxx` tail, the residue table row now has *two* entries (HEAD + FINALISE) not one. Any code that greps for `LEVEL1_TAIL_RESIDUE` as a single label will no longer match — use the `_HEAD`/`_FINALISE` suffixes.
