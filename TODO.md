# TODO

## Milestone: `INTERLACE_BLIT_P1/P2` carved (2026-04-17)

The last large twin pair in `<<game code 03A8>>` ---
previously called `STRIPE_COPY_PAGE1/PAGE2` in the earlier carve
plans --- is now fully RE'd and renamed:

- **`INTERLACE_BLIT_P1`** at `$054E` (445 bytes): 3-band perspective
  sprite blitter.  Walks X from `ZP_BLIT_X_START` ($59, inclusive)
  down to `ZP_BLIT_X_END` ($58, exclusive), pulling 35 source bytes
  per painted column from `(ZP_BLIT_SRC),Y` ($FE/$FF); each source
  byte lands in all three perspective bands at the same relative row
  (rows 72-106 band 0, 112-146 band 1, 152-186 band 2 on hi-res page
  1).  Y is never reset between columns, so the source layout is a
  flat column-major stream of 35 bytes per column, rightmost column
  first.  An `CPX #$28` pre-paint guard skips columns >=40 while
  still advancing Y by 35 (offscreen-source alignment safety).
- **`INTERLACE_BLIT_P2`** at `$070B` (445 bytes): page-2 twin;
  byte-for-byte identical except each STA operand high nibble is
  $20 higher (writes to $40xx-$5Fxx instead of $20xx-$3Fxx).

The two helpers are the streaming analogue of `INTERLACE_FILL_P1/P2`:
same 105-row, 3-band row pattern, but source bytes come from `($FE),Y`
instead of A.  Three caller sites (all still inside hex blobs near
`$625F`, `$62C6`, `$6317`) read a 16-bit sprite pointer from tables at
`$7500/$7600` (persistent + swappable sprite data) and use the
`BIT $00 / BMI` page-flag gate to pick P1 vs P2 --- the same gating
already documented for `INTERLACE_RESTORE_P1/P2`.

**Byte count retired from `<<game code 03A8>>`:** 890 bytes (blob
now covers $08C8-$09FD, 310 bytes; was $054E-$09FD, 1200 bytes).
The remaining tail contains only `ROW_PAINT_P1_38/P2_38` at
$08C8/$08DF and `TEXT_ROW_FROM_A30D_P1/P2` at $08F6/$097A.  New ZP
EQUs: `ZP_BLIT_X_END = $58`, `ZP_BLIT_X_START = $59`,
`ZP_BLIT_SRC = $FE` (pointer lo; +1 is hi byte).

PNG rendered: `images/interlace_blit_demo_sprite7700.png` shows the
triple-ghost 3-band effect when blitting the 4-column, 140-byte
sprite at $7700 to columns 15..19 of hi-res page 1 (Figure
`fig:interlace-blit-demo` in main.nw).  The companion
`images/interlace_blit_demo_singleband.png` shows the same sprite
painted to band 0 only so the artwork (a decorative pillar) is
legible without the 3x perspective repeat.

Prior-doc corrections:

- Three prose references to the old working name
  `STRIPE_COPY_PAGE1` have been upgraded to `INTERLACE_BLIT_P1`: in
  the sector-residue analysis at $4713 and in `INTERLACE_RESTORE_P1`'s
  caller list.
- The `% TODO-SYM: $054E $05FF` marker on the sector-residue section
  has been dropped (both addresses are now symbolic-reachable).

Next-session priorities:

1. The three `INTERLACE_BLIT` caller sites at $625F / $62C6 / $6317
   are inside `<<game engine A>>` / `<<game engine A tail>>` hex
   blobs.  Each is the 2-step "playfield refresh" paired with
   `INTERLACE_RESTORE_P{1,2}` (text strip) + `INTERLACE_BLIT_P{1,2}`
   (playfield sprite).  Carving them would finally retire the last
   raw-hex `JSR $054E` / `JSR $070B` / `JSR $09FE` / `JSR $0B4B`
   references in main.nw and make the page-flag-gated twin dispatch
   explicit.  This also unlocks the sprite-pointer tables at
   $7500/$7600 (indexed by ZP slot numbers) and connects the
   playfield refresh to the entity-draw dispatch.
2. The four remaining helpers in `<<game code 03A8>>`'s tail
   (`ROW_PAINT_P1_38/P2_38` at $08C8/$08DF, 23 bytes each;
   `TEXT_ROW_FROM_A30D_P1/P2` at $08F6/$097A, 132 bytes each) ---
   the last 310 bytes of hex in the chunk.

## Milestone: `INTERLACE_RESTORE_P1/P2` carved; `INTERLACE_FILL_P1/P2` verified complete (2026-04-17)

Confirmed the primary target `INTERLACE_FILL_P1` ($0A0F) and
`INTERLACE_FILL_P2` ($0B5C) were already fully carved in the
preceding `CLEAR_PAGE1/CLEAR_PAGE2` session (commit `40a2421`):
each is a 315-byte unrolled row-broadcast painter that writes A
across 105 interlaced hi-res rows at column X (3 bands of 35 rows:
rows 72-106 / 112-146 / 152-186 of pages 1/2 respectively, in
strict-twin form with only $20 added to each STA operand's high
byte).  Inputs: A (paint byte), X (column $00..$27); clobbers:
none.  Used by `CLEAR_PAGE1/CLEAR_PAGE2` (per outer-loop
iteration with A=$00) and by the `INTERLACE_RESTORE` helpers
described below (one byte per column, from the $0300 buffer).

Carved this session:

- **`INTERLACE_RESTORE_P1`** at `$09FE` (16 bytes): loops X from
  `ZP_SCORE_0` ($2B) down to `ZP_SCORE_1+1` ($2C), loading the
  text-buffer byte at $0300,X and calling `INTERLACE_FILL_P1` to
  broadcast it across 105 interlaced rows per column.  Replaces
  the trailing 17 HEX bytes of `<<game code 03A8>>`.
- **`INTERLACE_RESTORE_P2`** at `$0B4B` (16 bytes): page-2 twin;
  replaces the `<<game code 0B4B>>` HEX stub.  Byte-for-byte
  identical to P1 except the inner JSR targets `INTERLACE_FILL_P2`.

Both restore helpers are called from three sibling-paired sites in
the game engine A region ($625C, $62BC, $630F area), always as the
non-negative-ZP-flag branch of `BIT $00; BMI`; the page-2 variants
are the `BMI` targets ($6263, $62C3).  Each pair is
`INTERLACE_RESTORE_PN + STRIPE_COPY_PAGEN` = "restore the score-HUD
text strip at columns $2B..$2C, then copy a new playfield stripe
from ($FE) into columns $58..$59" --- the full 2-step screen refresh
used during player-sprite redraws and level-transition repaints.
The paired bounds explain why the four HUD score slots at $2B-$2E
double as two (low, high) column-range pairs: $2B/$2C for the
score-strip restore, $2D/$2E for the main playfield clear.

**Byte count retired from `<<game code 03A8>>`:** 17 bytes (blob
now covers $054E-$09FD, 1200 bytes; was $054E-$0A0E, 1217 bytes).
The blob still contains `STRIPE_COPY_PAGE1/PAGE2` at $054E/$070B
(two 445-byte streaming 3-band perspective-floor painters),
`ROW_PAINT_P1_38/P2_38` at $08C8/$08DF (two 23-byte row-4
painters), and `TEXT_ROW_FROM_A30D_P1/P2` at $08F6/$097A (two
132-byte text-row painters from the fixed $A30D source).  Improved
the blob's intro comment with the newly-understood streaming-3-band
semantics of the `STRIPE_COPY` pair (each source byte from
`($FE),Y` paints the same relative row in all three perspective
bands --- a streaming analogue of `INTERLACE_FILL`'s constant A
broadcast).  Chunk `<<game code 0B4B>>` is retired.

No PNG: this session's new routines are framebuffer plumbing, not
displayable art.

## Milestone: `$4713-$47FF` identified as dead sector-image residue (2026-04-17)

The 237-byte HEX blob at `$4713-$47FF` --- previously labelled
`GAME_INIT_EXTRA` and stubbed as "screen-init routines" that would
paint the DROL title logo --- has been investigated and confirmed to
be **statically unreachable dead code**, not a title-logo painter.
Three independent lines of evidence:

1. An exhaustive scan of all five reference binaries (boot1, loader,
   rwts, drol, level1) for JSR/JMP/JMP-indirect with operand in
   `$4713-$47FF` returns zero hits.  No immediate load of `#$47`
   into any pointer appears either, ruling out runtime-built vectors.
