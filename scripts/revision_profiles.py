#!/usr/bin/env python3
"""Validate, inspect, and split private Solomon's Key revision profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable

from project import ProjectError, digest, parse_ines, safe_asset_path, write_if_changed
from room_data import (
    ROOM_COUNT,
    ROOM_DATA_LAYOUTS,
    decode_mirror_enemy_sets,
    decode_mirror_schedules,
    decode_room,
    decode_room_tile_patterns,
    extract_prg,
    roundtrip_rooms,
)


ROOT = Path(__file__).resolve().parent.parent
PROFILE_STATES = {"complete", "in-progress", "planned"}
TIMING_MODES = {"ntsc", "pal"}
IMAGE_REGIONS = ("header", "prg", "chr")
HASH_FIELDS = (("sha1", 40), ("sha256", 64))
ROOM_FAMILIES = (
    "tile_patterns",
    "mirror_schedules",
    "mirror_enemy_sets",
    "room_blocks",
    "room_enemies",
    "room_items",
)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProjectError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_profiles(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectError(f"cannot read revision manifest {path}: {exc}") from exc
    errors = validate_profiles(document)
    if errors:
        raise ProjectError("; ".join(errors))
    return document


def valid_hash(value: object, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def validate_region(
    profile_id: str,
    name: str,
    descriptor: object,
    errors: list[str],
) -> None:
    if not isinstance(descriptor, dict):
        errors.append(f"{profile_id} has no {name} region contract")
        return
    size = descriptor.get("size")
    if not isinstance(size, int) or size <= 0:
        errors.append(f"{profile_id} has invalid {name} size")
    for hash_name, length in HASH_FIELDS:
        if not valid_hash(descriptor.get(hash_name), length):
            errors.append(f"{profile_id} has invalid {name} {hash_name}")


def validate_asset(
    profile_id: str,
    descriptor: object,
    errors: list[str],
) -> None:
    if not isinstance(descriptor, dict):
        errors.append(f"{profile_id} has an invalid extracted asset")
        return
    asset_id = descriptor.get("id")
    path = descriptor.get("path")
    region = descriptor.get("region")
    offset = descriptor.get("offset")
    size = descriptor.get("size")
    if not isinstance(asset_id, str) or not asset_id:
        errors.append(f"{profile_id} has an asset without an id")
    if not isinstance(path, str):
        errors.append(f"{profile_id}/{asset_id} has an invalid path")
    else:
        try:
            safe_asset_path(Path("assets/generated"), path)
        except ProjectError as exc:
            errors.append(f"{profile_id}/{asset_id}: {exc}")
    if region not in IMAGE_REGIONS:
        errors.append(f"{profile_id}/{asset_id} has an invalid region")
    if not isinstance(offset, int) or offset < 0:
        errors.append(f"{profile_id}/{asset_id} has an invalid offset")
    if not isinstance(size, int) or size <= 0:
        errors.append(f"{profile_id}/{asset_id} has an invalid size")
    for hash_name, length in HASH_FIELDS:
        if not valid_hash(descriptor.get(hash_name), length):
            errors.append(f"{profile_id}/{asset_id} has invalid {hash_name}")


def validate_source_range(
    profile_id: str,
    descriptor: object,
    profile: dict[str, Any],
    errors: list[str],
) -> None:
    if not isinstance(descriptor, dict):
        errors.append(f"{profile_id} has an invalid verified source range")
        return
    range_id = descriptor.get("id")
    region = descriptor.get("region")
    offset = descriptor.get("offset")
    size = descriptor.get("size")
    if not isinstance(range_id, str) or not range_id:
        errors.append(f"{profile_id} has a source range without an id")
    if region not in IMAGE_REGIONS:
        errors.append(f"{profile_id}/{range_id} has an invalid source region")
        return
    if not isinstance(offset, int) or offset < 0:
        errors.append(f"{profile_id}/{range_id} has an invalid source offset")
    if not isinstance(size, int) or size <= 0:
        errors.append(f"{profile_id}/{range_id} has an invalid source size")
    if isinstance(offset, int) and isinstance(size, int):
        if offset + size > int(profile[region]["size"]):
            errors.append(f"{profile_id}/{range_id} exceeds {region}")
    for hash_name, length in HASH_FIELDS:
        if not valid_hash(descriptor.get(hash_name), length):
            errors.append(f"{profile_id}/{range_id} has invalid source {hash_name}")


def validate_profiles(document: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        return ["revision profile manifest is not schema 1"]
    profiles = document.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        return ["revision profile manifest has no profiles"]

    identifiers: list[object] = []
    asset_paths: dict[str, tuple[object, ...]] = {}
    for profile in profiles:
        if not isinstance(profile, dict):
            errors.append("revision profile is not an object")
            continue
        profile_id = profile.get("id")
        identifiers.append(profile_id)
        if not isinstance(profile_id, str) or not profile_id:
            errors.append("revision profile has no id")
            profile_id = "<missing>"
        if not isinstance(profile.get("name"), str) or not profile["name"]:
            errors.append(f"{profile_id} has no display name")
        if profile.get("timing") not in TIMING_MODES:
            errors.append(f"{profile_id} has an invalid timing mode")
        if profile.get("room_layout") not in ROOM_DATA_LAYOUTS:
            errors.append(f"{profile_id} has an unknown room layout")
        if profile.get("source_status") not in PROFILE_STATES:
            errors.append(f"{profile_id} has an invalid source status")
        assembly_define = profile.get("assembly_define")
        if profile.get("source_status") == "planned":
            if assembly_define is not None:
                errors.append(f"{profile_id} planned source has an assembly define")
        elif not isinstance(assembly_define, int) or assembly_define < 0:
            errors.append(f"{profile_id} has no assembly define")
        reference = profile.get("reference_rom")
        if (
            not isinstance(reference, str)
            or Path(reference).name != reference
            or not reference.lower().endswith(".nes")
        ):
            errors.append(f"{profile_id} has an unsafe reference filename")
        if not isinstance(profile.get("reference_provenance"), str):
            errors.append(f"{profile_id} has no reference provenance note")

        validate_region(profile_id, "rom", profile.get("rom"), errors)
        for region_name in IMAGE_REGIONS:
            validate_region(profile_id, region_name, profile.get(region_name), errors)
        try:
            total_size = sum(int(profile[name]["size"]) for name in IMAGE_REGIONS)
            rom_size = int(profile["rom"]["size"])
        except (KeyError, TypeError, ValueError):
            pass
        else:
            if total_size != rom_size:
                errors.append(f"{profile_id} region sizes do not compose the ROM")

        assets = profile.get("extracted_assets")
        if not isinstance(assets, list):
            errors.append(f"{profile_id} has no extracted asset list")
            continue
        asset_ids: list[object] = []
        for asset in assets:
            validate_asset(profile_id, asset, errors)
            if not isinstance(asset, dict):
                continue
            asset_ids.append(asset.get("id"))
            region = asset.get("region")
            try:
                region_size = int(profile[str(region)]["size"])
                end = int(asset["offset"]) + int(asset["size"])
            except (KeyError, TypeError, ValueError):
                continue
            if end > region_size:
                errors.append(f"{profile_id}/{asset.get('id')} exceeds {region}")
            path = asset.get("path")
            signature = (
                asset.get("size"),
                asset.get("sha1"),
                asset.get("sha256"),
            )
            if isinstance(path, str):
                previous = asset_paths.setdefault(path, signature)
                if previous != signature:
                    errors.append(f"asset path has conflicting profile data: {path}")
        if len(asset_ids) != len(set(asset_ids)):
            errors.append(f"{profile_id} has duplicate extracted asset ids")
        source_ranges = profile.get("verified_source_ranges")
        if not isinstance(source_ranges, list):
            errors.append(f"{profile_id} has no verified source range list")
        else:
            range_ids: list[object] = []
            occupied: dict[str, list[tuple[int, int]]] = {}
            for source_range in source_ranges:
                validate_source_range(profile_id, source_range, profile, errors)
                if not isinstance(source_range, dict):
                    continue
                range_ids.append(source_range.get("id"))
                region = source_range.get("region")
                offset = source_range.get("offset")
                size = source_range.get("size")
                if not isinstance(region, str) or not isinstance(offset, int) or not isinstance(size, int):
                    continue
                span = (offset, offset + size)
                for previous in occupied.setdefault(region, []):
                    if span[0] < previous[1] and previous[0] < span[1]:
                        errors.append(
                            f"{profile_id} has overlapping verified source ranges"
                        )
                occupied[region].append(span)
            if len(range_ids) != len(set(range_ids)):
                errors.append(f"{profile_id} has duplicate verified source range ids")
        fingerprints = profile.get("room_fingerprints")
        if not isinstance(fingerprints, dict):
            errors.append(f"{profile_id} has no room fingerprints")
        elif tuple(fingerprints) != ROOM_FAMILIES:
            errors.append(f"{profile_id} room fingerprint families differ")
        else:
            for family, fingerprint in fingerprints.items():
                if not valid_hash(fingerprint, 64):
                    errors.append(
                        f"{profile_id} has invalid {family} room fingerprint"
                    )

    if len(identifiers) != len(set(identifiers)):
        errors.append("revision profile ids are not unique")
    default = document.get("default_profile")
    by_id = {
        profile.get("id"): profile
        for profile in profiles
        if isinstance(profile, dict)
    }
    if default not in by_id:
        errors.append("default revision profile does not exist")
    elif by_id[default].get("source_status") != "complete":
        errors.append("default revision profile is not source-complete")
    required = document.get("source_2_required_profiles")
    if not isinstance(required, list) or not required:
        errors.append("Source 2.0 required profiles are missing")
    else:
        for profile_id in required:
            if profile_id not in by_id:
                errors.append(f"required profile does not exist: {profile_id}")
    return errors


def get_profile(document: dict[str, Any], profile_id: str) -> dict[str, Any]:
    matches = [profile for profile in document["profiles"] if profile["id"] == profile_id]
    if len(matches) != 1:
        raise ProjectError(f"revision profile not found: {profile_id}")
    return matches[0]


def selected_profiles(
    document: dict[str, Any],
    profile_id: str | None,
    all_profiles: bool,
) -> list[dict[str, Any]]:
    if profile_id:
        return [get_profile(document, profile_id)]
    identifiers = (
        [profile["id"] for profile in document["profiles"]]
        if all_profiles
        else document["source_2_required_profiles"]
    )
    return [get_profile(document, identifier) for identifier in identifiers]


def resolve_reference(
    profile: dict[str, Any],
    private_root: Path,
    override: Path | None = None,
) -> Path:
    return override if override is not None else private_root / profile["reference_rom"]


def verify_payload(
    name: str,
    payload: bytes,
    descriptor: dict[str, Any],
) -> None:
    if len(payload) != descriptor["size"]:
        raise ProjectError(
            f"{name} size mismatch: got {len(payload)}, expected {descriptor['size']}"
        )
    for hash_name, _ in HASH_FIELDS:
        actual = digest(payload, hash_name)
        expected = descriptor[hash_name]
        if actual != expected:
            raise ProjectError(
                f"{name} {hash_name} mismatch: got {actual}, expected {expected}"
            )


def verify_reference(path: Path, profile: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise ProjectError(f"private reference ROM not found: {path}")
    try:
        image = path.read_bytes()
    except OSError as exc:
        raise ProjectError(f"cannot read private reference ROM {path}: {exc}") from exc
    parsed = parse_ines(image)
    verify_payload(f"{profile['id']} ROM", image, profile["rom"])
    for name in IMAGE_REGIONS:
        verify_payload(f"{profile['id']} {name}", parsed[name], profile[name])
    return parsed


def require_buildable_source(profile: dict[str, Any]) -> int:
    value = profile.get("assembly_define")
    if profile.get("source_status") == "planned" or not isinstance(value, int):
        raise ProjectError(f"{profile['id']} has no buildable source profile")
    return value


def verify_source_ranges(
    built_path: Path,
    reference_path: Path,
    profile: dict[str, Any],
) -> None:
    parsed_reference = verify_reference(reference_path, profile)
    if not built_path.is_file():
        raise ProjectError(f"source-built revision image not found: {built_path}")
    parsed_built = parse_ines(built_path.read_bytes())
    source_ranges = profile["verified_source_ranges"]
    if not source_ranges:
        raise ProjectError(f"{profile['id']} has no verified source ranges")
    checked = 0
    for descriptor in source_ranges:
        region_name = descriptor["region"]
        start = descriptor["offset"]
        end = start + descriptor["size"]
        expected = parsed_reference[region_name][start:end]
        actual = parsed_built[region_name][start:end]
        verify_payload(
            f"{profile['id']}/{descriptor['id']} reference",
            expected,
            descriptor,
        )
        if actual != expected:
            difference = next(
                index
                for index, (left, right) in enumerate(zip(actual, expected))
                if left != right
            )
            raise ProjectError(
                f"{profile['id']}/{descriptor['id']} source range differs at "
                f"{region_name} + ${start + difference:04X}: "
                f"${actual[difference]:02X} != ${expected[difference]:02X}"
            )
        checked += len(actual)
        print(
            f"[OK] {profile['id']}/{descriptor['id']}: "
            f"{len(actual)} source-built bytes match"
        )
    print(f"[OK] {profile['id']}: {checked} verified source-range bytes")


def verify_built_revision(
    built_path: Path,
    reference_path: Path,
    profile: dict[str, Any],
) -> None:
    verify_reference(reference_path, profile)
    if not built_path.is_file():
        raise ProjectError(f"source-built revision image not found: {built_path}")
    try:
        built_image = built_path.read_bytes()
        reference_image = reference_path.read_bytes()
    except OSError as exc:
        raise ProjectError(f"cannot read revision image: {exc}") from exc
    parsed_built = parse_ines(built_image)
    verify_payload(f"{profile['id']} built ROM", built_image, profile["rom"])
    for name in IMAGE_REGIONS:
        verify_payload(f"{profile['id']} built {name}", parsed_built[name], profile[name])
    if built_image != reference_image:
        raise ProjectError(
            f"{profile['id']} built image differs despite matching recorded identity"
        )
    print(
        f"[OK] {profile['id']}: complete source-built ROM matches "
        f"{profile['rom']['sha256']}"
    )


def split_profile(
    profile: dict[str, Any],
    parsed: dict[str, Any],
    output_root: Path,
) -> list[Path]:
    written: list[Path] = []
    for descriptor in profile["extracted_assets"]:
        region = parsed[descriptor["region"]]
        start = descriptor["offset"]
        payload = region[start : start + descriptor["size"]]
        verify_payload(
            f"{profile['id']}/{descriptor['id']}",
            payload,
            descriptor,
        )
        destination = safe_asset_path(output_root, descriptor["path"])
        action = write_if_changed(destination, payload)
        print(f"[{action}] {profile['id']}: {destination} ({len(payload)} bytes)")
        written.append(destination)
    return written


def identify_profile(document: dict[str, Any], image: bytes) -> dict[str, Any]:
    image_hash = digest(image, "sha256")
    matches = [
        profile for profile in document["profiles"]
        if profile["rom"]["sha256"] == image_hash
    ]
    if len(matches) != 1:
        raise ProjectError(f"no unique profile matches ROM SHA-256 {image_hash}")
    return matches[0]


def without_locations(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: without_locations(item)
            for key, item in value.items()
            if key != "prg_offset"
        }
    if isinstance(value, list):
        return [without_locations(item) for item in value]
    return value


def room_document(parsed: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    prg = extract_prg(parsed["prg"])
    layout = ROOM_DATA_LAYOUTS[profile["room_layout"]]
    roundtrip_rooms(prg, layout)
    rooms = [decode_room(prg, index, layout) for index in range(ROOM_COUNT)]
    return without_locations(
        {
            "tile_patterns": decode_room_tile_patterns(prg, layout),
            "mirror_schedules": decode_mirror_schedules(prg, layout),
            "mirror_enemy_sets": decode_mirror_enemy_sets(prg, layout),
            "room_blocks": [room["blocks"] for room in rooms],
            "room_enemies": [room["enemy_stream"] for room in rooms],
            "room_items": [room["item_stream"] for room in rooms],
        }
    )


def room_fingerprint(parsed: dict[str, Any], profile: dict[str, Any]) -> str:
    canonical = json.dumps(
        room_document(parsed, profile),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def content_fingerprint(value: Any) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def room_family_fingerprints(
    parsed: dict[str, Any], profile: dict[str, Any]
) -> dict[str, str]:
    document = room_document(parsed, profile)
    return {name: content_fingerprint(document[name]) for name in ROOM_FAMILIES}


def audit_room_fingerprints(
    parsed: dict[str, Any], profile: dict[str, Any]
) -> dict[str, str]:
    actual = room_family_fingerprints(parsed, profile)
    for family in ROOM_FAMILIES:
        expected = profile["room_fingerprints"][family]
        if actual[family] != expected:
            raise ProjectError(
                f"{profile['id']} {family} fingerprint mismatch: "
                f"got {actual[family]}, expected {expected}"
            )
    return actual


def first_structural_difference(
    left: Any,
    right: Any,
    path: str = "room_data",
) -> tuple[str, Any, Any] | None:
    if type(left) is not type(right):
        return path, left, right
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return f"{path}.keys", tuple(left), tuple(right)
        for key in left:
            difference = first_structural_difference(
                left[key], right[key], f"{path}.{key}"
            )
            if difference is not None:
                return difference
        return None
    if isinstance(left, list):
        if len(left) != len(right):
            return f"{path}.length", len(left), len(right)
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            difference = first_structural_difference(
                left_item, right_item, f"{path}[{index}]"
            )
            if difference is not None:
                return difference
        return None
    return None if left == right else (path, left, right)


def print_profile(profile: dict[str, Any]) -> None:
    print(
        f"{profile['id']:<7} {profile['timing']:<4} "
        f"source={profile['source_status']:<11} "
        f"rom={profile['rom']['sha256']} {profile['name']}"
    )


def add_selection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile")
    parser.add_argument("--all-profiles", action="store_true")
    parser.add_argument("--private-root", type=Path, default=ROOT)
    parser.add_argument("--reference-rom", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "config" / "revision_profiles.json",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list known profiles")
    identify = commands.add_parser("identify", help="identify a private ROM by SHA-256")
    identify.add_argument("--image", required=True, type=Path)
    source_check = commands.add_parser(
        "source-check", help="require a buildable source profile"
    )
    source_check.add_argument("--profile", required=True)
    verify_source = commands.add_parser(
        "verify-source", help="verify declared source-built ranges"
    )
    verify_source.add_argument("--profile", required=True)
    verify_source.add_argument("--built", required=True, type=Path)
    verify_source.add_argument("--private-root", type=Path, default=ROOT)
    verify_source.add_argument("--reference-rom", type=Path)
    verify_built = commands.add_parser(
        "verify-built", help="verify a complete source-built revision image"
    )
    verify_built.add_argument("--profile", required=True)
    verify_built.add_argument("--built", required=True, type=Path)
    verify_built.add_argument("--private-root", type=Path, default=ROOT)
    verify_built.add_argument("--reference-rom", type=Path)
    for name, help_text in (
        ("verify", "verify private reference images"),
        ("split", "extract manifest-owned private assets"),
    ):
        command = commands.add_parser(name, help=help_text)
        add_selection_arguments(command)
        if name == "split":
            command.add_argument(
                "--output-dir",
                required=True,
                type=Path,
            )
    compare = commands.add_parser(
        "compare-rooms",
        help="compare canonical room content between two profiles",
    )
    compare.add_argument("--left", required=True)
    compare.add_argument("--right", required=True)
    compare.add_argument("--private-root", type=Path, default=ROOT)
    report = commands.add_parser(
        "room-report",
        help="print canonical room-family fingerprints",
    )
    add_selection_arguments(report)
    audit = commands.add_parser(
        "audit-rooms",
        help="verify room-family fingerprints and lossless codecs",
    )
    add_selection_arguments(audit)
    return parser


def run_selected(
    document: dict[str, Any],
    profiles: Iterable[dict[str, Any]],
    private_root: Path,
    override: Path | None,
    output_root: Path | None,
) -> None:
    selected = list(profiles)
    if override is not None and len(selected) != 1:
        raise ProjectError("--reference-rom requires exactly one --profile")
    for profile in selected:
        reference = resolve_reference(profile, private_root, override)
        parsed = verify_reference(reference, profile)
        if output_root is not None:
            split_profile(profile, parsed, output_root)
        else:
            print(
                f"[OK] {profile['id']}: private reference matches "
                f"{profile['rom']['sha256']}"
            )


def main() -> int:
    args = build_parser().parse_args()
    try:
        document = load_profiles(args.manifest)
        if args.command == "list":
            for profile in document["profiles"]:
                print_profile(profile)
        elif args.command == "identify":
            image = args.image.read_bytes()
            profile = identify_profile(document, image)
            print_profile(profile)
        elif args.command == "source-check":
            profile = get_profile(document, args.profile)
            value = require_buildable_source(profile)
            print(
                f"[OK] {profile['id']}: source={profile['source_status']} "
                f"assembly define={value}"
            )
        elif args.command == "verify-source":
            profile = get_profile(document, args.profile)
            require_buildable_source(profile)
            reference = resolve_reference(
                profile, args.private_root, args.reference_rom
            )
            verify_source_ranges(args.built, reference, profile)
        elif args.command == "verify-built":
            profile = get_profile(document, args.profile)
            require_buildable_source(profile)
            if profile.get("source_status") != "complete":
                raise ProjectError(
                    f"{profile['id']} source profile is not marked complete"
                )
            reference = resolve_reference(
                profile, args.private_root, args.reference_rom
            )
            verify_built_revision(args.built, reference, profile)
        elif args.command in {"verify", "split"}:
            profiles = selected_profiles(document, args.profile, args.all_profiles)
            run_selected(
                document,
                profiles,
                args.private_root,
                args.reference_rom,
                args.output_dir if args.command == "split" else None,
            )
        elif args.command in {"room-report", "audit-rooms"}:
            profiles = selected_profiles(document, args.profile, args.all_profiles)
            if args.reference_rom is not None and len(profiles) != 1:
                raise ProjectError("--reference-rom requires exactly one --profile")
            for profile in profiles:
                parsed = verify_reference(
                    resolve_reference(profile, args.private_root, args.reference_rom),
                    profile,
                )
                fingerprints = audit_room_fingerprints(parsed, profile)
                if args.command == "audit-rooms":
                    print(
                        f"[OK] {profile['id']}: {ROOM_COUNT} rooms, "
                        f"{len(ROOM_FAMILIES)} format families"
                    )
                    continue
                print(f"{profile['id']}:")
                for family, fingerprint in fingerprints.items():
                    print(f"  {family:<18} {fingerprint}")
        else:
            left = get_profile(document, args.left)
            right = get_profile(document, args.right)
            left_parsed = verify_reference(
                resolve_reference(left, args.private_root), left
            )
            right_parsed = verify_reference(
                resolve_reference(right, args.private_root), right
            )
            left_document = room_document(left_parsed, left)
            right_document = room_document(right_parsed, right)
            difference = first_structural_difference(left_document, right_document)
            left_families = room_family_fingerprints(left_parsed, left)
            right_families = room_family_fingerprints(right_parsed, right)
            for family in left_families:
                matches = left_families[family] == right_families[family]
                state = "MATCH" if matches else "DIFF"
                print(
                    f"[{state}] {family}: {left_families[family]} / "
                    f"{right_families[family]}"
                )
                if not matches:
                    family_difference = first_structural_difference(
                        left_document[family],
                        right_document[family],
                        family,
                    )
                    if family_difference is not None:
                        path, left_value, right_value = family_difference
                        print(f"       first at {path}: {left_value!r} != {right_value!r}")
            if difference is None:
                fingerprint = room_fingerprint(left_parsed, left)
                print(
                    f"[OK] {left['id']} and {right['id']}: {ROOM_COUNT} canonical "
                    f"rooms and auxiliary room data match ({fingerprint})"
                )
            else:
                path, left_value, right_value = difference
                print(
                    f"[INFO] first semantic difference at {path}: "
                    f"{left_value!r} != {right_value!r}"
                )
    except (OSError, KeyError, TypeError, ProjectError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
