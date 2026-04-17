#!/usr/bin/env python3
"""Render all reverse-engineered Drol sprite-table families to PNG grids.

Inputs:
    reference/drol.bin    — persistent game code ($0100-$8BFF)
    reference/level1.bin  — level-1 swappable data pages ($0000-$BDFF)

Outputs (under images/):
    projectile_sprites.png         — PROJ_SPR_L + PROJ_SPR_R, W+1=3, H=3
    rescue_sprites.png             — 4 tables x 7 frames (rescue children)
    enemy_c_auxiliary.png          — ENEMY_C_TAIL (7) + single puff/peek
    companion_sprites.png          — 6 pose tables x 7 frames
    special_body_sprites.png       — 4 poses x 7 frames
    enemy_a_sprites.png            — A_BODY / FEET / STEP1 / STEP2 x 7
    enemy_b_sprites.png            — enemy-B body x 7
    special_puff_sprites.png       — drift-puff x 7
    sprite_table_ui.png            — beam + ready-prompt from SPRITE_TABLE
    drol_logo.png                  — the fixed DROL logo ($BCF1, $12x$08)
    sprite_family_map.png          — summary grid of one representative
                                     frame per family (reference sheet)

Player sprites (in-range, covered by drol.bin) are rendered by a separate
render_player_sprites.py.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from render_sprite_lib import render_sprite_image, save_grid  # noqa: E402

DROL = pathlib.Path("reference/drol.bin")
LVL1 = pathlib.Path("reference/level1.bin")
DROL_BASE = 0x0100
LVL1_BASE = 0x0000


def drol_ptr(data: bytes, lo_addr: int, hi_addr: int, idx: int) -> int:
    lo = data[lo_addr - DROL_BASE + idx]
    hi = data[hi_addr - DROL_BASE + idx]
    return (hi << 8) | lo


def lvl_ptr(data: bytes, lo_addr: int, hi_addr: int, idx: int) -> int:
    return (data[hi_addr + idx] << 8) | data[lo_addr + idx]


def main() -> None:
    drol = DROL.read_bytes()
    lvl = LVL1.read_bytes()
    pathlib.Path("images").mkdir(exist_ok=True)

    # -----------------------------------------------------------------
    # Projectiles: PROJ_SPR_L ($AFD3/$B053, level data) and PROJ_SPR_R
    # ($75F7/$76F7, in drol.bin as pointers). Both point into level data.
    # DRAW_SPRITE params: W=2 (3 bytes/row), H=3 (3 rows), 9 bytes each.
    # Eight frames per direction indexed by PROJ_FRAME_IDX.
    # -----------------------------------------------------------------
    proj = []
    proj_labels = []
    for i in range(8):
        ptr = drol_ptr(drol, 0x75F7, 0x76F7, i)
        img = render_sprite_image(lvl, ptr, w_param=2, height_rows=3,
                                  scale=7, base=LVL1_BASE)
        proj.append(img)
        proj_labels.append(f"R[{i}] ${ptr:04X}")
    for i in range(8):
        ptr = lvl_ptr(lvl, 0xAFD3, 0xB053, i)
        img = render_sprite_image(lvl, ptr, w_param=2, height_rows=3,
                                  scale=7, base=LVL1_BASE)
        proj.append(img)
        proj_labels.append(f"L[{i}] ${ptr:04X}")
    save_grid("images/projectile_sprites.png", proj, proj_labels, columns=8)

    # -----------------------------------------------------------------
    # Rescue children: 4 tables x 7 frames. From RESCUE_DRAW ($6589),
    # W=3 (4 bytes/row), H=$1A (end) or $1C (mid). 4 x 26 = 104 bytes for
    # end, 4 x 28 = 112 bytes for mid. Verified by pointer deltas.
    # -----------------------------------------------------------------
    rescue = []
    rescue_labels = []
    for label, lo, hi, h in [
        ("pos_end", 0x75E9, 0x76E9, 0x1A),
        ("pos_mid", 0x75F0, 0x76F0, 0x1C),
        ("neg_end", 0x75DB, 0x76DB, 0x1A),
        ("neg_mid", 0x75E2, 0x76E2, 0x1C),
    ]:
        for i in range(7):
            ptr = drol_ptr(drol, lo, hi, i)
            img = render_sprite_image(lvl, ptr, w_param=3, height_rows=h,
                                      scale=4, base=LVL1_BASE)
            rescue.append(img)
            rescue_labels.append(f"{label}[{i}]")
    save_grid("images/rescue_sprites.png", rescue, rescue_labels, columns=7)

    # -----------------------------------------------------------------
    # Enemy-C auxiliaries.
    #   ENEMY_C_TAIL  $7549/$7649  W=1 H=7  (2 bytes/row x 7 rows) — 7 frames
    #   ENEMY_C_PUFF  $7559/$7659  W=2 H=6  (3 bytes/row x 6 rows) — 1 ptr
    #   ENEMY_B_PUFF  $755A/$765A  W=2 H=6  — 1 ptr
    #   SPECIAL_PEEK  $755B/$765B  W=2 H=6  — 1 ptr
    # Stride: C_TAIL[0]=$8C10, [1]=$8C1E -> 14 bytes = 2*7. OK.
    # Puff/peek: all three adjacent pointers step by $12 -> 18 bytes = 3*6.
    # -----------------------------------------------------------------
    aux = []
    aux_labels = []
    for i in range(7):
        ptr = drol_ptr(drol, 0x7549, 0x7649, i)
        img = render_sprite_image(lvl, ptr, w_param=1, height_rows=7,
                                  scale=6, base=LVL1_BASE)
        aux.append(img)
        aux_labels.append(f"C_tail[{i}]")
    for name, lo, hi in [
        ("C_puff", 0x7559, 0x7659),
        ("B_puff", 0x755A, 0x765A),
        ("special_peek", 0x755B, 0x765B),
    ]:
        ptr = drol_ptr(drol, lo, hi, 0)
        img = render_sprite_image(lvl, ptr, w_param=2, height_rows=6,
                                  scale=6, base=LVL1_BASE)
        aux.append(img)
        aux_labels.append(f"{name} ${ptr:04X}")
    save_grid("images/enemy_c_auxiliary.png", aux, aux_labels, columns=7)

    # -----------------------------------------------------------------
    # Companion sprites — 6 poses (NEG_POSE{1,2,3} and POS_POSE{1,2,3}),
    # 7 frames each. Stride between $A051 and $A071 is $20 bytes;
    # 4 bytes/row x 8 rows = 32. So W=3, H=8.
    # -----------------------------------------------------------------
    comp = []
    comp_labels = []
    tables = [
        ("N1", 0x75A2, 0x76A2), ("N2", 0x75A9, 0x76A9),
        ("N3", 0x75B0, 0x76B0), ("P1", 0x75B7, 0x76B7),
        ("P2", 0x75BE, 0x76BE), ("P3", 0x75C5, 0x76C5),
    ]
    for label, lo_tbl, hi_tbl in tables:
        for i in range(7):
            ptr = drol_ptr(drol, lo_tbl, hi_tbl, i)
            img = render_sprite_image(lvl, ptr, w_param=3, height_rows=8,
                                      scale=5, base=LVL1_BASE)
            comp.append(img)
            comp_labels.append(f"{label}[{i}]")
    save_grid("images/companion_sprites.png", comp, comp_labels, columns=7)

    # -----------------------------------------------------------------
    # Special body: 4 poses x 7 frames. From SPECIAL_DRAW ($6B39):
    # W=6, H=$14 -> 7 bytes/row * 20 rows = 140 bytes. Verified by stride.
    # -----------------------------------------------------------------
    spec = []
    spec_labels = []
    for pose, (lo_tbl, hi_tbl) in enumerate([
        (0x7578, 0x7678), (0x757F, 0x767F),
        (0x7586, 0x7686), (0x758D, 0x768D),
    ]):
        for i in range(7):
            ptr = drol_ptr(drol, lo_tbl, hi_tbl, i)
            img = render_sprite_image(lvl, ptr, w_param=6, height_rows=0x14,
                                      scale=3, base=LVL1_BASE)
            spec.append(img)
            spec_labels.append(f"P{pose}[{i}]")
    save_grid("images/special_body_sprites.png", spec, spec_labels, columns=7)

    # -----------------------------------------------------------------
    # Enemy-A family.
    #   body  W=3 H=$13 (76B, delta $4C)
    #   feet  W=3 H=3   (12B, delta $0C)
    #   step1 W=3 H=4   (16B, delta $10)
    #   step2 W=3 H=4   (16B, delta $10)
    # All four tables are 7-entry, indexed by PROJ_FRAME_IDX.
    # -----------------------------------------------------------------
    enemy_a = []
    enemy_a_labels = []
    for i in range(7):
        ptr = lvl_ptr(lvl, 0xB009, 0xB089, i)
        img = render_sprite_image(lvl, ptr, w_param=3, height_rows=0x13,
                                  scale=4, base=LVL1_BASE)
        enemy_a.append(img)
        enemy_a_labels.append(f"A_body[{i}]")
    for i in range(7):
        ptr = lvl_ptr(lvl, 0xB017, 0xB097, i)
        img = render_sprite_image(lvl, ptr, w_param=3, height_rows=3,
                                  scale=6, base=LVL1_BASE)
        enemy_a.append(img)
        enemy_a_labels.append(f"A_feet[{i}]")
    for i in range(7):
        ptr = lvl_ptr(lvl, 0xB010, 0xB090, i)
        img = render_sprite_image(lvl, ptr, w_param=3, height_rows=4,
                                  scale=6, base=LVL1_BASE)
        enemy_a.append(img)
        enemy_a_labels.append(f"A_step1[{i}]")
    for i in range(7):
        ptr = lvl_ptr(lvl, 0xB01E, 0xB09E, i)
        img = render_sprite_image(lvl, ptr, w_param=3, height_rows=4,
                                  scale=6, base=LVL1_BASE)
        enemy_a.append(img)
        enemy_a_labels.append(f"A_step2[{i}]")
    save_grid("images/enemy_a_sprites.png", enemy_a, enemy_a_labels, columns=7)

    # -----------------------------------------------------------------
    # Enemy-B body (SPRITE_TABLE_B at $B025/$B0A5). W=5 H=$11 -> 6x17 = 102.
    # -----------------------------------------------------------------
    enemy_b = []
    enemy_b_labels = []
    for i in range(7):
        ptr = lvl_ptr(lvl, 0xB025, 0xB0A5, i)
        img = render_sprite_image(lvl, ptr, w_param=5, height_rows=0x11,
                                  scale=3, base=LVL1_BASE)
        enemy_b.append(img)
        enemy_b_labels.append(f"B[{i}] ${ptr:04X}")
    save_grid("images/enemy_b_sprites.png", enemy_b, enemy_b_labels, columns=7)

    # -----------------------------------------------------------------
    # Enemy-C body (SPRITE_TABLE_C at $AFE1/$B061). W=2 H=$0B -> 3x11 = 33.
    # -----------------------------------------------------------------
    enemy_c = []
    enemy_c_labels = []
    for i in range(7):
        ptr = lvl_ptr(lvl, 0xAFE1, 0xB061, i)
        img = render_sprite_image(lvl, ptr, w_param=2, height_rows=0x0B,
                                  scale=5, base=LVL1_BASE)
        enemy_c.append(img)
        enemy_c_labels.append(f"C[{i}] ${ptr:04X}")
    save_grid("images/enemy_c_sprites.png", enemy_c, enemy_c_labels, columns=7)

    # -----------------------------------------------------------------
    # SPECIAL_PUFF (drift-mode puff): W=4 H=$0F -> 5x15 = 75.
    # -----------------------------------------------------------------
    puff = []
    puff_labels = []
    for i in range(7):
        ptr = lvl_ptr(lvl, 0xAFDA, 0xB05A, i)
        img = render_sprite_image(lvl, ptr, w_param=4, height_rows=0x0F,
                                  scale=4, base=LVL1_BASE)
        puff.append(img)
        puff_labels.append(f"puff[{i}] ${ptr:04X}")
    save_grid("images/special_puff_sprites.png", puff, puff_labels, columns=7)

    # -----------------------------------------------------------------
    # SPRITE_TABLE at $B000/$B080 — the main persistent UI sprite pointer
    # table. Two entries with known dimensions:
    #   [0] = $B529   beam sprite    W=2 H=4  (12B delta verified)
    #   [1] = $B535   ready prompt   W=3 H=$0F (60B delta verified)
    # Remaining entries [2..] are reused by ATTRACT_SPR2/ATTRACT_SPR at
    # different offsets with runtime-set widths; we don't render those.
    # -----------------------------------------------------------------
    ui = []
    ui_labels = []
    ptr = lvl_ptr(lvl, 0xB000, 0xB080, 0)
    ui.append(render_sprite_image(lvl, ptr, w_param=2, height_rows=4,
                                  scale=6, base=LVL1_BASE))
    ui_labels.append(f"beam ${ptr:04X}")
    ptr = lvl_ptr(lvl, 0xB000, 0xB080, 1)
    ui.append(render_sprite_image(lvl, ptr, w_param=3, height_rows=0x0F,
                                  scale=5, base=LVL1_BASE))
    ui_labels.append(f"ready-prompt ${ptr:04X}")
    save_grid("images/sprite_table_ui.png", ui, ui_labels, columns=2)

    # -----------------------------------------------------------------
    # DROL logo — ATTRACT_ANIM_4 draws it at $BCF1 with W=$12, H=$08
    # fixed -> 19 bytes/row * 8 rows = 152 bytes.
    # -----------------------------------------------------------------
    logo = render_sprite_image(lvl, 0xBCF1, w_param=0x12, height_rows=8,
                               scale=4, base=LVL1_BASE)
    logo.save("images/drol_logo.png")
    print(f"Wrote images/drol_logo.png ({logo.width}x{logo.height}).")


if __name__ == "__main__":
    main()
