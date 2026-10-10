#!/usr/bin/env python3
"""Decode all 53 Solomon's Key room records as JSON."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Iterable


ROOM_COUNT = 53
ROOM_WIDTH = 16
ROOM_HEIGHT = 12
BITPLANE_SIZE = ROOM_WIDTH * ROOM_HEIGHT // 8
BLOCK_BYTES_PER_ROOM = BITPLANE_SIZE * 2
ROOM_TILE_PATTERN_COUNT = 58
ROOM_TILE_PATTERN_SIZE = 4
EXPECTED_ROOM_CHR_BANKS = (
    0, 0, 1, 0, 2, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 2, 2,
    0, 1, 0, 1, 2, 1, 2, 2, 1, 1, 1, 0, 1, 1, 2, 0, 2, 2,
    1, 1, 2, 2, 0, 1, 1, 2, 1, 1, 0, 2, 2, 0, 0, 1, 2,
)
EXPECTED_ROOM_CHR_BANK_COUNTS = (17, 21, 15, 0)

# Offsets within the 32 KiB PRG. Published file offsets include the 16-byte
# iNES header, hence the $10 difference from the ROM-map document. The USA and
# Japan room formats share addresses; the Europe revision moves this complete
# data area $80 bytes earlier.


@dataclass(frozen=True)
class RoomDataLayout:
    name: str
    room_tile_pattern_data: int
    special_room_item_positions: int
    special_room_item_types: int
    mirror_schedule_table: int
    mirror_enemy_set_table: int
    mirror_schedule_data: int
    enemy_pointer_table: int
    block_data: int
    item_pointer_table: int
    item_data_end: int
    audio_engine: int
    solomon_seal_positions: int
    princess_room_hidden_cells: int
    room_20_special_bitplane: int
    room_30_special_bitplane: int


USA_ROOM_DATA_LAYOUT = RoomDataLayout(
    name="usa",
    room_tile_pattern_data=0x5000,
    special_room_item_positions=0x19C2,
    special_room_item_types=0x19E2,
    mirror_schedule_table=0x5C00,
    mirror_enemy_set_table=0x5C20,
    mirror_schedule_data=0x5C42,
    enemy_pointer_table=0x5CEC,
    block_data=0x602C,
    item_pointer_table=0x6A1C,
    item_data_end=0x6FC4,
    audio_engine=0x7000,
    solomon_seal_positions=0x3FC6,
    princess_room_hidden_cells=0x3FD6,
    room_20_special_bitplane=0x3FE2,
    room_30_special_bitplane=0x3FFA,
)
JAPAN_ROOM_DATA_LAYOUT = RoomDataLayout(
    name="japan",
    room_tile_pattern_data=0x5000,
    special_room_item_positions=0x1945,
    special_room_item_types=0x1965,
    mirror_schedule_table=0x5C00,
    mirror_enemy_set_table=0x5C20,
    mirror_schedule_data=0x5C42,
    enemy_pointer_table=0x5CEC,
    block_data=0x602C,
    item_pointer_table=0x6A1C,
    item_data_end=0x6FC4,
    audio_engine=0x7000,
    solomon_seal_positions=0x3B96,
    princess_room_hidden_cells=0x3BA6,
    room_20_special_bitplane=0x3BB2,
    room_30_special_bitplane=0x3BCA,
)
EUROPE_ROOM_DATA_LAYOUT = RoomDataLayout(
    name="europe",
    room_tile_pattern_data=0x4F80,
    special_room_item_positions=0x19CA,
    special_room_item_types=0x19EA,
    mirror_schedule_table=0x5B80,
    mirror_enemy_set_table=0x5BA0,
    mirror_schedule_data=0x5BC2,
    enemy_pointer_table=0x5C6C,
    block_data=0x5FAC,
    item_pointer_table=0x699C,
    item_data_end=0x6F44,
    audio_engine=0x6F80,
    solomon_seal_positions=0x3FC6,
    princess_room_hidden_cells=0x3FD6,
    room_20_special_bitplane=0x3FE2,
    room_30_special_bitplane=0x3FFA,
)
ROOM_DATA_LAYOUTS = {
    layout.name: layout
    for layout in (
        USA_ROOM_DATA_LAYOUT,
        JAPAN_ROOM_DATA_LAYOUT,
        EUROPE_ROOM_DATA_LAYOUT,
    )
}

# Compatibility names for source-generation tools and callers that target the
# reconstructed USA image.
ROOM_TILE_PATTERN_DATA = USA_ROOM_DATA_LAYOUT.room_tile_pattern_data
SPECIAL_ROOM_RANDOM_POSITION_COUNT = 32
SPECIAL_ROOM_RANDOM_ITEM_COUNT = 16
SOLOMON_SEAL_ROOMS = (9, 13, 17, 19, 21, 29, 46, 47)
PRINCESS_ROOM_HIDDEN_CELL_COUNT = 12
SPECIAL_ROOM_DATA_SIZE = 116
MIRROR_SCHEDULE_TABLE = USA_ROOM_DATA_LAYOUT.mirror_schedule_table
MIRROR_ENEMY_SET_TABLE = USA_ROOM_DATA_LAYOUT.mirror_enemy_set_table
MIRROR_SCHEDULE_DATA = USA_ROOM_DATA_LAYOUT.mirror_schedule_data
MIRROR_SCHEDULE_COUNT = 16
MIRROR_SCHEDULE_SIZE = 8
MIRROR_ENEMY_SET_COUNT = 17
MIRROR_ENEMY_SET_LOOP_BASE = 0x90
ENEMY_TYPE_MINIMUM = 0x18
ENEMY_TYPE_MAXIMUM = 0x83
ENEMY_POINTER_TABLE = USA_ROOM_DATA_LAYOUT.enemy_pointer_table
BLOCK_DATA = USA_ROOM_DATA_LAYOUT.block_data
ITEM_POINTER_TABLE = USA_ROOM_DATA_LAYOUT.item_pointer_table
ITEM_DATA_END = USA_ROOM_DATA_LAYOUT.item_data_end
AUDIO_ENGINE = USA_ROOM_DATA_LAYOUT.audio_engine


class RoomDataError(ValueError):
    pass


def extract_prg(image: bytes) -> bytes:
    if image[:4] == b"NES\x1a":
        if len(image) < 16:
            raise RoomDataError("truncated iNES header")
        trainer_size = 512 if image[6] & 0x04 else 0
        prg_size = image[4] * 16_384
        start = 16 + trainer_size
        end = start + prg_size
        if len(image) < end:
            raise RoomDataError("truncated PRG")
        return image[start:end]
    if len(image) == 32_768:
        return image
    raise RoomDataError("expected a Solomon's Key iNES image or 32 KiB PRG")


def position(value: int) -> dict[str, int]:
    return {"x": value & 0x0F, "y": (value >> 4) - 1, "raw": value}


def rotate_left_3(value: int) -> int:
    return ((value & 0x1F) << 3) | (value >> 5)


def decode_room_tile_patterns(
    prg: bytes, layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT
) -> list[dict[str, int]]:
    start = layout.room_tile_pattern_data
    end = start + ROOM_TILE_PATTERN_COUNT * ROOM_TILE_PATTERN_SIZE
    if len(prg) < end:
        raise RoomDataError("truncated RoomMap tile pattern table")
    patterns: list[dict[str, int]] = []
    for index in range(ROOM_TILE_PATTERN_COUNT):
        offset = start + index * ROOM_TILE_PATTERN_SIZE
        first, top_right, bottom_left, bottom_right = prg[offset : offset + 4]
        patterns.append(
            {
                "index": index,
                "palette": first & 0x03,
                "top_left": first & 0xFC,
                "top_right": top_right,
                "bottom_left": bottom_left,
                "bottom_right": bottom_right,
            }
        )
    return patterns


def encode_room_tile_patterns(patterns: list[dict[str, int]]) -> bytes:
    if len(patterns) != ROOM_TILE_PATTERN_COUNT:
        raise RoomDataError(
            f"RoomMap tile pattern count must be {ROOM_TILE_PATTERN_COUNT}"
        )
    encoded = bytearray()
    for index, pattern in enumerate(patterns):
        if pattern.get("index") != index:
            raise RoomDataError("RoomMap tile pattern indices are not contiguous")
        palette = pattern.get("palette")
        top_left = pattern.get("top_left")
        other_tiles = (
            pattern.get("top_right"),
            pattern.get("bottom_left"),
            pattern.get("bottom_right"),
        )
        if not isinstance(palette, int) or not 0 <= palette <= 3:
            raise RoomDataError(f"invalid RoomMap palette at pattern {index}")
        if not isinstance(top_left, int) or not 0 <= top_left <= 0xFC:
            raise RoomDataError(f"invalid top-left tile at pattern {index}")
        if top_left & 0x03:
            raise RoomDataError(f"top-left tile overlaps palette at pattern {index}")
        if any(
            not isinstance(tile, int) or not 0 <= tile <= 0xFF
            for tile in other_tiles
        ):
            raise RoomDataError(f"invalid RoomMap tile byte at pattern {index}")
        encoded.extend((top_left | palette, *other_tiles))
    return bytes(encoded)


def split_pointer(prg: bytes, table: int, index: int, count: int) -> int:
    low = prg[table + index]
    high = prg[table + count + index]
    cpu_address = low | (high << 8)
    if not 0x8000 <= cpu_address <= 0xFFFF:
        raise RoomDataError(f"pointer outside PRG CPU window: ${cpu_address:04X}")
    return cpu_address - 0x8000


def decode_bitplane(data: bytes) -> list[list[bool]]:
    if len(data) != BITPLANE_SIZE:
        raise RoomDataError(f"bitplane must be {BITPLANE_SIZE} bytes")
    rows: list[list[bool]] = []
    for y in range(ROOM_HEIGHT):
        row: list[bool] = []
        for packed in data[y * 2 : y * 2 + 2]:
            row.extend(bool(packed & (1 << bit)) for bit in range(7, -1, -1))
        rows.append(row)
    return rows


def true_positions(rows: Iterable[Iterable[bool]]) -> list[dict[str, int]]:
    return [
        {"x": x, "y": y}
        for y, row in enumerate(rows)
        for x, occupied in enumerate(row)
        if occupied
    ]


def encode_position(value: dict[str, int]) -> int:
    raw = value.get("raw")
    if raw is not None:
        if position(raw) != value:
            raise RoomDataError(f"position fields disagree: {value!r}")
        return raw
    x = value.get("x")
    y = value.get("y")
    if not isinstance(x, int) or not isinstance(y, int) or not 0 <= x < ROOM_WIDTH:
        raise RoomDataError(f"invalid position: {value!r}")
    encoded_y = y + 1
    if not 0 <= encoded_y <= 0x0F:
        raise RoomDataError(f"invalid position: {value!r}")
    return (encoded_y << 4) | x


def encode_bitplane(positions: Iterable[dict[str, int]]) -> bytes:
    output = bytearray(BITPLANE_SIZE)
    occupied: set[tuple[int, int]] = set()
    for value in positions:
        x = value.get("x")
        y = value.get("y")
        if not isinstance(x, int) or not isinstance(y, int):
            raise RoomDataError(f"invalid block position: {value!r}")
        if not 0 <= x < ROOM_WIDTH or not 0 <= y < ROOM_HEIGHT:
            raise RoomDataError(f"block position outside room: {value!r}")
        coordinate = (x, y)
        if coordinate in occupied:
            raise RoomDataError(f"duplicate block position: {value!r}")
        occupied.add(coordinate)
        output[y * 2 + x // 8] |= 0x80 >> (x % 8)
    return bytes(output)


def encode_split_pointers(offsets: Iterable[int]) -> bytes:
    cpu_addresses = [offset + 0x8000 for offset in offsets]
    if any(not 0x8000 <= address <= 0xFFFF for address in cpu_addresses):
        raise RoomDataError("pointer outside PRG CPU window")
    return bytes(address & 0xFF for address in cpu_addresses) + bytes(
        address >> 8 for address in cpu_addresses
    )


def decode_mirror_schedules(
    prg: bytes, layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT
) -> list[dict[str, object]]:
    schedules: list[dict[str, object]] = []
    for index in range(MIRROR_SCHEDULE_COUNT):
        offset = split_pointer(
            prg, layout.mirror_schedule_table, index, MIRROR_SCHEDULE_COUNT
        )
        data = prg[offset : offset + MIRROR_SCHEDULE_SIZE]
        if len(data) != MIRROR_SCHEDULE_SIZE:
            raise RoomDataError(f"truncated Demon Mirror schedule {index}")
        schedules.append(
            {
                "index": index,
                "prg_offset": offset,
                "initial_phase": list(data[:4]),
                "loop_phase": list(data[4:]),
            }
        )
    return schedules


def encode_mirror_schedule(schedule: dict[str, object]) -> bytes:
    initial = schedule.get("initial_phase")
    loop = schedule.get("loop_phase")
    if (
        not isinstance(initial, list)
        or not isinstance(loop, list)
        or len(initial) != 4
        or len(loop) != 4
        or any(not isinstance(value, int) or not 0 <= value <= 0xFF for value in initial + loop)
    ):
        raise RoomDataError(f"invalid Demon Mirror schedule: {schedule!r}")
    return bytes(initial + loop)


def decode_mirror_enemy_sets(
    prg: bytes, layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT
) -> list[dict[str, object]]:
    enemy_sets: list[dict[str, object]] = []
    for index in range(MIRROR_ENEMY_SET_COUNT):
        offset = split_pointer(
            prg, layout.mirror_enemy_set_table, index, MIRROR_ENEMY_SET_COUNT
        )
        cursor = offset
        enemy_types: list[int] = []
        while cursor < layout.enemy_pointer_table:
            value = prg[cursor]
            cursor += 1
            if value >= MIRROR_ENEMY_SET_LOOP_BASE:
                enemy_sets.append(
                    {
                        "index": index,
                        "prg_offset": offset,
                        "encoded_size": cursor - offset,
                        "enemy_types": enemy_types,
                        "loop_offset": value - MIRROR_ENEMY_SET_LOOP_BASE,
                    }
                )
                break
            enemy_types.append(value)
        else:
            raise RoomDataError(f"unterminated Demon Mirror enemy set {index}")
    return enemy_sets


def encode_mirror_enemy_set(enemy_set: dict[str, object]) -> bytes:
    enemy_types = enemy_set.get("enemy_types")
    loop_offset = enemy_set.get("loop_offset")
    if not isinstance(enemy_types, list) or not enemy_types or any(
        not isinstance(value, int)
        or not ENEMY_TYPE_MINIMUM <= value <= ENEMY_TYPE_MAXIMUM
        for value in enemy_types
    ):
        raise RoomDataError(f"invalid Demon Mirror enemy types: {enemy_types!r}")
    if (
        not isinstance(loop_offset, int)
        or not 0 <= loop_offset < len(enemy_types)
    ):
        raise RoomDataError(f"invalid Demon Mirror loop offset: {loop_offset!r}")
    return bytes(enemy_types + [MIRROR_ENEMY_SET_LOOP_BASE + loop_offset])


def decode_enemies(
    prg: bytes,
    room_index: int,
    layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT,
) -> dict[str, object]:
    offset = split_pointer(prg, layout.enemy_pointer_table, room_index, ROOM_COUNT)
    encoded_lifetime = prg[offset]
    enemies: list[dict[str, object]] = []
    cursor = offset + 1
    while True:
        enemy_type = prg[cursor]
        cursor += 1
        if enemy_type == 0:
            break
        enemies.append({"type": enemy_type, "position": position(prg[cursor])})
        cursor += 1
    return {
        "prg_offset": offset,
        "encoded_size": cursor - offset,
        "spawn_lifetime": rotate_left_3(encoded_lifetime),
        "spawn_lifetime_encoded": encoded_lifetime,
        "enemies": enemies,
    }


def encode_enemies(stream: dict[str, object]) -> bytes:
    encoded_lifetime = stream.get("spawn_lifetime_encoded")
    enemies = stream.get("enemies")
    if not isinstance(encoded_lifetime, int) or not 0 <= encoded_lifetime <= 0xFF:
        raise RoomDataError("invalid encoded enemy lifetime")
    if not isinstance(enemies, list):
        raise RoomDataError("enemy list is missing")
    output = bytearray((encoded_lifetime,))
    for enemy in enemies:
        if not isinstance(enemy, dict) or not isinstance(enemy.get("type"), int):
            raise RoomDataError(f"invalid enemy record: {enemy!r}")
        enemy_type = enemy["type"]
        if not ENEMY_TYPE_MINIMUM <= enemy_type <= ENEMY_TYPE_MAXIMUM:
            raise RoomDataError(f"invalid enemy type: {enemy_type!r}")
        enemy_position = enemy.get("position")
        if not isinstance(enemy_position, dict):
            raise RoomDataError(f"invalid enemy position: {enemy_position!r}")
        output.extend((enemy_type, encode_position(enemy_position)))
    output.append(0)
    return bytes(output)


def decode_items(
    prg: bytes,
    room_index: int,
    layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT,
) -> dict[str, object]:
    offset = split_pointer(prg, layout.item_pointer_table, room_index, ROOM_COUNT)
    header = prg[offset : offset + 10]
    if len(header) != 10:
        raise RoomDataError("truncated item metadata")
    status_rate = header[4]
    metadata: dict[str, object] = {
        "mirror_2_schedule": header[0],
        "mirror_1_schedule": header[1],
        "mirror_2_enemy_set": header[2],
        "mirror_1_enemy_set": header[3],
        "key_status": (
            "hidden" if status_rate >= 0x80 else
            "in_block" if status_rate >= 0x40 else
            "normal"
        ),
        "time_decrease_rate": status_rate & 0x0F,
        "status_rate_raw": status_rate,
        "door": position(header[5]),
        "key": position(header[6]),
        "player_start": position(header[7]),
        "mirror_1": position(header[8]),
        "mirror_2": position(header[9]),
    }
    items: list[dict[str, object]] = []
    commands: list[dict[str, object]] = []
    constellation: dict[str, object] | None = None
    cursor = offset + 10
    chr_bank = 0
    while True:
        code = prg[cursor]
        cursor += 1
        if code == 0 or 0xE0 <= code <= 0xEF:
            commands.append({"kind": "end", "opcode": code})
            chr_bank = (code >> 2) & 3
            break
        if 0xF0 <= code <= 0xFB:
            constellation = {"type": code, "position": position(prg[cursor])}
            commands.append(
                {
                    "kind": "constellation",
                    "opcode": code,
                    "position": position(prg[cursor]),
                }
            )
            cursor += 1
            chr_bank = (code >> 2) & 3
            break
        if 0xC0 <= code <= 0xDF:
            count = code - 0xC0 + 1
            item_type = prg[cursor]
            cursor += 1
            positions: list[dict[str, int]] = []
            for _ in range(count):
                item_position = position(prg[cursor])
                positions.append(item_position)
                items.append({"type": item_type, "position": item_position})
                cursor += 1
            commands.append(
                {
                    "kind": "repeat",
                    "opcode": code,
                    "type": item_type,
                    "positions": positions,
                }
            )
            continue
        item_position = position(prg[cursor])
        commands.append(
            {"kind": "item", "type": code, "position": item_position}
        )
        items.append({"type": code, "position": item_position})
        cursor += 1
    return {
        "prg_offset": offset,
        "encoded_size": cursor - offset,
        "metadata": metadata,
        "chr_bank": chr_bank,
        "constellation": constellation,
        "items": items,
        "commands": commands,
    }


def encode_items(stream: dict[str, object]) -> bytes:
    metadata = stream.get("metadata")
    commands = stream.get("commands")
    if not isinstance(metadata, dict) or not isinstance(commands, list):
        raise RoomDataError("item metadata or commands are missing")
    status_rate = metadata.get("status_rate_raw")
    if not isinstance(status_rate, int) or not 0 <= status_rate <= 0xFF:
        raise RoomDataError("invalid raw key-status/time-rate byte")
    header_values: list[int] = []
    for field in (
        "mirror_2_schedule",
        "mirror_1_schedule",
        "mirror_2_enemy_set",
        "mirror_1_enemy_set",
    ):
        value = metadata.get(field)
        if not isinstance(value, int) or not 0 <= value <= 0xFF:
            raise RoomDataError(f"invalid item metadata field: {field}")
        header_values.append(value)
    header_values.append(status_rate)
    for field in ("door", "key", "player_start", "mirror_1", "mirror_2"):
        value = metadata.get(field)
        if not isinstance(value, dict):
            raise RoomDataError(f"invalid item metadata position: {field}")
        header_values.append(encode_position(value))
    output = bytearray(header_values)
    for command in commands:
        if not isinstance(command, dict):
            raise RoomDataError(f"invalid item command: {command!r}")
        kind = command.get("kind")
        if kind == "end":
            opcode = command.get("opcode")
            if not isinstance(opcode, int) or not (opcode == 0 or 0xE0 <= opcode <= 0xEF):
                raise RoomDataError(f"invalid item end command: {command!r}")
            output.append(opcode)
        elif kind == "constellation":
            opcode = command.get("opcode")
            value = command.get("position")
            if not isinstance(opcode, int) or not 0xF0 <= opcode <= 0xFB or not isinstance(value, dict):
                raise RoomDataError(f"invalid constellation command: {command!r}")
            output.extend((opcode, encode_position(value)))
        elif kind == "repeat":
            opcode = command.get("opcode")
            item_type = command.get("type")
            positions = command.get("positions")
            if (
                not isinstance(opcode, int)
                or not 0xC0 <= opcode <= 0xDF
                or not isinstance(item_type, int)
                or not 0 <= item_type <= 0xFF
                or not isinstance(positions, list)
                or len(positions) != opcode - 0xC0 + 1
            ):
                raise RoomDataError(f"invalid repeated-item command: {command!r}")
            output.extend((opcode, item_type))
            for value in positions:
                if not isinstance(value, dict):
                    raise RoomDataError(f"invalid repeated-item position: {value!r}")
                output.append(encode_position(value))
        elif kind == "item":
            item_type = command.get("type")
            value = command.get("position")
            if (
                not isinstance(item_type, int)
                or not (1 <= item_type < 0xC0 or 0xFC <= item_type <= 0xFF)
                or not isinstance(value, dict)
            ):
                raise RoomDataError(f"invalid item command: {command!r}")
            output.extend((item_type, encode_position(value)))
        else:
            raise RoomDataError(f"unknown item command: {kind!r}")
    if not commands or commands[-1].get("kind") not in {"end", "constellation"}:
        raise RoomDataError("item command stream has no terminator")
    return bytes(output)


def decode_blocks(
    prg: bytes,
    room_index: int,
    layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT,
) -> dict[str, object]:
    offset = layout.block_data + room_index * BLOCK_BYTES_PER_ROOM
    brown = decode_bitplane(prg[offset : offset + BITPLANE_SIZE])
    white = decode_bitplane(
        prg[offset + BITPLANE_SIZE : offset + BLOCK_BYTES_PER_ROOM]
    )
    return {
        "prg_offset": offset,
        "brown": true_positions(brown),
        "white": true_positions(white),
    }


def encode_blocks(blocks: dict[str, object]) -> bytes:
    brown = blocks.get("brown")
    white = blocks.get("white")
    if not isinstance(brown, list) or not isinstance(white, list):
        raise RoomDataError("block planes are missing")
    return encode_bitplane(brown) + encode_bitplane(white)


def decode_special_room_data(
    prg: bytes,
    layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT,
) -> dict[str, object]:
    """Decode fixed tables consumed by room-specific scripts and loaders."""
    position_start = layout.special_room_item_positions
    type_start = layout.special_room_item_types
    seal_start = layout.solomon_seal_positions
    princess_start = layout.princess_room_hidden_cells
    room_20_start = layout.room_20_special_bitplane
    room_30_start = layout.room_30_special_bitplane
    return {
        "random_bonus_room": {
            "positions": [
                position(value)
                for value in prg[
                    position_start : position_start
                    + SPECIAL_ROOM_RANDOM_POSITION_COUNT
                ]
            ],
            "item_types": list(
                prg[type_start : type_start + SPECIAL_ROOM_RANDOM_ITEM_COUNT]
            ),
        },
        "solomon_seals": [
            {"room": room, "position": position(prg[seal_start + index])}
            for index, room in enumerate(SOLOMON_SEAL_ROOMS)
        ],
        "princess_room_hidden_cells": [
            position(value)
            for value in prg[
                princess_start : princess_start + PRINCESS_ROOM_HIDDEN_CELL_COUNT
            ]
        ],
        "room_20_bat_symbols": true_positions(
            decode_bitplane(prg[room_20_start : room_20_start + BITPLANE_SIZE])
        ),
        "room_30_blue_opals": true_positions(
            decode_bitplane(prg[room_30_start : room_30_start + BITPLANE_SIZE])
        ),
    }


def encode_special_room_data(value: object) -> dict[str, bytes]:
    if not isinstance(value, dict):
        raise RoomDataError("special-room data is missing")
    bonus = value.get("random_bonus_room")
    seals = value.get("solomon_seals")
    princess = value.get("princess_room_hidden_cells")
    room_20 = value.get("room_20_bat_symbols")
    room_30 = value.get("room_30_blue_opals")
    if not isinstance(bonus, dict):
        raise RoomDataError("random bonus-room data is missing")
    positions = bonus.get("positions")
    item_types = bonus.get("item_types")
    if (
        not isinstance(positions, list)
        or len(positions) != SPECIAL_ROOM_RANDOM_POSITION_COUNT
        or any(not isinstance(position_value, dict) for position_value in positions)
    ):
        raise RoomDataError(
            f"random bonus room must contain {SPECIAL_ROOM_RANDOM_POSITION_COUNT} positions"
        )
    if (
        not isinstance(item_types, list)
        or len(item_types) != SPECIAL_ROOM_RANDOM_ITEM_COUNT
        or any(
            not isinstance(item, int) or not 1 <= item < 0xC0
            for item in item_types
        )
    ):
        raise RoomDataError(
            f"random bonus room must contain {SPECIAL_ROOM_RANDOM_ITEM_COUNT} item types"
        )
    if not isinstance(seals, list) or len(seals) != len(SOLOMON_SEAL_ROOMS):
        raise RoomDataError("Solomon Seal table must contain eight room positions")
    seal_positions: list[dict[str, int]] = []
    for expected_room, record in zip(SOLOMON_SEAL_ROOMS, seals):
        if not isinstance(record, dict) or record.get("room") != expected_room:
            raise RoomDataError("Solomon Seal room identities are not canonical")
        position_value = record.get("position")
        if not isinstance(position_value, dict):
            raise RoomDataError("Solomon Seal position is missing")
        seal_positions.append(position_value)
    if (
        not isinstance(princess, list)
        or len(princess) != PRINCESS_ROOM_HIDDEN_CELL_COUNT
        or any(not isinstance(position_value, dict) for position_value in princess)
    ):
        raise RoomDataError(
            f"Princess room must contain {PRINCESS_ROOM_HIDDEN_CELL_COUNT} hidden cells"
        )
    if not isinstance(room_20, list) or not isinstance(room_30, list):
        raise RoomDataError("special room bitplanes are missing")
    return {
        "random_bonus_room_positions": bytes(
            encode_position(position_value) for position_value in positions
        ),
        "random_bonus_room_item_types": bytes(item_types),
        "solomon_seal_positions": bytes(
            encode_position(position_value) for position_value in seal_positions
        ),
        "princess_room_hidden_cells": bytes(
            encode_position(position_value) for position_value in princess
        ),
        "room_20_bat_symbols": encode_bitplane(room_20),
        "room_30_blue_opals": encode_bitplane(room_30),
    }


def special_room_segments(
    encoded: dict[str, bytes],
    layout: RoomDataLayout,
) -> tuple[tuple[str, int, bytes], ...]:
    segments = (
        (
            "random_bonus_room_positions",
            layout.special_room_item_positions,
        ),
        (
            "random_bonus_room_item_types",
            layout.special_room_item_types,
        ),
        ("solomon_seal_positions", layout.solomon_seal_positions),
        ("princess_room_hidden_cells", layout.princess_room_hidden_cells),
        ("room_20_bat_symbols", layout.room_20_special_bitplane),
        ("room_30_blue_opals", layout.room_30_special_bitplane),
    )
    result = tuple((name, offset, encoded[name]) for name, offset in segments)
    if sum(len(payload) for _name, _offset, payload in result) != SPECIAL_ROOM_DATA_SIZE:
        raise RoomDataError("special-room encoded size differs from 116 bytes")
    return result


def decode_room(
    prg: bytes,
    room_index: int,
    layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT,
) -> dict[str, object]:
    if not 0 <= room_index < ROOM_COUNT:
        raise RoomDataError(f"room index outside 0..{ROOM_COUNT - 1}: {room_index}")
    return {
        "room": room_index + 1,
        "index": room_index,
        "blocks": decode_blocks(prg, room_index, layout),
        "enemy_stream": decode_enemies(prg, room_index, layout),
        "item_stream": decode_items(prg, room_index, layout),
    }


def emit_enemy_source(
    prg: bytes, layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT
) -> str:
    """Render all room enemy pointers and records as readable ca65 source."""
    rooms = [decode_enemies(prg, index, layout) for index in range(ROOM_COUNT)]
    labels = [f"RoomEnemyStream{index + 1:02d}" for index in range(ROOM_COUNT)]
    lines = [
        "; Per-room enemy pointers, encoded lifetimes, and spawn records",
        "",
        "RoomEnemyStreamCount = 53",
        "",
        ".macro RoomEnemySpawnLifetime encoded_value",
        "    .byte encoded_value",
        ".endmacro",
        "",
        ".macro RoomEnemyRecord enemy_type, map_position",
        "    .byte enemy_type, map_position",
        ".endmacro",
        "",
        ".macro EndRoomEnemyStream",
        "    .byte $00",
        ".endmacro",
        "",
        '.segment "PRG_ROOM_ENEMY_POINTERS"',
        "",
        "RoomEnemyPointerLowTable:",
    ]
    for index in range(0, ROOM_COUNT, 2):
        row = labels[index : index + 2]
        lines.append("    .byte " + ", ".join(f"<{label}" for label in row))
    lines.extend(("", "RoomEnemyPointerHighTable:"))
    for index in range(0, ROOM_COUNT, 2):
        row = labels[index : index + 2]
        lines.append("    .byte " + ", ".join(f">{label}" for label in row))
    lines.extend(
        (
            "",
            ".assert RoomEnemyPointerHighTable - RoomEnemyPointerLowTable = "
            "RoomEnemyStreamCount, error, \"unexpected room enemy pointer count\"",
            ".assert * - RoomEnemyPointerHighTable = RoomEnemyStreamCount, "
            "error, \"unexpected room enemy pointer count\"",
            "",
            '.segment "PRG_ROOM_ENEMY_DATA"',
            "",
        )
    )
    for label, stream in zip(labels, rooms):
        encoded_lifetime = stream["spawn_lifetime_encoded"]
        enemies = stream["enemies"]
        if not isinstance(encoded_lifetime, int) or not isinstance(enemies, list):
            raise RoomDataError("decoded enemy stream has invalid fields")
        lines.append(f"{label}:")
        lines.append(f"    RoomEnemySpawnLifetime ${encoded_lifetime:02X}")
        for enemy in enemies:
            if not isinstance(enemy, dict):
                raise RoomDataError("decoded enemy record is invalid")
            enemy_type = enemy.get("type")
            enemy_position = enemy.get("position")
            if not isinstance(enemy_type, int) or not isinstance(enemy_position, dict):
                raise RoomDataError("decoded enemy record has invalid fields")
            lines.append(
                f"    RoomEnemyRecord ${enemy_type:02X}, "
                f"${encode_position(enemy_position):02X}"
            )
        lines.append("    EndRoomEnemyStream")
    data_size = layout.block_data - rooms[0]["prg_offset"]
    if not isinstance(data_size, int):
        raise RoomDataError("invalid room enemy data extent")
    lines.extend(
        (
            "",
            f".assert * - {labels[0]} = ${data_size:04X}, error, "
            '"unexpected room enemy data size"',
            "",
        )
    )
    return "\n".join(lines)


def emit_block_source(
    prg: bytes, layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT
) -> str:
    """Render all 53 paired room block bitplanes as readable ca65 source."""
    lines = [
        "; Paired 16x12 brown/breakable and white/solid room bitplanes",
        "",
        "RoomBlockDataSize = 53 * 48",
        "",
        '.segment "PRG_ROOM_BLOCK_DATA"',
        "",
    ]
    for room_index in range(ROOM_COUNT):
        label = "RoomBlockData" if room_index == 0 else f"RoomBlockDataRoom{room_index + 1:02d}"
        blocks = decode_blocks(prg, room_index, layout)
        encoded = encode_blocks(blocks)
        lines.append(f"{label}:")
        lines.append("; Brown/breakable block plane")
        for offset in range(0, BITPLANE_SIZE, 8):
            row = encoded[offset : offset + 8]
            lines.append("    .byte " + ", ".join(f"${value:02X}" for value in row))
        lines.append("; White/solid block plane")
        white = encoded[BITPLANE_SIZE:]
        for offset in range(0, BITPLANE_SIZE, 8):
            row = white[offset : offset + 8]
            lines.append("    .byte " + ", ".join(f"${value:02X}" for value in row))
    lines.extend(
        (
            "",
            ".assert * - RoomBlockData = RoomBlockDataSize, error, "
            '"unexpected room block data size"',
            "",
        )
    )
    return "\n".join(lines)


def emit_item_source(
    prg: bytes, layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT
) -> str:
    """Render all room item pointers, metadata, and commands as ca65 source."""
    rooms = [decode_items(prg, index, layout) for index in range(ROOM_COUNT)]
    labels = [f"RoomItemStream{index + 1:02d}" for index in range(ROOM_COUNT)]
    lines = [
        "; Per-room metadata and compressed item placement commands",
        "",
        "RoomItemStreamCount = 53",
        "",
        ".macro RoomItemHeader mirror_2_schedule, mirror_1_schedule, mirror_2_enemy_set, mirror_1_enemy_set, status_rate, door_position, key_position, player_start_position, mirror_1_position, mirror_2_position",
        "    .byte mirror_2_schedule, mirror_1_schedule",
        "    .byte mirror_2_enemy_set, mirror_1_enemy_set, status_rate",
        "    .byte door_position, key_position, player_start_position",
        "    .byte mirror_1_position, mirror_2_position",
        ".endmacro",
        "",
        ".macro RoomItemRecord item_type, map_position",
        "    .byte item_type, map_position",
        ".endmacro",
        "",
        ".macro BeginRoomItemRepeat item_type, repeat_count",
        "    .byte $C0 + repeat_count - 1, item_type",
        ".endmacro",
        "",
        ".macro EndRoomItemStream opcode",
        "    .byte opcode",
        ".endmacro",
        "",
        ".macro RoomConstellationItem opcode, map_position",
        "    .byte opcode, map_position",
        ".endmacro",
        "",
        '.segment "PRG_ROOM_ITEM_POINTERS"',
        "",
        "RoomItemPointerLowTable:",
    ]
    for index in range(0, ROOM_COUNT, 2):
        row = labels[index : index + 2]
        lines.append("    .byte " + ", ".join(f"<{label}" for label in row))
    lines.extend(("", "RoomItemPointerHighTable:"))
    for index in range(0, ROOM_COUNT, 2):
        row = labels[index : index + 2]
        lines.append("    .byte " + ", ".join(f">{label}" for label in row))
    lines.extend(
        (
            "",
            ".assert RoomItemPointerHighTable - RoomItemPointerLowTable = "
            "RoomItemStreamCount, error, \"unexpected room item pointer count\"",
            ".assert * - RoomItemPointerHighTable = RoomItemStreamCount, "
            "error, \"unexpected room item pointer count\"",
            "",
            '.segment "PRG_ROOM_ITEM_DATA"',
            "",
        )
    )
    for label, stream in zip(labels, rooms):
        metadata = stream.get("metadata")
        commands = stream.get("commands")
        if not isinstance(metadata, dict) or not isinstance(commands, list):
            raise RoomDataError("decoded item stream has invalid fields")
        header_fields = [
            metadata.get("mirror_2_schedule"),
            metadata.get("mirror_1_schedule"),
            metadata.get("mirror_2_enemy_set"),
            metadata.get("mirror_1_enemy_set"),
            metadata.get("status_rate_raw"),
        ]
        for field in ("door", "key", "player_start", "mirror_1", "mirror_2"):
            value = metadata.get(field)
            if not isinstance(value, dict):
                raise RoomDataError(f"invalid item metadata position: {field}")
            header_fields.append(encode_position(value))
        if any(not isinstance(value, int) for value in header_fields):
            raise RoomDataError("decoded item metadata has invalid scalar fields")
        lines.append(f"{label}:")
        lines.append(
            "    RoomItemHeader "
            + ", ".join(f"${value:02X}" for value in header_fields)
        )
        for command in commands:
            if not isinstance(command, dict):
                raise RoomDataError("decoded item command is invalid")
            kind = command.get("kind")
            if kind == "item":
                item_type = command.get("type")
                item_position = command.get("position")
                if not isinstance(item_type, int) or not isinstance(item_position, dict):
                    raise RoomDataError("decoded item record has invalid fields")
                lines.append(
                    f"    RoomItemRecord ${item_type:02X}, "
                    f"${encode_position(item_position):02X}"
                )
            elif kind == "repeat":
                item_type = command.get("type")
                positions = command.get("positions")
                if not isinstance(item_type, int) or not isinstance(positions, list):
                    raise RoomDataError("decoded repeated-item command is invalid")
                lines.append(
                    f"    BeginRoomItemRepeat ${item_type:02X}, {len(positions)}"
                )
                encoded_positions = []
                for value in positions:
                    if not isinstance(value, dict):
                        raise RoomDataError("decoded repeated-item position is invalid")
                    encoded_positions.append(encode_position(value))
                for offset in range(0, len(encoded_positions), 8):
                    row = encoded_positions[offset : offset + 8]
                    lines.append(
                        "    .byte " + ", ".join(f"${value:02X}" for value in row)
                    )
            elif kind == "constellation":
                opcode = command.get("opcode")
                item_position = command.get("position")
                if not isinstance(opcode, int) or not isinstance(item_position, dict):
                    raise RoomDataError("decoded constellation command is invalid")
                lines.append(
                    f"    RoomConstellationItem ${opcode:02X}, "
                    f"${encode_position(item_position):02X}"
                )
            elif kind == "end":
                opcode = command.get("opcode")
                if not isinstance(opcode, int):
                    raise RoomDataError("decoded item terminator is invalid")
                lines.append(f"    EndRoomItemStream ${opcode:02X}")
            else:
                raise RoomDataError(f"unknown decoded item command: {kind!r}")
    data_size = max(
        int(stream["prg_offset"]) + int(stream["encoded_size"])
        for stream in rooms
    ) - int(rooms[0]["prg_offset"])
    lines.extend(
        (
            "",
            f".assert * - {labels[0]} = ${data_size:04X}, error, "
            '"unexpected room item data size"',
            "",
            '.segment "PRG_FILLER_BEFORE_AUDIO"',
            "",
            "PreAudioPadding:",
        )
    )
    padding = prg[layout.item_data_end : layout.audio_engine]
    for offset in range(0, len(padding), 8):
        row = padding[offset : offset + 8]
        lines.append("    .byte " + ", ".join(f"${value:02X}" for value in row))
    lines.extend(
        (
            "",
            f".assert * - PreAudioPadding = ${len(padding):04X}, error, "
            '"unexpected pre-audio padding size"',
            "",
        )
    )
    return "\n".join(lines)


def roundtrip_rooms(
    prg: bytes, layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT
) -> dict[str, int]:
    rooms = [decode_room(prg, index, layout) for index in range(ROOM_COUNT)]
    mirror_schedules = decode_mirror_schedules(prg, layout)
    mirror_enemy_sets = decode_mirror_enemy_sets(prg, layout)
    tile_patterns = decode_room_tile_patterns(prg, layout)
    enemy_offsets: list[int] = []
    item_offsets: list[int] = []
    checked_bytes = 0
    for room in rooms:
        blocks = room["blocks"]
        enemies = room["enemy_stream"]
        items = room["item_stream"]
        if not isinstance(blocks, dict) or not isinstance(enemies, dict) or not isinstance(items, dict):
            raise RoomDataError("decoded room has an invalid structure")
        block_offset = int(blocks["prg_offset"])
        encoded_blocks = encode_blocks(blocks)
        if encoded_blocks != prg[block_offset : block_offset + len(encoded_blocks)]:
            raise RoomDataError(f"room {room['room']} block round trip differs")
        enemy_offset = int(enemies["prg_offset"])
        encoded_enemies = encode_enemies(enemies)
        if encoded_enemies != prg[enemy_offset : enemy_offset + len(encoded_enemies)]:
            raise RoomDataError(f"room {room['room']} enemy round trip differs")
        item_offset = int(items["prg_offset"])
        encoded_items = encode_items(items)
        if encoded_items != prg[item_offset : item_offset + len(encoded_items)]:
            raise RoomDataError(f"room {room['room']} item round trip differs")
        enemy_offsets.append(enemy_offset)
        item_offsets.append(item_offset)
        checked_bytes += len(encoded_blocks) + len(encoded_enemies) + len(encoded_items)

    enemy_pointers = encode_split_pointers(enemy_offsets)
    item_pointers = encode_split_pointers(item_offsets)
    if enemy_pointers != prg[
        layout.enemy_pointer_table : layout.enemy_pointer_table + len(enemy_pointers)
    ]:
        raise RoomDataError("enemy pointer-table round trip differs")
    if item_pointers != prg[
        layout.item_pointer_table : layout.item_pointer_table + len(item_pointers)
    ]:
        raise RoomDataError("item pointer-table round trip differs")
    checked_bytes += len(enemy_pointers) + len(item_pointers)

    schedule_offsets: list[int] = []
    for schedule in mirror_schedules:
        offset = int(schedule["prg_offset"])
        encoded = encode_mirror_schedule(schedule)
        if encoded != prg[offset : offset + len(encoded)]:
            raise RoomDataError(f"Demon Mirror schedule {schedule['index']} differs")
        schedule_offsets.append(offset)
        checked_bytes += len(encoded)
    schedule_pointers = encode_split_pointers(schedule_offsets)
    if schedule_pointers != prg[
        layout.mirror_schedule_table : layout.mirror_schedule_table
        + len(schedule_pointers)
    ]:
        raise RoomDataError("Demon Mirror schedule pointer round trip differs")
    checked_bytes += len(schedule_pointers)

    enemy_set_offsets: list[int] = []
    for enemy_set in mirror_enemy_sets:
        offset = int(enemy_set["prg_offset"])
        encoded = encode_mirror_enemy_set(enemy_set)
        if encoded != prg[offset : offset + len(encoded)]:
            raise RoomDataError(f"Demon Mirror enemy set {enemy_set['index']} differs")
        enemy_set_offsets.append(offset)
        checked_bytes += len(encoded)
    enemy_set_pointers = encode_split_pointers(enemy_set_offsets)
    if enemy_set_pointers != prg[
        layout.mirror_enemy_set_table : layout.mirror_enemy_set_table
        + len(enemy_set_pointers)
    ]:
        raise RoomDataError("Demon Mirror enemy-set pointer round trip differs")
    checked_bytes += len(enemy_set_pointers)

    encoded_tile_patterns = encode_room_tile_patterns(tile_patterns)
    if encoded_tile_patterns != prg[
        layout.room_tile_pattern_data : layout.room_tile_pattern_data
        + len(encoded_tile_patterns)
    ]:
        raise RoomDataError("RoomMap tile pattern round trip differs")
    checked_bytes += len(encoded_tile_patterns)

    special_data = encode_special_room_data(decode_special_room_data(prg, layout))
    for name, offset, encoded in special_room_segments(special_data, layout):
        if encoded != prg[offset : offset + len(encoded)]:
            raise RoomDataError(f"{name} round trip differs")
        checked_bytes += len(encoded)

    return {"rooms": len(rooms), "format_families": 7, "checked_bytes": checked_bytes}


def group_room_chr_banks(room_banks: Iterable[int]) -> dict[int, list[int]]:
    """Group one-based room numbers by decoded 8 KiB CHR bank."""
    groups = {bank: [] for bank in range(4)}
    for room_number, bank in enumerate(room_banks, start=1):
        if bank not in groups:
            raise RoomDataError(f"room {room_number} has invalid CHR bank {bank}")
        groups[bank].append(room_number)
    return groups


def decode_room_chr_banks(
    prg: bytes, layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT
) -> tuple[int, ...]:
    banks: list[int] = []
    for index in range(ROOM_COUNT):
        decoded = decode_items(prg, index, layout)
        bank = decoded.get("chr_bank")
        if not isinstance(bank, int):
            raise RoomDataError(f"room {index + 1} has no decoded CHR bank")
        banks.append(bank)
    return tuple(banks)


def room_chr_bank_groups(
    prg: bytes, layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT
) -> dict[int, list[int]]:
    return group_room_chr_banks(decode_room_chr_banks(prg, layout))


def audit_room_chr_banks(
    prg: bytes, layout: RoomDataLayout = USA_ROOM_DATA_LAYOUT
) -> dict[int, list[int]]:
    banks = decode_room_chr_banks(prg, layout)
    if banks != EXPECTED_ROOM_CHR_BANKS:
        room_number = next(
            index + 1
            for index, (actual, expected) in enumerate(
                zip(banks, EXPECTED_ROOM_CHR_BANKS)
            )
            if actual != expected
        )
        raise RoomDataError(
            f"room {room_number} CHR bank is {banks[room_number - 1]}, "
            f"expected {EXPECTED_ROOM_CHR_BANKS[room_number - 1]}"
        )
    groups = group_room_chr_banks(banks)
    counts = tuple(len(groups[bank]) for bank in range(4))
    if counts != EXPECTED_ROOM_CHR_BANK_COUNTS:
        raise RoomDataError(
            f"unexpected room CHR bank counts: {counts}, "
            f"expected {EXPECTED_ROOM_CHR_BANK_COUNTS}"
        )
    return groups


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="iNES image or bare 32 KiB PRG")
    parser.add_argument(
        "--layout",
        choices=tuple(ROOM_DATA_LAYOUTS),
        default="usa",
        help="regional PRG layout (default: usa)",
    )
    parser.add_argument("--room", type=int, help="one-based room number (default: all)")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--source-enemies",
        action="store_true",
        help="emit reviewed ca65 source for all room enemy data",
    )
    parser.add_argument(
        "--source-blocks",
        action="store_true",
        help="emit reviewed ca65 source for all room block data",
    )
    parser.add_argument(
        "--source-items",
        action="store_true",
        help="emit reviewed ca65 source for all room item data",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="decode every room and print only a structural summary",
    )
    parser.add_argument(
        "--roundtrip",
        action="store_true",
        help="decode and re-encode every room-data record and pointer table",
    )
    parser.add_argument(
        "--chr-bank-report",
        action="store_true",
        help="report one-based room numbers grouped by decoded CHR bank",
    )
    parser.add_argument(
        "--chr-bank-audit",
        action="store_true",
        help="verify the decoded gameplay-room CHR bank profile",
    )
    args = parser.parse_args()
    try:
        prg = extract_prg(Path(args.image).read_bytes())
        layout = ROOM_DATA_LAYOUTS[args.layout]
        if args.source_enemies:
            print(emit_enemy_source(prg, layout), end="")
            return 0
        if args.source_blocks:
            print(emit_block_source(prg, layout), end="")
            return 0
        if args.source_items:
            print(emit_item_source(prg, layout), end="")
            return 0
        if args.roundtrip:
            result = roundtrip_rooms(prg, layout)
            print(
                f"[OK] round-tripped {result['format_families']} room format "
                f"families across {result['rooms']} rooms "
                f"({result['checked_bytes']} checked bytes)"
            )
            return 0
        if args.chr_bank_report:
            groups = room_chr_bank_groups(prg, layout)
            result = {
                "banks": [
                    {
                        "bank": bank,
                        "room_count": len(groups[bank]),
                        "rooms": groups[bank],
                    }
                    for bank in range(4)
                ]
            }
            print(json.dumps(result, indent=2 if args.pretty else None))
            return 0
        if args.chr_bank_audit:
            groups = audit_room_chr_banks(prg, layout)
            counts = ", ".join(
                f"bank {bank}={len(groups[bank])}" for bank in range(4)
            )
            print(f"[OK] room CHR banks: {counts} across {ROOM_COUNT} rooms")
            return 0
        if args.validate:
            rooms = [decode_room(prg, index, layout) for index in range(ROOM_COUNT)]
            enemy_count = sum(
                len(room["enemy_stream"]["enemies"]) for room in rooms
            )
            item_count = sum(len(room["item_stream"]["items"]) for room in rooms)
            print(
                f"[OK] decoded {len(rooms)} rooms, {enemy_count} placed enemies, "
                f"and {item_count} item records"
            )
            return 0
        if args.room is None:
            result: object = [
                decode_room(prg, index, layout) for index in range(ROOM_COUNT)
            ]
        else:
            result = decode_room(prg, args.room - 1, layout)
    except (OSError, RoomDataError, IndexError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
