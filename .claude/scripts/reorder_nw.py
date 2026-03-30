"""Reorder main.nw chunk definitions into a new narrative order.

Parses main.nw into "segments" — units of text that travel together when
reordering — then reassembles them according to an ordering specification.

A segment consists of:
  1. Optional preceding prose/LaTeX headers (@ text, \\section{}, etc.)
  2. A primary chunk definition (<<name>>=  ...  @ %def)
  3. Any immediately following <<defines>>= or <<zero page defines>>= blocks
     that are "attached" (no intervening primary chunk)

The file has three fixed regions that don't move:
  - Preamble: everything before the first movable chapter
  - Postamble: from <<main.asm>>= through end of file
  - Part I: already well-organized boot/startup content

Usage:
  python reorder_nw.py main.nw ordering.txt > main_reordered.nw
"""

import re
import sys
from dataclasses import dataclass, field


CHUNK_DEF = re.compile(r'^<<([-._  0-9A-Za-z]*)>>=\s*$')
DOC_START = re.compile(r'^(@ )|(^@$)')
PERCENT_DEF = re.compile(r'^@ %def\b')
APPEND_CHUNKS = {'defines', 'zero page defines', 'Macros'}


@dataclass
class Segment:
    """A movable unit of text in the noweb file."""
    # The primary chunk name (None for prose-only segments)
    chunk_name: str | None
    # All chunk names defined in this segment (including appended defines)
    all_chunk_names: list[str] = field(default_factory=list)
    # The lines of text
    lines: list[str] = field(default_factory=list)
    # Line number in original file (1-based)
    start_line: int = 0
    # A unique key for ordering lookup
    key: str = ""
    # For appended chunks, which instance this is (0-based)
    instance: int = 0


def parse_segments(lines: list[str], movable_start: int, movable_end: int) -> tuple[list[str], list[Segment], list[str]]:
    """Parse lines[movable_start:movable_end] into segments.

    Returns (preamble_lines, segments, postamble_lines).
    """
    preamble = lines[:movable_start]
    postamble = lines[movable_end:]
    body = lines[movable_start:movable_end]

    segments = []
    current_prose: list[str] = []
    current_chunks: list[str] = []
    current_chunk_names: list[str] = []
    primary_name: str | None = None
    in_chunk = False
    chunk_start_line = movable_start

    # Track instance counts for appended chunks
    instance_counts: dict[str, int] = {}

    def flush_segment():
        nonlocal current_prose, current_chunks, current_chunk_names, primary_name
        if current_prose or current_chunks:
            seg = Segment(
                chunk_name=primary_name,
                all_chunk_names=current_chunk_names[:],
                lines=current_prose + current_chunks,
                start_line=chunk_start_line + 1,  # 1-based
            )
            if primary_name:
                inst = instance_counts.get(primary_name, 0)
                instance_counts[primary_name] = inst + 1
                seg.instance = inst
                if inst == 0:
                    seg.key = primary_name
                else:
                    seg.key = f"{primary_name}#{inst}"
            else:
                # Prose-only segment — use line number as key
                seg.key = f"__prose_{seg.start_line}"
            segments.append(seg)
        current_prose = []
        current_chunks = []
        current_chunk_names = []
        primary_name = None

    i = 0
    while i < len(body):
        line = body[i]
        m = CHUNK_DEF.match(line)

        if m:
            chunk_name = m.group(1)

            if chunk_name in APPEND_CHUNKS:
                # This is an appended defines/macros block — attach to current segment
                if not in_chunk:
                    current_chunks.append(line)
                    current_chunk_names.append(chunk_name)
                    in_chunk = True
                    i += 1
                    continue
                else:
                    # We're already in a chunk — this appended block follows
                    current_chunks.append(line)
                    current_chunk_names.append(chunk_name)
                    i += 1
                    continue
            else:
                # This is a primary chunk definition
                if primary_name is not None:
                    # We already have a primary chunk — flush the previous segment
                    # But first, the prose before this chunk belongs to THIS segment
                    # We need to split: prose accumulated after the last @ %def
                    # belongs to the new segment
                    flush_segment()
                    chunk_start_line = movable_start + i

                if primary_name is None and not current_chunks:
                    # First primary chunk in this segment
                    chunk_start_line = movable_start + i - len(current_prose)

                primary_name = chunk_name
                current_chunk_names.append(chunk_name)
                current_chunks.append(line)
                in_chunk = True
                i += 1
                continue

        if in_chunk:
            current_chunks.append(line)
            # Check if this is a @ %def line or a @ doc start
            if PERCENT_DEF.match(line):
                in_chunk = False
            elif line.strip() == '@' or (DOC_START.match(line) and not PERCENT_DEF.match(line)):
                # End of chunk, start of new doc section
                in_chunk = False
                # This line is prose for the next segment
                # But wait — if there's no primary chunk yet, it might be
                # an intermediate @ between appended chunks
                # Let's peek ahead to see if next non-blank is an appended chunk
                pass
            i += 1
            continue

        # We're in prose/doc territory
        if m is None and not in_chunk:
            # Check if this line starts a new primary chunk (already handled above)
            # It's prose — accumulate it
            # But if we have a completed primary chunk (primary_name is set and
            # we're no longer in_chunk), this prose belongs to the NEXT segment
            if primary_name is not None:
                # Check if this is a blank line or a @ line after @ %def
                # Peek ahead: if next chunk is an appended chunk, keep accumulating
                next_chunk_idx = None
                for j in range(i, min(i + 5, len(body))):
                    nm = CHUNK_DEF.match(body[j])
                    if nm:
                        next_chunk_idx = j
                        break
                if next_chunk_idx is not None and CHUNK_DEF.match(body[next_chunk_idx]):
                    next_name = CHUNK_DEF.match(body[next_chunk_idx]).group(1)
                    if next_name in APPEND_CHUNKS:
                        # Keep this in the current segment
                        current_chunks.append(line)
                        i += 1
                        continue

                # This prose belongs to the next segment — flush current
                flush_segment()
                chunk_start_line = movable_start + i
                current_prose.append(line)
            else:
                current_prose.append(line)
            i += 1
            continue

        i += 1

    # Flush any remaining segment
    flush_segment()

    return preamble, segments, postamble


