#!/usr/bin/env python3
"""Apply macro substitutions to main.nw.

Scans main.nw for multi-instruction sequences that match dasm macro
patterns and replaces them with the equivalent single-line macro call.

Supported macros (grouped by instruction count):

  7-instr:  ADDW, ADDWC, SUBW, SUBWL
  6-instr:  LDWIY
  6+label:  ADDB, ADDB2, SUBB, SUBB2
  5+label:  ADDA
  4+label:  ADDAC
  4-instr:  STOW, STOW2, MOVW, PSHW, PULW
  3+label:  INCW
  2-instr:  STOB, MOVB, PULB, ROLW, RORW,
            BAEQ, BANE, BAPL, BAMI, BALT, BAGE,
            BXEQ, BXNE, BYEQ, BYNE

Matching is done in passes from longest to shortest so that a long
pattern is never misidentified as several shorter ones.
"""

from __future__ import annotations

import re
from collections import Counter

# Type aliases for the tuples threaded through the script.
# ParsedInstr: (mnemonic, operand, comment, indent)
# ParsedLine:  (lineno, ParsedInstr | None, raw_line, local_label | None, in_macro)
# InstrEntry:  (parsed_lines_index, lineno, ParsedInstr, raw_line)
# Substitution: (set_of_line_nums, first_line_num, replacement_text)

FILE = 'main.nw'


# ---------------------------------------------------------------------------
# Operand helpers
# ---------------------------------------------------------------------------

def parse_hex(s: str) -> int | None:
    """Parse a hex address like ``$BE`` or ``$1234``, return its integer value."""
    m = re.match(r'^\$([0-9A-Fa-f]+)$', s.strip())
    return int(m.group(1), 16) if m else None


def parse_imm_hex(s: str) -> int | None:
    """Parse an immediate hex value like ``#$BE``, return its integer value."""
    m = re.match(r'^#\$([0-9A-Fa-f]+)$', s.strip())
    return int(m.group(1), 16) if m else None


def addrs_adjacent(a: str, b: str) -> bool:
    """Return True if *b* is the byte after *a*.

    Works for hex literals (``$BE`` / ``$BF``) and symbolic expressions
    (``SYMBOL`` / ``SYMBOL+1``, ``SYMBOL+2`` / ``SYMBOL+3``).
    """
    va, vb = parse_hex(a), parse_hex(b)
    if va is not None and vb is not None:
        return vb == va + 1
    a_clean = a.replace(' ', '')
    b_clean = b.replace(' ', '')
    if b_clean == a_clean + '+1':
        return True
    m1 = re.match(r'^(.+)\+(\d+)$', a_clean)
    m2 = re.match(r'^(.+)\+(\d+)$', b_clean)
    if m1 and m2 and m1.group(1) == m2.group(1):
        return int(m2.group(2)) == int(m1.group(2)) + 1
    return False


def is_eligible(addr: str) -> bool:
    """Return True if *addr* can be a macro argument.

    Rejects local labels (``.name``), indexed (``addr,X``), and
    indirect (``(addr)``) addressing modes.
    """
    addr = addr.strip()
    if not addr:
        return False
    if addr.startswith('.'):
        return False
    if ',X' in addr.upper() or ',Y' in addr.upper():
        return False
    if '(' in addr or ')' in addr:
        return False
    return True


def is_immediate(operand: str) -> bool:
    """Return True if *operand* is an immediate value (starts with ``#``)."""
    return operand.strip().startswith('#')


def parse_lo_hi(operand: str) -> tuple[str, str] | None:
    """Parse ``#<SYMBOL`` or ``#>SYMBOL``.

    Returns ``('<', 'SYMBOL')`` or ``('>', 'SYMBOL')``, or None.
    """
    s = operand.strip()
    if not s.startswith('#'):
        return None
    s = s[1:]
    if s.startswith('<') or s.startswith('>'):
        return (s[0], s[1:])
    return None


def parse_bare_lo_hi(operand: str) -> tuple[str, str] | None:
    """Parse ``<SYMBOL`` or ``>SYMBOL`` (no ``#`` prefix, used by SUBWL).

    Returns ``('<', 'SYMBOL')`` or ``('>', 'SYMBOL')``, or None.
    """
    s = operand.strip()
    if s.startswith('<') or s.startswith('>'):
        return (s[0], s[1:])
    return None


