#!/usr/bin/env python3
"""Decode and audit object animation descriptors and frame records."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from scripts.authoring.room_data import RoomDataError, extract_prg


PRG_BASE = 0x8000

OBJECT_ANIMATION_MANIFESTS = {
    "usa": "object_animations.json",
    "europe": "object_animations_europe.json",
}


@dataclass(frozen=True)
class AnimationDescriptor:
    cpu_address: int
    initial_phase: int
    delay: int
    uses_variants: bool
    data_pointer: int


@dataclass(frozen=True)
class AnimationFrameRecord:
    cpu_address: int
    payload: tuple[int, int, int]


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


def cpu_slice(prg: bytes, start: int, end: int, label: str) -> bytes:
    if end < start:
        raise RoomDataError(f"invalid {label} range: ${start:04X}-${end:04X}")
    offset = prg_offset(start)
    stop = prg_offset(end) + 1
    if stop > len(prg):
        raise RoomDataError(f"truncated {label} at ${start:04X}")
    return prg[offset:stop]


def decode_words(prg: bytes, cpu_address: int, count: int) -> list[int]:
    if count <= 0:
        raise RoomDataError(f"word count must be positive: {count}")
    data = cpu_slice(
        prg, cpu_address, cpu_address + count * 2 - 1, "little-endian word table"
    )
    return [data[index] | (data[index + 1] << 8) for index in range(0, len(data), 2)]


def encode_words(values: list[int]) -> bytes:
    encoded = bytearray()
    for value in values:
        if not 0 <= value <= 0xFFFF:
            raise RoomDataError(f"word outside 16-bit range: {value}")
        encoded.extend((value & 0xFF, value >> 8))
    return bytes(encoded)


def decode_descriptors(
    prg: bytes, cpu_address: int, count: int
) -> list[AnimationDescriptor]:
    if count <= 0:
        raise RoomDataError(f"descriptor count must be positive: {count}")
    data = cpu_slice(
        prg, cpu_address, cpu_address + count * 4 - 1, "animation descriptors"
    )
    return [
        AnimationDescriptor(
            cpu_address=cpu_address + index,
            initial_phase=data[index],
            delay=data[index + 1] >> 1,
            uses_variants=bool(data[index + 1] & 1),
            data_pointer=data[index + 2] | (data[index + 3] << 8),
        )
        for index in range(0, len(data), 4)
    ]


def encode_descriptors(descriptors: list[AnimationDescriptor]) -> bytes:
    encoded = bytearray()
    for descriptor in descriptors:
        if not 0 <= descriptor.initial_phase <= 0xFF:
            raise RoomDataError("animation initial phase is outside byte range")
        if not 0 <= descriptor.delay <= 0x7F:
            raise RoomDataError("animation delay is outside seven-bit range")
        encoded.extend(
            (
                descriptor.initial_phase,
                descriptor.delay * 2 + descriptor.uses_variants,
            )
        )
        encoded.extend(encode_words([descriptor.data_pointer]))
    return bytes(encoded)


def decode_frame_records(
    prg: bytes, cpu_address: int, count: int
) -> list[AnimationFrameRecord]:
    if count <= 0:
        raise RoomDataError(f"frame record count must be positive: {count}")
    data = cpu_slice(
        prg, cpu_address, cpu_address + count * 3 - 1, "animation frame records"
    )
    return [
        AnimationFrameRecord(cpu_address + index, tuple(data[index : index + 3]))
        for index in range(0, len(data), 3)
    ]


def encode_frame_records(records: list[AnimationFrameRecord]) -> bytes:
    return bytes(value for record in records for value in record.payload)


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RoomDataError("unsupported object animation manifest schema")
    groups = value.get("descriptor_groups")
    if not isinstance(groups, list) or not groups:
        raise RoomDataError("object animation manifest needs descriptor_groups")
    pointers = value.get("object_type_pointers")
    if not isinstance(pointers, list) or not pointers:
        raise RoomDataError("object animation manifest needs object_type_pointers")
    return value


def validate_manifest_profile(manifest: dict[str, Any], profile: str) -> None:
    actual = manifest.get("profile", "usa")
    if actual != profile:
        raise RoomDataError(
            f"object animation profile mismatch: expected={profile}, manifest={actual}"
        )


def sha1_range(prg: bytes, start: int, end: int, label: str) -> str:
    return hashlib.sha1(cpu_slice(prg, start, end, label)).hexdigest()


def descriptor_report(descriptor: AnimationDescriptor) -> dict[str, object]:
    return {
        "address": descriptor.cpu_address,
        "initial_phase": descriptor.initial_phase,
        "delay": descriptor.delay,
        "uses_variants": descriptor.uses_variants,
        "data_pointer": descriptor.data_pointer,
    }


def collect_report(prg: bytes, manifest: dict[str, Any]) -> dict[str, object]:
    pointer_address = parse_number(
        manifest.get("pointer_table_address"), "pointer_table_address"
    )
    expected_type_pointers = manifest["object_type_pointers"]
    type_pointers = decode_words(prg, pointer_address, len(expected_type_pointers))

    groups: list[dict[str, object]] = []
    descriptors: list[AnimationDescriptor] = []
    definition_coverage: list[int] = []
    definition_round_trip = True
    for index, declaration in enumerate(manifest["descriptor_groups"]):
        if not isinstance(declaration, dict):
            raise RoomDataError(f"descriptor group {index} must be an object")
        address = parse_number(declaration.get("address"), f"group {index}.address")
        count = parse_number(declaration.get("action_count"), f"group {index}.count")
        decoded = decode_descriptors(prg, address, count)
        descriptors.extend(decoded)
        definition_coverage.extend(range(address, address + count * 4))
        definition_round_trip &= encode_descriptors(decoded) == cpu_slice(
            prg, address, address + count * 4 - 1, "animation descriptors"
        )
        groups.append(
            {
                "address": address,
                "action_count": count,
                "descriptors": [descriptor_report(item) for item in decoded],
            }
        )

    variant_selectors: list[dict[str, object]] = []
    variant_pointer_addresses: set[int] = set()
    for index, value in enumerate(manifest.get("variant_selector_addresses", [])):
        address = parse_number(value, f"variant selector {index}")
        pointers = decode_words(prg, address, 4)
        variant_pointer_addresses.add(address)
        definition_coverage.extend(range(address, address + 8))
        definition_round_trip &= encode_words(pointers) == cpu_slice(
            prg, address, address + 7, "animation variant selector"
        )
        variant_selectors.append({"address": address, "pointers": pointers})

    frame_start = parse_number(manifest.get("frame_data_start"), "frame_data_start")
    frame_end = parse_number(manifest.get("frame_data_end"), "frame_data_end")
    frame_data = cpu_slice(prg, frame_start, frame_end, "animation frame data")
    if len(frame_data) % 3:
        raise RoomDataError("animation frame data is not a whole number of records")
    frame_records = decode_frame_records(prg, frame_start, len(frame_data) // 3)

    frame_pointers: set[int] = set()
    invalid_variant_references: list[int] = []
    for descriptor in descriptors:
        if descriptor.uses_variants:
            if descriptor.data_pointer not in variant_pointer_addresses:
                invalid_variant_references.append(descriptor.cpu_address)
                continue
            frame_pointers.update(decode_words(prg, descriptor.data_pointer, 4))
        else:
            frame_pointers.add(descriptor.data_pointer)

    invalid_frame_pointers = sorted(
        pointer
        for pointer in frame_pointers
        if not frame_start <= pointer <= frame_end
        or (pointer - frame_start) % 3 != 0
    )
    definition_start = parse_number(
        manifest.get("definition_data_start"), "definition_data_start"
    )
    definition_end = parse_number(
        manifest.get("definition_data_end"), "definition_data_end"
    )
    expected_definition_coverage = list(range(definition_start, definition_end + 1))
    pointer_round_trip = encode_words(type_pointers) == cpu_slice(
        prg,
        pointer_address,
        pointer_address + len(type_pointers) * 2 - 1,
        "animation pointer table",
    )
    definition_coverage_exact = sorted(definition_coverage) == expected_definition_coverage
    frame_round_trip = encode_frame_records(frame_records) == frame_data

    return {
        "pointer_table_address": pointer_address,
        "object_type_pointers": type_pointers,
        "object_type_count": len(type_pointers),
        "descriptor_group_count": len(groups),
        "descriptor_count": len(descriptors),
        "variant_descriptor_count": sum(item.uses_variants for item in descriptors),
        "variant_selectors": variant_selectors,
        "frame_sequence_starts": sorted(frame_pointers),
        "frame_sequence_count": len(frame_pointers),
        "frame_record_count": len(frame_data) // 3,
        "definition_coverage_exact": definition_coverage_exact,
        "invalid_variant_references": invalid_variant_references,
        "invalid_frame_pointers": invalid_frame_pointers,
        "pointer_round_trip": pointer_round_trip,
        "definition_round_trip": definition_round_trip,
        "frame_round_trip": frame_round_trip,
        "round_trip": pointer_round_trip
        and definition_coverage_exact
        and definition_round_trip
        and frame_round_trip,
        "round_trip_size": len(type_pointers) * 2
        + len(expected_definition_coverage)
        + len(frame_data),
        "pointer_sha1": sha1_range(
            prg,
            pointer_address,
            pointer_address + len(type_pointers) * 2 - 1,
            "animation pointer table",
        ),
        "definition_sha1": sha1_range(
            prg, definition_start, definition_end, "animation definitions"
        ),
        "frame_sha1": hashlib.sha1(frame_data).hexdigest(),
        "groups": groups,
    }


def validate_report(report: dict[str, object], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_pointers = [
        parse_number(value, "object_type_pointers")
        for value in manifest["object_type_pointers"]
    ]
    if report.get("object_type_pointers") != expected_pointers:
        errors.append("object-type animation pointers differ from reviewed values")
    for field in ("descriptor_count", "frame_sequence_count", "frame_record_count"):
        expected = parse_number(manifest.get(field), field)
        if report.get(field) != expected:
            errors.append(
                f"{field} differs: got {report.get(field)!r}, expected {expected}"
            )
    for field in ("pointer_sha1", "definition_sha1", "frame_sha1"):
        if report.get(field) != manifest.get(field):
            errors.append(
                f"{field} differs: got {report.get(field)!r}, "
                f"expected {manifest.get(field)!r}"
            )
    if not report.get("definition_coverage_exact"):
        errors.append("descriptor groups and variant selectors do not cover definitions")
    if report.get("invalid_variant_references"):
        errors.append("variant descriptors reference undeclared selector tables")
    if report.get("invalid_frame_pointers"):
        errors.append("animation frame pointers leave or misalign the frame-data range")
    if not report.get("round_trip"):
        errors.append("decoded object animation data does not round-trip byte-for-byte")
    return errors


def emit_source(prg: bytes, manifest: dict[str, Any]) -> str:
    """Render the reviewed animation region as readable ca65 source."""
    report = collect_report(prg, manifest)
    groups = report["groups"]
    if not isinstance(groups, list):
        raise RoomDataError("animation report has no descriptor groups")
    frame_starts = report["frame_sequence_starts"]
    if not isinstance(frame_starts, list):
        raise RoomDataError("animation report has no frame sequence starts")

    type_pointers = report["object_type_pointers"]
    if not isinstance(type_pointers, list):
        raise RoomDataError("animation report has no object type pointers")
    group_labels: dict[int, str] = {}
    for index, pointer in enumerate(type_pointers):
        if not isinstance(pointer, int):
            raise RoomDataError("invalid object type pointer in report")
        group_labels.setdefault(
            pointer, f"ObjectAnimationDescriptorsType{index * 4:02X}"
        )
    variant_addresses = [
        parse_number(value, "variant_selector_addresses")
        for value in manifest.get("variant_selector_addresses", [])
    ]
    variant_labels = {
        address: f"ObjectAnimationVariantSelector{index:02d}"
        for index, address in enumerate(variant_addresses)
    }
    frame_labels = {
        address: f"ObjectAnimationFrames{index:03d}"
        for index, address in enumerate(frame_starts)
        if isinstance(address, int)
    }

    lines = [
        "; Object action descriptors, variant selectors, and sprite frame records",
        "",
        ".macro ObjectAnimationDescriptor initial_phase, delay, frames",
        "    .byte initial_phase, delay * 2",
        "    .word frames",
        ".endmacro",
        "",
        ".macro VariantObjectAnimationDescriptor initial_phase, delay, selector",
        "    .byte initial_phase, delay * 2 + 1",
        "    .word selector",
        ".endmacro",
        "",
        '.segment "PRG_OBJECT_ANIMATION_DEFINITIONS"',
    ]
    layout: list[tuple[int, str, object]] = []
    for group in groups:
        if not isinstance(group, dict):
            raise RoomDataError("invalid descriptor group in report")
        address = group.get("address")
        if not isinstance(address, int):
            raise RoomDataError("descriptor group has no address")
        layout.append((address, "group", group))
    for address in variant_addresses:
        layout.append((address, "selector", decode_words(prg, address, 4)))

    for layout_address, kind, value in sorted(layout, key=lambda item: item[0]):
        if kind == "group":
            group = value
            if not isinstance(group, dict):
                raise RoomDataError("invalid descriptor group")
            address = group["address"]
            descriptors = group["descriptors"]
            if not isinstance(address, int) or not isinstance(descriptors, list):
                raise RoomDataError("invalid descriptor group fields")
            lines.extend(("", f"{group_labels[address]}:"))
            for descriptor in descriptors:
                if not isinstance(descriptor, dict):
                    raise RoomDataError("invalid animation descriptor")
                initial_phase = descriptor["initial_phase"]
                delay = descriptor["delay"]
                pointer = descriptor["data_pointer"]
                if not all(isinstance(item, int) for item in (initial_phase, delay, pointer)):
                    raise RoomDataError("invalid animation descriptor fields")
                if descriptor["uses_variants"]:
                    macro = "VariantObjectAnimationDescriptor"
                    target = variant_labels[pointer]
                else:
                    macro = "ObjectAnimationDescriptor"
                    target = frame_labels[pointer]
                lines.append(
                    f"    {macro} ${initial_phase:02X}, ${delay:02X}, {target}"
                )
        else:
            pointers = value
            if not isinstance(pointers, list):
                raise RoomDataError("invalid variant selector")
            lines.extend(
                (
                    "",
                    f"{variant_labels[layout_address]}:",
                    "    .word " + ", ".join(frame_labels[pointer] for pointer in pointers),
                )
            )

    definition_start = parse_number(
        manifest.get("definition_data_start"), "definition_data_start"
    )
    definition_end = parse_number(
        manifest.get("definition_data_end"), "definition_data_end"
    )
    lines.extend(
        (
            "",
            f".assert * - {group_labels[definition_start]} = "
            f"${definition_end - definition_start + 1:04X}, error, "
            '"unexpected object animation definition size"',
            "",
            '.segment "PRG_OBJECT_ANIMATION_FRAMES"',
            "",
            "; Each row below holds one or two three-byte sprite frame records",
        )
    )
    frame_end = parse_number(manifest.get("frame_data_end"), "frame_data_end")
    for index, address in enumerate(frame_starts):
        if not isinstance(address, int):
            raise RoomDataError("invalid frame sequence address")
        next_address = frame_starts[index + 1] if index + 1 < len(frame_starts) else frame_end + 1
        if not isinstance(next_address, int) or (next_address - address) % 3:
            raise RoomDataError("misaligned animation frame sequence")
        data = cpu_slice(prg, address, next_address - 1, "animation frame sequence")
        lines.append(f"{frame_labels[address]}:")
        for offset in range(0, len(data), 6):
            row = data[offset : offset + 6]
            lines.append("    .byte " + ", ".join(f"${byte:02X}" for byte in row))

    frame_start = parse_number(manifest.get("frame_data_start"), "frame_data_start")
    lines.extend(
        (
            "",
            f".assert * - {frame_labels[frame_start]} = "
            f"${frame_end - frame_start + 1:04X}, error, "
            '"unexpected object animation frame data size"',
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
        "--profile", choices=tuple(OBJECT_ANIMATION_MANIFESTS), default="usa"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    manifest_path = args.manifest or (
        root / "config" / OBJECT_ANIMATION_MANIFESTS[args.profile]
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
        print(
            f"[FAIL] Object animation audit found {len(errors)} error(s)",
            file=sys.stderr,
        )
        return 1
    print(
        "[OK] Object animations: "
        f"{report['object_type_count']} type pointers, "
        f"{report['descriptor_count']} descriptors, "
        f"{report['frame_sequence_count']} sequences, and "
        f"{report['frame_record_count']} frame records; "
        f"{report['round_trip_size']} bytes round-tripped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