2. The "code" at `$474E` is a truncated copy of `STRIPE_COPY_PAGE1`'s
   prologue + first 13 iterations, cut off mid-instruction at
   `$4800` followed by 5120 bytes of `$00` (which would dispatch
   as `BRK`).  No real routine could return from here.
3. The bytes at `$4713-$47FF` are **byte-exact identical** to
   `$0513-$05FF` (a 237-byte window spanning the tail of
   `CLEAR_PAGE2` + `CLEAR_PAGE2_TEXT_ENTRY` + the first half of
   `STRIPE_COPY_PAGE1`).  The leading `$0B` at `$4713` is the high
   byte of `JSR INTERLACE_FILL_P2`'s operand at `$0512-$0513` ---
   mid-instruction, not a purposeful constant.

The mechanism is incidental: `PAGE_TABLE` at `$5400` maps track 2
sector 15 → page `$47` and track 1 sector 3 → page `$05`, and those
two sectors on disk happen to contain the same bytes (build
artefact, possibly a deliberate sector-level duplicate for
error-recovery).  Because `GAME_INIT`'s stream terminates at `$4712`
and nothing else calls into `$47xx`, the residue has no runtime
effect.  Confirmed by `level1.bin`, built by replaying the loader's
reload-phase track read (which targets different pages): it has
`$00` throughout `$4700-$47FF`.

**Corrections** (applied this session):

- Renamed chunk `<<game init remaining>>` to `<<sector residue 47xx>>`
  with label `SECTOR_RESIDUE_47XX` (retires the `GAME_INIT_EXTRA`
  misnomer).
- Updated the HUD-frame prose in `\section{HUD/frame unpacker}` to
  correct the previous claim that `$4713-$47FF` held screen-init
  routines.  The DROL logo is actually drawn by the attract-mode
  sprite routines `ATTRACT_ANIM_1..4` at `$17A6/$17E1/$1813/$1844`
  compositing sprite pointer tables into hi-res page~2 during the
  animated title sequence --- not by any code at `$47xx`.
- No PNG rendered for `$4713-$47FF`: the bytes are neither
  executable game logic nor displayable art.
- The existing `images/drol_logo.png` caption is already correct
  (identifies the sprite at `$BCF1` as the "© 1983 Broderbund"
  attribution strip, drawn by `ATTRACT_ANIM_4`) --- no change needed.

## Milestone: `CLEAR_PAGE1`/`CLEAR_PAGE2` carved + entity-table data split (2026-04-17)

First cut into the 2288-byte `<<game code 03A8>>` hex blob:

- **Entity state tables** at $03A8-$03F7 (80 bytes) carved as data chunk
  `<<entity tables 03A8>>`.  Rounds out the 8-table entity record
  block (first 4 tables at $0358-$03A7 were already in
  `<<game data 02C6>>`).  The `ENTITY_ACTIVE = $03A8` EQU is
  retired; the address is now the module-level label `ENTITY_ACTIVE`
  at the top of the data chunk.  Disk bytes at $03BC, $03D0, and
  $03E4-$03EF carry non-zero initial values on-disk --- these are
  stale/residue; game-init zeros the block.
- **FLOOR_Y_TABLE** 8 bytes at $03F8-$03FF carved as `<<floor y table data>>`.
  Disk bytes are all zero; FIRST_BOOT writes the sentinel values
  ($00, $43, $6B, $93, $BB).
- **CLEAR_PAGE1** ($0400-$04A6, 167 bytes): zero-paints hi-res
  page 1 ($2000-$3FFF) across playfield column range
  `[ZP_CLEAR_COL_END+1 .. ZP_CLEAR_COL]` and then copies the 40-byte
  text-row buffer at $0300,X into 12 interlaced hi-res bottom rows.
  Called from player-tick code at $61E8.
- **CLEAR_PAGE2** ($04A7-$054D, 167 bytes): page-2 counterpart
  ($4000-$5FFF).  Exposes two sub-entries: `CLEAR_PAGE2_ENTRY`
  ($04AB, skip register setup) and `CLEAR_PAGE2_TEXT_ENTRY` ($051E,
  skip hi-res paint loop, used by reset-screen code at $4719/$474A).
  Called from $61EC.

Both CLEAR routines call out to `INTERLACE_FILL_P1` at $0A0F and
`INTERLACE_FILL_P2` at $0B5C; these are declared as EQU stubs
(not yet carved).  New ZP EQU: `ZP_CLEAR_COL_END = $2D`
(low-column terminator; game-time alias `ZP_SCORE_2`).

**Remaining hex tail** `<<game code 03A8>>` now covers $054E-$0C97
(1866 bytes).  It is entirely hi-res framebuffer library code:

- $054E-$070A: `STRIPE_COPY_PAGE1` --- copies `($FE),Y` into
  hi-res page 1 stripe columns.  Y indexes source bytes; X counts
  from `$59` down to `$58`.  Inner body is a 33-way stripe fanout
  matching the row-decimation pattern of CLEAR_PAGE1.
- $070B-$08C7: `STRIPE_COPY_PAGE2` --- page-2 twin.
- $08C8-$08DE: `ROW_PAINT_P1_38` --- small painter (4-row stripe at
  col 38).  Single caller: $62DA.
- $08DF-$08F5: `ROW_PAINT_P2_38` --- page-2 twin.  Single caller: $62DE.
- $08F6-$0979: `TEXT_ROW_FROM_A30D_P1` --- paints from a fixed source
  at $A30D,Y into page 1 text-area rows.  Called from $6370.
- $097A-$09FD: `TEXT_ROW_FROM_A30D_P2` --- page-2 twin.  Called from $6374.
- $09FE-$0B4A: `INTERLACE_RESTORE_P1` --- restores text bytes from
  $0300,X via `INTERLACE_FILL_P1` ($0A0F) helper.
- $0B4B-$0C97: `INTERLACE_RESTORE_P2` --- page-2 twin; $0B5C is the
  `INTERLACE_FILL_P2` helper used by CLEAR_PAGE2.

Next-session priorities (in order):

1. Carve `INTERLACE_FILL_P1` ($0A0F) and `INTERLACE_FILL_P2` ($0B5C)
   first --- retires the EQU stubs and unblocks full understanding of
   the other 6 routines.
2. Carve the two stripe-copy routines ($054E + $070B) --- 942 bytes
   of near-identical twinned code.
3. The 4 smaller routines ($08C8/$08DF/$08F6/$097A) and the two
   restore routines ($09FE/$0B4B).

Any aligned entry point I can reach from the game engine A tail
($614B-$64CA) calls one of these routines, so the whole region is
used during level transitions and screen refreshes, not per-frame.

## Milestone: `RESCUE_DRAW` carved from `<<projectile handler>>` (2026-04-17)

The 441-byte `<<projectile handler>>` HEX blob at $0C98-$0E50 (the
last misnamed `PROJECTILE_HANDLER` stub --- the routine has nothing
to do with general projectiles) has been fully RE'd as
`RESCUE_DRAW`, the per-frame draw + collision sibling of
`RESCUE_UPDATE` ($6F9C).  Carved as one main routine with a
sub-entry pre-compute helper (`RESCUE_DRAW_PERSPECTIVE_CACHE` at
$0D8C).  All structural rules pass: byte-perfect drol.bin and zero
new chunk-placement violations.

**Surprise discovery:** rescue children are NOT pure friendlies.
The "no-collision" tail of RESCUE_DRAW ($0E13-$0E50) spawns hostile
projectiles into the $C5/$C9/$CD slot table when the rescue child
is on the player's floor at an odd row.  `HAZARD_CHECK` then ticks
the projectile on subsequent frames as a normal hazard.  So
rescue-children also harass the player on their assigned floor ---
the +$0035 BCD pickup is the reward for catching them before they
keep firing.

**Now `<<game code 03A8>>` (the largest remaining HEX blob) shrinks
from 2288 bytes ($03A8-$0C97) to no longer needing to span $0C97;
the rest of $03A8-$0C97 is still HEX-blobbed in `<<game code 03A8>>`,
but the gap to the next labeled chunk (`<<rescue draw>>` at $0C98)
is now closed.**  The remaining blob is 2288 bytes covering
$03A8-$0C97, the entity sprite-data tables and several entity
update routines (rescue marker draw, etc.).

## Milestone: `<<game engine B tail>>` FULLY RETIRED (2026-04-17)

