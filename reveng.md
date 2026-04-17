# Reverse Engineering an Apple II Game Binary

This document describes the process for reverse engineering an Apple II game from a `.dsk` disk image into a fully documented, reassemblable literate programming document (`main.nw`).

## Prerequisites

The template repository must contain:

- `noweb.sty` — LaTeX noweb style file
- `main.nw` — minimal literate programming source (document preamble, empty chapters)
- `weave.py` — noweb tangler (extracts `.asm` files from `main.nw`)
- `.claude/scripts/dasm6502.py` — 6502 disassembler for reference binaries
- `.claude/skills/assemble/verify.py` — byte-level comparison of assembled output against reference
- `.claude/skills/assemble/reorder_chunks.py` — fix ORG address ordering in chunks
- `.claude/skills/chunk-placement/check_placement.py` — verify chunk placement rules
- `.claude/skills/annotate/` — routine annotation skill
- `.claude/skills/disassemble/` — disassembly skill
- `.claude/skills/re-next/` — find and RE the next unlabeled address
- `CLAUDE.md` — project conventions (assembly style, chunk rules, code chunk rules, annotation rules)

Inputs:

- A `.dsk` disk image of the game
- Optionally, a Ghidra project with the binary loaded

## Agent architecture

A **main agent** coordinates the reverse engineering process. It dispatches work to **skill agents** that run sequentially (not in parallel), because each step depends on the output of the previous one. The main agent:

1. Plans the next RE target (which routine or data region)
2. Launches a skill agent to disassemble, document, or annotate
3. Verifies the result (assemble + binary compare)
4. Updates the collection chunk and commits

Skill agents should not edit `main.nw` concurrently. Each skill agent completes its work, returns results to the main agent, and the main agent applies changes and verifies before proceeding.

## Round 0: Project setup

### Extract reference binaries

Before any RE work, extract the raw binary data from the `.dsk` image. This requires understanding the game's boot chain and disk layout.

1. **Identify the disk format.** Most Apple II games use either DOS 3.3, ProDOS, or a custom boot chain. Check Track 0 Sector 0 for the boot sector.

2. **Determine the sector interleave.** The `.dsk` file format stores sectors in a specific order. Common orderings:
   - **DOS order (.do/.dsk):** sectors stored in DOS 3.3 logical order. Physical sector P is at file offset `track * 4096 + DOS_SKEW[P] * 256`, where `DOS_SKEW = [0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15]`.
   - **ProDOS order (.po):** sectors stored in ProDOS block order.
   - **Raw physical order:** no translation needed.

   To determine which: disassemble the boot sector, find the sector read routine, and compare assembled code against the `.dsk` data. If the bytes don't match, try applying the DOS 3.3 skew. Verify against an emulator if available.

3. **Trace the boot chain.** Starting from the boot sector:
   - What sectors are loaded, to what addresses?
   - Is there a page table or sector map?
   - What relocations happen after loading?
   - What is the final entry point?

4. **Build reference binaries.** Write a script that reads the `.dsk` with the correct interleave and page table, producing one flat binary per assembly target. Each binary should cover a contiguous address range. Verify key bytes against an emulator.

5. **Document the disk layout** in `main.nw` with tables showing track/sector to memory mappings.

### Initialize main.nw

Set up the document structure:

```latex
\chapter{Boot sequence}
\chapter{Loader}          % if applicable
\chapter{Game code}       % main game logic
\appendix
\chapter{...}             % reference material
```

Create the first assembly target (e.g., `boot1.asm`) with a defines chunk and a collection chunk.

## Round 1: Boot sector

The boot sector is the simplest starting point — it's small (usually 256 bytes), self-contained, and the entry point is known ($0801 for standard Apple II boot).

### Process

1. **Disassemble** the boot sector from the reference binary using `dasm6502.py`.
2. **Trace the logic** — register states, memory writes, conditional branches.
3. **Identify phases** — boot sectors typically: load more sectors, relocate code, set up vectors, jump to loader.
4. **Write the chunk** in `main.nw`:
   - Create `<<boot1 defines>>=` with EQUs for all referenced addresses.
   - Create `<<boot1 entry>>=` with the annotated assembly.
   - Create `<<boot1.asm>>=` collection chunk.
   - Add `SUBROUTINE` after `ORG`, header plate comment, `@ %def` line.