def parse_segments_v2(lines: list[str], movable_start: int, movable_end: int) -> tuple[list[str], list[Segment], list[str]]:
    """Forward-pass parser that groups lines into movable segments.

    Strategy: walk forward through the body, accumulating lines into a
    "buffer". When we encounter a primary chunk definition, we check if
    we already have a primary chunk in the buffer. If so, we flush the
    buffer as a completed segment (up to the start of the new segment's
    prose) and start a new buffer.

    The tricky part is deciding where one segment ends and the next begins
    when there's prose between them. The rule: prose/headers/append-chunks
    that appear AFTER a primary chunk's @ %def (or bare @) belong to the
    NEXT segment.
    """
    preamble = lines[:movable_start]
    postamble = lines[movable_end:]
    body = lines[movable_start:movable_end]

    # Strategy: find all primary chunk definitions, then assign each line
    # to a segment based on proximity to primary chunks.
    #
    # Each primary chunk "owns" all lines from the end of the previous
    # primary chunk's last @ %def/@ to the end of this chunk's last @ %def/@.
    # Any append chunks (<<defines>>=, etc.) and prose between primary chunks
    # go with the NEXT primary chunk, not the previous one.

    segments = []
    instance_counts: dict[str, int] = {}

    # Pass 1: Find all primary chunk positions
    primary_chunks = []  # (line_index, name)
    for i, line in enumerate(body):
        m = CHUNK_DEF.match(line)
        if m and m.group(1) not in APPEND_CHUNKS:
            primary_chunks.append((i, m.group(1)))

    if not primary_chunks:
        if body:
            segments.append(Segment(
                chunk_name=None, lines=body[:],
                start_line=movable_start + 1, key="__prose_body",
            ))
        return preamble, segments, postamble

    # Pass 2: For each primary chunk, find its FIRST end marker (@ %def or
    # bare @). This is where the primary chunk's code ends. Everything after
    # this marker (up to and including the next primary chunk's first end
    # marker) belongs to the NEXT segment.
    #
    # This means prose and append chunks between two primary chunks go with
    # the LATER primary chunk, not the earlier one.

    chunk_first_ends = []
    for pi in range(len(primary_chunks)):
        chunk_line = primary_chunks[pi][0]
        first_end = chunk_line  # fallback
        for j in range(chunk_line + 1, len(body)):
            line = body[j]
            if PERCENT_DEF.match(line) or line.strip() == '@':
                first_end = j
                break
        chunk_first_ends.append(first_end)

    # Build segments: segment pi runs from (prev chunk's first_end + 1) to
    # (this chunk's first_end), inclusive.
    for pi in range(len(primary_chunks)):
        chunk_line, name = primary_chunks[pi]

        if pi == 0:
            start = 0
        else:
            start = chunk_first_ends[pi - 1] + 1

        # End of this segment: if there's a next primary chunk, this segment
        # extends to include all content up through its own last @ %def/@ that
        # precedes the next primary chunk. But actually, with our approach:
        # this segment ends at this chunk's first_end.
        # EXCEPT: any append chunks after the primary chunk's first_end but
        # before the next primary chunk should go with this segment.
        # NO — they should go with the NEXT segment (that's our rule).
        #
        # Actually the rule is simpler: each segment includes everything from
        # (prev_first_end + 1) through (this_first_end). All intervening
        # prose and append chunks between the prev primary chunk's end and
        # this primary chunk become preamble for this segment.
        end = chunk_first_ends[pi] + 1  # exclusive

        # For the last segment, include everything to end of body
        if pi == len(primary_chunks) - 1:
            end = len(body)

        seg_lines = body[start:end]

        # Collect all chunk names
        all_names = []
        for line in seg_lines:
            m = CHUNK_DEF.match(line)
            if m:
                all_names.append(m.group(1))

        inst = instance_counts.get(name, 0)
        instance_counts[name] = inst + 1

        seg = Segment(
            chunk_name=name,
            all_chunk_names=all_names,
            lines=seg_lines,
            start_line=movable_start + start + 1,
            instance=inst,
            key=name if inst == 0 else f"{name}#{inst}",
        )
        segments.append(seg)

    return preamble, segments, postamble