# ---------------------------------------------------------------------------
# Line parsing
# ---------------------------------------------------------------------------

def parse_line(line: str) -> tuple[str, str, str, str] | None:
    """Parse an indented assembly instruction line.

    Returns ``(mnemonic, operand, comment, indent)`` or None if the line
    is not an instruction (e.g. a label, directive, blank, or doc line).
    """
    if not line or line[0] not in (' ', '\t'):
        return None
    indent = ''
    for ch in line:
        if ch in (' ', '\t'):
            indent += ch
        else:
            break
    stripped = line.rstrip()
    code = stripped
    comment = ''
    in_str = False
    for i, ch in enumerate(code):
        if ch == '"':
            in_str = not in_str
        elif ch == ';' and not in_str:
            comment = code[i:].strip()
            code = code[:i].strip()
            break
    code = code.strip()
    if not code:
        return None
    parts = code.split(None, 1)
    mnemonic = parts[0].upper()
    operand = parts[1].strip() if len(parts) > 1 else ''
    return (mnemonic, operand, comment, indent)


def is_local_label(line: str) -> str | None:
    """If *line* defines a local label (e.g. ``.loop``), return its name."""
    s = line.strip()
    if s.startswith('.') and not s.startswith('. '):
        return s.rstrip(':')
    return None


# ---------------------------------------------------------------------------
# Helpers used during matching
# ---------------------------------------------------------------------------

def are_consecutive(*line_nums: int) -> bool:
    """Return True if all line numbers are strictly consecutive."""
    for i in range(1, len(line_nums)):
        if line_nums[i] != line_nums[i - 1] + 1:
            return False
    return True


def best_comment(*comments: str) -> str:
    """Pick the most informative comment from a group.

    Skips empty comments and pure box-drawing markers like
    ``; \\``, ``; |``, ``; /``.  Strips a leading box marker
    from the chosen comment (e.g. ``; \\  text`` becomes ``; text``).
    """
    for c in comments:
        if not c:
            continue
        clean = c.lstrip('; ').strip()
        if clean in ('\\', '|', '/', ''):
            continue
        # Strip leading box-drawing marker from chosen comment
        m = re.match(r'^(;\s*)[\\|/]\s+(.+)$', c)
        if m:
            return f'{m.group(1)}{m.group(2)}'
        return c
    return ''


def record(macro_name: str, macro_args: str, indent: str,
           line_nums: list[int], comments: list[str]) -> None:
    """Record a substitution: replace *line_nums* with a macro call."""
    bc = best_comment(*comments)
    comment_str = f' {bc}' if bc else ''
    args_str = f'    {macro_args}' if macro_args else ''
    replacement = f'{indent}{macro_name}{args_str}{comment_str}\n'
    lns = set(line_nums)
    substitutions.append((lns, line_nums[0], replacement))
    found_lines.update(lns)


# ---------------------------------------------------------------------------
# Main script
# ---------------------------------------------------------------------------

with open(FILE, 'r', encoding='utf-8') as f:
    lines: list[str] = f.readlines()

# --- Build parsed_lines index ---
in_macro: bool = False
parsed_lines: list[tuple[int, tuple[str, str, str, str] | None, str, str | None, bool]] = []
for i, line in enumerate(lines):
    lineno = i + 1
    stripped = line.strip()
    upper_parts = stripped.upper().split()
    if 'MACRO' in upper_parts:
        in_macro = True
        parsed_lines.append((lineno, None, line, None, True))
        continue
    if stripped.upper().startswith('ENDM'):
        in_macro = False
        parsed_lines.append((lineno, None, line, None, True))
        continue
    if in_macro:
        parsed_lines.append((lineno, None, line, None, True))
        continue
    ll = is_local_label(line)
    p = parse_line(line)
    parsed_lines.append((lineno, p, line, ll, False))

# --- Build instruction-only index (skipping macro bodies) ---
instr_entries: list[tuple[int, int, tuple[str, str, str, str], str]] = []
for idx, (lineno, parsed, raw, ll, in_m) in enumerate(parsed_lines):
    if in_m:
        continue
    if parsed is not None:
        instr_entries.append((idx, lineno, parsed, raw))

# --- Map line numbers to local label names ---
label_at_line: dict[int, str] = {}
for idx, (lineno, parsed, raw, ll, in_m) in enumerate(parsed_lines):
    if ll:
        label_at_line[lineno] = ll


