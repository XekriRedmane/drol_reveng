# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Reverse engineering of **Drol**, a 1983 Apple II action game by Broderbund. The project uses literate programming (noweb format) to produce annotated 6502 assembly that assembles to byte-perfect matches against the original disk image.

## Build pipeline

```bash
# Tangle: extract assembly files from literate source
python3 weave.py main.nw output

# Assemble all targets (from output/)
cd output
dasm boot1.asm -f3 -oboot1.bin -lboot1.lst -sboot1.sym
dasm loader.asm -f3 -oloader.bin -lloader.lst -sloader.sym
dasm rwts.asm -f3 -orwts.bin -lrwts.lst -srwts.sym

# Verify against reference binaries (from project root)
python3 .claude/skills/assemble/verify.py boot1
python3 .claude/skills/assemble/verify.py loader
python3 .claude/skills/assemble/verify.py rwts

# Disassemble a region from a reference binary
python3 .claude/scripts/dasm6502.py --file reference/boot1.bin --base 0800 0801
```

Skill: `/assemble` runs the full tangle+build+verify pipeline.

## Assembly targets

| Target | Output | Reference | Base addr | Description |
|--------|--------|-----------|-----------|-------------|
| boot1 | output/boot1.bin | reference/boot1.bin | $0800 | Boot sector (T0S0) |
| loader | output/loader.bin | reference/loader.bin | $5000 | Loader + RWTS ($5000-$59FF) |
| rwts | output/rwts.bin | reference/rwts.bin | $BE00 | Relocated RWTS ($BE00-$BFFF) — misnomer, see note |
| drol | output/drol.bin | reference/drol.bin | $0100 | Game code ($0100-$8BFF) |

**Note on "rwts" naming:** The $BE00-$BFFF region is called "RWTS" (Read/Write Track/Sector) but most of its routines have nothing to do with disk I/O — it contains screen scroll/restore, hi-res clearing, ROM-to-LC copy, reset handlers, Applesoft patches, and a division routine. Only `RWTS_RELOAD` and `NIBBLE_READER` are disk-related. When reverse engineering the game code, consider reorganizing these chunks under more accurate names.

## Architecture: main.nw

`main.nw` is the single source of truth. It contains LaTeX documentation interleaved with 6502 assembly code chunks. `weave.py` tangles it to produce `.asm` files; `pdflatex` weaves it to produce documentation.

### Assembly file structure

Each `.asm` file is built from named chunks. A collection chunk at the end of the chapter assembles them in address order:

```noweb
<<rwts.asm>>=
        PROCESSOR 6502
<<rwts defines>>
<<rwts reload>>
<<nibble reader>>
...
```

Individual routine chunks are named after their subroutine (e.g., `<<scroll up>>`, `<<reset handlers>>`). EQU definitions go in a `<<xxx defines>>` chunk referenced at the top of the collection.

### Chunk conventions

- Each `\section{}` gets its own code chunk with the routine's assembly.
- Section headers never contain numeric addresses.
- Chunk names are lowercase with spaces (e.g., `<<rwts reload>>`).
- End chunks with `@ %def SYMBOL1 SYMBOL2` to declare exported symbols.
- `<<filename.asm>>=` chunks produce output files when tangled.
- Every data and code chunk must start with an `ORG` directive (hex literal, never a symbol).
- After every `ORG`, there must be a label. If unreferenced, investigate as potential dead code.

### Chunk placement rules

- Data chunks with labels go immediately before the first code chunk that references the label.
- EQU definitions go just before the chunk that first uses them, with prose explaining purpose.
- Chunk references in the collection chunk follow ascending ORG address order.
- After adding a chunk, run `python .claude/skills/chunk-placement/check_placement.py` to verify.

### Code chunk rules

- Replace raw hex addresses to code with labels in the code: `JSR $XXXX` and `JMP $XXXX` must use labels.
- Replace raw hex addresses to data that is not in zero-page with labels for the data: `LDA $XXXX` / `STA $XXXX`, especially when indexed, e.g. `LDA $XXXX,X` or `LDA ($XXXX),Y`. If the address is a zero-page address, then use
a symbolic name with EQU.
- If a label is not known in the reverse-engineered code or data yet, then it may be given a symbolic name with
an EQU until such time as the code or data is reverse-engineered. For addresses in ROM, an EQU may be used.
- If an immediate value is known to be a label, then use the label.
- If an immediate value is known to be the low or high value of the label, then use `#<label` or `#>label`.
- If an immediate value is known to be an offset into a record, then create a symbolic name for the offset
with an EQU and use the symbolic name.
- For 16-bit data addresses, only create a label for the first address. Use label+1 for the second address.