5. **Assemble and verify**: `python3 weave.py main.nw output && dasm output/boot1.asm -f3 -oboot1.bin && python3 .claude/skills/assemble/verify.py boot1`.
6. **Commit** with a descriptive message.

### What to learn from the boot sector

- Slot detection and disk I/O method
- Memory layout (where code gets loaded)
- Relocation targets (language card, high memory)
- Reset/NMI vector setup
- Entry point to the next stage (loader)

## Round 2: Loader / RWTS

The loader is typically the next stage — it reads the game from disk into memory. It reveals the complete memory map.

### Process

1. **Start with the RWTS** (Read/Write Track/Sector) — the low-level sector reading routines. These are usually compact and self-contained.
2. **Document the page table** — the mapping from sector positions to memory pages. This is critical for building correct reference binaries.
3. **Document the seek and motor control** routines.
4. **Document the high-level loader** — the dispatch logic that decides which tracks to load and when.
5. **Document any relocated code** — code that lives at one address on disk but runs at another after relocation.

### What to learn from the loader

- Complete disk-to-memory mapping (which tracks → which pages)
- Persistent vs. swappable memory regions
- Level/phase loading mechanism
- The game's entry point after loading completes
- Any initialization performed before entering game code

### Key pattern: the page table

The page table is the Rosetta Stone of the project. It maps sector numbers to destination memory pages. Document it thoroughly — every subsequent reference binary depends on it being correct.

## Round 3: Game entry and main loop

With the boot chain documented, trace execution into the game code.

### Find the entry point

1. Check what address the loader jumps to after loading completes.
2. It may be indirect (`JMP ($xxxx)`) — check what the zero-page pointer contains from the initial ZP state.
3. The entry point may be in a swappable region (level data) — this is normal for games that show a title screen before gameplay.

### Document the main loop

Most games have a recognizable main loop structure:

```
MAIN_LOOP:
    JSR render_setup
    JSR read_input
    JSR update_physics
    JSR check_collisions
    JSR draw_sprites
    JSR flip_page
    JMP MAIN_LOOP
```

1. **Disassemble the main loop dispatcher.** Identify each JSR target.
2. **Create EQU stubs** for all called routines (`RENDER_SETUP = $XXXX ; STUB`).
3. **Identify self-modifying code** — games often patch JSR/BIT opcodes to enable/disable subsystems (e.g., attract mode vs. game mode).
4. **Document the frame structure** — what order things happen each frame.
5. **Identify exit conditions** — level complete, game over, return to attract.

### Document the input system

The input system is a high-value early target because:
- It reveals the control scheme (what keys/buttons do what)
- It often patches the main loop (enabling movement directions)
- It references game state variables that help understand other systems

### Attract mode

Many games have an attract/demo mode that shares code with the main loop but disables input. Document how attract mode differs — typically self-modifying JSR/BIT toggles.

## Round 4: Systematic routine documentation

After the main loop is understood, work outward from the most-referenced routines.

### Prioritization

1. **Most called** — routines called from many places provide the most context.
2. **Adjacent to documented code** — fills gaps, reduces fragmentation.
3. **Small and self-contained** — quick wins that build coverage.
4. **Data tables** — understanding lookup tables unlocks multiple routines at once.

### Process for each routine

Use the `/re-next` skill to find candidates, or pick manually based on the main loop's JSR targets. For each routine:

1. **Disassemble** from the reference binary.
2. **Trace register and memory state** through every instruction.
3. **Identify inputs, outputs, and side effects.**
4. **Choose a descriptive name** (UPPER_SNAKE_CASE).
5. **Write the chunk** with:
   - Prose `\section{}` explaining the routine's purpose
   - EQU defines for any new addresses (in a defines chunk, placed just before first use)
   - Annotated assembly with header plate, section headers, aligned comments
   - `@ %def` declaring exported symbols