The 1763-byte "game engine B tail" HEX blob that started as raw data
has been fully carved out.  Final session retires the last 513 bytes
at `$6F9C-$719C` as `RESCUE_UPDATE` --- the per-frame tick for the
20-slot rescue-child entity subsystem (Drol's scoring objective).
Together with prior carves:

- `SPECIAL_TICK` ($6ABA, 127 bytes) --- bonus creature tick
- `SPECIAL_DRAW` + `SPECIAL_BODY_STEP1..6` + `SPECIAL_INACTIVE_DRAW`
  ($6B39..$6CFD, 453 bytes) --- bonus creature draw + palindromic
  walk cycle
- `COMPANION_UPDATE` ($6CFE, 670 bytes) --- two-slot hostile walker
- `RESCUE_UPDATE` ($6F9C, 513 bytes) --- 20-slot rescue children

`drol.bin` is now **100.0% documented, zero gaps**.

## Status snapshot (2026-04-17)

The **attract/game/restart state machine is now fully documented**:
MAIN_LOOP's two exit arms (`$7208` on lives-out, `$BDA0` on hit-
credits-out) reach `LIFE_LOST_HANDLER` and `GAME_OVER` respectively;
LIFE_LOST_HANDLER exhausts the extras stash `$8C` via animated
frames and tails into `RESTART_NEW_GAME` ($7255) which resets game
state and falls through to `ATTRACT_LOOP`; ATTRACT_LOOP polls input
and on keypress enters `START_GAME_FROM_ATTRACT` ($7299) which
re-resets and jumps into MAIN_LOOP.  The three callers of
`GAME_START_INIT` are now all labeled sub-entries
(`START_GAME_FROM_ATTRACT` at $7299, `RESTART_NEW_GAME` at $7255,
`INPUT_PROCESS.check_restart` at $6121).  `RESUME_GAMEPLAY_SMC`
($6AA7) is now a module-level sub-entry inside LEVEL_INTRO_TICK's
`.activate` (retiring the EQU stub).  `RESTART_DISPATCH` ($5EC5)
has been carved out of `<<staging buffers>>` and is documented as
statically dead code --- no JMP/JSR in any of the four reference
binaries targets it, and the `ZP_RESTART_FLAG` ($44) write at
GAME_START_INIT's tail is effectively a dead store.

The **entity-draw triplet is complete**: all three enemy advance
routines and all three enemy draw routines are byte-perfect RE'd
(`$13D6`, `$1423`, `$1536`, `$1591`, `$1646`, `$16AC`).  See the
"Entity-slot triplet" section below for the topology summary.
With the triplet, `BEAM_UPDATE` ($130A), `DRAW_ENTITIES` ($683C),
`DISPLAY_UPDATE` ($10AB), `DIFFICULTY_UPDATE` ($719D),
`LEVEL_INTRO_TICK` ($699C), `SFX_TONE` ($67C1), `INPUT_DISPATCH`
($6000), `DRAW_PLAYER` ($64DF), `PLAYER_MOVE_TICK` ($64CB),
`GAME_START_INIT` ($13A4), and the three blitters (`DRAW_SPRITE`,
`DRAW_SPRITE_PLAYFIELD`, `DRAW_SPRITE_OPAQUE`) all documented, the
MAIN_LOOP dispatch is now fully named --- every `JSR` target in the
main loop either has its own ORG chunk or sits inside one of the
named hex blobs awaiting further carve-out.  Prior sessions carved
`SPECIAL_TICK` ($6ABA, 127 bytes) out of the head of
`<<game engine B tail>>`, retiring the `SOUND_UPDATE` EQU stub.
A prior session carved `SPECIAL_DRAW` ($6B39, 262 bytes),
`SPECIAL_BODY_STEP1..6` ($6C3F, 156 bytes) and
`SPECIAL_INACTIVE_DRAW` ($6CDB, 35 bytes) --- 453 bytes --- out of
the same hex blob, retiring the `SPECIAL_DRAW = $6B39` EQU stub.
A prior session carved `COMPANION_UPDATE` ($6CFE, 670 bytes) ---
the two-slot "hostile walker" tick+draw pair --- out of the same
hex blob, retiring the `ENTITY_PROCESS = $6CFE` EQU stub.
This session carves `RESCUE_UPDATE` ($6F9C, 513 bytes) --- the
20-slot rescue-child entity tick --- retiring the
`LEVEL_LOGIC = $6F9C` EQU stub and fully eliminating
`<<game engine B tail>>` from the blob list.  The rescue-child
subsystem is Drol's actual scoring objective: children walk
across the perspective floors, chase the player when on the
same floor, and award +$0035 BCD (35 decimal) when intercepted
in the $40..$50 screen-X centre band.  Sibling draw +
collision logic lives at $0C98 (still inside the $03A8..$0C97
HEX blob); marker-sprite draw in DRAW_ENTITIES phase 5 at
$694E.
The remaining high-priority work is the remaining hex tail of
`<<game engine A>>` at $614B-$64CA (player movement-tick
handlers and the DO_ASCEND/DO_DESCEND/DO_MOVE_LEFT/DO_MOVE_RIGHT
input handlers called via SMC from MAIN_LOOP), plus the huge
$0348..$0C97 ("game code 03A8") blob that contains the rescue
draw sibling at $0C98 and the projectile + hazard subsystems.

### State-machine topology

```
 cold-start
      |
      v
 GAME_START_INIT ($13A4) --resets score/lives/HUD--> RESUME_GAMEPLAY_SMC ($6AA7)
      ^     ^                                                 |
      |     |                                                 v (RTS)
      |     +-- $6121 INPUT_PROCESS.check_restart (Ctrl-R)    |
      |                                                       |
      |    +-- $7255 RESTART_NEW_GAME (lives-out fall-through)|
      |    |                                                  |
      |    +-- $7299 START_GAME_FROM_ATTRACT (input detected) |
      |                                                       v
      |                                                 MAIN_LOOP ($67CB)
      |                                                    |     |
      |                                                    |     |
      |     +------ $5E < 0 (BCD underflow)  JMP $7208 ----+     |
      |     |                                                    |
      |     v                                                    |
      |  LIFE_LOST_HANDLER ($7208) --+                           |
      |    |                         |                           |
      |    |  $8C > 0 ->             |  $8C == 0 fall-through    |
      |    |    one-frame anim       |                           |
      |    |    then RE-ENTER        v                           |
      |    |    via $682F      RESTART_NEW_GAME ($7255)          |
      |    |                         |                           |
      |    |                         |  fall through             |
      |    |                         v                           |
      |    |                   ATTRACT_LOOP ($7263)              |
      |    |                         |                           |
      |    |            input detect |                           |
      |    |                         v                           |
      |    |                   START_GAME_FROM_ATTRACT ($7299)   |
      |    +-------------------------+                           |
      |                                                          |
      |         $39 < 0 (hit-credit out)    JMP $BDA0 -----------+
      |                                           |
      |                                           v
      |                                       GAME_OVER (at $BDA0,
      |                                         in relocated RWTS)
      |
      +-- $5EC5 RESTART_DISPATCH (dead code; originally dispatched
          on ZP_RESTART_FLAG $44 to pick among three restart flows
          but has no live caller in any of the reference binaries)
```

## Immediate: apply new code chunk rules

CLAUDE.md now requires raw hex addresses in code to use labels or EQUs.
Review existing chunks for violations:

- [ ] `<<boot1 entry>>`: `JMP $C65C` (PROM re-entry), `JMP $51C0` (loader entry), `STA $0400,X` (text page), raw copy-loop addresses ($5800, $BE00, $BF00, $5000, $D000)
- [ ] `<<rwts entry>>`: `JMP $XXXX` targets within the chunk are already labeled; check for any remaining raw data addresses
- [ ] `<<dispatch>>`: `JSR $4000` should use `GAME_INIT_NOP` or `GAME_INIT`, raw addresses like `$72BA`, `$6022`, `$600E`, `($004E)`
- [ ] `<<main loop>>`: all 25 JSR targets are raw hex — create EQU stubs or ORG stubs as routines are RE'd
- [ ] `<<attract loop>>`: `JSR $17A6`, `JSR $17E1`, `JSR $1813`, `JSR $1844`, `JSR $13A4` are raw hex

## Continue game RE

### High-priority routines (called from main loop)

