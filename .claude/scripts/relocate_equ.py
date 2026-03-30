"""Relocate EQU definitions to be close to their first usage.

For each label defined in a <<defines>>= or <<zero page defines>>= block,
find the first code usage and move the EQU to a block near that usage.

An EQU is "misplaced" if it's more than MAX_DIST lines from its first usage.
"""

import re
import sys

CHUNK_DEF = re.compile(r'^<<([-._  0-9A-Za-z]*)>>=\s*$')
PERCENT_DEF = re.compile(r'^@ %def\b')
EQU_LINE = re.compile(r'^(\w+)\s+EQU\s+(.*)$')
APPEND_CHUNKS = {'defines', 'zero page defines'}

MAX_DIST = 150  # only move EQUs further than this from first usage


def find_primary_chunk_before(lines, target_line):
    """Find the primary chunk definition line just before target_line."""
    best = None
    for i in range(target_line - 1, -1, -1):
        m = CHUNK_DEF.match(lines[i])
        if m and m.group(1) not in APPEND_CHUNKS:
            best = i
            break
    return best


def find_defines_block_before(lines, target_line):
    """Find a <<defines>>= block just before target_line (within 5 lines)."""
    # Look for an existing <<defines>>= block between the previous chunk's
    # @ %def and the target chunk
    for i in range(target_line - 1, max(target_line - 20, 0), -1):
        m = CHUNK_DEF.match(lines[i])
        if m and m.group(1) in APPEND_CHUNKS:
            return i
        # Stop if we hit a primary chunk definition
        if m and m.group(1) not in APPEND_CHUNKS:
            break
    return None