### Chunk annotation

Every routine with a `SUBROUTINE` directive must have a **header plate** comment block immediately after `SUBROUTINE`:

```asm
ROUTINE_LABEL:
        SUBROUTINE
        ; Brief one-line description of what the routine does.
        ;
        ; Inputs:
        ;   LABEL1  — what it means and how the routine uses it
        ;   LABEL2  — ...
        ;
        ; Behavior:
        ;   2-4 lines summarizing the algorithm or control flow.
        ;
        ; Outputs:  (if applicable)
        ;   What registers or memory locations hold results on return.
        ;
        ; Modifies:
        ;   List of memory locations written (EQU names, not raw addresses).
        ; Clobbers: A, X, Y  (whichever apply)
```

Omit the Outputs section if the routine doesn't return meaningful values (e.g., ends with `JMP`). Omit Modifies if only registers are affected.

Additional annotation rules:
- Comment the **purpose**, not the mechanics: "extract location tier" not "rotate left 4 times".
- **Numeric addresses in comments must serve a purpose beyond identification.** Specifically, a raw `$XXXX` in a comment is wrong when it is either (a) the instruction's own assembled address — `STA $3CA8,X ; $05B4: row 79` or `STA ZP_SCORE_2 ; $629E (A was 0)` are both noise, since the `.lst` file already carries the PC; or (b) the address of a symbol that exists, in which case use the symbol — `; $7519 → ZP_BLIT_SRC` becomes `; WALL_L_SPR_LO → ZP_BLIT_SRC`. Bare `; $XXXX` comments that carry no other information get removed entirely. Addresses may remain in comments when they are something the reader actually needs to know in numeric form — an unlabeled address not yet RE'd (flag with a `TODO-SYM` note), a memory-region span described literally, an opcode byte value, etc.
- **In comments, refer to indexed tables by `SYMBOL[Y]` notation, never `$XXXX,Y` or `SYMBOL,Y`.** The `,Y` form mimics the instruction syntax on the same line — `LDA FOO,Y ; $7519,Y -> ptr` reads as two copies of the same thing, and uses raw hex where a symbol exists. Write `LDA FOO,Y ; FOO[Y] -> ptr` instead (or simply `; load pointer by frame index` if the mechanic is what matters). The `[Y]` bracket form is unambiguously prose, not asm.
- Use `; --- section name ---` headers between logical phases within a long routine.
- Align all `;` comments to the same column within each routine.
- Routines without `SUBROUTINE` (simple trampolines like `JMP target`) get a one-line `;` comment above instead of a full plate.

The `/annotate` skill automates these passes for an existing routine.

## Assembly style and rules

### Labels and naming

- All routine labels must be `UPPER_SNAKE_CASE` (e.g., `BOOT1_ENTRY`).
- Local labels: `.local_name` within `SUBROUTINE` scope.
- EQU constants: `UPPER_SNAKE_CASE` with descriptive comment.
- Zero-page aliasing: define multiple EQU names for the same address when used for different purposes; use the contextually appropriate name at each reference.
- Align all `;` comments to the same column within each chunk/subroutine.

### Label hygiene

- Before creating a label, search for existing EQUs at that address. If one exists, keep the label and remove the EQU.
- After documenting a routine, grep `main.nw` for raw hex references (`JSR $XXXX`, `JMP $XXXX`) and replace with the new label name. When replacing, skip lines containing `EQU` and `%def` to avoid circular definitions.
- Never use EQU stubs for routines — create an ORG stub chunk with `; STUB — not yet disassembled` instead.
- Before doing `replace_all` on a label, verify one instance first. Assemble and binary-compare before applying globally.
- Watch for prefix collisions when renaming (use word-boundary regex).

### dasm specifics

