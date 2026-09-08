#!/usr/bin/env python3
"""Decode and audit the 29-entry item-interaction handler appendix."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from scripts.authoring.room_data import RoomDataError, extract_prg
from scripts.validation.enemy_ai_data import decode_handler_table, parse_number, prg_offset


ITEM_HANDLER_MANIFESTS = {
    "usa": "item_handlers.json",
    "europe": "item_handlers_europe.json",
}


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RoomDataError("unsupported item handler manifest schema")
    handlers = value.get("handlers")
    if not isinstance(handlers, list) or not handlers:
        raise RoomDataError("item handler manifest handlers must be a non-empty list")
    for index, handler in enumerate(handlers):
        if not isinstance(handler, dict):
            raise RoomDataError(f"item handler {index} must be an object")
        if not isinstance(handler.get("name"), str) or not handler["name"]:
            raise RoomDataError(f"item handler {index} needs a name")
        parse_number(handler.get("address"), f"handler {index} address")
    return value


def validate_manifest_profile(manifest: dict[str, Any], profile: str) -> None:
    actual = manifest.get("profile", "usa")
    if actual != profile:
        raise RoomDataError(
            f"item handler profile mismatch: expected={profile}, manifest={actual}"
        )


def collect_report(prg: bytes, manifest: dict[str, Any]) -> dict[str, object]:
    table_address = parse_number(manifest.get("table_address"), "table_address")
    first_map_tile = parse_number(manifest.get("first_map_tile"), "first_map_tile")
    declarations = manifest["handlers"]
    handlers = decode_handler_table(prg, table_address, len(declarations))
    table_offset = prg_offset(table_address)
    encoded = prg[table_offset : table_offset + len(handlers) * 2]
    return {
        "table_address": table_address,
        "table_end_address": table_address + len(encoded) - 1,
        "table_sha1": hashlib.sha1(encoded).hexdigest(),
        "handler_count": len(handlers),
        "unique_handler_count": len(set(handlers)),
        "entries": [
            {
                "selector": index,
                "map_tile": first_map_tile + index,
                "name": declaration["name"],
                "address": address,
            }
            for index, (declaration, address) in enumerate(zip(declarations, handlers))
        ],
    }


def validate_report(report: dict[str, object], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_hash = manifest.get("table_sha1")
    if report.get("table_sha1") != expected_hash:
        errors.append(
            f"item handler table SHA-1 differs: got {report.get('table_sha1')}, "
            f"expected {expected_hash}"
        )
    entries = report.get("entries", [])
    declarations = manifest["handlers"]
    if len(entries) != len(declarations):
        errors.append(
            f"item handler count differs: got {len(entries)}, expected {len(declarations)}"
        )
    for index, (entry, declaration) in enumerate(zip(entries, declarations)):
        expected_address = parse_number(declaration.get("address"), f"handler {index} address")
        if entry["address"] != expected_address:
            errors.append(
                f"item handler {index} ({declaration['name']}) differs: "
                f"got ${entry['address']:04X}, expected ${expected_address:04X}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "audit"))
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--profile", choices=tuple(ITEM_HANDLER_MANIFESTS), default="usa"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    manifest_path = args.manifest or (
        root / "config" / ITEM_HANDLER_MANIFESTS[args.profile]
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
        print(f"[FAIL] Item handler audit found {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(
        f"[OK] Item handlers: {report['handler_count']} entries, "
        f"{report['unique_handler_count']} unique targets, "
        f"SHA-1 {report['table_sha1']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