6. **Replace the EQU stub** in the defines chunk with the real label.
7. **Update raw hex references** throughout `main.nw` — replace `JSR $XXXX` with `JSR LABEL_NAME`.
8. **Add to the collection chunk** in ascending ORG address order.
9. **Assemble, verify, commit.**

### Building up data structure understanding

Game state is typically stored in zero-page arrays and fixed-memory tables. Understanding builds gradually:

1. **Name ZP addresses as you encounter them.** Use contextual aliases — the same address may serve different purposes in different routines.
2. **Track record structures.** When you see indexed access patterns like `LDA table,X` with X iterating, you've found an array. When you see `LDY #offset; LDA (ptr),Y`, you've found a record field. Create EQUs for field offsets.
3. **Build the memory map incrementally.** Each routine reveals which addresses are code, which are data tables, and which are scratch buffers.
4. **Cross-reference.** When routine A writes to an address and routine B reads it, document the data flow in both routines' prose.

### Common 6502 game patterns to recognize

- **Self-modifying code**: `STA target+1` to patch an operand. Use `label = *+1` or `label = *+2` for the modified byte.
- **BIT abs as 3-byte NOP**: `DC.B $2C` before `LDA #imm` creates a multi-entry point. The `BIT` reads the `LDA` operand harmlessly.
- **JSR/BIT toggle**: Patching a `JSR` opcode byte ($20) to `BIT` ($2C) disables a subroutine call without changing the operand bytes.
- **Indexed dispatch**: `LDA table,X; STA target+1` followed by `JMP target` implements a jump table.
- **Page-crossing tricks**: Placing data at page boundaries to exploit 6502 page-crossing behavior.
- **Unrolled loops**: Repeated instruction sequences with different operands for speed.

## Round 5: Data regions

After code routines are documented, fill in data regions:

1. **Sprite/shape tables** — typically contiguous byte arrays with a known record size.
2. **Level data** — maps, enemy placements, item locations. Often in swappable memory regions.
3. **String tables** — text displayed on screen.
4. **Lookup tables** — math tables (multiply, divide), screen address tables, color tables.

For each data region:
- Determine the structure (record size, field layout)
- Create labels and EQUs for field offsets
- Emit as `HEX` with comments, or as structured `DC.B`/`DC.W` where the format is known
- Document the structure in prose

### Fonts and images

See the "Standing rule: render any graphics data you uncover" section below
for the process. Graphics rendering is not a Round-5-specific task — it
applies whenever a session uncovers pixel data, code or data round alike.

Round-5-specific notes: when fonts and sprite sheets are the primary focus
of a session, render the full character set as a grid and label each frame
of each sprite-animation sequence. Note the ASCII offset or custom character
order for fonts. Cross-reference the tile dimensions against the draw
routines that consume them (often the draw routine's `ZP_SPRITE_W`/`_H`
values or SMC-patched operands encode these).

## Standing rule: render any graphics data you uncover

This is a **continuous** behavior, not a Round-5-only task. Any time a session
uncovers graphics data — a sprite, font glyph, tile, title/HUD image, unpacker
stream, or any byte region that is used as pixel data by a draw routine —
render it to a PNG and embed it in the document in the same commit as the RE.

The rule applies even when the graphics are a byproduct of RE'ing a code
routine (e.g. you RE a draw routine and it reveals where its sprite table
lives, or you decode a self-modifying sprite pointer and resolve where it
points). Don't defer the image work to a separate pass; do it in the same
session while the data layout is fresh.

### Steps

1. **Figure out the record format** — dimensions (W×H in bytes or columns×rows),
   data ordering (row-major vs column-major, forward vs reversed), how many
   frames, what palette bits do.
2. **Write or extend a Python renderer.** Save to `.claude/scripts/render_<name>.py`.
   The template is `/project/drol_re/.claude/scripts/render_hud_frame.py`:
   it opens `reference/drol.bin`, reads the data at a known offset, applies
   Apple~II hi-res palette rules, and writes a scaled PNG. Re-use its
   `render_row` helper (or a close variant) rather than rewriting palette
   logic from scratch. For sprite tables, iterate each frame and either save
   one PNG per frame or assemble them into a grid image.