def main():
    with open('main.nw', 'r', encoding='cp1252') as f:
        lines = f.readlines()

    # Parse all EQU definitions in <<defines>>= and <<zero page defines>>= blocks
    equ_defs = []  # (line_idx, label, value, block_type, block_start_idx)
    current_block = None
    current_block_start = None

    for i, line in enumerate(lines):
        m = CHUNK_DEF.match(line)
        if m:
            if m.group(1) in APPEND_CHUNKS:
                current_block = m.group(1)
                current_block_start = i
            else:
                current_block = None
        if current_block:
            em = EQU_LINE.match(line)
            if em:
                equ_defs.append((i, em.group(1), line, current_block, current_block_start))

    print(f"Found {len(equ_defs)} EQU definitions in append blocks", file=sys.stderr)

    # For each EQU, find first code usage
    moves = []  # (label, from_line, to_before_line, equ_text, block_type)
    for def_idx, label, equ_text, block_type, block_start in equ_defs:
        pattern = re.compile(r'\b' + re.escape(label) + r'\b')

        first_usage = None
        for i, line in enumerate(lines):
            if i == def_idx:
                continue
            # Skip @ %def lines and the EQU definition itself
            if PERCENT_DEF.match(line):
                continue
            if EQU_LINE.match(line) and line.strip().startswith(label):
                continue
            # Skip prose lines (@ text)
            if line.startswith('@ ') and not PERCENT_DEF.match(line):
                continue
            # Skip chapter/section headers
            if '\\chapter{' in line or '\\section{' in line:
                continue
            if pattern.search(line):
                first_usage = i
                break

        if first_usage is None:
            continue

        dist = abs(first_usage - def_idx)
        if dist > MAX_DIST:
            # Find the primary chunk containing the first usage
            chunk_line = find_primary_chunk_before(lines, first_usage)
            if chunk_line is not None:
                moves.append((label, def_idx, chunk_line, equ_text, block_type, dist))

    moves.sort(key=lambda x: -x[5])
    print(f"Found {len(moves)} EQUs to relocate (>{MAX_DIST} lines from first usage)", file=sys.stderr)

    if '--dry-run' in sys.argv:
        for label, from_line, to_line, _, block_type, dist in moves:
            print(f"  {label:30s} L{from_line+1:5d} -> before L{to_line+1:5d} (dist={dist})")
        return

    # Group moves by destination chunk
    # For each destination, we'll insert a <<defines>>= block before the chunk
    # containing all the EQUs that need to go there
    dest_groups = {}  # chunk_line -> [(label, equ_text, block_type)]
    labels_to_remove = set()

    for label, from_line, to_chunk, equ_text, block_type, dist in moves:
        if to_chunk not in dest_groups:
            dest_groups[to_chunk] = []
        dest_groups[to_chunk].append((label, equ_text, block_type))
        labels_to_remove.add(label)

    # Build new file:
    # 1. Remove moved EQU lines from their original blocks
    # 2. Remove empty blocks
    # 3. Update @ %def lines
    # 4. Insert new blocks at destinations

    # First pass: mark lines for removal and collect block info
    remove_lines = set()
    block_ranges = []  # (start, end, block_type) for each append block

    current_block_start = None
    current_block_type = None
    for i, line in enumerate(lines):
        m = CHUNK_DEF.match(line)
        if m and m.group(1) in APPEND_CHUNKS:
            current_block_start = i
            current_block_type = m.group(1)
        elif current_block_start is not None:
            if PERCENT_DEF.match(line) or (m and m.group(1) not in APPEND_CHUNKS):
                block_ranges.append((current_block_start, i, current_block_type))
                current_block_start = None

    # Mark EQU lines for removal
    for def_idx, label, equ_text, block_type, block_start in equ_defs:
        if label in labels_to_remove:
            remove_lines.add(def_idx)

    # Update @ %def lines to remove moved labels
    new_lines = []
    skip_empty_block = False
    i = 0
    while i < len(lines):
        line = lines[i]

        if i in remove_lines:
            i += 1
            continue

        if PERCENT_DEF.match(line):
            # Remove moved labels from @ %def
            parts = line.strip().split()
            # parts[0] = '@', parts[1] = '%def', rest = labels
            remaining = [p for p in parts[2:] if p not in labels_to_remove]
            if remaining:
                new_lines.append('@ %def ' + ' '.join(remaining) + '\n')
            else:
                new_lines.append(line)
            i += 1
            continue

        new_lines.append(line)
        i += 1

    # Remove empty append blocks (blocks that only have the header and @ %def)
    final_lines = []
    i = 0
    while i < len(new_lines):
        line = new_lines[i]
        m = CHUNK_DEF.match(line)
        if m and m.group(1) in APPEND_CHUNKS:
            # Look ahead: is this block empty?
            block_content = [line]
            j = i + 1
            has_equ = False
            while j < len(new_lines):
                block_content.append(new_lines[j])
                if EQU_LINE.match(new_lines[j]):
                    has_equ = True
                if PERCENT_DEF.match(new_lines[j]):
                    break
                nm = CHUNK_DEF.match(new_lines[j])
                if nm:
                    break
                j += 1

            if not has_equ:
                # Empty block — skip it and its @ %def
                # Also skip surrounding blank lines
                i = j + 1
                while i < len(new_lines) and new_lines[i].strip() == '':
                    i += 1
                continue
            else:
                final_lines.extend(block_content)
                i = j + 1
                continue

        final_lines.append(line)
        i += 1

    # Now insert new blocks at destinations
    # Build a mapping from original line content to the chunk name,
    # so we can match destination chunks robustly

    # First, find chunk names for each destination line in the ORIGINAL file
    dest_chunk_names = {}
    for chunk_line_orig in dest_groups:
        m = CHUNK_DEF.match(lines[chunk_line_orig])
        if m:
            dest_chunk_names[chunk_line_orig] = m.group(1)

    # Find insertion points in final_lines by matching chunk names
    inserts = {}  # line_in_final -> text_to_insert
    used_positions = set()  # avoid matching same line twice

    for chunk_line_orig, equs in dest_groups.items():
        chunk_name = dest_chunk_names.get(chunk_line_orig)
        if not chunk_name:
            print(f"WARNING: no chunk name for destination L{chunk_line_orig+1}", file=sys.stderr)
            continue

        # Find this chunk definition in final_lines
        target_re = re.compile(r'^<<' + re.escape(chunk_name) + r'>>=\s*$')
        found = False
        for fi, fl in enumerate(final_lines):
            if fi in used_positions:
                continue
            if target_re.match(fl):
                used_positions.add(fi)
                # Group by block type
                defines_equs = [e for e in equs if e[2] == 'defines']
                zp_equs = [e for e in equs if e[2] == 'zero page defines']

                insert_text = []
                if defines_equs:
                    insert_text.append('<<defines>>=\n')
                    for label, equ_text, _ in defines_equs:
                        insert_text.append(equ_text)
                    labels_str = ' '.join(e[0] for e in defines_equs)
                    insert_text.append(f'@ %def {labels_str}\n')
                    insert_text.append('\n')
                if zp_equs:
                    insert_text.append('<<zero page defines>>=\n')
                    for label, equ_text, _ in zp_equs:
                        insert_text.append(equ_text)
                    labels_str = ' '.join(e[0] for e in zp_equs)
                    insert_text.append(f'@ %def {labels_str}\n')
                    insert_text.append('\n')

                inserts[fi] = insert_text
                found = True
                break

        if not found:
            print(f"WARNING: could not find chunk '{chunk_name}' in output for insertion", file=sys.stderr)

    # Build output with insertions
    output = []
    for i, line in enumerate(final_lines):
        if i in inserts:
            output.extend(inserts[i])
        output.append(line)

    with open('main.nw', 'w', encoding='cp1252') as f:
        f.writelines(output)

    print(f"Relocated {len(labels_to_remove)} EQU labels", file=sys.stderr)
    print(f"Inserted {len(dest_groups)} new <<defines>>= blocks", file=sys.stderr)


if __name__ == '__main__':
    main()
