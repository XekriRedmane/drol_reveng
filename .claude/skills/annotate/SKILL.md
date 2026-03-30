# annotate

Annotate an existing documented routine: replace raw addresses and constants with named EQUs, add inline comments, align comments, and add a header comment plate.

## Usage

```
/annotate ROUTINE_NAME
/annotate all routines in SECTION_NAME
```

ROUTINE_NAME is the label of a routine already in main.nw (e.g., `DISPLAY_SHOP`).

When annotating all routines in a section or subsection:
1. Find the section boundaries by **line number**: search for the `\section{...}` or `\subsection{...}` header, then find the NEXT `\section` or `\subsection` (at the same or higher level). The range is ALL lines between these two headers. Do NOT use the address range in the subsection title as the boundary — the title is just a summary and may not cover all routines in the subsection.
2. List ALL routines (ORG + `@ %def` pairs) within the line range. Print the list and verify it is complete before proceeding.
3. Skip routines that already have plate comments (a `;` comment block with `; Input:` or `; Behavior:` immediately after SUBROUTINE).
4. Launch **parallel sub-agents** (one per routine, or group small related routines). Each sub-agent receives the routine source text as INPUT and returns PROPOSED REPLACEMENT TEXT. Sub-agents must **NOT edit the file directly** — they only return text. This prevents concurrent clobbering when multiple agents run in parallel on the same file.
5. Collect all sub-agent results. The parent (you) applies each replacement **sequentially** to main.nw, normalizing comment style as needed.
6. Assemble and verify after all changes are applied.

## Instructions

This skill improves the readability of an already-documented routine by applying three passes. After each pass, assemble and verify (`python3 weave.py main.nw output && dasm output/main.asm -f3 -ooutput/main.bin -loutput/main.lst -soutput/main.sym && python3 .claude/skills/assemble/verify.py`).

### Pass 1: Replace raw addresses and constants with names

For every raw hex address or constant in the routine:

1. **Subroutine calls** (`JSR $XXXX`, `JMP $XXXX`): look up the label in main.sym or main.nw and replace.
2. **Data addresses** (`LDA $XXXX`, `STA $XXXX`, etc.): check if an EQU exists. If not and the address appears meaningful (game state, display buffer, etc.), create one with a descriptive name.
3. **Immediate constants** (`LDA #$XX`, `LDY #$XX`, `CMP #$XX`): if the value has a known meaning (field offset, bitmask, record size, character code), create an EQU. Define the EQU WITHOUT `#` (e.g., `LEVEL_MASK EQU $1F`) and use `#` on the instruction (e.g., `AND #LEVEL_MASK`).
4. **Record field offsets**: ANY `LDY #imm` followed by `LDA (ptr),Y` or `STA (ptr),Y` is a record field access. The immediate value MUST have a named field offset EQU. Determine the record type from the pointer (CHAR_PTR → `CFIELD_*`, ENTITY_PTR/MOB_PTR/ENTITY_REC → `MFIELD_*`, EVENT_PTR → `EVFIELD_*`, SHOP_DATA_PTR → shop record offsets). Group all field offset EQUs for the same record type together in a central `<<defines>>=` chunk. Check if an offset EQU already exists before creating a new one. When `INY`/`DEY` adjusts Y to reach another field, comment which field Y now points to.
5. **Bitmasks**: ANY `AND #$XX` or `ORA #$XX` instruction MUST have a named EQU for the mask value. Name it after the field it operates on (e.g., `HP_MASK`, `STRENGTH_MASK`, `FLAGS_CLASS_MASK`). Group masks for the same byte together with their field offset EQU. If a mask and its complement both appear (e.g., `#$C0` and `#$3F` on byte 15), define both. Check if a mask EQU already exists before creating a new one — reuse it if the same mask applies to the same field.
6. **Zero-page addresses**: ANY `STA $XX`, `LDA $XX`, `INC $XX`, etc. where `$XX` is a zero-page address without an existing EQU MUST get a named EQU. If the address serves a specific purpose throughout the program (e.g., a game state variable, a pointer), give it a global descriptive name. If it is scratch/temporary used only in one routine or subsystem, give it a context-specific alias (e.g., `AI_SCRATCH`, `SAVED_CHAR`, `DIST_COL`). Follow the zero-page aliasing convention: the same ZP address used for different purposes in different subsystems gets different EQU names.
7. **Indirect addressing** (`LDA ($XX),Y`): check if the ZP pointer has an EQU name.
8. **Indexed addressing** (`STA $XXXX,X`): check if the base address has an EQU name.

### Pass 2: Add inline comments and align

For each instruction or group of instructions:

1. **Comment the purpose**, not the mechanics. "extract location tier" not "rotate left 4 times".
2. **Use bracket comments** (`; \` ... `; /`) to group multi-instruction operations (pointer copies, field extractions, loops).
3. **Add section headers** (`; --- section name ---`) between logical phases of the routine.
4. **Label comments** on `.local` labels explaining the branch condition or loop purpose.
5. **Align all `;` comments** to the same column within the routine (typically column 40 for short instructions, further right if needed for long operands).

### Pass 3: Add header comment plate

Add a comment block immediately after the `SUBROUTINE` directive with:

```
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

Omit the Outputs section if the routine doesn't return meaningful values (e.g., it ends with `JMP` to another routine).

### Pass 4: Rewrite prose documentation

The noweb `@` prose that precedes each chunk should be a clear, structured summary — not a dense wall of text. Rewrite it using LaTeX formatting:

1. **Opening paragraph**: 1-2 sentences stating what the routine does and when it is called.
2. **`\paragraph{}` sections** for each distinct game mechanic or algorithm phase. Use descriptive names like "Willingness score.", "Hit roll.", "Flee probability.", "Defense calculation."
3. **Itemized lists** (`\begin{itemize}`) for branching conditions, HP thresholds, outcome tables, or multi-step processes.
4. **Tables** (`\begin{tabular}`) for data-driven mechanics with multiple modifiers or lookup values (e.g., willingness deltas, damage tiers).
5. **Cross-references**: use `[[LABEL]]` for routine and variable names in prose.
6. Keep prose concise — the code comments have the instruction-level detail; the prose explains the *game design* and *algorithm structure*.

Reference examples: RESOLVE_ATTACK (willingness table), PLAYER_ATTACK (target classification list), APPLY_DAMAGE (HP threshold list with death handler steps), DISPLAY_SHOP (shop record structure).

### Reference: DISPLAY_SHOP

The routine DISPLAY_SHOP ($70DF) in main.nw is the reference example of a fully annotated routine. Study its style for comment alignment, bracket grouping, section headers, and header plate format.

### Notes

- Always verify byte-for-byte match after changes. Comments and EQU substitutions must not change assembled output.
- Do NOT rename labels that are already well-named.
- Do NOT add EQUs for ROM addresses ($C000-$FFFF) or well-known Apple II constants unless they improve clarity.
- When creating EQUs, place them in `<<defines>>=` or `<<zero page defines>>=` chunks just before the routine's chunk, following chunk placement rules.
- If a raw address is used in only one routine and has no broader meaning, a comment may be better than an EQU.
- **dasm EQU values are always addresses.** For immediate-mode constants (masks, sizes, offsets), define the EQU without `#` (e.g., `LEVEL_MASK EQU $1F`) and use `#` on the instruction (e.g., `AND #LEVEL_MASK`). Never put `#` in the EQU value — dasm ignores it and the instruction will assemble as zero-page addressing instead of immediate.
