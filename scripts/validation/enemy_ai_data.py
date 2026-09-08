#!/usr/bin/env python3
"""Decode and audit the inline enemy-AI handler appendix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.authoring.room_data import RoomDataError, extract_prg


PRG_BASE = 0x8000


def parse_number(value: object, field: str) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    raise RoomDataError(f"invalid integer for {field}: {value!r}")


def prg_offset(cpu_address: int) -> int:
    if not PRG_BASE <= cpu_address <= 0xFFFF:
        raise RoomDataError(f"CPU address outside PRG: ${cpu_address:04X}")
    return cpu_address - PRG_BASE


def decode_handler_table(prg: bytes, address: int, count: int) -> list[int]:
    if count < 0:
        raise RoomDataError(f"negative handler count: {count}")
    offset = prg_offset(address)
    end = offset + count * 2
    if end > len(prg):
        raise RoomDataError(f"truncated handler table at ${address:04X}")
    return [prg[index] | (prg[index + 1] << 8) for index in range(offset, end, 2)]


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RoomDataError("unsupported enemy AI manifest schema")
    handlers = value.get("handlers")
    if not isinstance(handlers, list) or not handlers:
        raise RoomDataError("enemy AI manifest handlers must be a non-empty list")
    return value


def collect_report(prg: bytes, manifest: dict[str, Any]) -> dict[str, object]:
    dispatcher = parse_number(manifest.get("dispatcher_address"), "dispatcher_address")
    table = parse_number(manifest.get("table_address"), "table_address")
    expected = manifest["handlers"]
    handlers = decode_handler_table(prg, table, len(expected))
    return {
        "dispatcher_address": dispatcher,
        "table_address": table,
        "handler_count": len(handlers),
        "unique_handler_count": len(set(handlers)),
        "handlers": handlers,
    }


def validate_report(report: dict[str, object], manifest: dict[str, Any]) -> list[str]:
    expected = [parse_number(value, "handlers") for value in manifest["handlers"]]
    actual = report["handlers"]
    if actual == expected:
        return []
    errors: list[str] = []
    for index, (actual_value, expected_value) in enumerate(zip(actual, expected)):
        if actual_value != expected_value:
            errors.append(
                f"handler {index} differs: got ${actual_value:04X}, "
                f"expected ${expected_value:04X}"
            )
    if len(actual) != len(expected):
        errors.append(f"handler count differs: got {len(actual)}, expected {len(expected)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "audit"))
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    manifest_path = args.manifest or root / "config" / "validation" / "enemy_ai_handlers.json"
    try:
        manifest = load_manifest(manifest_path)
        report = collect_report(extract_prg(args.image.read_bytes()), manifest)
        if args.command == "report":
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0
        errors = validate_report(report, manifest)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, RoomDataError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        print(f"[FAIL] Enemy AI handler audit found {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(
        f"[OK] Enemy AI handlers: {report['handler_count']} entries, "
        f"{report['unique_handler_count']} unique targets"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