- [x] `$6000` — `INPUT_DISPATCH`: keyboard/joystick input dispatcher.
- [x] `$699C` — `LEVEL_INTRO_TICK`: per-frame level-start state machine. Init
      (disables input/render SMC slots, clears state, $18=$12, $19=$40),
      countdown (odd-frame tick + flickering sprite draw + SFX_TONE pulse),
      wait-for-start (BCD-decrement $5E, poll keyboard / input-handler MSBs /
      timeout, then activate by restoring JSR opcodes + setting $1E=1).
      Introduced ZPs: ZP_INTRO_Y ($17), ZP_INTRO_COUNTDOWN ($18),
      ZP_INTRO_TIMEOUT ($19); SMC aliases SMC_SR_HEIGHT ($64F6),
      SMC_SR_YSRC ($64FA), SMC_SPRITE_MASK_OP/ARG ($65B7/$65B8); tables
      LEVEL_DATA_BASE ($0200), SPRITE_TABLE_LO/HI ($B000/$B080); stub
      SFX_TONE ($67C1).
- [x] `$719D` — `DIFFICULTY_UPDATE`: score-driven difficulty tier update
      (misnamed "SCROLL_CAMERA" previously --- the routine never touches
      scroll or camera state).  Runs only when `ZP_FRAME_COUNTER` ($FD)
      wraps to 0 (every 256 frames ~= 4s).  Builds a tier index from
      two BCD digits of the score (`ZP_SCORE_HI` low-nibble << 4 |
      `ZP_SCORE_MID` high-nibble >> 4) and dispatches to one of four
      presets that write slot-count maxima, tier thresholds, and the
      per-tick timer-advance rate.  Sub-entry `DIFFICULTY_RESET` ($71D6)
      is the minimum preset, also called by `GAME_START_INIT` to
      initialize.  Renamed `ZP_ENTITY_D1/D2/D3` ($D1/$D2/$D3) to
      `ZP_SCORE_HI/MID/LO` (these are the BCD score, not entity state;
      also confirmed by `SCORE_ADD`, `POST_FRAME`, `LEVEL_TRANSITION`).
      New ZP EQUs: `ZP_PROJ_GATE` ($32), `ZP_DIFF_THRESH_A/B` ($34/$35),
      `ZP_ADVANCE_RATE` ($40), `ZP_DIFF_TMP` ($5C), `ZP_FRAME_COUNTER`
      ($FD).  `$32` and `$40` are read by the not-yet-RE'd routines at
      `$130A` (BPL gate) and `$13F7` / `$1675` (SBC decrement).  `$40`
      consumer at `$13F7` is now documented as `ENEMY_A_ADVANCE` (see
      below); `$1675` remains open as `ENEMY_C_ADVANCE`.