def find_boundaries(lines: list[str]) -> tuple[int, int]:
    """Find the movable region boundaries.

    Returns (movable_start, movable_end) as 0-based line indices.
    movable_start = first line after Part I (after Startup chapter content)
    movable_end = first line of <<main.asm>>= root chunk
    """
    movable_start = None
    movable_end = None

    # Find the start of the movable region:
    # After the "Startup" chapter content — look for \chapter{Apple II Graphics}
    # or the first content after line ~1760
    for i, line in enumerate(lines):
        if '\\chapter{Apple II Graphics}' in line:
            movable_start = i
            break
        # Fallback: look for the chapter that follows Startup
        if movable_start is None and i > 1600:
            if line.startswith('\\chapter{') and 'Startup' not in line and 'boot' not in line.lower():
                movable_start = i
                break

    # Find the end of the movable region:
    # The line where <<main.asm>>= begins
    for i, line in enumerate(lines):
        if line.strip().startswith('@ \\chapter{Assembly output}'):
            movable_end = i
            break
        if line.strip() == '<<main.asm>>=':
            # Back up to include the chapter header
            for j in range(i - 1, max(i - 10, 0), -1):
                if 'chapter{' in lines[j] or lines[j].strip().startswith('@ \\chapter'):
                    movable_end = j
                    break
            else:
                movable_end = i
            break

    if movable_start is None:
        raise ValueError("Could not find movable region start")
    if movable_end is None:
        raise ValueError("Could not find movable region end (<<main.asm>>=)")

    return movable_start, movable_end


def load_ordering(path: str) -> list[dict]:
    """Load ordering specification from a text file.

    Format:
      # Comments start with #
      ## Chapter Title        -> inserts \\chapter{Title}
      ### Section Title       -> inserts \\section{Title}
      #### Subsection Title   -> inserts \\subsection{Title}
      chunk_name              -> places the segment for this chunk
      chunk_name#1            -> places the 2nd instance of an appended chunk
      ---                     -> blank line separator
      @@ prose text           -> inserts literal prose (@ text)
      > literal line          -> inserts a literal line as-is

    Returns list of dicts with keys: type, value
    """
    entries = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n').rstrip('\r')
            if not line or line.startswith('#!'):
                continue
            if line.startswith('####'):
                title = line[4:].strip()
                entries.append({'type': 'subsection', 'value': title})
            elif line.startswith('###'):
                title = line[3:].strip()
                entries.append({'type': 'section', 'value': title})
            elif line.startswith('## '):
                title = line[3:].strip()
                entries.append({'type': 'chapter', 'value': title})
            elif line.startswith('#'):
                continue  # comment
            elif line.strip() == '---':
                entries.append({'type': 'blank', 'value': ''})
            elif line.startswith('@@'):
                entries.append({'type': 'prose', 'value': line[2:].strip()})
            elif line.startswith('>'):
                entries.append({'type': 'literal', 'value': line[1:]})
            else:
                chunk_name = line.strip()
                if chunk_name:
                    entries.append({'type': 'chunk', 'value': chunk_name})
    return entries


