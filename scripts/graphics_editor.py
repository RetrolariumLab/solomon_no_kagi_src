#!/usr/bin/env python3
"""Export, validate, and rebuild editable Solomon's Key CHR documents."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any, Iterable

from project import ProjectError, digest, parse_ines, write_if_changed
from revision_profiles import (
    ROOT,
    get_profile,
    load_profiles,
    resolve_reference,
    verify_reference,
)
from room_data import RoomDataError


DOCUMENT_SCHEMA = 2
DOCUMENT_GAME = "solomons-key-nes-graphics"
CHR_BANK_COUNT = 4
CHR_BANK_SIZE = 8192
CHR_SIZE = CHR_BANK_COUNT * CHR_BANK_SIZE
TILE_SIZE = 16
TILES_PER_BANK = CHR_BANK_SIZE // TILE_SIZE
TILE_WIDTH = 8
TILE_HEIGHT = 8
PIXEL_VALUES = "0123"
PRG_BASE = 0x8000
ROOM_PALETTE_HEADER = bytes((0x3F, 0x00, 0x5F))
ROOM_PALETTE_COUNT = 8
COLORS_PER_PALETTE = 4
ROOM_PALETTE_PAYLOAD_SIZE = ROOM_PALETTE_COUNT * COLORS_PER_PALETTE
ROOM_GROUP_COLOR_COUNT = 14
ENDING_PALETTE_VALUE_COUNT = 3


class GraphicsEditorError(ValueError):
    """An invalid CHR document or fixed graphics allocation."""


def indexed_records(
    value: object, field: str, count: int
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != count:
        raise GraphicsEditorError(f"{field} must contain exactly {count} records")
    records: list[dict[str, Any]] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict) or record.get("index") != index:
            raise GraphicsEditorError(f"{field}[{index}] has a non-contiguous index")
        records.append(record)
    return records


def profile_address(profile: dict[str, Any], field: str) -> int:
    value = profile.get("graphics_authoring", {}).get(field)
    try:
        address = int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise GraphicsEditorError(f"profile has no valid {field}") from exc
    if not PRG_BASE <= address < 0x10000:
        raise GraphicsEditorError(f"profile {field} is outside PRG CPU space")
    return address


def prg_slice(prg: bytes, profile: dict[str, Any], field: str, size: int) -> bytes:
    offset = profile_address(profile, field) - PRG_BASE
    payload = prg[offset : offset + size]
    if len(payload) != size:
        raise GraphicsEditorError(f"profile {field} extends outside PRG")
    return payload


def validate_palette_value(value: object, field: str) -> int:
    if not isinstance(value, int) or not 0 <= value <= 0x3F:
        raise GraphicsEditorError(f"{field} must be a NES palette index 0..63")
    return value


def validate_palette_data(value: object) -> dict[str, list[int]]:
    if not isinstance(value, dict):
        raise GraphicsEditorError("palette_data must be an object")
    palettes = value.get("room_palettes")
    if not isinstance(palettes, list) or len(palettes) != ROOM_PALETTE_COUNT:
        raise GraphicsEditorError("room_palettes must contain exactly 8 palettes")
    flat: list[int] = []
    for palette_index, palette in enumerate(palettes):
        if not isinstance(palette, list) or len(palette) != COLORS_PER_PALETTE:
            raise GraphicsEditorError(
                f"room_palettes[{palette_index}] must contain exactly 4 colors"
            )
        flat.extend(
            validate_palette_value(color, f"room_palettes[{palette_index}]")
            for color in palette
        )
    groups = value.get("room_group_colors")
    if not isinstance(groups, list) or len(groups) != ROOM_GROUP_COLOR_COUNT:
        raise GraphicsEditorError("room_group_colors must contain exactly 14 values")
    checked_groups: list[int] = []
    for index, color in enumerate(groups):
        if not isinstance(color, int) or color not in range(0x40) and color != 0x80:
            raise GraphicsEditorError(
                f"room_group_colors[{index}] must be 0..63 or special marker $80"
            )
        checked_groups.append(color)
    ending = value.get("ending_fade")
    if not isinstance(ending, list) or len(ending) != ENDING_PALETTE_VALUE_COUNT:
        raise GraphicsEditorError("ending_fade must contain exactly 3 colors")
    checked_ending = [
        validate_palette_value(color, f"ending_fade[{index}]")
        for index, color in enumerate(ending)
    ]
    return {
        "room_palettes": flat,
        "room_group_colors": checked_groups,
        "ending_fade": checked_ending,
    }


def decode_tile(data: bytes) -> list[str]:
    if len(data) != TILE_SIZE:
        raise GraphicsEditorError(f"CHR tile must contain {TILE_SIZE} bytes")
    rows: list[str] = []
    for row in range(TILE_HEIGHT):
        low = data[row]
        high = data[row + TILE_HEIGHT]
        rows.append(
            "".join(
                str(
                    ((low >> (7 - column)) & 1)
                    | (((high >> (7 - column)) & 1) << 1)
                )
                for column in range(TILE_WIDTH)
            )
        )
    return rows


def validate_rows(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or len(value) != TILE_HEIGHT:
        raise GraphicsEditorError(f"{field} must contain exactly 8 pixel rows")
    rows: list[str] = []
    for row_index, row in enumerate(value):
        if not isinstance(row, str) or len(row) != TILE_WIDTH:
            raise GraphicsEditorError(f"{field}[{row_index}] must be an 8-pixel string")
        if any(pixel not in PIXEL_VALUES for pixel in row):
            raise GraphicsEditorError(f"{field}[{row_index}] contains a non-2-bit pixel")
        rows.append(row)
    return rows


def encode_tile(rows: object, field: str = "tile rows") -> bytes:
    checked = validate_rows(rows, field)
    low = bytearray(TILE_HEIGHT)
    high = bytearray(TILE_HEIGHT)
    for row_index, row in enumerate(checked):
        for column, character in enumerate(row):
            pixel = int(character)
            mask = 0x80 >> column
            if pixel & 1:
                low[row_index] |= mask
            if pixel & 2:
                high[row_index] |= mask
    return bytes(low + high)


def export_document(image: bytes, profile: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_ines(image)
    chr_data = bytes(parsed["chr"])
    prg = bytes(parsed["prg"])
    if len(chr_data) != CHR_SIZE:
        raise GraphicsEditorError(
            f"Solomon's Key CHR must contain {CHR_SIZE} bytes, got {len(chr_data)}"
        )
    banks: list[dict[str, Any]] = []
    for bank_index in range(CHR_BANK_COUNT):
        bank_offset = bank_index * CHR_BANK_SIZE
        tiles: list[dict[str, Any]] = []
        for tile_index in range(TILES_PER_BANK):
            offset = bank_offset + tile_index * TILE_SIZE
            tiles.append(
                {
                    "index": tile_index,
                    "rows": decode_tile(chr_data[offset : offset + TILE_SIZE]),
                }
            )
        banks.append({"index": bank_index, "tiles": tiles})
    palette_template = prg_slice(
        prg, profile, "room_palette_template_address", 36
    )
    if (
        palette_template[:3] != ROOM_PALETTE_HEADER
        or palette_template[-1] != 0
    ):
        raise GraphicsEditorError("room palette template framing differs")
    palette_bytes = palette_template[3:-1]
    return {
        "schema_version": DOCUMENT_SCHEMA,
        "game": DOCUMENT_GAME,
        "source_profile": profile["id"],
        "source_rom_sha256": profile["rom"]["sha256"],
        "source_chr_sha256": profile["chr"]["sha256"],
        "layout": {
            "bank_count": CHR_BANK_COUNT,
            "bank_size": CHR_BANK_SIZE,
            "tiles_per_bank": TILES_PER_BANK,
            "tile_width": TILE_WIDTH,
            "tile_height": TILE_HEIGHT,
            "bits_per_pixel": 2,
        },
        "palette_data": {
            "room_palettes": [
                list(
                    palette_bytes[
                        index * COLORS_PER_PALETTE : (index + 1)
                        * COLORS_PER_PALETTE
                    ]
                )
                for index in range(ROOM_PALETTE_COUNT)
            ],
            "room_group_colors": list(
                prg_slice(
                    prg,
                    profile,
                    "room_group_colors_address",
                    ROOM_GROUP_COLOR_COUNT,
                )
            ),
            "ending_fade": list(
                prg_slice(
                    prg,
                    profile,
                    "ending_palette_values_address",
                    ENDING_PALETTE_VALUE_COUNT,
                )
            ),
        },
        "banks": banks,
    }


def validate_header(document: object, profile: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise GraphicsEditorError("graphics document is not an object")
    if document.get("schema_version") != DOCUMENT_SCHEMA:
        raise GraphicsEditorError("unsupported graphics document schema")
    if document.get("game") != DOCUMENT_GAME:
        raise GraphicsEditorError("graphics document belongs to another game")
    if document.get("source_profile") != profile.get("id"):
        raise GraphicsEditorError("graphics document profile differs from selected profile")
    if document.get("source_rom_sha256") != profile.get("rom", {}).get("sha256"):
        raise GraphicsEditorError("graphics document source ROM identity differs")
    if document.get("source_chr_sha256") != profile.get("chr", {}).get("sha256"):
        raise GraphicsEditorError("graphics document source CHR identity differs")
    expected_layout = {
        "bank_count": CHR_BANK_COUNT,
        "bank_size": CHR_BANK_SIZE,
        "tiles_per_bank": TILES_PER_BANK,
        "tile_width": TILE_WIDTH,
        "tile_height": TILE_HEIGHT,
        "bits_per_pixel": 2,
    }
    if document.get("layout") != expected_layout:
        raise GraphicsEditorError("graphics document layout differs from fixed CHR")
    return document


def upgrade_document(
    document: dict[str, Any], base_image: bytes, profile: dict[str, Any]
) -> dict[str, Any]:
    if document.get("schema_version") == DOCUMENT_SCHEMA:
        return document
    if document.get("schema_version") != 1:
        raise GraphicsEditorError("unsupported graphics document schema")
    upgraded = copy.deepcopy(document)
    upgraded["schema_version"] = DOCUMENT_SCHEMA
    upgraded["palette_data"] = export_document(base_image, profile)["palette_data"]
    validate_header(upgraded, profile)
    encode_document(upgraded, profile)
    encode_palette_writes(upgraded, profile)
    return upgraded


def iter_tiles(
    document: object, profile: dict[str, Any]
) -> Iterable[tuple[int, int, list[str]]]:
    checked = validate_header(document, profile)
    banks = indexed_records(checked.get("banks"), "banks", CHR_BANK_COUNT)
    for bank_index, bank in enumerate(banks):
        tiles = indexed_records(
            bank.get("tiles"), f"banks[{bank_index}].tiles", TILES_PER_BANK
        )
        for tile_index, tile in enumerate(tiles):
            yield bank_index, tile_index, validate_rows(
                tile.get("rows"), f"banks[{bank_index}].tiles[{tile_index}].rows"
            )


def encode_document(document: object, profile: dict[str, Any]) -> bytes:
    output = bytearray()
    for bank_index, tile_index, rows in iter_tiles(document, profile):
        output.extend(
            encode_tile(rows, f"banks[{bank_index}].tiles[{tile_index}].rows")
        )
    if len(output) != CHR_SIZE:
        raise GraphicsEditorError(
            f"graphics encode produced {len(output)}/{CHR_SIZE} bytes"
        )
    return bytes(output)


def encode_palette_writes(
    document: object, profile: dict[str, Any]
) -> list[tuple[int, bytes]]:
    checked = validate_header(document, profile)
    palettes = validate_palette_data(checked.get("palette_data"))
    template = (
        ROOM_PALETTE_HEADER
        + bytes(palettes["room_palettes"])
        + bytes((0,))
    )
    return [
        (
            profile_address(profile, "room_palette_template_address") - PRG_BASE,
            template,
        ),
        (
            profile_address(profile, "room_group_colors_address") - PRG_BASE,
            bytes(palettes["room_group_colors"]),
        ),
        (
            profile_address(profile, "ending_palette_values_address") - PRG_BASE,
            bytes(palettes["ending_fade"]),
        ),
    ]


def build_graphics_image(
    document: object,
    base_image: bytes,
    profile: dict[str, Any],
) -> bytes:
    if digest(base_image, "sha256") != profile["rom"]["sha256"]:
        raise GraphicsEditorError("base ROM does not match the graphics profile")
    parsed = parse_ines(base_image)
    chr_data = encode_document(document, profile)
    if len(parsed["chr"]) != len(chr_data):
        raise GraphicsEditorError("base ROM CHR allocation differs from the document")
    prg = bytearray(parsed["prg"])
    for offset, payload in encode_palette_writes(document, profile):
        if offset < 0 or offset + len(payload) > len(prg):
            raise GraphicsEditorError("graphics palette write extends outside PRG")
        prg[offset : offset + len(payload)] = payload
    return bytes(parsed["header"]) + bytes(prg) + chr_data


def canonical_document(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"))


def validate_rebuilt_document(
    document: dict[str, Any],
    image: bytes,
    profile: dict[str, Any],
) -> None:
    rebuilt = export_document(image, profile)
    if canonical_document(rebuilt) != canonical_document(document):
        raise GraphicsEditorError("rebuilt ROM does not decode to the graphics document")


def load_document(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GraphicsEditorError(f"cannot read graphics document {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GraphicsEditorError("graphics document is not an object")
    return value


def save_document(path: Path, document: dict[str, Any]) -> str:
    payload = (json.dumps(document, indent=2) + "\n").encode("utf-8")
    action = write_if_changed(path, payload)
    print(f"[{action}] graphics document: {path}")
    return action


def document_summary(document: dict[str, Any]) -> str:
    banks = document.get("banks", [])
    tile_count = sum(
        len(bank.get("tiles", [])) for bank in banks if isinstance(bank, dict)
    )
    palettes = document.get("palette_data", {}).get("room_palettes", [])
    return (
        f"{len(banks)} CHR banks, {tile_count} tiles, {tile_count * 64} pixels, "
        f"{len(palettes)} room palettes"
    )


def command_export(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    profile = get_profile(profiles, args.profile)
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    verify_reference(reference, profile)
    document = export_document(reference.read_bytes(), profile)
    save_document(args.output, document)
    print(f"[OK] {profile['id']}: {document_summary(document)}")


def command_validate(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    document = load_document(args.input)
    profile = get_profile(profiles, document.get("source_profile"))
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    verify_reference(reference, profile)
    document = upgrade_document(document, reference.read_bytes(), profile)
    image = build_graphics_image(document, reference.read_bytes(), profile)
    validate_rebuilt_document(document, image, profile)
    print(f"[OK] valid {profile['id']} graphics: {document_summary(document)}")


def command_build(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    document = load_document(args.input)
    profile = get_profile(profiles, document.get("source_profile"))
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    verify_reference(reference, profile)
    document = upgrade_document(document, reference.read_bytes(), profile)
    image = build_graphics_image(document, reference.read_bytes(), profile)
    validate_rebuilt_document(document, image, profile)
    action = write_if_changed(args.output, image)
    print(f"[{action}] graphics ROM: {args.output}")


def command_roundtrip(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    profile = get_profile(profiles, args.profile)
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    verify_reference(reference, profile)
    document = export_document(reference.read_bytes(), profile)
    original = reference.read_bytes()
    rebuilt = build_graphics_image(document, original, profile)
    validate_rebuilt_document(document, rebuilt, profile)
    if rebuilt != original:
        mismatch = next(
            index
            for index, (actual, expected) in enumerate(zip(rebuilt, original))
            if actual != expected
        )
        raise GraphicsEditorError(
            f"graphics round trip differs at ROM offset ${mismatch:04X}"
        )
    print(
        f"[OK] {profile['id']}: byte-identical graphics round trip; "
        f"{document_summary(document)}"
    )


def add_private_input_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-rom", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profiles",
        type=Path,
        default=ROOT / "config" / "revision_profiles.json",
    )
    parser.add_argument("--private-root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("--profile", required=True)
    export.add_argument("--output", required=True, type=Path)
    add_private_input_arguments(export)
    for name in ("validate", "build"):
        command = commands.add_parser(name)
        command.add_argument("--input", required=True, type=Path)
        add_private_input_arguments(command)
        if name == "build":
            command.add_argument("--output", required=True, type=Path)
    roundtrip = commands.add_parser("roundtrip")
    roundtrip.add_argument("--profile", required=True)
    add_private_input_arguments(roundtrip)
    summary = commands.add_parser("summary")
    summary.add_argument("--input", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        profiles = load_profiles(args.profiles)
        if args.command == "export":
            command_export(args, profiles)
        elif args.command == "validate":
            command_validate(args, profiles)
        elif args.command == "build":
            command_build(args, profiles)
        elif args.command == "roundtrip":
            command_roundtrip(args, profiles)
        else:
            print(document_summary(load_document(args.input)))
    except (
        GraphicsEditorError,
        RoomDataError,
        ProjectError,
        OSError,
        KeyError,
        IndexError,
        json.JSONDecodeError,
    ) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
