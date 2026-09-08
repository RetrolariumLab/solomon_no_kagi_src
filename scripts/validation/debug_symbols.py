#!/usr/bin/env python3
"""Validate ld65 debug metadata and export debugger-friendly symbol files."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

from scripts.build.atomic_io import atomic_write_text


RECORD_FIELD_RE = re.compile(r'(?:^|,)([a-z]+)=("(?:[^"]|"")*"|[^,]*)')
VICE_LABEL_RE = re.compile(r"^al ([0-9A-Fa-f]{6}) \.([A-Za-z_][A-Za-z0-9_]*)$")
CONFIDENCE_LEVELS = frozenset({"tentative", "high", "confirmed"})


class SymbolError(ValueError):
    """A debugger-artifact validation error."""


def parse_record(line: str) -> tuple[str, dict[str, str]]:
    """Parse one record from an ld65 .dbg file."""

    kind, separator, payload = line.partition("\t")
    if not separator:
        return kind, {}
    fields: dict[str, str] = {}
    for match in RECORD_FIELD_RE.finditer(payload):
        value = match.group(2)
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1].replace('""', '"')
        fields[match.group(1)] = value
    return kind, fields


def load_vice_labels(path: Path) -> dict[str, int]:
    """Load the symbol-to-address mapping written by ld65's -Ln option."""

    labels: dict[str, int] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = VICE_LABEL_RE.fullmatch(line)
        if not match:
            if line.strip():
                raise SymbolError(f"unsupported label line {path}:{line_number}: {line}")
            continue
        address = int(match.group(1), 16)
        name = match.group(2)
        if name in labels and labels[name] != address:
            raise SymbolError(f"label {name} has conflicting addresses")
        labels[name] = address
    if not labels:
        raise SymbolError(f"label file is empty: {path}")
    return labels


def load_debug_file(path: Path) -> tuple[dict[str, int], dict[str, int], dict[int, str]]:
    """Return record counts, all symbol values, and source file names."""

    counts: dict[str, int] = defaultdict(int)
    symbols: dict[str, int] = {}
    files: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        kind, fields = parse_record(line)
        counts[kind] += 1
        if kind == "file" and {"id", "name"} <= fields.keys():
            files[int(fields["id"], 0)] = fields["name"]
        if kind != "sym" or not {"name", "val"} <= fields.keys():
            continue
        name = fields["name"]
        address = int(fields["val"], 0)
        if name in symbols and symbols[name] != address:
            raise SymbolError(f"debug symbol {name} has conflicting addresses")
        symbols[name] = address
    return dict(counts), symbols, files


