"""Relocate EQU definitions so each appears just before the chunk that first uses it.

Rule: every label in a <<defines>>= or <<zero page defines>>= block must be
used in the NEXT primary chunk. If not, move it to just before the chunk
that first uses it.
"""

import re
import sys

CHUNK_DEF = re.compile(r'^<<([-._  0-9A-Za-z]*)>>=\s*$')
PERCENT_DEF = re.compile(r'^@ %def\b')
EQU_LINE = re.compile(r'^(\w+)\s+EQU\s+(.*)$')
APPEND_CHUNKS = {'defines', 'zero page defines'}


def parse_file(lines):
    """Parse the file into a sequence of blocks.

    Returns a list of blocks. Each block is a dict:
      type: 'primary_chunk' | 'append_chunk' | 'prose' | 'percent_def'
      lines: list of line strings
      start: 0-based line index
      name: chunk name (for chunk types)
      labels: list of EQU labels (for append chunks)
    """
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = CHUNK_DEF.match(line)
        if m:
            name = m.group(1)
            is_append = name in APPEND_CHUNKS
            # Collect chunk body until @ %def, bare @, or next chunk
            chunk_lines = [line]
            labels = []
            j = i + 1
            while j < len(lines):
                cline = lines[j]
                if PERCENT_DEF.match(cline):
                    chunk_lines.append(cline)
                    j += 1
                    break
                if cline.strip() == '@':
                    chunk_lines.append(cline)
                    j += 1
                    break
                m2 = CHUNK_DEF.match(cline)
                if m2:
                    break  # don't consume next chunk
                em = EQU_LINE.match(cline)
                if em:
                    labels.append(em.group(1))
                chunk_lines.append(cline)
                j += 1

            blocks.append({
                'type': 'append_chunk' if is_append else 'primary_chunk',
                'lines': chunk_lines,
                'start': i,
                'name': name,
                'labels': labels,
            })
            # After @ %def, any prose before the next <<chunk>>= is a
            # separate prose block — don't leave it attached to the chunk
            i = j
        else:
            # Prose or other content
            prose_lines = [line]
            j = i + 1
            while j < len(lines):
                if CHUNK_DEF.match(lines[j]):
                    break
                prose_lines.append(lines[j])
                j += 1
            blocks.append({
                'type': 'prose',
                'lines': prose_lines,
                'start': i,
                'name': None,
                'labels': [],
            })
            i = j

    return blocks


def find_next_primary(blocks, block_idx):
    """Find the next primary chunk after block_idx."""
    for i in range(block_idx + 1, len(blocks)):
        if blocks[i]['type'] == 'primary_chunk':
            return i
    return None


def chunk_uses_label(block, label):
    """Check if a primary chunk block uses the given label."""
    pattern = re.compile(r'\b' + re.escape(label) + r'\b')
    for line in block['lines']:
        # Skip the chunk definition line and @ %def line
        if CHUNK_DEF.match(line) or PERCENT_DEF.match(line):
            continue
        if EQU_LINE.match(line) and line.strip().startswith(label):
            continue
        if pattern.search(line):
            return True
    return False


def find_first_using_chunk(blocks, label, start_idx=0):
    """Find the first primary chunk that uses this label."""
    pattern = re.compile(r'\b' + re.escape(label) + r'\b')
    for i in range(start_idx, len(blocks)):
        if blocks[i]['type'] != 'primary_chunk':
            continue
        for line in blocks[i]['lines']:
            if CHUNK_DEF.match(line) or PERCENT_DEF.match(line):
                continue
            if EQU_LINE.match(line) and line.strip().startswith(label):
                continue
            if pattern.search(line):
                return i
    return None


