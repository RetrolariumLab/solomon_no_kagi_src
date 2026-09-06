#!/usr/bin/env python3
"""Import, validate, and rebuild editable Solomon's Key level documents."""

from __future__ import annotations

import argparse
import copy
import csv
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, Callable, Iterable

from project import ProjectError, digest, parse_ines, write_if_changed
from revision_profiles import (
    ROOT,
    get_profile,
    load_profiles,
    resolve_reference,
    verify_reference,
)
from room_data import (
    BLOCK_BYTES_PER_ROOM,
    MIRROR_ENEMY_SET_COUNT,
    MIRROR_SCHEDULE_COUNT,
    MIRROR_SCHEDULE_SIZE,
    ROOM_COUNT,
    ROOM_DATA_LAYOUTS,
    ROOM_HEIGHT,
    ROOM_TILE_PATTERN_COUNT,
    ROOM_TILE_PATTERN_SIZE,
    ROOM_WIDTH,
    RoomDataError,
    decode_mirror_enemy_sets,
    decode_mirror_schedules,
    decode_room,
    decode_room_tile_patterns,
    encode_blocks,
    encode_enemies,
    encode_items,
    encode_mirror_enemy_set,
    encode_mirror_schedule,
    encode_room_tile_patterns,
    encode_split_pointers,
)


DOCUMENT_SCHEMA = 1
DOCUMENT_GAME = "solomons-key-nes"
POSITION_FIELDS = ("door", "key", "player_start", "mirror_1", "mirror_2")
KEY_STATUS_BITS = {"normal": 0x00, "in_block": 0x40, "hidden": 0x80}


class LevelEditorError(ValueError):
    """An invalid editor document or level-data layout."""