- `SUBROUTINE` after each `ORG` to scope `.local` labels.
- ORG directives must be in strictly ascending address order. Use `python .claude/skills/assemble/reorder_chunks.py` to fix.
- Accumulator addressing: use bare `ASL`/`LSR`/`ROL`/`ROR`, not `ASL A`.
- `HEX` directives: at most 8 bytes per line. Longer rows overflow the PDF column and wrap awkwardly. Break any hex blob into 8-byte lines; put the inline comment (if any) on the first line only.
- Use `-f3` for raw binary output (not `-f1` which adds a 2-byte header).
- Always produce `.lst` and `.sym` files when assembling.
- Force absolute addressing when dasm optimizes to zero-page: `DC.B $9D,$00,$00` for `STA $0000,X`.
- BIT-abs skip trick for multi-entry points: `DC.B $2C` before `LDA #imm`.
- Self-modifying code: `label = *+1` or `label = *+2` to name the patched operand byte. For indexed self-modification (`STA base,X`), calculate: base = effective\_addr - X.
- NMOS 6502 has no `STZ` instruction.

### Noweb / LaTeX

- Do not escape underscores or dollar signs inside `[[ ]]` noweb code refs. Write `[[$4000]]` and `[[GAME_INIT]]`, not `[[\$4000]]` or `[[GAME\_INIT]]` — `[[ ]]` content is literal code, and weave.py LaTeX-escapes it automatically; any author-written `\` prefix will render as a visible backslash in the PDF. (weave.py strips `\_`, `\$`, `\&`, `\#`, `\%`, `\{`, `\}` inside `[[ ]]` as a safety net, but keep the source clean.)
- Never put `<<chunk>>` inside assembly comments — the tangler expands them.
- Never put LaTeX math inside `[[ ]]` noweb code refs.
- `@ %def` must not have duplicate identifiers across chunks.

### Prose rules

LaTeX prose in `main.nw` (sections, paragraphs, captions, figure labels, list items, table-cell text) must follow two standing rules for memory addresses:

**1. Every numeric address gets wrapped in `[[ ]]`.** Never write a bare `\$XXXX` or `$XXXX` in prose. Always `[[$XXXX]]` or `[[SYMBOL]]`. A raw `\$XXXX` renders as plain hex with no navigation; the `[[ ]]` form renders as a tt-styled chunk-cross-reference hyperlink in the PDF. No exceptions in normal prose — not captions, not parentheticals, not "for example $XXXX", nothing. The wrap is mechanical and total.

