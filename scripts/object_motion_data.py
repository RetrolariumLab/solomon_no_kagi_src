#!/usr/bin/env python3
"""Decode and audit object motion selector tables and Y/X vectors."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

try:
    from .object_animation_data import (
        cpu_slice,
        decode_words,
        encode_words,
        parse_number,
        sha1_range,
    )
    from .room_data import RoomDataError, extract_prg
except ImportError:
    from object_animation_data import (
        cpu_slice,
        decode_words,
        encode_words,
        parse_number,
        sha1_range,
    )
    from room_data import RoomDataError, extract_prg


@dataclass(frozen=True)
class MotionVector:
    index: int
    y_velocity: int
    x_velocity: int


OBJECT_MOTION_MANIFESTS = {
    "usa": "object_motion.json",
    "europe": "object_motion_europe.json",
}


def encode_selectors(selectors: list[int]) -> bytes:
    if any(not 0 <= selector <= 0xFF for selector in selectors):
        raise RoomDataError("object motion selector is outside byte range")
    return bytes(selectors)


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RoomDataError("unsupported object motion manifest schema")
    groups = value.get("selector_groups")
    if not isinstance(groups, list) or not groups:
        raise RoomDataError("object motion manifest needs selector_groups")
    pointers = value.get("object_type_pointers")
    if not isinstance(pointers, list) or not pointers:
        raise RoomDataError("object motion manifest needs object_type_pointers")
    return value


def validate_manifest_profile(manifest: dict[str, Any], profile: str) -> None:
    actual = manifest.get("profile", "usa")
    if actual != profile:
        raise RoomDataError(
            f"object motion profile mismatch: expected={profile}, manifest={actual}"
        )


def decode_motion_vectors(
    prg: bytes, cpu_address: int, count: int
) -> list[MotionVector]:
    if count <= 0:
        raise RoomDataError(f"motion vector count must be positive: {count}")
    data = cpu_slice(
        prg, cpu_address, cpu_address + count * 2 - 1, "object motion vectors"
    )
    return [
        MotionVector(index // 2, data[index], data[index + 1])
        for index in range(0, len(data), 2)
    ]


def encode_motion_vectors(vectors: list[MotionVector]) -> bytes:
    encoded = bytearray()
    for vector in vectors:
        if not 0 <= vector.y_velocity <= 0xFF or not 0 <= vector.x_velocity <= 0xFF:
            raise RoomDataError("object motion component is outside byte range")
        encoded.extend((vector.y_velocity, vector.x_velocity))
    return bytes(encoded)


def collect_report(prg: bytes, manifest: dict[str, Any]) -> dict[str, object]:
    pointer_address = parse_number(
        manifest.get("pointer_table_address"), "pointer_table_address"
    )
    expected_type_pointers = manifest["object_type_pointers"]
    type_pointers = decode_words(prg, pointer_address, len(expected_type_pointers))

    selector_start = parse_number(
        manifest.get("selector_data_start"), "selector_data_start"
    )
    selector_end = parse_number(manifest.get("selector_data_end"), "selector_data_end")
    selector_coverage: list[int] = []
    selector_round_trip = True
    selector_groups: list[dict[str, object]] = []
    direct_selectors: list[int] = []
    room_state_masks: list[int] = []
    for index, declaration in enumerate(manifest["selector_groups"]):
        if not isinstance(declaration, dict):
            raise RoomDataError(f"selector group {index} must be an object")
        address = parse_number(declaration.get("address"), f"group {index}.address")
        count = parse_number(declaration.get("action_count"), f"group {index}.count")
        data = cpu_slice(
            prg, address, address + count - 1, "object motion selector group"
        )
        selector_coverage.extend(range(address, address + count))
        selector_round_trip &= encode_selectors(list(data)) == cpu_slice(
            prg, address, address + count - 1, "object motion selector group"
        )
        direct_selectors.extend(value for value in data if value < 0x80)
        room_state_masks.extend(value for value in data if value >= 0x80)
        selector_groups.append(
            {"address": address, "action_count": count, "selectors": list(data)}
        )

    vector_address = parse_number(
        manifest.get("motion_vector_address"), "motion_vector_address"
    )
    vector_count = parse_number(manifest.get("motion_vector_count"), "motion_vector_count")
    vectors = decode_motion_vectors(prg, vector_address, vector_count)
    invalid_direct_selectors = sorted(
        set(selector for selector in direct_selectors if selector >= vector_count)
    )

    pointer_round_trip = encode_words(type_pointers) == cpu_slice(
        prg,
        pointer_address,
        pointer_address + len(type_pointers) * 2 - 1,
        "object motion pointer table",
    )
    selector_coverage_exact = sorted(selector_coverage) == list(
        range(selector_start, selector_end + 1)
    )
    vector_round_trip = encode_motion_vectors(vectors) == cpu_slice(
        prg,
        vector_address,
        vector_address + vector_count * 2 - 1,
        "object motion vectors",
    )

    return {
        "pointer_table_address": pointer_address,
        "object_type_pointers": type_pointers,
        "object_type_count": len(type_pointers),
        "selector_group_count": len(selector_groups),
        "selector_count": len(direct_selectors) + len(room_state_masks),
        "direct_selector_count": len(direct_selectors),
        "room_state_mask_count": len(room_state_masks),
        "selector_coverage_exact": selector_coverage_exact,
        "invalid_direct_selectors": invalid_direct_selectors,
        "motion_vector_count": len(vectors),
        "motion_vectors": [
            {
                "index": vector.index,
                "y_velocity": vector.y_velocity,
                "x_velocity": vector.x_velocity,
            }
            for vector in vectors
        ],
        "pointer_sha1": sha1_range(
            prg,
            pointer_address,
            pointer_address + len(type_pointers) * 2 - 1,
            "object motion pointer table",
        ),
        "selector_sha1": sha1_range(
            prg, selector_start, selector_end, "object motion selectors"
        ),
        "vector_sha1": sha1_range(
            prg,
            vector_address,
            vector_address + vector_count * 2 - 1,
            "object motion vectors",
        ),
        "pointer_round_trip": pointer_round_trip,
        "selector_round_trip": selector_round_trip,
        "vector_round_trip": vector_round_trip,
        "round_trip": pointer_round_trip
        and selector_coverage_exact
        and selector_round_trip
        and vector_round_trip,
        "round_trip_size": len(type_pointers) * 2
        + selector_end
        - selector_start
        + 1
        + vector_count * 2,
        "selector_groups": selector_groups,
    }


def validate_report(report: dict[str, object], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_pointers = [
        parse_number(value, "object_type_pointers")
        for value in manifest["object_type_pointers"]
    ]
    if report.get("object_type_pointers") != expected_pointers:
        errors.append("object-type motion pointers differ from reviewed values")
    for field in ("selector_count", "motion_vector_count"):
        expected = parse_number(manifest.get(field), field)
        if report.get(field) != expected:
            errors.append(
                f"{field} differs: got {report.get(field)!r}, expected {expected}"
            )
    for field in ("pointer_sha1", "selector_sha1", "vector_sha1"):
        if report.get(field) != manifest.get(field):
            errors.append(
                f"{field} differs: got {report.get(field)!r}, "
                f"expected {manifest.get(field)!r}"
            )
    if not report.get("selector_coverage_exact"):
        errors.append("motion selector groups do not exactly cover their data range")
    if report.get("invalid_direct_selectors"):
        errors.append("direct motion selectors exceed the motion vector table")
    if not report.get("round_trip"):
        errors.append("decoded object motion data does not round-trip byte-for-byte")
    return errors


def emit_source(prg: bytes, manifest: dict[str, Any]) -> str:
    """Render the reviewed motion region as readable ca65 source."""
    report = collect_report(prg, manifest)
    type_pointers = report["object_type_pointers"]
    selector_groups = report["selector_groups"]
    vectors = report["motion_vectors"]
    if not isinstance(type_pointers, list):
        raise RoomDataError("object motion report has no type pointers")
    if not isinstance(selector_groups, list):
        raise RoomDataError("object motion report has no selector groups")
    if not isinstance(vectors, list):
        raise RoomDataError("object motion report has no vectors")

    group_labels: dict[int, str] = {}
    for index, pointer in enumerate(type_pointers):
        if not isinstance(pointer, int):
            raise RoomDataError("invalid object motion type pointer")
        group_labels.setdefault(pointer, f"ObjectMotionSelectorsType{index * 4:02X}")

    lines = [
        "; Object-type action selectors and paired fixed-point motion values",
        "",
        ".macro ObjectMotionVectorSelector index",
        "    .byte index",
        ".endmacro",
        "",
        ".macro ObjectRoomStateMotionSelector mask",
        "    .byte mask",
        ".endmacro",
        "",
        ".macro ObjectMotionVector y_velocity, x_velocity",
        "    .byte y_velocity, x_velocity",
        ".endmacro",
        "",
        '.segment "PRG_OBJECT_MOTION_SELECTOR_POINTERS"',
        "",
        "ObjectMotionSelectorPointers:",
    ]
    lines.extend(f"    .word {group_labels[pointer]}" for pointer in type_pointers)
    lines.extend(("", '.segment "PRG_OBJECT_MOTION_SELECTORS"'))

    for group in sorted(selector_groups, key=lambda item: item["address"]):
        if not isinstance(group, dict):
            raise RoomDataError("invalid object motion selector group")
        address = group.get("address")
        selectors = group.get("selectors")
        if not isinstance(address, int) or not isinstance(selectors, list):
            raise RoomDataError("invalid object motion selector group fields")
        lines.extend(("", f"{group_labels[address]}:"))
        for selector in selectors:
            if not isinstance(selector, int):
                raise RoomDataError("invalid object motion selector")
            macro = (
                "ObjectRoomStateMotionSelector"
                if selector >= 0x80
                else "ObjectMotionVectorSelector"
            )
            lines.append(f"    {macro} ${selector:02X}")

    selector_start = parse_number(
        manifest.get("selector_data_start"), "selector_data_start"
    )
    selector_end = parse_number(manifest.get("selector_data_end"), "selector_data_end")
    lines.extend(
        (
            "",
            f".assert * - {group_labels[selector_start]} = "
            f"${selector_end - selector_start + 1:04X}, error, "
            '"unexpected object motion selector data size"',
            "",
            '.segment "PRG_OBJECT_MOTION_VALUES"',
            "",
            "ObjectMotionValues:",
        )
    )
    for vector in vectors:
        if not isinstance(vector, dict):
            raise RoomDataError("invalid object motion vector")
        y_velocity = vector.get("y_velocity")
        x_velocity = vector.get("x_velocity")
        if not isinstance(y_velocity, int) or not isinstance(x_velocity, int):
            raise RoomDataError("invalid object motion vector fields")
        lines.append(f"    ObjectMotionVector ${y_velocity:02X}, ${x_velocity:02X}")
    lines.extend(
        (
            "",
            ".assert * - ObjectMotionValues = "
            f"{len(vectors)} * 2, error, "
            '"unexpected object motion vector count"',
            "",
        )
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "audit", "source"))
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--profile", choices=tuple(OBJECT_MOTION_MANIFESTS), default="usa"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    manifest_path = args.manifest or (
        root / "config" / OBJECT_MOTION_MANIFESTS[args.profile]
    )
    try:
        manifest = load_manifest(manifest_path)
        validate_manifest_profile(manifest, args.profile)
        prg = extract_prg(args.image.read_bytes())
        if args.command == "source":
            print(emit_source(prg, manifest), end="")
            return 0
        report = collect_report(prg, manifest)
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
        print(f"[FAIL] Object motion audit found {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(
        f"[OK] Object motion ({args.profile}): "
        f"{report['object_type_count']} type pointers, "
        f"{report['selector_group_count']} selector groups, "
        f"{report['selector_count']} action selectors, and "
        f"{report['motion_vector_count']} Y/X vectors; "
        f"{report['round_trip_size']} bytes round-tripped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