def clean_position(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        raise LevelEditorError(f"position is not an object: {value!r}")
    x = value.get("x")
    y = value.get("y")
    if not isinstance(x, int) or not isinstance(y, int):
        raise LevelEditorError(f"position has non-integer coordinates: {value!r}")
    if not 0 <= x < ROOM_WIDTH or not -1 <= y <= 13:
        raise LevelEditorError(f"position is outside the encodable grid: {value!r}")
    return {"x": x, "y": y}


def encoded_lifetime(value: object) -> int:
    if not isinstance(value, int) or not 0 <= value <= 0xFF:
        raise LevelEditorError(f"enemy spawn lifetime is invalid: {value!r}")
    return (value >> 3) | ((value & 0x07) << 5)


def decoded_lifetime(value: int) -> int:
    return ((value & 0x1F) << 3) | (value >> 5)


def status_rate_byte(metadata: dict[str, Any]) -> int:
    status = metadata.get("key_status")
    rate = metadata.get("time_decrease_rate")
    if status not in KEY_STATUS_BITS:
        raise LevelEditorError(f"invalid key status: {status!r}")
    if not isinstance(rate, int) or not 0 <= rate <= 0x0F:
        raise LevelEditorError(f"invalid time decrease rate: {rate!r}")
    return KEY_STATUS_BITS[status] | rate


def export_metadata(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LevelEditorError("decoded room metadata is missing")
    result: dict[str, Any] = {}
    for field in (
        "mirror_2_schedule",
        "mirror_1_schedule",
        "mirror_2_enemy_set",
        "mirror_1_enemy_set",
        "key_status",
        "time_decrease_rate",
    ):
        result[field] = value.get(field)
    for field in POSITION_FIELDS:
        result[field] = clean_position(value.get(field))
    return result


def export_item_command(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LevelEditorError(f"decoded item command is invalid: {value!r}")
    kind = value.get("kind")
    if kind == "item":
        return {
            "kind": kind,
            "type": value.get("type"),
            "position": clean_position(value.get("position")),
        }
    if kind == "repeat":
        positions = value.get("positions")
        if not isinstance(positions, list):
            raise LevelEditorError("decoded repeated item positions are missing")
        return {
            "kind": kind,
            "type": value.get("type"),
            "positions": [clean_position(position) for position in positions],
        }
    if kind == "constellation":
        return {
            "kind": kind,
            "opcode": value.get("opcode"),
            "position": clean_position(value.get("position")),
        }
    if kind == "end":
        return {"kind": kind, "opcode": value.get("opcode")}
    raise LevelEditorError(f"unknown decoded item command: {kind!r}")


def export_room(value: dict[str, Any]) -> dict[str, Any]:
    blocks = value["blocks"]
    enemies = value["enemy_stream"]
    items = value["item_stream"]
    return {
        "number": value["room"],
        "blocks": {
            "brown": [clean_position(position) for position in blocks["brown"]],
            "white": [clean_position(position) for position in blocks["white"]],
        },
        "enemies": {
            "spawn_lifetime": enemies["spawn_lifetime"],
            "placements": [
                {
                    "type": enemy["type"],
                    "position": clean_position(enemy["position"]),
                }
                for enemy in enemies["enemies"]
            ],
        },
        "items": {
            "metadata": export_metadata(items["metadata"]),
            "commands": [
                export_item_command(command) for command in items["commands"]
            ],
        },
    }


def export_schedule(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": value["index"],
        "initial_phase": list(value["initial_phase"]),
        "loop_phase": list(value["loop_phase"]),
    }


def export_enemy_set(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": value["index"],
        "enemy_types": list(value["enemy_types"]),
        "loop_offset": value["loop_offset"],
    }


def export_document(parsed: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    prg = parsed["prg"]
    layout = ROOM_DATA_LAYOUTS[profile["room_layout"]]
    return {
        "schema_version": DOCUMENT_SCHEMA,
        "game": DOCUMENT_GAME,
        "source_profile": profile["id"],
        "source_rom_sha256": profile["rom"]["sha256"],
        "dimensions": {"width": ROOM_WIDTH, "height": ROOM_HEIGHT},
        "tile_patterns": decode_room_tile_patterns(prg, layout),
        "mirror_schedules": [
            export_schedule(value) for value in decode_mirror_schedules(prg, layout)
        ],
        "mirror_enemy_sets": [
            export_enemy_set(value) for value in decode_mirror_enemy_sets(prg, layout)
        ],
        "rooms": [
            export_room(decode_room(prg, index, layout))
            for index in range(ROOM_COUNT)
        ],
    }


def encode_item_command(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LevelEditorError(f"item command is not an object: {value!r}")
    kind = value.get("kind")
    if kind == "item":
        return {
            "kind": kind,
            "type": value.get("type"),
            "position": clean_position(value.get("position")),
        }
    if kind == "repeat":
        positions = value.get("positions")
        if not isinstance(positions, list) or not 1 <= len(positions) <= 32:
            raise LevelEditorError("repeated item must contain 1..32 positions")
        return {
            "kind": kind,
            "opcode": 0xC0 + len(positions) - 1,
            "type": value.get("type"),
            "positions": [clean_position(position) for position in positions],
        }
    if kind == "constellation":
        return {
            "kind": kind,
            "opcode": value.get("opcode"),
            "position": clean_position(value.get("position")),
        }
    if kind == "end":
        return {"kind": kind, "opcode": value.get("opcode")}
    raise LevelEditorError(f"unknown item command: {kind!r}")


def encode_room_blocks(value: object) -> bytes:
    if not isinstance(value, dict):
        raise LevelEditorError("room block planes are missing")
    return encode_blocks(
        {
            "brown": [clean_position(position) for position in value.get("brown", [])],
            "white": [clean_position(position) for position in value.get("white", [])],
        }
    )


def encode_room_enemies(value: object) -> bytes:
    if not isinstance(value, dict):
        raise LevelEditorError("room enemy data is missing")
    placements = value.get("placements")
    if not isinstance(placements, list):
        raise LevelEditorError("room enemy placements are missing")
    stream = {
        "spawn_lifetime_encoded": encoded_lifetime(value.get("spawn_lifetime")),
        "enemies": [
            {
                "type": placement.get("type") if isinstance(placement, dict) else None,
                "position": clean_position(
                    placement.get("position") if isinstance(placement, dict) else None
                ),
            }
            for placement in placements
        ],
    }
    return encode_enemies(stream)


def encode_room_items(value: object) -> bytes:
    if not isinstance(value, dict):
        raise LevelEditorError("room item data is missing")
    metadata = value.get("metadata")
    commands = value.get("commands")
    if not isinstance(metadata, dict) or not isinstance(commands, list):
        raise LevelEditorError("room item metadata or commands are missing")
    encoded_metadata = {
        field: metadata.get(field)
        for field in (
            "mirror_2_schedule",
            "mirror_1_schedule",
            "mirror_2_enemy_set",
            "mirror_1_enemy_set",
        )
    }
    encoded_metadata["status_rate_raw"] = status_rate_byte(metadata)
    for field in POSITION_FIELDS:
        encoded_metadata[field] = clean_position(metadata.get(field))
    return encode_items(
        {
            "metadata": encoded_metadata,
            "commands": [encode_item_command(command) for command in commands],
        }
    )


def require_indexed_records(
    value: object,
    name: str,
    count: int,
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != count:
        raise LevelEditorError(f"{name} must contain exactly {count} records")
    records: list[dict[str, Any]] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            raise LevelEditorError(f"{name} record {index} is not an object")
        identity = record.get("number" if name == "rooms" else "index")
        expected = index + 1 if name == "rooms" else index
        if identity != expected:
            raise LevelEditorError(
                f"{name} identities are not contiguous at {index}: {identity!r}"
            )
        records.append(record)
    return records


def validate_document_header(document: object) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise LevelEditorError("level document is not an object")
    if document.get("schema_version") != DOCUMENT_SCHEMA:
        raise LevelEditorError("unsupported level document schema")
    if document.get("game") != DOCUMENT_GAME:
        raise LevelEditorError("level document belongs to another game")
    dimensions = document.get("dimensions")
    if dimensions != {"width": ROOM_WIDTH, "height": ROOM_HEIGHT}:
        raise LevelEditorError("level document dimensions differ from 16x12")
    if not isinstance(document.get("source_profile"), str):
        raise LevelEditorError("level document has no source profile")
    source_hash = document.get("source_rom_sha256")
    if (
        not isinstance(source_hash, str)
        or len(source_hash) != 64
        or any(character not in "0123456789abcdef" for character in source_hash)
    ):
        raise LevelEditorError("level document has an invalid source ROM hash")
    return document


def pack_records(
    prg: bytearray,
    pointer_table: int,
    data_start: int,
    data_end: int,
    records: Iterable[bytes],
    name: str,
) -> tuple[int, int]:
    encoded = list(records)
    offsets: list[int] = []
    cursor = data_start
    for index, payload in enumerate(encoded):
        if cursor + len(payload) > data_end:
            raise LevelEditorError(
                f"{name} record {index} exceeds its ${data_end - data_start:04X}-byte budget"
            )
        offsets.append(cursor)
        prg[cursor : cursor + len(payload)] = payload
        cursor += len(payload)
    pointers = encode_split_pointers(offsets)
    prg[pointer_table : pointer_table + len(pointers)] = pointers
    return cursor - data_start, data_end - data_start


@dataclass(frozen=True)
class EncodedLevelDocument:
    tile_patterns: bytes
    mirror_schedules: tuple[bytes, ...]
    mirror_enemy_sets: tuple[bytes, ...]
    room_enemies: tuple[bytes, ...]
    room_blocks: bytes
    room_items: tuple[bytes, ...]
    usage: dict[str, tuple[int, int]]

    @property
    def room_enemy_sizes(self) -> tuple[int, ...]:
        return tuple(len(record) for record in self.room_enemies)

    @property
    def room_item_sizes(self) -> tuple[int, ...]:
        return tuple(len(record) for record in self.room_items)


def encode_level_document(
    document_value: object,
    profile: dict[str, Any],
) -> EncodedLevelDocument:
    """Encode every editable family and report its profile allocation."""
    document = validate_document_header(document_value)
    if document["source_profile"] != profile["id"]:
        raise LevelEditorError(
            f"document profile {document['source_profile']} does not match {profile['id']}"
        )
    if document["source_rom_sha256"] != profile["rom"]["sha256"]:
        raise LevelEditorError("document source ROM identity differs from its profile")
    layout = ROOM_DATA_LAYOUTS[profile["room_layout"]]

    tile_patterns = document.get("tile_patterns")
    if not isinstance(tile_patterns, list):
        raise LevelEditorError("tile pattern table is missing")
    encoded_patterns = encode_room_tile_patterns(tile_patterns)
    schedules = require_indexed_records(
        document.get("mirror_schedules"),
        "mirror_schedules",
        MIRROR_SCHEDULE_COUNT,
    )
    encoded_schedules = tuple(
        encode_mirror_schedule(schedule) for schedule in schedules
    )
    enemy_sets = require_indexed_records(
        document.get("mirror_enemy_sets"),
        "mirror_enemy_sets",
        MIRROR_ENEMY_SET_COUNT,
    )
    encoded_enemy_sets = tuple(
        encode_mirror_enemy_set(enemy_set) for enemy_set in enemy_sets
    )
    rooms = require_indexed_records(document.get("rooms"), "rooms", ROOM_COUNT)
    encoded_enemies = tuple(
        encode_room_enemies(room.get("enemies")) for room in rooms
    )
    encoded_blocks = b"".join(
        encode_room_blocks(room.get("blocks")) for room in rooms
    )
    expected_block_size = ROOM_COUNT * BLOCK_BYTES_PER_ROOM
    if len(encoded_blocks) != expected_block_size:
        raise LevelEditorError("room block payload size is invalid")
    encoded_items = tuple(encode_room_items(room.get("items")) for room in rooms)

    pointer_bytes = ROOM_COUNT * 2
    schedule_end = layout.mirror_schedule_data + (
        MIRROR_SCHEDULE_COUNT * MIRROR_SCHEDULE_SIZE
    )
    usage = {
        "mirror_schedules": (
            sum(map(len, encoded_schedules)),
            schedule_end - layout.mirror_schedule_data,
        ),
        "mirror_enemy_sets": (
            sum(map(len, encoded_enemy_sets)),
            layout.enemy_pointer_table - schedule_end,
        ),
        "room_enemies": (
            sum(map(len, encoded_enemies)),
            layout.block_data - (layout.enemy_pointer_table + pointer_bytes),
        ),
        "room_blocks": (len(encoded_blocks), expected_block_size),
        "room_items": (
            sum(map(len, encoded_items)),
            layout.item_data_end - (layout.item_pointer_table + pointer_bytes),
        ),
    }
    return EncodedLevelDocument(
        encoded_patterns,
        encoded_schedules,
        encoded_enemy_sets,
        encoded_enemies,
        encoded_blocks,
        encoded_items,
        usage,
    )


def build_level_image(
    document_value: object,
    base_image: bytes,
    profile: dict[str, Any],
) -> tuple[bytes, dict[str, tuple[int, int]]]:
    encoded = encode_level_document(document_value, profile)
    parsed = parse_ines(base_image)
    if digest(base_image, "sha256") != profile["rom"]["sha256"]:
        raise LevelEditorError("base ROM does not match the document profile")
    layout = ROOM_DATA_LAYOUTS[profile["room_layout"]]
    prg = bytearray(parsed["prg"])
    pattern_start = layout.room_tile_pattern_data
    pattern_end = pattern_start + ROOM_TILE_PATTERN_COUNT * ROOM_TILE_PATTERN_SIZE
    prg[pattern_start:pattern_end] = encoded.tile_patterns

    schedule_end = layout.mirror_schedule_data + (
        MIRROR_SCHEDULE_COUNT * MIRROR_SCHEDULE_SIZE
    )
    usage: dict[str, tuple[int, int]] = {}
    usage["mirror_schedules"] = pack_records(
        prg,
        layout.mirror_schedule_table,
        layout.mirror_schedule_data,
        schedule_end,
        encoded.mirror_schedules,
        "Demon Mirror schedule",
    )

    usage["mirror_enemy_sets"] = pack_records(
        prg,
        layout.mirror_enemy_set_table,
        schedule_end,
        layout.enemy_pointer_table,
        encoded.mirror_enemy_sets,
        "Demon Mirror enemy set",
    )

    pointer_bytes = ROOM_COUNT * 2
    enemy_data_start = layout.enemy_pointer_table + pointer_bytes
    usage["room_enemies"] = pack_records(
        prg,
        layout.enemy_pointer_table,
        enemy_data_start,
        layout.block_data,
        encoded.room_enemies,
        "room enemy stream",
    )

    expected_block_size = ROOM_COUNT * BLOCK_BYTES_PER_ROOM
    prg[layout.block_data : layout.block_data + expected_block_size] = encoded.room_blocks
    usage["room_blocks"] = (len(encoded.room_blocks), expected_block_size)

    item_data_start = layout.item_pointer_table + pointer_bytes
    usage["room_items"] = pack_records(
        prg,
        layout.item_pointer_table,
        item_data_start,
        layout.item_data_end,
        encoded.room_items,
        "room item stream",
    )
    if usage != encoded.usage:
        raise LevelEditorError("level allocation calculation disagrees with ROM packing")
    image = bytes(parsed["header"]) + bytes(prg) + bytes(parsed["chr"])
    return image, usage


def load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LevelEditorError(f"cannot read level document {path}: {exc}") from exc
    return validate_document_header(document)


def save_document(path: Path, document: dict[str, Any]) -> str:
    payload = (json.dumps(document, indent=2) + "\n").encode("utf-8")
    action = write_if_changed(path, payload)
    print(f"[{action}] level document: {path}")
    return action


def canonical_document(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"))


def validate_rebuilt_document(
    document: dict[str, Any],
    image: bytes,
    profile: dict[str, Any],
) -> None:
    parsed = parse_ines(image)
    rebuilt = export_document(parsed, profile)
    rebuilt["source_rom_sha256"] = document["source_rom_sha256"]
    if canonical_document(rebuilt) != canonical_document(document):
        raise LevelEditorError("rebuilt ROM does not decode to the edited document")


def usage_text(usage: dict[str, tuple[int, int]]) -> str:
    return ", ".join(
        f"{name}={used}/{capacity}"
        for name, (used, capacity) in usage.items()
    )


def command_export(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    profile = get_profile(profiles, args.profile)
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    parsed = verify_reference(reference, profile)
    document = export_document(parsed, profile)
    save_document(args.output, document)
    print(f"[OK] exported {ROOM_COUNT} rooms from {profile['id']}")


def command_build(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    document = load_document(args.input)
    profile = get_profile(profiles, document["source_profile"])
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    verify_reference(reference, profile)
    base_image = reference.read_bytes()
    image, usage = build_level_image(document, base_image, profile)
    validate_rebuilt_document(document, image, profile)
    action = write_if_changed(args.output, image)
    print(f"[{action}] level ROM: {args.output}")
    print(f"[OK] {usage_text(usage)}")


def command_validate(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    document = load_document(args.input)
    profile = get_profile(profiles, document["source_profile"])
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    verify_reference(reference, profile)
    image, usage = build_level_image(document, reference.read_bytes(), profile)
    validate_rebuilt_document(document, image, profile)
    print(f"[OK] valid {profile['id']} level document: {usage_text(usage)}")


def command_roundtrip(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    profile = get_profile(profiles, args.profile)
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    parsed = verify_reference(reference, profile)
    document = export_document(parsed, profile)
    rebuilt, usage = build_level_image(document, reference.read_bytes(), profile)
    if rebuilt != reference.read_bytes():
        for offset, (actual, expected) in enumerate(zip(rebuilt, reference.read_bytes())):
            if actual != expected:
                raise LevelEditorError(
                    f"untouched {profile['id']} round trip differs at file "
                    f"offset ${offset:05X}: ${actual:02X} != ${expected:02X}"
                )
        raise LevelEditorError(f"untouched {profile['id']} round trip size differs")
    validate_rebuilt_document(document, rebuilt, profile)
    print(
        f"[OK] {profile['id']}: untouched {ROOM_COUNT}-room document is "
        f"byte-identical ({usage_text(usage)})"
    )


def command_summary(args: argparse.Namespace) -> None:
    document = load_document(args.input)
    rooms = require_indexed_records(document.get("rooms"), "rooms", ROOM_COUNT)
    brown = sum(len(room["blocks"]["brown"]) for room in rooms)
    white = sum(len(room["blocks"]["white"]) for room in rooms)
    enemies = sum(len(room["enemies"]["placements"]) for room in rooms)
    commands = sum(len(room["items"]["commands"]) for room in rooms)
    print(
        f"profile={document['source_profile']} rooms={len(rooms)} "
        f"brown_blocks={brown} white_blocks={white} enemies={enemies} "
        f"item_commands={commands}"
    )


def load_level_block_reference(path: Path) -> list[list[list[int]]]:
    """Read the author's 53-room, 16x12 combined-bitplane CSV export."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    levels: list[list[list[int]]] = []
    index = 0
    while index < len(rows):
        row = rows[index]
        if not row or not row[0].startswith("Level "):
            index += 1
            continue
        expected_name = f"Level {len(levels) + 1}"
        if row[0] != expected_name:
            raise LevelEditorError(
                f"level-block CSV expected {expected_name}, found {row[0]!r}"
            )
        level: list[list[int]] = []
        for y in range(ROOM_HEIGHT):
            index += 1
            if index >= len(rows):
                raise LevelEditorError(f"{expected_name} ends before row {y + 1}")
            data_row = rows[index]
            if len(data_row) < 2 or data_row[1] != str(y + 1):
                raise LevelEditorError(f"{expected_name} has invalid row {y + 1}")
            try:
                values = [int(token, 16) for token in data_row[0].split(",")]
            except ValueError as exc:
                raise LevelEditorError(
                    f"{expected_name} row {y + 1} contains a non-hex cell"
                ) from exc
            if len(values) != ROOM_WIDTH or any(value not in range(4) for value in values):
                raise LevelEditorError(
                    f"{expected_name} row {y + 1} must contain 16 values 00..03"
                )
            level.append(values)
        levels.append(level)
        index += 1
    if len(levels) != ROOM_COUNT:
        raise LevelEditorError(
            f"level-block CSV contains {len(levels)}/{ROOM_COUNT} levels"
        )
    return levels


def document_block_matrices(document: dict[str, Any]) -> list[list[list[int]]]:
    rooms = require_indexed_records(document.get("rooms"), "rooms", ROOM_COUNT)
    matrices: list[list[list[int]]] = []
    for room in rooms:
        brown = {(cell["x"], cell["y"]) for cell in room["blocks"]["brown"]}
        white = {(cell["x"], cell["y"]) for cell in room["blocks"]["white"]}
        matrices.append(
            [
                [
                    int((x, y) in brown) | (int((x, y) in white) << 1)
                    for x in range(ROOM_WIDTH)
                ]
                for y in range(ROOM_HEIGHT)
            ]
        )
    return matrices


def validate_level_block_reference(
    document: dict[str, Any], reference: list[list[list[int]]]
) -> int:
    actual = document_block_matrices(document)
    for room in range(ROOM_COUNT):
        for y in range(ROOM_HEIGHT):
            for x in range(ROOM_WIDTH):
                if actual[room][y][x] != reference[room][y][x]:
                    raise LevelEditorError(
                        f"level-block mismatch at room {room + 1}, ({x}, {y}): "
                        f"CSV={reference[room][y][x]:02X}, ROM={actual[room][y][x]:02X}"
                    )
    return ROOM_COUNT * ROOM_WIDTH * ROOM_HEIGHT


def command_check_block_reference(
    args: argparse.Namespace, profiles: dict[str, Any]
) -> None:
    profile = get_profile(profiles, args.profile)
    reference_path = resolve_reference(profile, args.private_root, args.base_rom)
    parsed = verify_reference(reference_path, profile)
    document = export_document(parsed, profile)
    cell_count = validate_level_block_reference(
        document, load_level_block_reference(args.csv)
    )
    print(
        f"[OK] {profile['id']}: {cell_count} room cells match {args.csv} "
        f"including both block bitplanes"
    )


def add_private_input_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--private-root", type=Path, default=ROOT)
    parser.add_argument("--base-rom", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profiles",
        type=Path,
        default=ROOT / "config" / "revision_profiles.json",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    export = commands.add_parser("export", help="export a revision to editable JSON")
    export.add_argument("--profile", required=True)
    export.add_argument("--output", required=True, type=Path)
    add_private_input_arguments(export)

    for name, help_text in (
        ("build", "build an edited ROM from JSON"),
        ("validate", "validate and round-trip an edited JSON document"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--input", required=True, type=Path)
        if name == "build":
            command.add_argument("--output", required=True, type=Path)
        add_private_input_arguments(command)

    roundtrip = commands.add_parser(
        "roundtrip", help="prove untouched JSON import/export byte identity"
    )
    roundtrip.add_argument("--profile", required=True)
    add_private_input_arguments(roundtrip)

    summary = commands.add_parser("summary", help="summarize an editor document")
    summary.add_argument("--input", required=True, type=Path)

    block_reference = commands.add_parser(
        "check-block-reference", help="compare room geometry with an external CSV"
    )
    block_reference.add_argument("--profile", required=True)
    block_reference.add_argument("--csv", required=True, type=Path)
    add_private_input_arguments(block_reference)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        profiles = load_profiles(args.profiles)
        commands: dict[str, Callable[..., None]] = {
            "export": command_export,
            "build": command_build,
            "validate": command_validate,
            "roundtrip": command_roundtrip,
            "check-block-reference": command_check_block_reference,
        }
        if args.command == "summary":
            command_summary(args)
        else:
            commands[args.command](args, profiles)
    except (
        OSError,
        KeyError,
        TypeError,
        ProjectError,
        RoomDataError,
        LevelEditorError,
    ) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