def reorder(input_path: str, ordering_path: str, output_path: str | None = None):
    """Main reorder function."""
    with open(input_path, 'r', encoding='cp1252') as f:
        lines = f.readlines()

    movable_start, movable_end = find_boundaries(lines)
    print(f"Movable region: lines {movable_start + 1}–{movable_end}", file=sys.stderr)

    preamble, segments, postamble = parse_segments_v2(lines, movable_start, movable_end)
    print(f"Parsed {len(segments)} segments", file=sys.stderr)

    # Build lookup by key
    seg_by_key: dict[str, Segment] = {}
    for seg in segments:
        if seg.key in seg_by_key:
            print(f"WARNING: duplicate key '{seg.key}' at lines {seg_by_key[seg.key].start_line} and {seg.start_line}", file=sys.stderr)
        seg_by_key[seg.key] = seg

    # Load ordering
    ordering = load_ordering(ordering_path)

    # Build output
    out_lines = preamble[:]

    placed_keys = set()
    for entry in ordering:
        if entry['type'] == 'chapter':
            out_lines.append(f"\n\\chapter{{{entry['value']}}}\n\n")
        elif entry['type'] == 'section':
            out_lines.append(f"\n\\section{{{entry['value']}}}\n\n")
        elif entry['type'] == 'subsection':
            out_lines.append(f"\n\\subsection{{{entry['value']}}}\n\n")
        elif entry['type'] == 'blank':
            out_lines.append('\n')
        elif entry['type'] == 'prose':
            out_lines.append(f"@ {entry['value']}\n\n")
        elif entry['type'] == 'literal':
            out_lines.append(entry['value'] + '\n')
        elif entry['type'] == 'chunk':
            key = entry['value']
            if key in seg_by_key:
                seg = seg_by_key[key]
                # Strip leading blank lines from segment
                seg_lines = seg.lines[:]
                while seg_lines and seg_lines[0].strip() == '':
                    seg_lines.pop(0)
                # Strip existing chapter/section headers from the segment
                # (we're inserting our own)
                cleaned = strip_structural_headers(seg_lines)
                out_lines.extend(cleaned)
                placed_keys.add(key)
            else:
                print(f"WARNING: chunk '{key}' not found in segments", file=sys.stderr)
                # Try fuzzy match
                for sk in seg_by_key:
                    if sk.replace(' ', '_') == key.replace(' ', '_'):
                        print(f"  Did you mean '{sk}'?", file=sys.stderr)

    # Check for unplaced segments
    unplaced = [seg for seg in segments if seg.key not in placed_keys]
    if unplaced:
        print(f"\nWARNING: {len(unplaced)} unplaced segments:", file=sys.stderr)
        for seg in unplaced:
            names = seg.chunk_name or "(prose-only)"
            print(f"  key='{seg.key}' chunk='{names}' line={seg.start_line}", file=sys.stderr)
        # Append unplaced segments at the end (before postamble)
        out_lines.append("\n@ \\section{Unplaced segments}\n\n")
        for seg in unplaced:
            out_lines.extend(seg.lines)

    out_lines.extend(postamble)

    # Write output
    if output_path:
        with open(output_path, 'w', encoding='cp1252') as f:
            f.writelines(out_lines)
    else:
        sys.stdout.buffer.write(''.join(out_lines).encode('cp1252'))


def strip_structural_headers(lines: list[str]) -> list[str]:
    """Remove \\chapter{}, \\section{}, \\subsection{} lines from segment.

    These will be replaced by the ordering spec's own headers.
    But keep \\subsubsection{} and \\paragraph{} as they're chunk-internal.
    Also keep \\label{} lines.
    """
    result = []
    skip_blank_after = False
    for line in lines:
        stripped = line.strip()
        # Remove @ \chapter{...} lines (the @ prefix form)
        if stripped.startswith('@ \\chapter{') or stripped.startswith('@ \\section{') or stripped.startswith('@ \\subsection{'):
            skip_blank_after = True
            continue
        # Remove bare \chapter{...} lines
        if stripped.startswith('\\chapter{') or stripped.startswith('\\section{') or stripped.startswith('\\subsection{'):
            skip_blank_after = True
            continue
        # Skip blank lines immediately after removed headers
        if skip_blank_after and stripped == '':
            skip_blank_after = False
            continue
        skip_blank_after = False
        result.append(line)
    return result


def list_segments(input_path: str):
    """List all segments in the file (for debugging)."""
    with open(input_path, 'r', encoding='cp1252') as f:
        lines = f.readlines()

    movable_start, movable_end = find_boundaries(lines)
    print(f"Movable region: lines {movable_start + 1}–{movable_end}")

    preamble, segments, postamble = parse_segments_v2(lines, movable_start, movable_end)

    for seg in segments:
        names = ', '.join(seg.all_chunk_names) if seg.all_chunk_names else '(prose-only)'
        first_line = seg.lines[0].rstrip() if seg.lines else ''
        print(f"  L{seg.start_line:5d}  key={seg.key!r:40s}  chunks=[{names}]")
        if len(first_line) > 80:
            first_line = first_line[:77] + '...'
        print(f"         first: {first_line}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python reorder_nw.py --list main.nw")
        print("  python reorder_nw.py main.nw ordering.txt [output.nw]")
        sys.exit(1)

    if sys.argv[1] == '--list':
        list_segments(sys.argv[2])
    else:
        input_path = sys.argv[1]
        ordering_path = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        reorder(input_path, ordering_path, output_path)