**2. Prefer the symbol over the hex, and do not annotate the symbol with its own address.** When a label, EQU, or `@ %def`-exported name exists for the address, write `[[SYMBOL]]` — never `[[SYMBOL]] ([[$XXXX]])`. The parenthetical hex adds no information: a reader who wants the numeric address can click the symbol and jump to its defining chunk. The only permissible numeric annotation on a symbol is a **range** that conveys extent (e.g. `[[SYMBOL]] ([[$XXXX]]--[[$YYYY]])` when documenting a region's span), and even then prefer stating the size in bytes (`SYMBOL (256 bytes)`) if that's the actual information being added.

**3. No backslash inside `[[ ]]`.** Write `[[$XXXX]]`, never `[[\$XXXX]]`. Noweb `[[ ]]` content is literal code; weave.py LaTeX-escapes automatically. Any `\` you write inside `[[ ]]` renders as a visible backslash in the PDF. (weave.py now strips `\_ \$ \& \# \% \{ \}` inside `[[ ]]` as a safety net, but the source must stay clean.)

**Unsymbolized addresses during active RE** (no label yet) are fine as `[[$XXXX]]`, but flag them so a later pass can upgrade:

```latex
The routine reads from [[$XXXX]] % TODO-SYM: needs label
```

Grep for `TODO-SYM` periodically. When introducing a new label for an address, grep main.nw for `$XXXX` occurrences in prose and replace with the symbol in the same commit.

**Exceptions where raw (unwrapped) addresses are expected** — narrow and specific:

- Memory-map tables and disk-layout tables designed to show raw addresses in their own column. Even then, consider whether wrapping makes the PDF more navigable.
- `ORG` directives in code chunks (governed by assembly rules, not prose).
- Comments explaining *why* a specific numeric value matters mechanically (e.g. "chosen because the address is page-aligned"). The address is the subject, not a reference.
- Code chunks themselves — governed by the separate code chunk rules above, which already require symbolic addresses in code.

If you're unsure whether something is prose or an exception, wrap it. Over-wrapping produces a navigable PDF; under-wrapping produces a worse one.

## Assembly pitfalls

### Branch labels

- **Compute branch targets from the binary first.** Most disassembly errors are labels placed on the wrong instruction. Calculate: `target = branch_addr + 2 + signed_offset`. If offset byte >= $80, it's a backward branch.
- **Loop labels must include re-executed calls.** If a loop re-calls a JSR each iteration, the branch target must be BEFORE the JSR. A 3-byte offset mismatch is the telltale sign.
- **Shared branch targets across routines** must share the same `SUBROUTINE` scope.
- **Backward branches for code reuse.** 6502 code heavily reuses earlier code via backward branches. Ghidra often misrepresents these as forward branches — always check manually.

### Self-modifying code

- Use `= *+N` labels for EACH modified operand byte; don't use arithmetic on another label.
- Self-modifying storage bytes must emit their disk-image initial values, not runtime values. Always check the reference binary.
- For indexed self-modification (`STA label+N,X`), the effective address is `label+N+X`. Work backward from the desired effective address.

### Code/data boundaries

- When a data region overlaps with code, truncate the HEX data at the overlap boundary and let the code ORG define the overlapping bytes.
- "Padding" bytes between routines may have specific values — always check the reference binary, never assume $00.
- Before creating a chunk for address $XXXX, grep main.nw for `ORG.*XXXX` to avoid duplicates.

### Fall-through and multiple entry points

- Watch for fall-through between adjacent routines — they must stay adjacent and the first must NOT duplicate the second's code.
- When branch/jump targets don't match by exactly 3 bytes, check for a second entry point that skips a JSR/JMP.

### Verification

After writing any new assembly chunk:
1. Assemble and compare byte-for-byte against the reference binary.
2. Verify every JSR/JMP operand, not just the ORG address.
3. Run `/assemble` for full regression.
4. Run `python .claude/skills/chunk-placement/check_placement.py` for label placement.
5. Sync new labels to Ghidra immediately (`batch_rename_function_components` for functions, `batch_create_labels` for data/local labels; then `save_program`).

### Ghidra caveats

- Do NOT decompile to C — work with disassembly directly.
- Ghidra branch structure is unreliable for hand-written 6502. For functions >50 bytes, dump raw bytes and manually trace every branch offset.
- Ghidra "fall-through" claims are often wrong — verify actual bytes.
- Use `batch_rename_function_components` (NOT `rename_function_by_address` — bugged).

## Disk layout

The Broderbund boot chain loads from a 35-track disk (no DOS 3.3 catalog):

- Track 0: boot1 + loader/RWTS
- Tracks 1-4: persistent game code (loaded once)
- Tracks 5-9, 10-14, 15-19, 20-24: four swappable level data sets

The P5A Disk II PROM reads sectors in physical position order: 0, 7, E, 6, D, 5, C, 4, B, 3, A, 2, 9, 1, 8, F. The .dsk file stores sectors in DOS 3.3 logical order. Drol's RWTS uses physical sector numbers in address fields. To read RWTS (physical) sector P from the .dsk: `dsk_offset = track * 4096 + DOS_SKEW[P] * 256`, where `DOS_SKEW = [0, 7, 14, 6, 13, 5, 12, 4, 11, 3, 10, 2, 9, 1, 8, 15]`.

## Memory map after first boot

- $0100-$12FF, $1900-$1FFF: game code (persistent, tracks 1-2)
- $1300-$18FF: level data (swappable)
- $2000-$3FFF: hi-res page 1 framebuffer (not loaded)
- $4000-$47FF: game code (persistent, entry at $4000)
- $5000-$59FF: loader/RWTS (persistent, from track 0)
- $6000-$66FF, $7300-$74FF, $7B00-$8BFF: game code (persistent, tracks 3-4)
- $6700-$72FF, $7500-$7AFF, $8C00-$BDFF: level data (swappable)
- $BE00-$BFFF: relocated RWTS/reset handlers
