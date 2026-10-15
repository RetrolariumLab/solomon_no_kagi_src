#!/usr/bin/env python3
"""Write a relocated copy of the source: one $EA byte at the end of every
segment placed before the filler that precedes the audio code, so each segment
moves a little further than the one before, and that filler shrinks by as many
bytes, so the audio code and the vectors stay put. A build that still plays
the attract mode shows that nothing depends on the original addresses.
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
# Segments whose size or position another segment asserts.
FIXED = {"PRG_ENEMY_LIFETIME"}


class RelocationError(ValueError):
    """The source does not have the shape the relocation expects."""


def moved_segments(linker_config: Path) -> list[str]:
    names = [match.group("name") for line in linker_config.read_text(encoding="utf-8").splitlines()
             if (match := SEGMENT_RE.match(line))]
    if FILLER_SEGMENT not in names:
        raise RelocationError(f"{linker_config.name} has no {FILLER_SEGMENT}")
    return [name for name in names[:names.index(FILLER_SEGMENT)] if name not in FIXED]


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
    """ca65 opens an include relative to the including file."""
    return Path(os.path.relpath(path, output.resolve().parent)).as_posix()


def relocate(main_source: Path, linker_config: Path, output: Path, only: int | None = None) -> int:
    source_root = main_source.resolve().parent
    segments = moved_segments(linker_config)
    if only is not None:
        segments = segments[only:only + 1]
    elif len(segments) >= FILLER_SIZE:
        segments = segments[::-(-len(segments) // (FILLER_SIZE - 4))]
    output.parent.mkdir(parents=True, exist_ok=True)
    filler = output.parent / Path(FILLER_MODULE).name
    filler.write_text(shrink_filler((source_root / FILLER_MODULE).read_text(encoding="utf-8"), len(segments)),
                      encoding="utf-8", newline="\n")
    lines: list[str] = []
    for line in main_source.read_text(encoding="utf-8").splitlines():
        match = INCLUDE_RE.fullmatch(line)
        if match is None:
            lines.append(line)
            continue
        path = filler if match.group("path") == FILLER_MODULE else (source_root / match.group("path")).resolve()
        lines.append(f'{match.group("indent")}.include "{include_path(path, output)}"{match.group("tail")}')
    lines.append("")
    lines.append("; Relocation: one byte at the end of each segment before the audio filler.")
    for name in segments:
        lines.append(f'.segment "{name}"')
        lines.append("    .byte $EA")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return len(segments)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--main", type=Path, required=True, help="src/main.asm")
    parser.add_argument("--linker-config", type=Path, required=True, help="config/linker/cnrom.cfg")
    parser.add_argument("--output", type=Path, required=True, help="the relocated main source")
    parser.add_argument("--only", type=int, help="move only what follows this one segment (for bisecting)")
    args = parser.parse_args()
    try:
        count = relocate(args.main, args.linker_config, args.output, args.only)
    except (OSError, RelocationError) as exc:
        print(f"[ERROR] {exc}")
        return 1
    print(f"[OK] Relocated source: {count} segments moved by 1 to {count} bytes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