- [x] `$683C` — `DRAW_ENTITIES`: final per-frame drawing dispatcher in
      MAIN_LOOP (misnamed "page flip" previously --- no display-page
      toggle here; that's `DISPLAY_PAGE_FLIP` at $6138).  Five phases:
      phase 1 restores one hit-entity's BG using 12-slot tables at
      `HIT_BG_HI/LO/BYTE0/BYTE1` ($0328/$0334/$034C/$0340), with a +$20
      page offset applied when `ZP_PAGE_FLAG` is negative; phase 2 draws
      the player (gated on $0E); phase 3 draws a "special" sprite
      (gated on $AB); phase 4 draws two "companion" slots (gated on
      $33) from ZP tables at $11/$13/$15; phase 5 iterates the 20-slot
      `ENTITY_ACTIVE` table at $03A8 with parallel tables
      `ENTITY_FLOOR_COL` ($0358), `ENTITY_XOFF_IDX` ($036C),
      `ENTITY_FLOOR_POS` ($0380).  All four draw phases set sprite
      params ($56/$57/$5B/$5D) and JSR `DRAW_SPRITE_PLAYFIELD`
      ($65D5, now disassembled), patching the sprite-data source
      operands at `SMC_PFB_SRC_LO/HI` ($6615/$6616).  Introduced lookup-table
      labels: `FLOOR_TO_ROW` ($1D40), `FLOOR_SPRITE_IDX` ($1E00),
      `FLOOR_SCREEN_COL` ($1F00), `FLOOR_BASE_ROW` ($188F).
- [x] `$67C1` — `SFX_TONE`: speaker-click tone / delay generator.
      Classic nested delay loop; A = pitch, X = duration; clicks the
      speaker via `CMP ($36),Y` where ($36,$37) is an indirect pointer
      built so that bit 4 of $36 toggles between $C030 (speaker, sound
      on) and $C020 (silent cassette output, sound off).  Renamed
      `ZP_SOUND_A`/`_B` to `ZP_SFX_CLICK` / `ZP_SFX_CLICK_SAVED`.
- [x] `$10AB` — `DISPLAY_UPDATE`: timer-animation HUD tile draw.
      Draws the timer element via `DRAW_SPRITE_OPAQUE`, gated on
      `ZP_ANIM_COUNTER` ($1F).
- [x] `$13D6` — `ENEMY_A_ADVANCE`: per-frame tick for the first of
      three ``moving hazard'' slots at $D4--$EC.  Emits an SFX click
      from `SND_PITCH_TBL_A` ($0229) gated on `ZP_ENEMY_A_SND_CTR`
      ($B8), then decrements the 16-bit advance counter
      `ZP_ENEMY_A_POS` ($DD/$DE) by `ZP_ADVANCE_RATE` ($40).  Gated by
      `ZP_ENEMY_A_STATE` ($DC): $00 off; positive = steady tick;
      negative = PRNG-gated drift (tick only when `ZP_PRNG_A` $5F <
      $09, ~3.5% per frame).  On narrow-band crossing ($0000..$003D),
      rearms: promotes drift->steady, writes $01 to
      `ZP_ENEMY_C_STATE` ($D4 --- cross-slot handshake that wakes the
      companion slot handled by `ENEMY_C_ADVANCE`/`ENEMY_C_DRAW`),
      reloads counter to $0361, and sets `ZP_ENEMY_A_ROW` ($DF) :=
      `ZP_ENEMY_C_ROW` ($D7) + 7.  Retires the `BG_RESTORE`
      misnomer --- this routine does no background restore.  Carved
      $13D6--$1422 out of the old 976-byte `<<sprite player code>>`
      HEX blob; the tail at $1423 is now `ENEMY_A_DRAW`.
- [x] `$1423` — `ENEMY_A_DRAW`: per-frame draw + player-collision
      for the enemy-A slot, completing the entity-draw triplet
      alongside `ENEMY_B_DRAW` and `ENEMY_C_DRAW`.  Two-sprite
      composite (body + feet) with a four-frame walking animation
      driven by `ZP_FRAME_COUNTER` bits 1-2 (phases 0,2 = stance;
      phases 1,3 = walk variants drawn at row-1 with 3x4 feet
      sprites from `SPRITE_TABLE_A_STEP1/2`).  Drift mode
      (state < 0, set externally by `ENEMY_C_DRAW`'s hit broadcast)
      collapses the animation to a fixed stance; there is no drift
      puff, unlike B and C.  Right-edge X clip is $9A (vs.\ B's $9C,
      C's $94); hit window is [$42, $4F) for X and
      [player-$14, player+$10] for Y (a $24-row band, 4 rows taller
      than B's $1B).  On player-overlap: writes $00 to
      `ZP_ENEMY_A_STATE` (immediate deactivation, not $FF drift like
      B), loads `ZP_ENEMY_A_SND_CTR` with $07 (one death click),
      decrements `ZP_GAME_OVER` ($39) --- the `DEC $39` at $1528
      that prior docs referenced --- and awards +$0300 BCD via
      `SCORE_ADD`, matching B's 300-point reward.  No cross-slot
      handshake writes.  Retires the `SPRITE_DRAW_1 = $1423` EQU
      stub and carves the last of the old `<<sprite player code>>`
      HEX blob.  Introduces ZP EQU `ZP_ENEMY_A_LEG_PHASE` ($0F,
      scratch alias distinct from the RWTS `ZP_TGT_TRACK`) and
      sprite-table EQUs `SPRITE_TABLE_A_BODY_LO/HI` ($B009/$B089),
      `SPRITE_TABLE_A_STEP1_LO/HI` ($B010/$B090),
      `SPRITE_TABLE_A_FEET_LO/HI` ($B017/$B097),
      `SPRITE_TABLE_A_STEP2_LO/HI` ($B01E/$B09E).
- [x] `$1646` — `ENEMY_C_ADVANCE`: per-frame tick for the third
      ``moving hazard'' slot, sibling of `ENEMY_A_ADVANCE` with the
      same tick+rearm shape but three notable differences.  (1)
      Click is `SND_DELAY_DOWN` ($1091) at duration $08 reading from
      `SND_PITCH_TBL_C` ($0224) gated on `ZP_ENEMY_C_SND_CTR` ($B7)
      --- a softer descending-tone chirp distinct from enemy-A's
      `SFX_TONE`.  (2) Drift mode (state bit~7 set) does NOT
      PRNG-gate the tick; instead it bobs `ZP_ENEMY_C_ROW` $\pm$1 on
      1-in-4 frames using `ZP_FRAME_COUNTER` bit~4 as the up/down
      phase, producing a vertical wobble.  Drift entry at $16A5
      counts the lo counter UP and falls into rearm on overflow.
      (3) Rearm writes $00 to `ZP_ENEMY_C_STATE` (deactivates
      itself) --- the topology edges live in `ENEMY_C_DRAW` instead
      (see below), giving three-slot model A$\rightarrow$C (rearm)
      and C$\rightarrow$\{A,C\} (hit).  Reload value $0352, rearm
      window $0000..$003B, row reload reads from a 3-entry table at
      $85/$86/$87 (addressed as $84,X for X $\in \{1,2,3\}$ with
      X~=~1 selected 2/4 of the time).  Carved $1646--$16AB out of
      the surviving `<<sprite player code>>` HEX blob.
      Retires `PLAYER_STATE = $1646` EQU stub.  Introduces ZPs
      `ZP_ENEMY_C_SND_CTR` ($B7), `ZP_ENEMY_C_POS` ($D5),
      `SND_PITCH_TBL_C` ($0224), `ENEMY_C_ROW_TBL` ($84).
- [x] `$16AC` — `ENEMY_C_DRAW`: per-frame draw + enemy-slot collision
      for enemy-C, replacing the `PLAYER_RENDER` stub (mis-named in
      the stub era --- this routine does not render the player).
      Steady-mode draws TWO sprites: a $02x$0B body from
      `SPRITE_TABLE_C_LO/HI` ($AFE1/$B061) and a $01x$07 ``tail''
      one column left and $0B rows below from the level-specific
      `ENEMY_C_TAIL_LO/HI` pointer-table ($7549/$7649, indexed by
      PROJ_FRAME_IDX).  Hit-test is against the 4-slot floor-enemy
      table at $9B/$9F/$A3 (same slots the beam subsystem targets),
      NOT the player --- walks X=3..0 for first active slot, checks
      clip_X vs ZP_ENEMY_COL and row vs ZP_ENEMY_Y.  On hit:
      $FF$\rightarrow$$D4 (self drift), $FF$\rightarrow$$DC if
      active (A into drift), retires the floor-enemy ($00$\rightarrow$$9B,X),
      rewinds position, awards +$0100 BCD, reloads click counter to
      $04.  No DEC ZP_GAME_OVER --- this hit path is not a
      life-loss event.  Drift-mode tail draws a $02x$06 puff from
      `ENEMY_C_PUFF_LO/HI` ($7559/$7659, un-indexed, one byte
      earlier than enemy-B's $755A/$765A puff).  Corrects prior
      prose that attributed the $1757--$1763 broadcast to
      `SPRITE_DRAW_3`/enemy-B firing.  Retires `PLAYER_RENDER`
      label.  Introduces EQUs `SPRITE_TABLE_C_LO/HI`,
      `ENEMY_C_TAIL_LO/HI`, `ENEMY_C_PUFF_LO/HI`.
- [x] `$130A` — `BEAM_UPDATE`: player laser-beam subsystem, gated on
      `ZP_PROJ_GATE` ($32).  Inactive at difficulty tiers minimum and
      moderate ($32 = $FF); active at standard and maximum ($32 = $01).
      Dispatches three sub-routines: `BEAM_TARGET_TICK` ($1230) state
      machine, `BEAM_TARGET_DRAW` ($1297) sprite-trail draw plus
      enemy-collision check (awards 100 BCD on hit), and
      `BEAM_TRACER_SPAWN` ($1376) per-floor tracer scheduler.  Then
      walks a 5-slot tracer table (`TRACER_STATE` $0237,
      `TRACER_ROW` $023C) and for each active slot decrements the
      state/X-column, draws a single $7F byte directly into hi-res at
      the row/col with HUD-bound clipping, and runs a hit test when
      the X-column enters the $12/$13 near-player window (sets
      `ZP_HIT_FLAG` $1E=$FF).  Uses SMC operands `SMC_TRACER_ADDR_LO`
      ($1359) / `SMC_TRACER_ADDR_HI` ($135A) patched inline.  Retires
      "Page flip preparation" stub name (real page flip is at $6138
      `DISPLAY_PAGE_FLIP`).
- [x] `$1536` — `ENEMY_B_ADVANCE`: enemy-B slot up-counter; see triplet section below.
- [x] `$1591` — `ENEMY_B_DRAW`: enemy-B sprite draw + player-collision
      handler, replacing the `SPRITE_DRAW_3` stub.  Steady-mode
      draws a $05x$11 body sprite from `SPRITE_TABLE_B_LO/HI`
      ($B025/$B0A5); drift-mode draws a $02x$06 puff sprite from the
      per-level pointer pair at `ENEMY_B_PUFF_LO/HI` ($755A/$765A).
      The player-overlap body at $15FE writes $FF to
      `ZP_ENEMY_B_STATE` only (putting B into drift mode for
      deferred self-deactivation), awards +300 BCD via
      `SCORE_ADD`, and decrements `ZP_GAME_OVER` ($39).
      **Correction to prior docs**: the B->{A,C} handshake is
      *not* in this routine --- the $1757-$1763 writes to $D4/$DC
      live in `PLAYER_RENDER` (enemy-C draw).  Enemy-B's collision
      only touches its own state $E0.  Introduces ZP EQUs
      `ZP_CLIP_X_LO` ($AF), `ZP_CLIP_X_HI` ($B0), `ZP_SPRITE_XREF`
      ($4C), `ZP_GAME_OVER` ($39); data EQUs `PERSPECTIVE_XOFF_LO`
      ($1A8F), `PERSPECTIVE_XOFF_HI` ($198F), `SPRITE_TABLE_B_LO`
      ($B025), `SPRITE_TABLE_B_HI` ($B0A5), `ENEMY_B_PUFF_LO`
      ($755A), `ENEMY_B_PUFF_HI` ($765A).  Retires the
      `SPRITE_DRAW_3 = $1591` EQU stub and carves $1591-$1645 out
      of the `<<sprite player code 1591>>` HEX blob.
- [x] `$64DF` — `DRAW_PLAYER`: main-loop player sprite renderer
      (retires the `SPRITE_RENDER` EQU stub).  Two paths selected
      by the action flag `ZP_ACTION_DIR` ($02 = $00 idle / $01
      ascend / $FF descend).  Idle path: single $03x$13 body from
      `PLAYER_SPR_IDLE_LO/HI` ($7527/$7627) indexed by
      `ZP_PLAYER_STANCE` ($03, clamped $03..$09), drawn at column
      $14 with Y from `ZP_PLAYER_COL` ($06) via the live SMC
      operand `SMC_SR_YSRC` ($64FA).  Action path: if `ZP_HIT_FLAG`
      ($1E) is positive and the stance is $03 or $09 (top/bottom
      floor), first draws a $00x$06 "teleport flicker" sprite
      whose source bytes come from the routine's *own code image*
      at `PLAYER_STATIC_LO/HI` ($6500/$6600 indexed by `$FD`), with
      the live `SMC_SPRITE_MASK_OP/ARG` slot in `DRAW_SPRITE`
      patched to `AND #$83` or `AND #$B0`.  Then the main body
      draws from `PLAYER_SPR_ACTIVE_LO/HI` ($7531/$7631) at
      $03x$14 (one row taller than idle).  Corrects the prior
      mis-naming `SMC_COLLISION_A/B` ($64FA/$64F6) which were
      actually `SMC_SR_YSRC` / `SMC_SR_HEIGHT` --- the self-mod
      operand bytes for `DRAW_PLAYER`'s idle path, patched by
      `LEVEL_INTRO_TICK` and restored by `LEVEL_COMPLETE`.
      Discovered: the "static" texture used for the teleport
      flicker has no dedicated data region; it is the routine's
      own opcodes interpreted as bytes (a code-as-data trick).
      **Note on `DRAW_ENTITIES` phase~2**: despite prior prose,
      the phase-2 draw is *not* the big centre-screen player
      sprite --- that is drawn by `DRAW_PLAYER` here, not from
      `DRAW_ENTITIES`.  Phase~2 is a small $01x$04 perspective-grid
      sprite drawn at `FLOOR_SCREEN_COL[$4A+$10]` using separate
      sprite-pointer tables at $7542/$7642/$7552/$7652; it
      represents the player (or a starting-position indicator)
      in the receding-floor perspective view, gated by `$0E` as
      an intro/wait-phase suppression flag (set to $FF during the
      countdown and $01 during wait-for-start/gameplay by
      `LEVEL_INTRO_TICK`).  New ZP EQUs: `ZP_ACTION_DIR` ($02),
      `ZP_PLAYER_STANCE` ($03).  New data EQUs:
      `PLAYER_SPR_IDLE_LO/HI`, `PLAYER_SPR_ACTIVE_LO/HI`,
      `PLAYER_STATIC_LO/HI`.  SMC aliases `SMC_SR_HEIGHT` /
      `SMC_SR_YSRC` relocated from the level-intro defines chunk
      to the draw-player defines chunk (where they are physically
      declared).  Carved out of `<<game engine A>>`, which now
      ends at $64DE (was $656E, 1060 bytes; now 916 bytes).
- [x] `$64CB` — `PLAYER_MOVE_TICK`: per-frame player-movement
      dispatcher, first JSR from MAIN_LOOP (retires the
      `COLLISION_DETECT` EQU stub --- misnomer: the routine is a
      tri-state dispatcher, not collision logic).  Dispatches on
      `ZP_MOVE_DIR` ($04, formerly misnamed `ZP_FAST_FLAG`):
      $00 idle --> JSR `PLAYER_TICK_IDLE` ($6184);
      negative ($FF) --> JSR `PLAYER_TICK_MOVE_LEFT` ($614B);
      positive ($01) --> JSR `PLAYER_TICK_MOVE_RIGHT` ($619A).
      All three tick handlers live inside the `<<game engine A>>`
      blob; the left and right variants advance `ZP_PLAYER_Y` ($4A)
      by one in the appropriate direction and cycle the walking-
      animation state at $4B/$4C before falling through (left) or
      re-joining (right via `JMP`) the 7-call per-frame update
      chain that `PLAYER_TICK_IDLE` runs on its own.
      $04 is set to $01 / $FF by the `DO_MOVE_RIGHT` / `DO_MOVE_LEFT`
      input handlers at $6409/$646D (still inside the game engine
      A hex tail), and cleared on direction change, clamp, rescue
      (by INPUT_DO_ASCEND/DESCEND), INIT_LEVEL_STATE, or LEVEL_INTRO
      init.  Also read by `HAZARD_CHECK` as a parallax cue:
      projectiles moving opposite the player's horizontal motion
      gain +2 pixels of speed per frame, giving a pseudo-parallax
      effect.  Only 20 bytes; carved from the tail of
      `<<game engine A>>` whose hex blob now ends at $64CA (was
      $64DE, 916 bytes; now 896 bytes).  New ZP EQU:
      `ZP_MOVE_DIR` ($04, replaces the misleading `ZP_FAST_FLAG`).
      New handler EQUs: `PLAYER_TICK_IDLE` ($6184),
      `PLAYER_TICK_MOVE_LEFT` ($614B),
      `PLAYER_TICK_MOVE_RIGHT` ($619A).
- [x] `$656F` — `DRAW_SPRITE`: transparent (OR) blit to hidden hi-res page.
- [x] `$65D5` — `DRAW_SPRITE_PLAYFIELD`: sibling of DRAW_SPRITE.
      Identical structure, but inner-loop column check rejects col
      `$0B` (left playfield wall) and cols `>= $1C` (right HISCORE HUD
      panel + offscreen), confining gameplay sprites to the
      playfield region.  No flicker SMC slot, no dead-code tail.
      Sole callers are the four JSR sites inside DRAW_ENTITIES
      (player / special / companion / entity list).
- [x] `$662C` — `DRAW_SPRITE_OPAQUE`: third blitter in the triplet.
      Opaque (plain STA) blit --- no source-zero skip, no ORA step,
      simple col `>= $28` offscreen check.  Used only for HUD tiles
      (timer animation from DISPLAY_UPDATE, score/hiscore/level BCD
      digits from POST_FRAME/DRAW_DIGIT).  Retires the last 72-byte
      `<<game engine A tail>>` HEX blob.  SMC source-pointer operand
      bytes exported as `SMC_TILE_SRC_LO/HI` ($6662/$6663) ---
      replaces the old `TILE_DATA_LO/HI` + `BLIT_TILE` EQU stubs.

### Entity-slot triplet (tick + draw) --- COMPLETE

All three advance (tick) routines and all three draw routines are
now fully RE'd.  Together they form the `entity-draw triplet`
dispatched from `MAIN_LOOP` in the sequence:

```
ENEMY_C_ADVANCE -> ENEMY_C_DRAW
ENEMY_A_ADVANCE -> ENEMY_A_DRAW
ENEMY_B_ADVANCE -> ENEMY_B_DRAW
```

with `BEAM_UPDATE` immediately after.  The three slots share the
perspective clip + `DRAW_SPRITE`-with-SMC idiom but differ in
sprite structure, hit target, and score reward:

| Slot  | Tick              | Draw              | Hit target        | Score | `$39` |
|-------|-------------------|-------------------|-------------------|-------|-------|
| A     | `$13D6` SBC       | `$1423` walk-anim | player            | +300  | yes   |
| B     | `$1536` ADC (up)  | `$1591` single    | player            | +300  | yes   |
| C     | `$1646` SBC       | `$16AC` body+tail | 4-slot floor-enemy | +100  | no    |

Handshake topology (enemy-X writing to enemy-Y's state byte):

```
A --wake $01--> C       (in ENEMY_A_ADVANCE rearm)
C --drift $FF--> A, C   (in ENEMY_C_DRAW hit)
A --zero $00--> A       (in ENEMY_A_DRAW hit, immediate deactivation)
B --drift $FF--> B      (in ENEMY_B_DRAW hit, deferred deactivation)
```

Individual TODO entries:

- [x] `$13D6` `ENEMY_A_ADVANCE` --- see detailed entry above.
- [x] `$1423` `ENEMY_A_DRAW` --- see detailed entry above.
- [x] `$1536` `ENEMY_B_ADVANCE` --- enemy-B slot ($E0/$E1/$E2/$E3, $E4
      sound, $0231 pitch table).  Counts UP (ADC, not SBC), with the
      per-frame increment patched by self-modifying code at
      `SMC_ENEMY_B_ADD` ($1551, the `ADC #imm` operand byte).  The
      gate inspects `ZP_ANIM_COUNTER` ($1F, the player animation frame
      index): if $1F in {1, 3} the SMC byte is rewritten to $1F so the
      next frame adds 1 or 3 (tripling the advance when the player is
      in anim frame 3).  Rearm triggers when counter >= $035A: reload
      to $003E, reseat row from $84,X with X = $1F & 3 (four-entry
      table, vs.\ enemy-C which uses only three entries).  Drift
      mode INCs lo-byte only and self-deactivates on 256-frame wrap.
      Retired `SPRITE_DRAW_2 = $1536` EQU stub.  Introduces
      ZPs `ZP_ENEMY_B_STATE` ($E0), `ZP_ENEMY_B_POS` ($E1/$E2),
      `ZP_ENEMY_B_ROW` ($E3), `ZP_ENEMY_B_SND_CTR` ($E4), and
      `SND_PITCH_TBL_B` ($0231).
- [x] `$1591` `ENEMY_B_DRAW` --- see detailed entry above.
- [x] `$1646` `ENEMY_C_ADVANCE` --- see detailed entry above.
- [x] `$16AC` `ENEMY_C_DRAW` --- see detailed entry above.

### Game flow routines

- [x] `$7208` — `LIFE_LOST_HANDLER`: end-of-life handler fired when
      `ZP_LIVES_BCD` ($5E) goes negative via BCD underflow.  Clears
      keyboard strobe, runs LEVEL_TRANSITION, pins SMC_ATTRACT_RTS
      to RTS ($60) so attract callbacks are silenced.  Then per
      iteration decrements the extras stash `ZP_EXTRA_LIVES` ($8C),
      draws a B6-sprite from $B67D, polls for input (diverts to
      ATTRACT_KEY_DETECT / ATTRACT_JOY_DETECT on press), and calls
      MAIN_LOOP.  MAIN_LOOP exits via `JMP LIFE_LOST_HANDLER`
      rather than RTS, so each animation frame is a fresh entry
      with slow stack growth.  When `$8C == 0`, falls through to
      `RESTART_NEW_GAME` ($7255).  **Correction:** this was
      previously stubbed as `LEVEL_COMPLETE`, but $5E is the BCD
      lives counter (not a level-complete flag), so the routine is
      actually the lives-out game-over path.  Sub-entry
      `LIFE_LOST_RESUME` at $720E skips the strobe/transition
      prologue --- reached only by the dead `RESTART_DISPATCH`
      ($5EC5).
- [x] `$7255` — `RESTART_NEW_GAME`: sub-entry of LIFE_LOST_HANDLER
      reached when extras stash is empty.  `JSR GAME_START_INIT`,
      save+replace `ZP_SFX_CLICK`, enable `SMC_RENDER`, fall
      through to `ATTRACT_LOOP`.  One of three GAME_START_INIT
      call sites (the others: `$6121` Ctrl-R restart, `$7299`
      START_GAME_FROM_ATTRACT).
- [x] `$7299` — `START_GAME_FROM_ATTRACT`: sub-entry at the end of
      ATTRACT_LOOP's input-detected path.  `JSR GAME_START_INIT`,
      restore `ZP_SFX_CLICK` from saved, `JMP MAIN_LOOP`.  Third
      GAME_START_INIT call site.
- [x] `$6AA7` — `RESUME_GAMEPLAY_SMC`: 13-byte SMC patch re-enables
      input dispatch (`SMC_INPUT = $20`), sprite render
      (`SMC_RENDER = $20`), and restores `SMC_SR_YSRC = $06` /
      `SMC_SR_HEIGHT = $13` for `DRAW_PLAYER`.  Sub-entry inside
      `LEVEL_INTRO_TICK`'s `.activate` block (the prefix at
      $6A95-$6AA6 reseeds player column + state flags on normal
      activation; the `.activate` fall-through reaches this label
      naturally, and `GAME_START_INIT` jumps here directly to
      skip the prefix).  Retired the EQU stub; now a proper
      module-level label.
- [x] `$5EC5` — `RESTART_DISPATCH`: 15-byte 3-way dispatch on
      `ZP_RESTART_FLAG` ($44).  **Statically dead code.**  No
      JMP/JSR in boot1/loader/rwts/drol.bin reaches this routine
      (nor anywhere in $5E00-$5EFF, a leftover RWTS-ish fragment
      around it).  Were it live: flag<0 --> MAIN_LOOP; flag==0 -->
      LIFE_LOST_RESUME; flag>0 --> `JSR GAME_RESTART` then
      MAIN_LOOP.  `$44` write at GAME_START_INIT's tail is
      effectively a dead store; `GAME_RESTART` ($13C2) is also
      unreached in practice.  Carved out of `<<staging buffers>>`
      as its own ORG chunk and documented.
- [ ] `$BDA0` — Game over handler (jumped to when $39 < 0).
      Outside drol.bin (in relocated RWTS region $BE00-$BFFF).
- [x] `$13A4` — `GAME_START_INIT`: resets BCD score triple, BCD lives
      counter ($5E=$04), HUD column bounds ($65AB/$65A7), restart flag
      ($44=$FF), player Y ($4A=$6B), and the two-entry sub-routine chain
      (DIFFICULTY_RESET + INIT_LEVEL_STATE).  Tail-calls
      `RESUME_GAMEPLAY_SMC` at $6AA7 to re-patch the main-loop SMC
      slots (SMC_SR_YSRC=$06, SMC_INPUT/SMC_RENDER=JSR, SMC_SR_HEIGHT=$13)
      that flip the engine from attract to game mode.  Exposes a
      sub-entry `GAME_RESTART` at $13C2 used by $5ECB that skips the
      player-position + HUD-column reseed.  **Key corrections:**
      (1) `$6AA7` was previously stubbed as `LOAD_LEVEL` --- it is
      actually `RESUME_GAMEPLAY_SMC`, a 13-byte SMC-patch routine,
      not a level loader.  (2) `$5E` was previously named
      `ZP_LEVEL_STATE` --- it is actually `ZP_LIVES_BCD`, the BCD
      on-screen lives counter drawn by POST_FRAME at HUD cols 4/6.
      (3) `$65AB`/`$65A7` were previously `SCORE_DISPLAY_VAL` /
      `LIVES_DISPLAY_VAL` --- they are actually `HUD_SCORE_COL` /
      `HUD_LIVES_COL`, the left/right playfield column bounds that
      gate the beam-tracer draw in BEAM_UPDATE.  (4) `$2E` was
      previously `ZP_LIVES` --- it is actually `ZP_CLEAR_COL`, the
      screen-clear loop counter / playfield right-edge column.
      (5) `$44` was previously `ZP_HIGH_SCORE_FLAG` --- it is a
      cold-start / restart dispatch flag tested at $5EC5 (value
      $FF=cold path, 0/negative select alternative restart paths).
      (6) `$46` is write-only in the game code --- likely a dead
      store or a signal to a not-yet-RE'd routine.

### Attract-mode subroutines

- [x] `$17A6`, `$17E1`, `$1813`, `$1844` — Attract animation routines
      (all four `ATTRACT_ANIM_1..4` documented as prose + assembly).
- [ ] `$67D7` entry through BIT instructions — document the dual-entry pattern

### Undocumented regions

- [x] `$4713-$47FF` — `SECTOR_RESIDUE_47XX`: 237 bytes of dead
      residue, NOT the DROL logo painter.  Exhaustive scan of all 5
      reference binaries finds zero JSR/JMP/JMP-indirect targeting
      this region.  The bytes are a byte-exact copy of $0513-$05FF
      (CLEAR_PAGE2 tail + CLEAR_PAGE2_TEXT_ENTRY body + truncated
      first ~13 iterations of STRIPE_COPY_PAGE1); the code is cut off
      mid-instruction at the $4800 page boundary, followed by 5120
      bytes ($4800-$5BFF) of $00.  Mechanism: PAGE_TABLE maps track~2
      sector~15 to page $47 and track~1 sector~3 to page $05; those
      two sectors on disk happen to contain identical bytes (build
      artefact), and since GAME_INIT's packed stream terminates at
      $4712 before reaching the residue, the bytes have no runtime
      effect.  Corroborated by level1.bin, which has $00 throughout
      $4700-$47FF.  The prior prose claim that these were "screen-
      init routines" painting the DROL title logo was wrong ---
      the actual title-screen logo is drawn by the attract sprite
      routines (ATTRACT_ANIM_1..4 at $17A6/$17E1/$1813/$1844)
      compositing sprite pointer tables into hi-res page~2 during
      the animated title sequence.  Retires the `GAME_INIT_EXTRA`
      misnomer; chunk is now `<<sector residue 47xx>>` with label
      `SECTOR_RESIDUE_47XX`.  No PNG rendered --- the bytes are
      neither executable game logic nor displayable art.
- [ ] `$4800-$67CA` — Large gap between game init and main loop
      (sprites, tables, game code).  Carved this session:
      `$5EC5` RESTART_DISPATCH (15 bytes, dead code) out of
      `<<staging buffers>>`, splitting it into two slices
      `$5C00-$5EC4` (709 bytes) and `$5ED4-$5FFF` (300 bytes).
- [x] `$683C-$699B` — Game engine B head: now documented as `DRAW_ENTITIES`
      (see above).  No longer a HEX blob.
- [x] `$6ABA` — `SPECIAL_TICK`: per-frame tick for the ``special''
      bonus-creature slot drawn by DRAW_ENTITIES phase 3 (retires the
      `SOUND_UPDATE` EQU stub --- misnomer: it emits only one of four
      parallel per-frame sound channels, not a dedicated sound
      subsystem).  Three-way state machine on `ZP_SPECIAL_STATE`
      ($AB): $00 inactive (8-bit timer increment on $AC; wrap falls
      into rearm); positive active (add $0002 to 16-bit
      `ZP_SPECIAL_POS` ($AC/$AD) per frame, rearm when hi=$03 &
      lo>=$5A); negative drift (fall 2 rows per frame, but at the
      four ``ladder'' rows $34/$5C/$84/$AC, 94% of frames return
      early and 6% climb one rung up via PRNG gate).  Sound emitted
      via `SND_DELAY_UP` ($109E) duration $0A, pitch from new
      `SND_PITCH_TBL_SPECIAL` ($0218, 12 entries), indexed by new
      `ZP_SPECIAL_SND_CTR` ($B5); only armed to $06 by
      `SPECIAL_DRAW`'s defeat edge (a short descending ``defeat
      jingle''), not on rearm.  Rearm sub-entry `SPECIAL_REARM`
      ($6B14) reseeds position to $003E, picks row anchor
      from `ENEMY_C_ROW_TBL[PRNG&3]-$0B`, arms new `ZP_SPECIAL_HP`
      ($08) to 4 (the number of floor-enemies this creature kills
      before exploding), and activates.  Introduces ZPs
      `ZP_SPECIAL_STATE`/`ZP_SPECIAL_POS`/`ZP_SPECIAL_SND_CTR`/`ZP_SPECIAL_HP`
      and data EQU `SND_PITCH_TBL_SPECIAL`.  Carved 127 bytes out of
      `<<game engine B tail>>` which now starts at $6B39 (1636
      bytes remaining).
- [x] `$6B39` — `SPECIAL_DRAW`: per-frame draw + collision partner of
      SPECIAL_TICK (retires the `SPECIAL_DRAW = $6B39` EQU stub ---
      previously misnamed `ANIM_UPDATE`, which was only a superficial
      reading of the SMC-chained dispatch as an ``animation update'').
      Three visual phases gated on `ZP_SPECIAL_STATE`:
      \emph{inactive} ($00) --- tail-JMP to `SPECIAL_INACTIVE_DRAW` at
      $6CDB, a 29-byte \$02x\$06 ``peek'' marker drawn from per-level
      pointer at $755B/$765B (new `SPECIAL_PEEK_LO/HI`);
      \emph{active} ($01..$7F) --- perspective-transform $AC/$AD
      against player world-X, 4-slot floor-enemy kill-box
      ($9B/$9F/$A3), 6-pose body-walk via SMC-chained dispatch to
      six 26-byte step handlers at $6C3F--$6CDA (new
      `SPECIAL_BODY_STEP1..6`), player-catch box sets hit-flag $1E;
      \emph{drift} ($80+) --- \$04x\$0F puff draw from new
      `SPECIAL_PUFF_LO/HI` ($AFDA/$B05A, indexed by
      perspective-frame Y), player-catch box awards +\$0500 BCD via
      `SCORE_ADD` and resets slot.  The six body-step handlers form
      a \emph{palindromic} walk cycle ($\{0, 7, 14, 21, 14, 7\}$
      byte offsets into four level-data sprite-pointer pairs at
      $7578..$758D/$7678..$768D); each handler rewrites new
      `SMC_SPECIAL_BODY_LO/HI` ($6BE9/$6BEA), the operand bytes of
      the `JMP` at $6BE8, to point to the next step.  The cycle is
      \emph{not} reset by `SPECIAL_REARM` --- animation phase
      persists across activations.  Uses `DRAW_SPRITE` (not
      `DRAW_SPRITE_PLAYFIELD`); SMC source-pointer goes to
      `SMC_DS_SRC_LO/HI` ($65B3/$65B4).  Second sound slot
      `ZP_SPECIAL_SND_CTR_B` ($B6) with new
      `SND_PITCH_TBL_SPECIAL_B` ($021F) clicks via `SFX_TONE`
      duration $08, armed to 4 on player-catch for a four-click
      pickup tone.  New ZPs: `ZP_SPECIAL_SND_CTR_B` ($B6),
      `ZP_SCREEN_X` ($AF), `ZP_SCREEN_X_HI` ($B0).
      **Correction to prior docs**: the SMC table was called
      ``7 ladder-step handlers'' in the pre-session peek, but is
      actually \emph{6} handlers (not 7), and they implement a
      walk-cycle animation, not ladder-row dispatch (ladder-row
      semantics live in `SPECIAL_TICK`'s drift-mode code, not in
      the draw).  Carved 453 bytes out of `<<game engine B tail>>`
      which now starts at $6CFE (1183 bytes remaining).
- [x] `$6CFE` — `COMPANION_UPDATE`: per-frame tick+draw routine for
      the two-slot "companion" walker subsystem (retires the
      `ENTITY_PROCESS = $6CFE` EQU stub and carves 670 bytes out of
      `<<game engine B tail>>`, which now starts at $6F9C with 513
      bytes remaining).  Despite the name inherited from
      DRAW_ENTITIES phase 4, companions are \emph{hostile}
      walker-creatures (not helpers): each slot patrols the
      perspective floor with a 16-bit world-X ($11/$13,X), flips
      direction ($B1,X) with ~5% PRNG chance per frame, damages the
      player on contact (writes `ZP_HIT_FLAG` $1E=$FF in a
      $40..$4F x $1A-row catch box), and enters a 4-px/frame
      floor-climb drift when it crosses a rescue-entity's row in
      the $40..$46 proximity window.  Three-state machine per slot
      (inactive $00 / active +ve / drift $FF), 3-pose SMC-chained
      walk cycle with separate pose tables for each direction at
      $75A2/$75A9/$75B0 (-dir) and $75B7/$75BE/$75C5 (+dir).  Gate
      is `ZP_COMPANION_GATE` ($33): active on all non-minimum
      difficulty tiers (score >= 4000).  Both slots auto-activate
      on the first frame the gate opens --- nothing externally
      writes $B3,X.  Introduced ZP EQUs `ZP_COMPANION_STATE` ($B3),
      `ZP_COMPANION_DIR` ($B1), `ZP_COMPANION_POS_LO/HI` ($11/$13,
      aliases for `ZP_COMPANION_COL/OFF`), `ZP_PLAYER_FLOOR` ($0A),
      `ENTITY_HIT_ROW` ($72); SMC labels
      `SMC_COMPANION_POS_LO/HI` ($6E31/$6E32) and
      `SMC_COMPANION_NEG_LO/HI` ($6EAA/$6EAB); sprite-table labels
      `COMPANION_POS_POSE1..3_LO/HI`, `COMPANION_NEG_POSE1..3_LO/HI`.
- [x] `$6F9C-$719C` — `RESCUE_UPDATE`: per-frame tick for the
      20-slot rescue-child entity subsystem (Drol's scoring
      objective).  Iterates Y=$13..0 through seven parallel
      tables: `ENTITY_ACTIVE` ($03A8), `ENTITY_FLOOR_COL`
      ($0358), `ENTITY_XOFF_IDX` ($036C), `ENTITY_FLOOR_POS`
      ($0380), `RESCUE_DIR` ($0394), `RESCUE_ANIM` ($03BC),
      `RESCUE_FLOOR` ($03D0), `RESCUE_COUNTDOWN` ($03E4).  Five
      states: $00 inactive (PRNG-gated spawn + one-shot
      player-floor trigger via BIT/JMP opcode patch at $705F),
      $01..$7F active walking (steps $\pm$ 3 world-X per frame,
      row bobble via 7-byte `RESCUE_BOBBLE` ($BD) table, chase
      AI when player on same floor), $FE exit animation
      (INC floor-col, deactivate on wrap), other negative drift
      countdown ($03E4 decrements every 2 frames, transitions
      to $FE).  Awards +$0035 BCD (35 decimal) on player
      pickup via sibling `$0C98` draw+collision, which sets
      `ZP_HIT_FLAG` $1E=$FF (reusing the player-hit flicker as
      the rescue-pickup animation).  No DEC $39 --- pickup is
      not a life-loss event.  Spawn direction alternates by
      slot parity (+dir at world-X $003E, -dir at $035C).
      New ZPs: `ZP_RESCUE_SPAWN_CTR` ($4D, free-running slot
      counter), `ZP_PLAYER_FLOOR_CUR` ($0C, per-frame copy of
      `ZP_PLAYER_FLOOR` $0A seeded at $6A9D),
      `PERSPECTIVE_XOFF_BYTE` ($B9, byte-domain perspective
      X-offset table also read by DRAW_ENTITIES phases 3/4/5).
      Retires `LEVEL_LOGIC = $6F9C` EQU stub and fully
      eliminates `<<game engine B tail>>` from the blob list
      (drol.bin now 100.0% documented).
- [ ] `$72A0-$72A2` — 3 bytes between attract loop exit and copy routine (JMP $67CB at $72A0)

## Fix reference binary build process

- [ ] Create a script to build `reference/drol.bin` from `drol.dsk` with DOS 3.3 sector skew
- [ ] Document the build process so the reference binary can be regenerated

## Structural

- [ ] Decide chapter organization: by memory region vs. by function
- [ ] The "RWTS" naming for $BE00-$BFFF needs revisiting — most routines are non-disk
- [ ] Consider splitting game code into chapters: initialization, main loop, input, rendering, entities, level data
