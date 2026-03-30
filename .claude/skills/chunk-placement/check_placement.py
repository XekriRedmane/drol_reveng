#!/usr/bin/env python3
"""Check data chunk label placement: every label must be in the chunk
immediately before its first code use.

Usage:
    python .claude/skills/chunk-placement/check_placement.py [chunk-name]

With no arguments, checks all data chunks. With a chunk name, checks
just that one.
"""

from __future__ import annotations

import re
import sys

FILE = 'main.nw'
DATA_DIRECTIVES = {'ORG', 'HEX', 'APSTR', 'DC.B', 'DC.W', 'SUBROUTINE'}

# Instruction mnemonics that constitute "code use" of a label
CODE_MNEMONICS = (
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
    'LDWIY', 'stow',
)


def find_data_chunks(lines: list[str]) -> list[tuple[str, int, list[str]]]:
    """Find all data-only chunks with labels."""
    chunks: list[tuple[str, int, list[str]]] = []
    i = 0
    while i < len(lines):
        m = re.match(r'^<<(.+)>>=\s*$', lines[i].strip())
        if m:
            chunk_name = m.group(1)
            is_data_only = True
            labels: list[str] = []
            j = i + 1
            while j < len(lines):
                line = lines[j].strip()
                if line.startswith('@ %def'):
                    labels = line[6:].split()
                    j += 1
                    break
                if line == '@' or (
                    line.startswith('<<') and line.endswith('>>=')
                    and line != f'<<{chunk_name}>>='
                ):
                    break
                if not line or line.startswith(';') or line.startswith('@'):
                    j += 1
                    continue
                if re.match(r'^[A-Za-z_]\w*\s*[:=]', line):
                    j += 1
                    continue
                first_word = line.split()[0] if line.split() else ''
                if first_word in DATA_DIRECTIVES:
                    j += 1
                    continue
                is_data_only = False
                break
            if is_data_only and labels:
                chunks.append((chunk_name, i, labels))
        i += 1
    return chunks


def find_containing_chunk(lines: list[str], target_line: int) -> str | None:
    """Find which chunk definition contains a given line number."""
    best_name: str | None = None
    for i in range(target_line, -1, -1):
        m = re.match(r'^<<(.+)>>=\s*$', lines[i].strip())
        if m:
            best_name = m.group(1)
            break
    return best_name


def find_chunk_def_line(lines: list[str], chunk_name: str) -> int | None:
    """Find the line number of a chunk's first definition."""
    target = f'<<{chunk_name}>>='
    for i, line in enumerate(lines):
        if line.strip() == target:
            return i
    return None


def is_data_only_chunk(lines: list[str], chunk_start: int) -> bool:
    """Check if a chunk starting at chunk_start contains only data directives."""
    j = chunk_start + 1
    while j < len(lines):
        line = lines[j].strip()
        if line.startswith('@ %def') or line == '@':
            return True
        if line.startswith('<<') and line.endswith('>>='):
            return True
        if not line or line.startswith(';') or line.startswith('@'):
            j += 1
            continue
        if re.match(r'^[A-Za-z_]\w*\s*[:=]', line):
            j += 1
            continue
        first_word = line.split()[0] if line.split() else ''
        if first_word in DATA_DIRECTIVES:
            j += 1
            continue
        return False
    return True


def chunk_immediately_before(
    lines: list[str], data_chunk: str, code_chunk: str
) -> bool:
    """Check if data_chunk definition appears immediately before code_chunk
    definition (with only prose/comments and other data-only chunks between)."""
    data_line = find_chunk_def_line(lines, data_chunk)
    code_line = find_chunk_def_line(lines, code_chunk)
    if data_line is None or code_line is None:
        return False
    if data_line >= code_line:
        return False
    # Check no code chunk definitions between them
    # (data-only chunks and continuations of data_chunk are allowed)
    for i in range(data_line + 1, code_line):
        m = re.match(r'^<<(.+)>>=\s*$', lines[i].strip())
        if m and m.group(1) != data_chunk:
            # Allow other data-only chunks between
            if not is_data_only_chunk(lines, i):
                return False
    return True


def main() -> None:
    with open(FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    filter_chunk = sys.argv[1] if len(sys.argv) > 1 else None

    all_chunks = find_data_chunks(lines)
    if filter_chunk:
        all_chunks = [(n, l, labs) for n, l, labs in all_chunks
                      if n == filter_chunk]

    violations = 0
    ok_count = 0

    for chunk_name, chunk_line, labels in all_chunks:
        chunk_issues: list[str] = []

        for label in labels:
            # Find first code use of this label
            first_use_line: int | None = None
            for i, line in enumerate(lines):
                stripped = line.strip()
                # Skip the definition itself
                if stripped.startswith(f'{label}:') or stripped.startswith(f'{label} ='):
                    continue
                if stripped.startswith('@ %def'):
                    continue
                # Check if this line uses the label in code
                words = stripped.split()
                if not words:
                    continue
                mnemonic = words[0].upper()
                if mnemonic in CODE_MNEMONICS and label in stripped:
                    first_use_line = i
                    break

            if first_use_line is None:
                # Label not used in any code — might be OK (data-only)
                continue

            code_chunk = find_containing_chunk(lines, first_use_line)
            if code_chunk is None:
                continue

            if chunk_immediately_before(lines, chunk_name, code_chunk):
                ok_count += 1
            else:
                chunk_issues.append(
                    f'    {label}: first used in <<{code_chunk}>>, '
                    f'but <<{chunk_name}>> is not immediately before it'
                )
                violations += 1

        if chunk_issues:
            print(f'<<{chunk_name}>> (line {chunk_line + 1}):')
            for issue in chunk_issues:
                print(issue)
            print()

    if violations == 0:
        print(f'All {ok_count} labels correctly placed.')
    else:
        print(f'{violations} violation(s), {ok_count} OK.')


if __name__ == '__main__':
    main()
