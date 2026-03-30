#!/usr/bin/env python3
"""Audit ORG label rule: every ORG must be followed by a label,
and that label must be referenced from at least one code line.

Reports:
  - ORGs with no label after them
  - Labels after ORGs that are never referenced in code
"""

from __future__ import annotations

import re
import sys

FILE = 'main.nw'

# Instruction mnemonics that constitute "code use" of a label
CODE_MNEMONICS: set[str] = {
    'LDA', 'STA', 'LDX', 'LDY', 'STX', 'STY', 'JSR', 'JMP',
    'ADC', 'SBC', 'AND', 'ORA', 'EOR', 'CMP', 'CPX', 'CPY', 'BIT',
    'INC', 'DEC', 'ASL', 'LSR', 'ROL', 'ROR',
    'BEQ', 'BNE', 'BCC', 'BCS', 'BPL', 'BMI', 'BVC', 'BVS',
    'STOW', 'STOW2', 'STOB', 'MOVB', 'MOVW', 'INCW',
    'PSHW', 'PULB', 'PULW',
    'ADDA', 'ADDAC', 'ADDB', 'ADDB2', 'ADDW', 'ADDWC',
    'SUBB', 'SUBB2', 'SUBW', 'SUBWL',
    'BAEQ', 'BANE', 'BAPL', 'BAMI', 'BALT', 'BAGE',
    'BXEQ', 'BXNE', 'BYEQ', 'BYNE',
    'LDWIY', 'stow', 'DC.W',
}

# Directives and pseudo-ops that are NOT code
DATA_DIRECTIVES: set[str] = {'ORG', 'HEX', 'APSTR', 'DC.B', 'DC.W', 'SUBROUTINE', 'EQU'}


def find_containing_chunk(lines: list[str], line_idx: int) -> str | None:
    """Find the chunk name containing a given line."""
    for i in range(line_idx, -1, -1):
        m = re.match(r'^<<(.+)>>=\s*$', lines[i].strip())
        if m:
            return m.group(1)
    return None


def is_code_chunk(lines: list[str], chunk_start: int) -> bool:
    """Check if a chunk contains any code instructions (not just data)."""
    j = chunk_start + 1
    while j < len(lines):
        line = lines[j].strip()
        if line.startswith('@ %def') or line == '@':
            return False
        if re.match(r'^<<.+>>=\s*$', line):
            return False
        if not line or line.startswith(';') or line.startswith('@'):
            j += 1
            continue
        # Label definition
        if re.match(r'^[A-Za-z_]\w*\s*[:=]', line):
            j += 1
            continue
        # Check first word
        words = line.split()
        if words:
            first = words[0].upper()
            if first in DATA_DIRECTIVES:
                j += 1
                continue
            # If it's a mnemonic, this is a code chunk
            if first in CODE_MNEMONICS or first in {
                'RTS', 'RTI', 'PHA', 'PLA', 'PHP', 'PLP',
                'TAX', 'TAY', 'TXA', 'TYA', 'TSX', 'TXS',
                'SEI', 'CLI', 'SEC', 'CLC', 'SED', 'CLD', 'CLV',
                'INX', 'INY', 'DEX', 'DEY', 'NOP', 'BRK',
            }:
                return True
            # Local label
            if first.startswith('.'):
                j += 1
                continue
        j += 1
    return False


