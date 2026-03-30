# macro-apply

Search main.nw for instruction sequences that can be replaced by assembly macros, and apply the substitutions.

## Usage

```
/macro-apply
```

No arguments. The skill scans all assembly chunks in main.nw automatically.

## Instructions

Run the apply script, verify the result, and report:

1. **Apply** — Run `python .claude/skills/macro-apply/apply_macros.py` from the project root. This scans main.nw for all macro candidates and applies substitutions in-place. It prints a summary of what it changed.

2. **Verify** — Run `python weave.py main.nw output` to retangle. Then assemble with `cd output && dasm main.asm -f3 -omain.bin -lmain.lst -smain.sym` and verify with `python .claude/skills/assemble/verify.py`.

3. **Report** — Show the user the script output (macro counts) and the binary comparison result.

If verification fails, restore from backup (`git checkout main.nw`) and investigate.

## Macro reference

The script detects these patterns (defined in `<<Macros>>` chunk of main.nw), matched longest-first:

| Macro | Pattern | Lines |
|-------|---------|-------|
| ADDW a,b,c | `CLC / LDA a / ADC b / STA c / LDA a+1 / ADC b+1 / STA c+1` | 7 |
| SUBW a,b,c | `SEC / LDA a / SBC b / STA c / LDA a+1 / SBC b+1 / STA c+1` | 7 |
| SUBWL #v,b,c | `SEC / LDA #<v / SBC b / STA c / LDA #>v / SBC b+1 / STA c+1` | 7 |
| ADDWC a,b,c | `LDA a / ADC b / STA c / LDA a+1 / ADC b+1 / STA c+1` | 6 |
| LDWIY ptr,#off,dst | `LDY #off / LDA (ptr),Y / STA dst / INY / LDA (ptr),Y / STA dst+1` | 6 |
| ADDB addr,val | `LDA addr / CLC / ADC val / STA addr / BCC .l / INC addr+1 / .l` | 6+label |
| ADDB2 addr,val | `CLC / LDA addr / ADC val / STA addr / BCC .l / INC addr+1 / .l` | 6+label |
| SUBB addr,val | `LDA addr / SEC / SBC val / STA addr / BCS .l / DEC addr+1 / .l` | 6+label |
| SUBB2 addr,val | `SEC / LDA addr / SBC val / STA addr / BCS .l / DEC addr+1 / .l` | 6+label |
| ADDA addr | `CLC / ADC addr / STA addr / BCC .l / INC addr+1 / .l` | 5+label |
| ADDAC addr | `ADC addr / STA addr / BCC .l / INC addr+1 / .l` | 4+label |
| STOW val,dst | `LDA #<val / STA dst / LDA #>val / STA dst+1` (also raw hex) | 4 |
| STOW2 val,dst | `LDA #>val / STA dst+1 / LDA #<val / STA dst` (also raw hex) | 4 |
| MOVW src,dst | `LDA src / STA dst / LDA src+1 / STA dst+1` | 4 |
| PSHW addr | `LDA addr / PHA / LDA addr+1 / PHA` | 4 |
| PULW addr | `PLA / STA addr+1 / PLA / STA addr` | 4 |
| INCW addr | `INC addr / BNE .l / INC addr+1 / .l` | 3+label |
| ROLW addr | `ROL addr / ROL addr+1` | 2 |
| RORW addr | `ROR addr+1 / ROR addr` | 2 |
| BAEQ val,lbl | `CMP val / BEQ lbl` | 2 |
| BANE val,lbl | `CMP val / BNE lbl` | 2 |
| BAPL val,lbl | `CMP val / BPL lbl` | 2 |
| BAMI val,lbl | `CMP val / BMI lbl` | 2 |
| BALT val,lbl | `CMP val / BCC lbl` | 2 |
| BAGE val,lbl | `CMP val / BCS lbl` | 2 |
| BXEQ val,lbl | `CPX val / BEQ lbl` | 2 |
| BXNE val,lbl | `CPX val / BNE lbl` | 2 |
| BYEQ val,lbl | `CPY val / BEQ lbl` | 2 |
| BYNE val,lbl | `CPY val / BNE lbl` | 2 |
| STOB #val,dst | `LDA #val / STA dst` | 2 |
| MOVB src,dst | `LDA src / STA dst` (non-immediate src) | 2 |
| PULB addr | `PLA / STA addr` | 2 |

### Eligibility rules

- Operands must NOT use indirect addressing (parentheses) — this breaks dasm macro arg parsing
- For most macros, operands must NOT be local labels (`.name`) or indexed (`,X`/`,Y`)
- For comparison macros (BAEQ etc.), the compare operand must not contain commas or parentheses; the branch target can be anything
- For macros with trailing labels (INCW, ADDB, etc.), the label must only be referenced by the branch in the pattern
- Lines inside `MACRO`/`ENDM` blocks are skipped
