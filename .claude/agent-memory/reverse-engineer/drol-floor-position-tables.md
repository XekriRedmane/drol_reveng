---
name: Drol floor-position lookup tables
description: Three 256-entry parallel tables at $1D40/$1E00/$1F00 drive DRAW_ENTITIES perspective projection
type: project
---

Three parallel floor-position lookup tables converted from raw HEX in `game data 1D47` chunk into labelled data chunks:

- **FLOOR_TO_ROW_DATA** ($1D47-$1DFF, 185 bytes): floor-pos to hi-res row, plateau-ramp $00..$21. EQU base is $1D40 (7 bytes before label) because the skipped $1D40-$1D46 is dasm FF gap fill and callers always pass X>=7.
- **FLOOR_SPRITE_IDX_DATA** ($1E00-$1EFF, 256 bytes): floor-pos to 7-frame sprite index, 28-byte cyclic ramp (4*[0..6]) repeated 9 times + 4 trailing zeros. Every 4 floor steps advances walk-cycle frame.
- **FLOOR_SCREEN_COL_DATA** ($1F00-$1FFF, 256 bytes): floor-pos to hi-res byte-column, plateaus $0C..$1E with foreshortening (16/12/16/12 width plateaus).

**Why:** These three tables + FLOOR_BASE_ROW ($188F, floor-column to base row) together describe the 3D perspective projection that DRAW_ENTITIES uses for all five sprite-draw phases (hit-entity restore, player, special, 2 companions, 20 entities).

**How to apply:** When RE'ing any DRAW_ENTITIES caller or perspective-related code, these lookups are the Rosetta Stone. Indexed by computed floor-position byte (player_y+$10, special_y+ZP_B9[off]-8, companion/entity floor-pos+$B9[off]-5).