3. **Run the renderer** with `/project/drol_re/.venv/bin/python`. Pillow
   (`PIL`) is already installed in the project-scoped venv; do not install
   packages globally. If PIL is missing in a future environment, reinstall
   into the existing venv: `.venv/bin/pip install Pillow`.
4. **Save the output under `images/`** at the repo root. Filenames should
   describe the content: `sprite_player_walk_frame3.png`, `font_glyphs.png`,
   `enemy_a_sprites.png`, `hud_frame.png`, etc. Use lowercase with
   underscores.
5. **Embed the image in `main.nw`**, right where the data is documented.
   Use a `figure` environment with a caption and a `\label{fig:...}`
   referenced from the prose. For tiny sprites (7-14 px wide), scale up so
   they're visible — `\includegraphics[scale=2]{...}` or
   `\includegraphics[width=0.3\textwidth]{...}`. Put the `\includegraphics`
   path as `{images/<name>.png}` (LaTeX runs from `output/`; the gen-pdf
   skill copies `images/` there before `pdflatex`).
6. **Describe the decoding in prose** immediately before or after the
   figure: record size, dimensions, frame count, how the game indexes into
   the table, any palette/color quirks specific to this data.
7. **Verify visually.** Read the PNG back (or trust the `Read` tool's
   display) and confirm it looks like recognizable game content. If it
   renders as noise or garbage, the format guess is wrong — don't ship a
   useless image; iterate until the picture makes sense.
8. **Commit in the same commit as the RE.** The image file, the renderer
   script, and the `main.nw` edits all go together.

### When the data format is genuinely unknown

If you find sprite-table entries referenced by a self-modifying pointer but
can't yet decode the format (e.g. RLE, stream-based, or tiled), note the
address, dimensions guess, and a TODO in the commit message. Don't force a
broken render.

### Don't skip this

Rendered images are the single highest-bandwidth communication between the
document and the reader — far more than prose describing byte layouts. Every
session that finds graphics without rendering them is leaving the document
less useful than it should be. Treat graphics rendering with the same
priority as writing prose or annotating assembly.

## Standing rule: use symbolic addresses in prose

Applies every session, not just to graphics work. In LaTeX prose (sections,
paragraphs, captions) inside `main.nw`, never write a raw numeric address
when a symbolic name exists for it. Use `[[LABEL]]` or `[[ZP_ALIAS]]` noweb
code refs — they render as navigable tt-styled hyperlinks to the defining
chunk; raw hex in prose fails the reader.

When no symbol exists yet, the raw form `[[$XXXX]]` is acceptable during
active RE, but mark it with a LaTeX comment so it can be upgraded later:

```latex
The routine reads from [[$XXXX]] % TODO-SYM: needs label
```

When a new label is introduced for an address, grep main.nw for the raw
hex in prose and replace with the symbol in the same commit. See the
"Prose rules" section of `CLAUDE.md` for the full policy, including the
exceptions (memory-map tables, ORG directives, numeric-value-matters
comments) where raw addresses are expected.

## Chunk hygiene

Throughout all rounds, maintain chunk quality:

### Every commit must pass

```bash
python3 weave.py main.nw output
cd output
dasm target.asm -f3 -otarget.bin -ltarget.lst -starget.sym
python3 .claude/skills/assemble/verify.py target
```

### Apply code chunk rules