def main():
    with open('main.nw', 'r', encoding='cp1252') as f:
        lines = f.readlines()

    blocks = parse_file(lines)
    print(f"Parsed {len(blocks)} blocks", file=sys.stderr)

    # For each append_chunk block, check each label
    moves = []  # (label, equ_line_text, from_block_idx, to_before_block_idx, block_type)

    for bi, block in enumerate(blocks):
        if block['type'] != 'append_chunk':
            continue

        next_primary = find_next_primary(blocks, bi)

        for label in block['labels']:
            # Is label used in the next primary chunk?
            used_in_next = False
            if next_primary is not None:
                used_in_next = chunk_uses_label(blocks[next_primary], label)
                # Also check any append chunks between this block and the next primary
                # (some EQUs might be used in intervening append blocks)
                for mi in range(bi + 1, next_primary):
                    if blocks[mi]['type'] == 'append_chunk':
                        if chunk_uses_label(blocks[mi], label):
                            used_in_next = True
                            break

            if not used_in_next:
                # Find where it's actually first used
                dest = find_first_using_chunk(blocks, label)
                if dest is not None and dest != next_primary:
                    # Find the EQU line text
                    equ_text = None
                    for line in block['lines']:
                        em = EQU_LINE.match(line)
                        if em and em.group(1) == label:
                            equ_text = line
                            break
                    if equ_text:
                        moves.append((label, equ_text, bi, dest, block['name']))

    print(f"Found {len(moves)} EQUs to relocate", file=sys.stderr)

    if '--dry-run' in sys.argv:
        for label, _, from_bi, to_bi, btype in moves:
            from_line = blocks[from_bi]['start'] + 1
            to_name = blocks[to_bi]['name']
            to_line = blocks[to_bi]['start'] + 1
            print(f"  {label:30s} L{from_line:5d} -> before <<{to_name}>> L{to_line:5d}")
        return

    # Apply moves:
    # 1. Remove labels from source blocks
    # 2. Insert new defines blocks before destination chunks

    labels_to_remove = {}  # block_idx -> set of labels to remove
    inserts = {}  # block_idx -> {block_type: [(label, equ_text)]}

    for label, equ_text, from_bi, to_bi, btype in moves:
        if from_bi not in labels_to_remove:
            labels_to_remove[from_bi] = set()
        labels_to_remove[from_bi].add(label)

        if to_bi not in inserts:
            inserts[to_bi] = {}
        if btype not in inserts[to_bi]:
            inserts[to_bi][btype] = []
        inserts[to_bi][btype].append((label, equ_text))

    # Build output
    output = []
    for bi, block in enumerate(blocks):
        # Insert new defines blocks before this chunk if needed
        if bi in inserts:
            for btype in sorted(inserts[bi].keys()):
                equs = inserts[bi][btype]
                output.append(f'<<{btype}>>=\n')
                for label, equ_text in equs:
                    output.append(equ_text)
                labels_str = ' '.join(e[0] for e in equs)
                output.append(f'@ %def {labels_str}\n')
                output.append('\n')

        if bi in labels_to_remove:
            # Filter out removed labels from this block
            removing = labels_to_remove[bi]
            remaining_labels = [l for l in block['labels'] if l not in removing]

            if not remaining_labels:
                # Entire block is empty — skip it, but check if the NEXT
                # block is bare prose (no @ prefix) that relied on this
                # block's @ %def for doc-mode context.  If so, we need to
                # ensure the prose survives in doc mode.
                if bi + 1 < len(blocks) and blocks[bi + 1]['type'] == 'prose':
                    next_prose = blocks[bi + 1]['lines']
                    # Check if the prose has proper @ prefix or needs one
                    first_nonblank = None
                    for pl in next_prose:
                        if pl.strip():
                            first_nonblank = pl
                            break
                    if first_nonblank and not first_nonblank.startswith('@ ') and \
                       not first_nonblank.startswith('\\') and \
                       first_nonblank.strip() != '@':
                        # Bare prose — add @ prefix to first non-blank line
                        for pi, pl in enumerate(blocks[bi + 1]['lines']):
                            if pl.strip() and pl == first_nonblank:
                                blocks[bi + 1]['lines'][pi] = '@ ' + pl
                                break
                continue  # skip the empty block

            # Emit block with removed labels filtered out
            for line in block['lines']:
                em = EQU_LINE.match(line)
                if em and em.group(1) in removing:
                    continue
                if PERCENT_DEF.match(line):
                    # Rewrite @ %def line without removed labels
                    parts = line.strip().split()
                    kept = [p for p in parts[2:] if p not in removing]
                    if kept:
                        output.append('@ %def ' + ' '.join(kept) + '\n')
                    # else skip the @ %def entirely
                    continue
                output.append(line)
        else:
            output.extend(block['lines'])

    with open('main.nw', 'w', encoding='cp1252') as f:
        f.writelines(output)

    print(f"Relocated {len(moves)} EQU labels", file=sys.stderr)
    unique_dests = len(inserts)
    print(f"Created/augmented {unique_dests} destination blocks", file=sys.stderr)


if __name__ == '__main__':
    main()
