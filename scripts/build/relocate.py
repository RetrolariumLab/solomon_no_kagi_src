#!/usr/bin/env python3
"""Write a relocated copy of a revision's source: one $EA byte at the end of
the segments placed before the filler that precedes the audio code (every
segment, or every n-th when there are more than the filler can absorb), so
each moves a little further than the one before, and that filler shrinks by
as many bytes, so the audio code and the vectors stay put. The attract mode
playing on such a build shows the moved code does not depend on its original
addresses (as far as that mode runs it).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re

INCLUDE_RE = re.compile(r'^(?P<indent>\s*)\.include "(?P<path>[^"]+)"(?P<tail>.*)$')
SEGMENT_RE = re.compile(r"^\s*(?P<name>PRG_\w+):\s*load\s*=\s*PRG\b")
FILLER_SEGMENT = "PRG_FILLER_BEFORE_AUDIO"
FILLER_MODULE = "data/rooms/items.asm"
FILLER_SIZE = 0x3C
# The probes the filler can absorb, leaving it a few bytes.
MOST_PROBES = FILLER_SIZE - 4
# Segments whose size or position another segment asserts.
FIXED = {"PRG_ENEMY_LIFETIME"}


class RelocationError(ValueError):
    """The source does not have the shape the relocation expects."""


def candidate_segments(linker_config: Path) -> list[str]:
    """Every segment before the audio filler that may move."""
    names = [
        match.group("name")
        for line in linker_config.read_text(encoding="utf-8").splitlines()
        if (match := SEGMENT_RE.match(line))
    ]
    if FILLER_SEGMENT not in names:
        raise RelocationError(f"{linker_config.name} has no {FILLER_SEGMENT}")
    return [name for name in names[: names.index(FILLER_SEGMENT)] if name not in FIXED]


def moved_segments(linker_config: Path) -> list[str]:
    """The segments that get a probe: all candidates, or every n-th with the
    smallest n that keeps them within MOST_PROBES."""
    candidates = candidate_segments(linker_config)
    step = -(-len(candidates) // MOST_PROBES)
    return candidates[::step]


def shrink_filler(source: str, count: int) -> str:
    """Drop count bytes from the end of the filler's byte lines and adjust its
    size assertion; the Europe branch reserves fewer bytes."""
    lines = source.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == f'.segment "{FILLER_SEGMENT}"')
    end = next(i for i in range(start, len(lines)) if lines[i].strip() == ".endif")
    body = [i for i in range(start, end) if lines[i].strip().startswith(".byte")]
    removed = 0
    for index in reversed(body):
        if removed == count:
            break
        values = lines[index].strip().removeprefix(".byte").split(",")
        keep = max(0, len(values) - (count - removed))
        removed += len(values) - keep
        lines[index] = "    .byte" + ",".join(values[:keep]) if keep else ""
    if removed != count:
        raise RelocationError(f"the filler holds fewer than {count} bytes")
    text = "\n".join(lines) + "\n"
    old_res = f"    .res ${FILLER_SIZE:04X}, $FF"
    old_assert = f"= ${FILLER_SIZE:04X}, error"
    if old_res not in text or old_assert not in text:
        raise RelocationError("the filler's size is not the expected one")
    text = text.replace(old_res, f"    .res ${FILLER_SIZE - count:04X}, $FF")
    return text.replace(old_assert, f"= ${FILLER_SIZE - count:04X}, error")


def include_path(path: Path, output: Path) -> str:
    """ca65 opens an include relative to the including file (or by its full
    path when the two are on different drives)."""
    try:
        return Path(os.path.relpath(path, output.resolve().parent)).as_posix()
    except ValueError:
        return path.as_posix()


def rewrite_includes(source: Path, output: Path, replacements: dict[Path, Path]) -> list[str]:
    """The lines of source with each include pointing at the same file from
    output, or at its replacement."""
    lines = []
    for line in source.read_text(encoding="utf-8").splitlines():
        match = INCLUDE_RE.fullmatch(line)
        if match is None:
            lines.append(line)
            continue
        path = (source.resolve().parent / match.group("path")).resolve()
        path = replacements.get(path, path)
        lines.append(f'{match.group("indent")}.include "{include_path(path, output)}"{match.group("tail")}')
    return lines


def relocate(entry: Path, linker_config: Path, output_dir: Path, only: int | None = None) -> int:
    """Write output_dir/<entry's name> (the entry, including the relocated
    main), output_dir/main.asm and the shrunk filler module."""
    main_source = entry.resolve().parent.parent / "main.asm"
    if not main_source.is_file():
        raise RelocationError(f"{entry} is not in src/revisions/ beside src/main.asm")
    source_root = main_source.parent
    segments = moved_segments(linker_config)
    if only is not None:
        if not 0 <= only < len(segments):
            raise RelocationError(f"--only takes 0 to {len(segments) - 1}: {len(segments)} segments move")
        segments = segments[only : only + 1]
    output_dir.mkdir(parents=True, exist_ok=True)
    filler = output_dir / Path(FILLER_MODULE).name
    filler.write_text(
        shrink_filler((source_root / FILLER_MODULE).read_text(encoding="utf-8"), len(segments)),
        encoding="utf-8",
        newline="\n",
    )
    main_output = output_dir / "main.asm"
    lines = rewrite_includes(main_source, main_output, {(source_root / FILLER_MODULE).resolve(): filler})
    lines.append("")
    lines.append("; Relocation: one byte at the end of each moved segment.")
    for name in segments:
        lines.append(f'.segment "{name}"')
        lines.append("    .byte $EA")
    main_output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    entry_output = output_dir / entry.name
    entry_lines = rewrite_includes(entry, entry_output, {main_source.resolve(): main_output})
    entry_output.write_text("\n".join(entry_lines) + "\n", encoding="utf-8", newline="\n")
    return len(segments)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--entry", type=Path, required=True, help="a revision's src/revisions/<id>.asm")
    parser.add_argument("--linker-config", type=Path, required=True, help="config/linker/cnrom.cfg")
    parser.add_argument("--output-dir", type=Path, required=True, help="where the relocated sources go")
    parser.add_argument("--only", type=int, help="probe only this one of the moved segments (for bisecting)")
    args = parser.parse_args()
    try:
        count = relocate(args.entry, args.linker_config, args.output_dir, args.only)
    except (OSError, RelocationError) as exc:
        print(f"[ERROR] {exc}")
        return 1
    print(f"[OK] Relocated source: {count} segments moved by 1 to {count} bytes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