def label_ref_count(label_name: str) -> int:
    """Count how many instruction operands reference *label_name*.

    Used to ensure a BNE/BCS/BCC target label isn't branched to from
    elsewhere (which would make the substitution unsafe).
    """
    count = 0
    for _, (_, parsed, _, _, in_m) in enumerate(parsed_lines):
        if in_m:
            continue
        if parsed and label_name in parsed[1]:
            count += 1
    return count


def check_trailing_label(last_instr_ln: int, branch_target: str) -> bool:
    """Verify a branch target label exists on the line after *last_instr_ln*
    and is only referenced once (by the branch itself)."""
    if not branch_target.startswith('.'):
        return False
    ll_name = label_at_line.get(last_instr_ln + 1)
    if ll_name != branch_target:
        return False
    return label_ref_count(branch_target) <= 1


def get_n(ei: int, n: int) -> list[tuple[int, int, tuple[str, str, str, str], str]] | None:
    """Get *n* consecutive instruction entries starting at *ei*.

    Returns None if there aren't enough entries or if their line numbers
    aren't consecutive or if any is already consumed.
    """
    if ei + n > len(instr_entries):
        return None
    entries = instr_entries[ei:ei + n]
    lns = [e[1] for e in entries]
    if lns[0] in found_lines:
        return None
    if not are_consecutive(*lns):
        return None
    return entries


# --- Collect substitutions ---
substitutions: list[tuple[set[int], int, str]] = []
found_lines: set[int] = set()


# === Pass 1: 7-instruction patterns (ADDW, SUBW, SUBWL, ADDWC) ===
for ei in range(len(instr_entries)):
    es = get_n(ei, 7)
    if es is None:
        continue
    lns = [e[1] for e in es]
    ps = [e[2] for e in es]
    ms = [p[0] for p in ps]
    os = [p[1] for p in ps]
    cs = [p[2] for p in ps]
    ind = ps[0][3]

    # ADDW: CLC / LDA a / ADC b / STA c / LDA a+1 / ADC b+1 / STA c+1
    if (ms == ['CLC', 'LDA', 'ADC', 'STA', 'LDA', 'ADC', 'STA']
            and os[0] == ''
            and not is_immediate(os[1]) and not is_immediate(os[4])
            and is_eligible(os[1]) and is_eligible(os[2]) and is_eligible(os[3])
            and addrs_adjacent(os[1], os[4])
            and addrs_adjacent(os[2], os[5])
            and addrs_adjacent(os[3], os[6])):
        record('ADDW', f'{os[1]},{os[2]},{os[3]}', ind, lns, cs)
        continue

    # SUBW: SEC / LDA a / SBC b / STA c / LDA a+1 / SBC b+1 / STA c+1
    if (ms == ['SEC', 'LDA', 'SBC', 'STA', 'LDA', 'SBC', 'STA']
            and os[0] == ''
            and not is_immediate(os[1]) and not is_immediate(os[4])
            and is_eligible(os[1]) and is_eligible(os[2]) and is_eligible(os[3])
            and addrs_adjacent(os[1], os[4])
            and addrs_adjacent(os[2], os[5])
            and addrs_adjacent(os[3], os[6])):
        record('SUBW', f'{os[1]},{os[2]},{os[3]}', ind, lns, cs)
        continue

    # SUBWL: SEC / LDA #<val / SBC b / STA c / LDA #>val / SBC b+1 / STA c+1
    #   (also: SEC / LDA <val / SBC b / STA c / LDA >val / SBC b+1 / STA c+1)
    if (ms == ['SEC', 'LDA', 'SBC', 'STA', 'LDA', 'SBC', 'STA']
            and os[0] == ''):
        # Try #</#> form
        lo = parse_lo_hi(os[1])
        hi = parse_lo_hi(os[4])
        if not lo:
            # Try bare </>  form (no #)
            lo = parse_bare_lo_hi(os[1])
            hi = parse_bare_lo_hi(os[4])
        if (lo and hi and lo[0] == '<' and hi[0] == '>' and lo[1] == hi[1]
                and is_eligible(os[2]) and is_eligible(os[3])
                and addrs_adjacent(os[2], os[5])
                and addrs_adjacent(os[3], os[6])):
            record('SUBWL', f'#{lo[1]},{os[2]},{os[3]}', ind, lns, cs)
            continue

    # ADDWC: LDA a / ADC b / STA c / LDA a+1 / ADC b+1 / STA c+1
    # (6 instructions, but check in 7-window to avoid overlap — handled in pass 2 below)