def load_config(path: Path, group: str) -> list[dict[str, object]]:
    """Load one versioned breakpoint or watch configuration."""

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SymbolError(f"cannot read {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise SymbolError(f"unsupported debugger config schema: {path}")
    entries = document.get(group)
    if not isinstance(entries, list) or not entries:
        raise SymbolError(f"{path} must contain a non-empty {group} list")
    if not all(isinstance(entry, dict) for entry in entries):
        raise SymbolError(f"invalid entry in {path}")
    return entries


def parse_config_address(
    entry: dict[str, object], path: Path, profile: str | None = None
) -> int:
    value = entry.get("address")
    profile_addresses = entry.get("profile_addresses", {})
    if not isinstance(profile_addresses, dict) or not all(
        isinstance(name, str) and isinstance(address, (int, str))
        for name, address in profile_addresses.items()
    ):
        raise SymbolError(f"invalid profile_addresses in {path}: {profile_addresses!r}")
    if profile is not None and profile in profile_addresses:
        value = profile_addresses[profile]
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise SymbolError(f"invalid address in {path}: {value!r}") from exc


def resolve_config(
    path: Path,
    group: str,
    symbols: dict[str, int],
    vice_labels: dict[str, int],
    profile: str | None = None,
) -> list[dict[str, object]]:
    """Bind debugger config entries to current linker-produced addresses."""

    resolved: list[dict[str, object]] = []
    identities: set[tuple[str, int, int]] = set()
    for entry in load_config(path, group):
        symbol = entry.get("symbol")
        name = entry.get("name")
        confidence = entry.get("confidence")
        if not isinstance(symbol, str) or not symbol:
            raise SymbolError(f"entry lacks symbol in {path}: {entry!r}")
        if not isinstance(name, str) or not name:
            raise SymbolError(f"entry lacks name in {path}: {entry!r}")
        if confidence not in CONFIDENCE_LEVELS:
            raise SymbolError(f"invalid confidence for {symbol} in {path}")
        if symbol not in symbols:
            raise SymbolError(f"unknown debug symbol {symbol} in {path}")
        address = parse_config_address(entry, path, profile)
        if symbols[symbol] != address:
            raise SymbolError(
                f"stale address for {symbol}: config ${address:04X}, "
                f"linker ${symbols[symbol]:04X}"
            )
        size = 1
        if group == "breakpoints":
            if entry.get("kind") != "execute" or address < 0x8000:
                raise SymbolError(f"invalid execute breakpoint for {symbol}")
            if vice_labels.get(symbol) != address:
                raise SymbolError(f"breakpoint {symbol} is missing from the VICE labels")
        else:
            size_value = entry.get("size")
            if not isinstance(size_value, int) or size_value <= 0:
                raise SymbolError(f"invalid watch size for {symbol}")
            size = size_value
            if address < 0 or address + size > 0x0800:
                raise SymbolError(f"watch range for {symbol} is outside internal RAM")
        identity = (name, address, size)
        if identity in identities:
            raise SymbolError(f"duplicate debugger entry in {path}: {name}")
        identities.add(identity)
        normalized = dict(entry)
        normalized["address"] = address
        normalized["address_hex"] = f"${address:04X}"
        resolved.append(normalized)
    return resolved


def validate_debug_artifacts(
    debug_path: Path,
    map_path: Path,
    labels_path: Path,
) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    """Validate source mappings and agreement between ld65 artifacts."""

    counts, debug_symbols, files = load_debug_file(debug_path)
    for kind in ("file", "line", "span", "sym"):
        if counts.get(kind, 0) == 0:
            raise SymbolError(f"debug file has no {kind} records")
    normalized_files = {name.replace("\\", "/") for name in files.values()}
    required_sources = {
        "src/main.asm",
        "src/memory/ram.inc",
        "src/system/thread_runtime.asm",
        "src/game/flow/runtime.asm",
    }
    missing_sources = sorted(required_sources - normalized_files)
    if missing_sources:
        raise SymbolError("debug file lacks source mappings: " + ", ".join(missing_sources))
    map_text = map_path.read_text(encoding="utf-8")
    for segment in ("PRG_NMI", "PRG_MAIN_THREAD", "PRG_LATE_ENEMY_AI", "VECTORS"):
        if segment not in map_text:
            raise SymbolError(f"linker map lacks segment {segment}")
    vice_labels = load_vice_labels(labels_path)
    for name, address in vice_labels.items():
        if name in debug_symbols and debug_symbols[name] != address:
            raise SymbolError(f"debug and VICE addresses disagree for {name}")
    return counts, debug_symbols, vice_labels


def choose_unique_addresses(symbols: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Choose one stable, semantic name at each address for FCEUX .nl files."""

    names_by_address: dict[int, list[str]] = defaultdict(list)
    for address, name in symbols:
        names_by_address[address].append(name)
    return [
        (address, min(names, key=lambda item: (item.startswith("_"), len(item), item)))
        for address, names in sorted(names_by_address.items())
    ]


def write_fceux_labels(
    output_dir: Path,
    rom_name: str,
    vice_labels: dict[str, int],
    debug_symbols: dict[str, int],
    ram_symbols: set[str],
) -> tuple[Path, Path]:
    """Export ROM labels and the reviewed RAM watch anchors for FCEUX."""

    output_dir.mkdir(parents=True, exist_ok=True)
    rom_path = output_dir / f"{rom_name}.0.nl"
    ram_path = output_dir / f"{rom_name}.ram.nl"
    groups = (
        (rom_path, [(address, name) for name, address in vice_labels.items() if address >= 0x8000]),
        (
            ram_path,
            [
                (debug_symbols[name], name)
                for name in ram_symbols
                if debug_symbols[name] < 0x0800
            ],
        ),
    )
    for output_path, entries in groups:
        lines = [f"${address:04X}#{name}#\n" for address, name in choose_unique_addresses(entries)]
        atomic_write_text(output_path, "".join(lines))
    return rom_path, ram_path


def expected_summary(args: argparse.Namespace) -> dict[str, object]:
    counts, debug_symbols, vice_labels = validate_debug_artifacts(
        args.debug, args.map, args.labels
    )
    breakpoints = resolve_config(
        args.breakpoints, "breakpoints", debug_symbols, vice_labels, args.profile
    )
    watches = resolve_config(
        args.watches, "watches", debug_symbols, vice_labels, args.profile
    )
    rom_labels, ram_labels = write_fceux_labels(
        args.output_dir,
        args.rom_name,
        vice_labels,
        debug_symbols,
        {str(entry["symbol"]) for entry in watches},
    )
    return {
        "schema_version": 1,
        "debug_file": args.debug.as_posix(),
        "map_file": args.map.as_posix(),
        "labels_file": args.labels.as_posix(),
        "fceux_rom_labels": rom_labels.as_posix(),
        "fceux_ram_labels": ram_labels.as_posix(),
        "records": {kind: counts[kind] for kind in sorted(counts)},
        "breakpoints": breakpoints,
        "watches": watches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug", required=True, type=Path)
    parser.add_argument("--map", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--breakpoints", required=True, type=Path)
    parser.add_argument("--watches", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--rom-name", required=True)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument(
        "--profile",
        help="select optional per-profile addresses while retaining base defaults",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        summary = expected_summary(args)
        serialized = json.dumps(summary, indent=2) + "\n"
        if args.check:
            if not args.summary.is_file() or args.summary.read_text(encoding="utf-8") != serialized:
                raise SymbolError(f"stale debugger symbol summary: {args.summary}")
        else:
            atomic_write_text(args.summary, serialized)
    except (OSError, SymbolError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(
        f"[OK] debugger symbols: {len(summary['breakpoints'])} breakpoints, "
        f"{len(summary['watches'])} watches, {summary['records']['sym']} symbols"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