After writing any chunk, verify it follows the rules in CLAUDE.md:
- `JSR $XXXX` / `JMP $XXXX` must use labels (create EQU stubs if not yet RE'd)
- Non-ZP data addresses must use labels
- ZP addresses must use symbolic EQU names
- Immediate values that are label addresses must use `#<label` / `#>label`
- 16-bit pointer EQUs use a single name with `+1` for the high byte
- Record field offsets get named EQUs
- Every routine with `SUBROUTINE` gets a header plate comment
- Chunk ends with `@ %def` for exported symbols
- Collection chunk lists chunks in ascending ORG address order

### Apply chunk placement rules

- EQU defines go just before the chunk that first uses them
- Data chunks go just before the first code chunk that references them
- Run `check_placement.py` after adding chunks

### Naming conventions

- Routine labels: `UPPER_SNAKE_CASE` describing purpose, not mechanism
- Local labels: `.lower_name` within `SUBROUTINE` scope
- EQU constants: `UPPER_SNAKE_CASE` with descriptive comment
- Chunk names: `<<lowercase with spaces>>`
- Section headers: no numeric addresses

## The discovery cycle

Reverse engineering is not a linear process. It is a continuous cycle of discovery:

```
    disassemble → analyze → name → document → discover new context
         ↑                                            |
         └────────── revisit and correct ←────────────┘
```

Each routine you document teaches you something that changes your understanding of routines you documented earlier. A zero-page address you named `ZP_TEMP` in round 3 might turn out to be `PLAYER_FLOOR` by round 5. A data table you emitted as raw HEX might reveal structure once you understand the record format from a later routine. A routine you named `GAME_ROUTINE_1255` gets a real name once you see what it does.

### Expect to revisit everything

- **Names evolve.** First pass: `COPY_HGR1_TO_HGR2`. After understanding purpose: `START_ATTRACT`. The initial name described mechanism; the final name describes intent. Rename freely as understanding deepens.
- **Comments get corrected.** "Set up vectors at $03F8" turns out to be "Initialize floor Y-coordinate table" once you find the code that reads it. Go back and fix the comment immediately — stale comments are worse than no comments.
- **Data becomes structured.** A HEX blob becomes `DC.W address` + `HEX pixel_data` once you understand the record format. Revisit data chunks as the routines that consume them are documented.
- **EQU stubs become real labels.** Every `STUB — not yet disassembled` is a promise to revisit. When you RE the routine, replace the EQU with an ORG + label, update all references, and verify.
- **Zero-page aliases multiply.** The same ZP address serves different purposes in different subsystems. Add aliases as you encounter new uses — `ZP_STREAM` in the unpacker, `ZP_SCROLL_PTR` in the renderer, both at $A0.

### The feedback loop

When you document routine B and discover it writes to an address that routine A reads:

1. Go back to routine A's documentation.
2. Update the comment on the load instruction to explain what B stored there.
3. Update A's header plate to list the new input.
4. Consider whether A's name still makes sense given the new context.
5. Consider whether the ZP/data address deserves a better name now that two routines use it.

This is not rework — it is the core of the process. The document improves in waves, not in a single pass.

### Practical cycle within a session

A typical session looks like:

1. **Pick a target** — highest-value unlabeled routine (most referenced, adjacent to known code, or blocking understanding of something else).
2. **Disassemble** — get the raw bytes, trace the logic instruction by instruction.
3. **Analyze** — what does it do? What are the inputs, outputs, side effects? What game concept does it implement?
4. **Name and document** — choose a name that describes purpose. Write the chunk with proper style. Add EQUs for new addresses.
5. **Discover** — the routine revealed new information. Maybe it writes to an address you've seen before. Maybe it calls routines you now understand differently. Maybe a "data" region is actually code.
6. **Propagate** — go back and update earlier documentation with the new knowledge. Rename EQU stubs. Fix comments. Restructure data.
7. **Verify and commit** — assemble, binary compare, commit. Never break the build.
8. **Repeat** — pick the next target, informed by what you just learned.

### Signs of progress

- Raw hex addresses in code are replaced with labels.
- EQU stubs (`STUB — not yet disassembled`) are replaced with real code.
- HEX data blobs gain structure (DC.W, record comments).
- Zero-page addresses have descriptive names in every routine that uses them.
- Prose sections explain game mechanics, not just byte manipulation.
- Cross-references between routines are documented in both directions.

### When to reorganize

As understanding grows, the chapter structure may need revision:

- Code that seemed related by address may be unrelated by function.
- A chapter called "RWTS" may contain mostly non-disk routines.
- Multiple small routines may belong together as a subsystem (e.g., "sprite rendering" spanning several address ranges).

Reorganize when the current structure actively misleads. Don't reorganize speculatively — wait until you have enough documented routines to see the real structure.

At every stage, the document must build and verify byte-perfect against the reference binary. Never break the build.