# === Pass 2: 6-instruction patterns (ADDB, ADDB2, SUBB, SUBB2, ADDWC) ===
for ei in range(len(instr_entries)):
    # --- 6-instruction patterns (no label) ---
    es = get_n(ei, 6)
    if es is not None:
        lns = [e[1] for e in es]
        ps = [e[2] for e in es]
        ms = [p[0] for p in ps]
        os = [p[1] for p in ps]
        cs = [p[2] for p in ps]
        ind = ps[0][3]

        # ADDWC: LDA a / ADC b / STA c / LDA a+1 / ADC b+1 / STA c+1
        if (ms == ['LDA', 'ADC', 'STA', 'LDA', 'ADC', 'STA']
                and not is_immediate(os[0]) and not is_immediate(os[3])
                and is_eligible(os[0]) and is_eligible(os[1]) and is_eligible(os[2])
                and addrs_adjacent(os[0], os[3])
                and addrs_adjacent(os[1], os[4])
                and addrs_adjacent(os[2], os[5])):
            record('ADDWC', f'{os[0]},{os[1]},{os[2]}', ind, lns, cs)
            continue

        # LDWIY: LDY #off / LDA (ptr),Y / STA dst / INY / LDA (ptr),Y / STA dst+1
        if (ms == ['LDY', 'LDA', 'STA', 'INY', 'LDA', 'STA']
                and is_immediate(os[0])
                and os[3] == ''  # INY has no operand
                and os[1] == os[4]  # same indirect operand
                and is_eligible(os[2])
                and addrs_adjacent(os[2], os[5])):
            # Extract pointer name from indirect operand like (PTR),Y
            m = re.match(r'^\((.+)\)\s*,\s*Y$', os[1], re.IGNORECASE)
            if m:
                ptr = m.group(1)
                record('LDWIY', f'{ptr},{os[0]},{os[2]}', ind, lns, cs)
                continue

    # --- 6-instruction + label patterns ---
    es = get_n(ei, 6)
    if es is None:
        continue
    lns = [e[1] for e in es]
    ps = [e[2] for e in es]
    ms = [p[0] for p in ps]
    os = [p[1] for p in ps]
    cs = [p[2] for p in ps]
    ind = ps[0][3]

    # ADDB: LDA addr / CLC / ADC val / STA addr / BCC .lbl / INC addr+1
    #   + .lbl on next line
    if (ms == ['LDA', 'CLC', 'ADC', 'STA', 'BCC', 'INC']
            and os[1] == ''
            and not is_immediate(os[0])
            and is_eligible(os[0]) and os[0] == os[3]
            and addrs_adjacent(os[0], os[5])
            and check_trailing_label(lns[5], os[4])):
        label_ln = lns[5] + 1
        record('ADDB', f'{os[0]},{os[2]}', ind, lns + [label_ln], cs)
        found_lines.add(label_ln)
        continue

    # ADDB2: CLC / LDA addr / ADC val / STA addr / BCC .lbl / INC addr+1
    if (ms == ['CLC', 'LDA', 'ADC', 'STA', 'BCC', 'INC']
            and os[0] == ''
            and not is_immediate(os[1])
            and is_eligible(os[1]) and os[1] == os[3]
            and addrs_adjacent(os[1], os[5])
            and check_trailing_label(lns[5], os[4])):
        label_ln = lns[5] + 1
        record('ADDB2', f'{os[1]},{os[2]}', ind, lns + [label_ln], cs)
        found_lines.add(label_ln)
        continue

    # SUBB: LDA addr / SEC / SBC val / STA addr / BCS .lbl / DEC addr+1
    if (ms == ['LDA', 'SEC', 'SBC', 'STA', 'BCS', 'DEC']
            and os[1] == ''
            and not is_immediate(os[0])
            and is_eligible(os[0]) and os[0] == os[3]
            and addrs_adjacent(os[0], os[5])
            and check_trailing_label(lns[5], os[4])):
        label_ln = lns[5] + 1
        record('SUBB', f'{os[0]},{os[2]}', ind, lns + [label_ln], cs)
        found_lines.add(label_ln)
        continue

    # SUBB2: SEC / LDA addr / SBC val / STA addr / BCS .lbl / DEC addr+1
    if (ms == ['SEC', 'LDA', 'SBC', 'STA', 'BCS', 'DEC']
            and os[0] == ''
            and not is_immediate(os[1])
            and is_eligible(os[1]) and os[1] == os[3]
            and addrs_adjacent(os[1], os[5])
            and check_trailing_label(lns[5], os[4])):
        label_ln = lns[5] + 1
        record('SUBB2', f'{os[1]},{os[2]}', ind, lns + [label_ln], cs)
        found_lines.add(label_ln)
        continue