def main() -> None:
    with open(FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Step 1: Find all ORGs and the label (if any) after each
    org_labels: list[tuple[int, str, str | None, str | None]] = []
    # (line_number, org_address, label_name_or_None, chunk_name)

    for i, line in enumerate(lines):
        stripped = line.strip()
        m = re.match(r'^\s*ORG\s+\$([0-9A-Fa-f]+)', stripped)
        if m:
            org_addr = m.group(1).upper()
            chunk_name = find_containing_chunk(lines, i)
            # Look for label within next few lines, skipping SUBROUTINE,
            # blank lines, and comments
            label_name: str | None = None
            for j in range(i + 1, min(i + 15, len(lines))):
                s = lines[j].strip()
                if not s or s.startswith(';'):
                    continue
                # Skip SUBROUTINE directive (scoping, not a label)
                if s.startswith('SUBROUTINE'):
                    continue
                # Label with colon
                lm = re.match(r'^([A-Za-z_]\w*)\s*:', s)
                if lm:
                    label_name = lm.group(1)
                    break
                # Standalone label (uppercase, no instruction)
                lm2 = re.match(r'^([A-Z_][A-Z0-9_]*)\s*$', s)
                if lm2:
                    label_name = lm2.group(1)
                    break
                # HEX/DC.B/DC.W/APSTR without a preceding label → no label
                first_word = s.split()[0].upper() if s.split() else ''
                if first_word in {'HEX', 'DC.B', 'DC.W', 'APSTR', 'INCLUDE'}:
                    break
                # Skip other directives and keep looking
                if first_word.startswith('.') or '=' in s:
                    continue
                break
            org_labels.append((i, org_addr, label_name, chunk_name))

    # Step 2: For each label, check if it's referenced from any code line
    no_label: list[tuple[int, str, str | None]] = []
    unreferenced: list[tuple[int, str, str, str | None, bool]] = []
    referenced_ok: list[tuple[int, str, str]] = []

    for line_idx, org_addr, label_name, chunk_name in org_labels:
        if label_name is None:
            no_label.append((line_idx, org_addr, chunk_name))
            continue

        # Skip local labels (start with .)
        if label_name.startswith('.'):
            continue

        # Search for references to this label in code lines
        found_code_ref = False
        found_any_ref = False
        ref_contexts: list[str] = []

        for i, ref_line in enumerate(lines):
            s = ref_line.strip()
            # Skip the definition itself
            if s.startswith(f'{label_name}:') or s.startswith(f'{label_name} ='):
                continue
            if s.startswith('@ %def') and label_name in s:
                continue
            # Skip EQU definitions
            if re.match(rf'^{re.escape(label_name)}\s+EQU\b', s):
                continue

            # Check if label appears in this line
            if label_name not in s:
                continue

            # Check if it's a word boundary match (not substring)
            if not re.search(rf'\b{re.escape(label_name)}\b', s):
                continue

            found_any_ref = True

            # Is this a code line?
            words = s.split()
            if words:
                first = words[0].upper()
                if first.startswith('.'):
                    first = words[1].upper() if len(words) > 1 else ''
                if first in CODE_MNEMONICS:
                    found_code_ref = True
                    break
                # Also count DC.W as a reference (pointer tables)
                if first == 'DC.W':
                    found_code_ref = True
                    break
                # stow (lowercase macro)
                if words[0] == 'stow':
                    found_code_ref = True
                    break

            # Prose reference in [[ ]]
            if f'[[{label_name}]]' in s:
                ref_contexts.append('prose')
            # EQU using this label
            elif 'EQU' in s:
                ref_contexts.append('EQU')

        if found_code_ref:
            referenced_ok.append((line_idx, org_addr, label_name))
        else:
            is_code = is_code_chunk(lines, line_idx)
            unreferenced.append((line_idx, org_addr, label_name, chunk_name, is_code))

    # Report
    if no_label:
        print("=== ORGs with no label ===")
        for line_idx, org_addr, chunk_name in no_label:
            cn = f' in <<{chunk_name}>>' if chunk_name else ''
            print(f"  L{line_idx + 1}: ORG ${org_addr}{cn}")
        print()

    if unreferenced:
        print("=== Labels after ORG not referenced from code ===")
        for line_idx, org_addr, label_name, chunk_name, is_code in unreferenced:
            cn = f' in <<{chunk_name}>>' if chunk_name else ''
            kind = 'CODE' if is_code else 'DATA'
            print(f"  L{line_idx + 1}: ORG ${org_addr} {label_name} [{kind}]{cn}")
        print()

    print(f"Summary: {len(referenced_ok)} OK, {len(no_label)} missing label, "
          f"{len(unreferenced)} unreferenced")


if __name__ == '__main__':
    main()
