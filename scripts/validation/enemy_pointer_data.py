#!/usr/bin/env python3
"""Decode and audit the split enemy/object record pointer tables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.authoring.room_data import RoomDataError, extract_prg


PRG_BASE = 0x8000
ENEMY_POINTER_MANIFESTS = {
    "usa": "enemy_record_pointers.json",
    "europe": "enemy_record_pointers_europe.json",
}


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


def decode_split_pointer_table(
    prg: bytes, low_address: int, high_address: int, count: int
) -> list[int]:
    if count <= 0:
        raise RoomDataError(f"pointer count must be positive: {count}")
    low_offset = prg_offset(low_address)
    high_offset = prg_offset(high_address)
    if low_offset + count > len(prg) or high_offset + count > len(prg):
        raise RoomDataError(
            f"truncated split pointer table at ${low_address:04X}/${high_address:04X}"
        )
    return [
        prg[low_offset + index] | (prg[high_offset + index] << 8)
        for index in range(count)
    ]


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RoomDataError("unsupported enemy pointer manifest schema")
    tables = value.get("tables")
    if not isinstance(tables, list) or not tables:
        raise RoomDataError("enemy pointer manifest tables must be a non-empty list")
    return value


def validate_manifest_profile(manifest: dict[str, Any], profile: str) -> None:
    actual = manifest.get("profile", "usa")
    if actual != profile:
        raise RoomDataError(
            f"enemy pointer profile mismatch: expected={profile}, manifest={actual}"
        )


def collect_report(prg: bytes, manifest: dict[str, Any]) -> dict[str, object]:
    reports: list[dict[str, object]] = []
    for table in manifest["tables"]:
        if not isinstance(table, dict):
            raise RoomDataError("enemy pointer table declaration must be an object")
        table_id = str(table.get("id", ""))
        if not table_id:
            raise RoomDataError("enemy pointer table id must not be empty")
        low_address = parse_number(table.get("low_address"), f"{table_id}.low_address")
        high_address = parse_number(
            table.get("high_address"), f"{table_id}.high_address"
        )
        count = parse_number(table.get("count"), f"{table_id}.count")
        reports.append(
            {
                "id": table_id,
                "low_address": low_address,
                "high_address": high_address,
                "pointers": decode_split_pointer_table(
                    prg, low_address, high_address, count
                ),
            }
        )
    return {"tables": reports}


def validate_report(
    report: dict[str, object], manifest: dict[str, Any]
) -> list[str]:
    actual_tables = report.get("tables")
    if not isinstance(actual_tables, list):
        return ["report has no table list"]
    errors: list[str] = []
    for declaration, actual in zip(manifest["tables"], actual_tables):
        if not isinstance(declaration, dict) or not isinstance(actual, dict):
            errors.append("invalid table record")
            continue
        table_id = str(declaration.get("id", ""))
        base = parse_number(declaration.get("base_address"), f"{table_id}.base")
        stride = parse_number(declaration.get("stride"), f"{table_id}.stride")
        count = parse_number(declaration.get("count"), f"{table_id}.count")
        expected = [base + index * stride for index in range(count)]
        pointers = actual.get("pointers")
        if pointers != expected:
            errors.append(
                f"{table_id} pointers differ: got {pointers!r}, expected {expected!r}"
            )
    if len(actual_tables) != len(manifest["tables"]):
        errors.append(
            f"table count differs: got {len(actual_tables)}, "
            f"expected {len(manifest['tables'])}"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "audit"))
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--profile", choices=tuple(ENEMY_POINTER_MANIFESTS), default="usa"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    manifest_path = args.manifest or (
        root / "config" / ENEMY_POINTER_MANIFESTS[args.profile]
    )
    try:
        manifest = load_manifest(manifest_path)
        validate_manifest_profile(manifest, args.profile)
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
        print(f"[FAIL] Enemy pointer audit found {len(errors)} error(s)", file=sys.stderr)
        return 1
    counts = [len(table["pointers"]) for table in report["tables"]]
    print(f"[OK] Enemy record pointers: {counts[0]} AI and {counts[1]} object records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