# === Pass 3: 5-instruction + label (ADDA) ===
for ei in range(len(instr_entries)):
    es = get_n(ei, 5)
    if es is None:
        continue
    lns = [e[1] for e in es]
    ps = [e[2] for e in es]
    ms = [p[0] for p in ps]
    os = [p[1] for p in ps]
    cs = [p[2] for p in ps]
    ind = ps[0][3]

    # ADDA: CLC / ADC addr / STA addr / BCC .lbl / INC addr+1
    if (ms == ['CLC', 'ADC', 'STA', 'BCC', 'INC']
            and os[0] == ''
            and not is_immediate(os[1])
            and is_eligible(os[1]) and os[1] == os[2]
            and addrs_adjacent(os[1], os[4])
            and check_trailing_label(lns[4], os[3])):
        label_ln = lns[4] + 1
        record('ADDA', f'{os[1]}', ind, lns + [label_ln], cs)
        found_lines.add(label_ln)
        continue

# === Pass 4: 4-instruction + label (ADDAC) and 4-instruction patterns ===
for ei in range(len(instr_entries)):
    # --- ADDAC: ADC addr / STA addr / BCC .lbl / INC addr+1 + .lbl ---
    es = get_n(ei, 4)
    if es is not None:
        lns = [e[1] for e in es]
        ps = [e[2] for e in es]
        ms = [p[0] for p in ps]
        os = [p[1] for p in ps]
        cs = [p[2] for p in ps]
        ind = ps[0][3]

        if (ms == ['ADC', 'STA', 'BCC', 'INC']
                and not is_immediate(os[0])
                and is_eligible(os[0]) and os[0] == os[1]
                and addrs_adjacent(os[0], os[3])
                and check_trailing_label(lns[3], os[2])):
            label_ln = lns[3] + 1
            record('ADDAC', f'{os[0]}', ind, lns + [label_ln], cs)
            found_lines.add(label_ln)
            continue

    # --- 4-instruction patterns (no label) ---
    es = get_n(ei, 4)
    if es is None:
        continue
    lns = [e[1] for e in es]
    ps = [e[2] for e in es]
    ms = [p[0] for p in ps]
    os = [p[1] for p in ps]
    cs = [p[2] for p in ps]
    ind = ps[0][3]

    macro_name: str | None = None
    macro_args: str | None = None

    # STOW with </>: LDA #<val / STA dst / LDA #>val / STA dst+1
    if ms == ['LDA', 'STA', 'LDA', 'STA']:
        lo = parse_lo_hi(os[0])
        hi = parse_lo_hi(os[2])
        if lo and hi and lo[0] == '<' and hi[0] == '>' and lo[1] == hi[1]:
            if is_eligible(os[1]) and addrs_adjacent(os[1], os[3]):
                macro_name = 'STOW'
                macro_args = f'{lo[1]},{os[1]}'

    # STOW with raw hex: LDA #$lo / STA dst / LDA #$hi / STA dst+1
    if not macro_name and ms == ['LDA', 'STA', 'LDA', 'STA']:
        lo_val = parse_imm_hex(os[0])
        hi_val = parse_imm_hex(os[2])
        if lo_val is not None and hi_val is not None:
            if is_eligible(os[1]) and addrs_adjacent(os[1], os[3]):
                word_val = (hi_val << 8) | lo_val
                macro_name = 'STOW'
                macro_args = f'${word_val:04X},{os[1]}'

    # STOW2 with </>: LDA #>val / STA dst+1 / LDA #<val / STA dst
    if not macro_name and ms == ['LDA', 'STA', 'LDA', 'STA']:
        hi = parse_lo_hi(os[0])
        lo = parse_lo_hi(os[2])
        if lo and hi and lo[0] == '<' and hi[0] == '>' and lo[1] == hi[1]:
            if is_eligible(os[3]) and addrs_adjacent(os[3], os[1]):
                macro_name = 'STOW2'
                macro_args = f'{lo[1]},{os[3]}'

    # STOW2 with raw hex: LDA #$hi / STA dst+1 / LDA #$lo / STA dst
    if not macro_name and ms == ['LDA', 'STA', 'LDA', 'STA']:
        hi_val = parse_imm_hex(os[0])
        lo_val = parse_imm_hex(os[2])
        if hi_val is not None and lo_val is not None:
            if is_eligible(os[3]) and addrs_adjacent(os[3], os[1]):
                word_val = (hi_val << 8) | lo_val
                macro_name = 'STOW2'
                macro_args = f'${word_val:04X},{os[3]}'

    # MOVW: LDA src / STA dst / LDA src+1 / STA dst+1
    if (not macro_name and ms == ['LDA', 'STA', 'LDA', 'STA']
            and not is_immediate(os[0]) and not is_immediate(os[2])):
        if (is_eligible(os[0]) and is_eligible(os[1])
                and addrs_adjacent(os[0], os[2]) and addrs_adjacent(os[1], os[3])):
            macro_name = 'MOVW'
            macro_args = f'{os[0]},{os[1]}'

    # PSHW: LDA addr / PHA / LDA addr+1 / PHA
    if (not macro_name and ms == ['LDA', 'PHA', 'LDA', 'PHA']
            and not is_immediate(os[0]) and not is_immediate(os[2])):
        if is_eligible(os[0]) and addrs_adjacent(os[0], os[2]):
            macro_name = 'PSHW'
            macro_args = os[0]

    # PULW: PLA / STA addr+1 / PLA / STA addr
    if (not macro_name and ms == ['PLA', 'STA', 'PLA', 'STA']
            and os[0] == '' and os[2] == ''):
        if is_eligible(os[3]) and addrs_adjacent(os[3], os[1]):
            macro_name = 'PULW'
            macro_args = os[3]

    if macro_name:
        record(macro_name, macro_args, ind, lns, cs)

# === Pass 5: 3-instruction + label (INCW) ===
for ei in range(len(instr_entries)):
    es = get_n(ei, 3)
    if es is None:
        continue
    lns = [e[1] for e in es]
    ps = [e[2] for e in es]
    ms = [p[0] for p in ps]
    os = [p[1] for p in ps]
    cs = [p[2] for p in ps]
    ind = ps[0][3]

    # INCW: INC addr / BNE .lbl / INC addr+1 / .lbl
    if (ms == ['INC', 'BNE', 'INC']
            and is_eligible(os[0]) and addrs_adjacent(os[0], os[2])
            and check_trailing_label(lns[2], os[1])):
        label_ln = lns[2] + 1
        record('INCW', os[0], ind, lns + [label_ln], cs)
        found_lines.add(label_ln)

# === Pass 6: 2-instruction patterns ===
for ei in range(len(instr_entries)):
    es = get_n(ei, 2)
    if es is None:
        continue
    lns = [e[1] for e in es]
    ps = [e[2] for e in es]
    ms = [p[0] for p in ps]
    os = [p[1] for p in ps]
    cs = [p[2] for p in ps]
    ind = ps[0][3]

    macro_name: str | None = None
    macro_args: str | None = None

    # ROLW: ROL addr / ROL addr+1
    if ms == ['ROL', 'ROL'] and is_eligible(os[0]) and addrs_adjacent(os[0], os[1]):
        macro_name = 'ROLW'
        macro_args = os[0]

    # RORW: ROR addr+1 / ROR addr
    if not macro_name and ms == ['ROR', 'ROR'] and is_eligible(os[1]) and addrs_adjacent(os[1], os[0]):
        macro_name = 'RORW'
        macro_args = os[1]

    # ROL2: ROL / ROL (accumulator, no operand)
    if not macro_name and ms == ['ROL', 'ROL'] and os[0] == '' and os[1] == '':
        macro_name = 'ROL2'
        macro_args = ''

    # Comparison macros: compare operand must not contain commas or
    # parentheses — those would break dasm's comma-separated macro args.
    # BAEQ: CMP val / BEQ lbl
    if not macro_name and ms == ['CMP', 'BEQ'] and ',' not in os[0] and '(' not in os[0]:
        macro_name = 'BAEQ'
        macro_args = f'{os[0]},{os[1]}'

    # BANE: CMP val / BNE lbl
    if not macro_name and ms == ['CMP', 'BNE'] and ',' not in os[0] and '(' not in os[0]:
        macro_name = 'BANE'
        macro_args = f'{os[0]},{os[1]}'

    # BAPL: CMP val / BPL lbl
    if not macro_name and ms == ['CMP', 'BPL'] and ',' not in os[0] and '(' not in os[0]:
        macro_name = 'BAPL'
        macro_args = f'{os[0]},{os[1]}'

    # BAMI: CMP val / BMI lbl
    if not macro_name and ms == ['CMP', 'BMI'] and ',' not in os[0] and '(' not in os[0]:
        macro_name = 'BAMI'
        macro_args = f'{os[0]},{os[1]}'

    # BALT: CMP val / BCC lbl
    if not macro_name and ms == ['CMP', 'BCC'] and ',' not in os[0] and '(' not in os[0]:
        macro_name = 'BALT'
        macro_args = f'{os[0]},{os[1]}'

    # BAGE: CMP val / BCS lbl
    if not macro_name and ms == ['CMP', 'BCS'] and ',' not in os[0] and '(' not in os[0]:
        macro_name = 'BAGE'
        macro_args = f'{os[0]},{os[1]}'

    # BXEQ: CPX val / BEQ lbl
    if not macro_name and ms == ['CPX', 'BEQ'] and ',' not in os[0] and '(' not in os[0]:
        macro_name = 'BXEQ'
        macro_args = f'{os[0]},{os[1]}'

    # BXNE: CPX val / BNE lbl
    if not macro_name and ms == ['CPX', 'BNE'] and ',' not in os[0] and '(' not in os[0]:
        macro_name = 'BXNE'
        macro_args = f'{os[0]},{os[1]}'

    # BYEQ: CPY val / BEQ lbl
    if not macro_name and ms == ['CPY', 'BEQ'] and ',' not in os[0] and '(' not in os[0]:
        macro_name = 'BYEQ'
        macro_args = f'{os[0]},{os[1]}'

    # BYNE: CPY val / BNE lbl
    if not macro_name and ms == ['CPY', 'BNE'] and ',' not in os[0] and '(' not in os[0]:
        macro_name = 'BYNE'
        macro_args = f'{os[0]},{os[1]}'

    # STOB: LDA #val / STA dst
    if not macro_name and ms == ['LDA', 'STA'] and is_immediate(os[0]) and is_eligible(os[1]):
        macro_name = 'STOB'
        macro_args = f'{os[0]},{os[1]}'

    # MOVB: LDA src / STA dst
    if (not macro_name and ms == ['LDA', 'STA']
            and not is_immediate(os[0]) and is_eligible(os[0]) and is_eligible(os[1])):
        macro_name = 'MOVB'
        macro_args = f'{os[0]},{os[1]}'

    # PULB: PLA / STA addr
    if not macro_name and ms == ['PLA', 'STA'] and os[0] == '' and is_eligible(os[1]):
        macro_name = 'PULB'
        macro_args = os[1]

    if macro_name:
        record(macro_name, macro_args, ind, lns, cs)


# ---------------------------------------------------------------------------
# Apply substitutions
# ---------------------------------------------------------------------------

substitutions.sort(key=lambda s: s[1])

lines_to_delete: set[int] = set()
replacements: dict[int, str] = {}

for lns_set, first_ln, replacement in substitutions:
    replacements[first_ln] = replacement
    for ln in lns_set:
        if ln != first_ln:
            lines_to_delete.add(ln)

output_lines: list[str] = []
for i, line in enumerate(lines):
    lineno = i + 1
    if lineno in lines_to_delete:
        continue
    if lineno in replacements:
        output_lines.append(replacements[lineno])
    else:
        output_lines.append(line)

with open(FILE, 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

# --- Report ---
counts: Counter[str] = Counter()
for lns_set, first_ln, replacement in substitutions:
    name = replacement.strip().split()[0]
    counts[name] += 1

total = sum(counts.values())
if total == 0:
    print("No macro candidates found.")
else:
    print(f"Applied {total} macro substitutions:")
    for macro, count in sorted(counts.items()):
        print(f"  {macro}: {count}")
