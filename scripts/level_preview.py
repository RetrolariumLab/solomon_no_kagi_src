#!/usr/bin/env python3
"""Render Solomon's Key room documents with the original NES background art."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


ROOM_WIDTH = 16
ROOM_HEIGHT = 12
CHR_BANK_SIZE = 8192
CHR_TILE_SIZE = 16
CHR_TILES_PER_BANK = CHR_BANK_SIZE // CHR_TILE_SIZE
BACKGROUND_PATTERN_BASE = 0x100
METATILE_SIZE = 16

ROOM_MAP_EMPTY = 0x10
ROOM_MAP_BROWN_BLOCK = 0x90
ROOM_MAP_WHITE_BLOCK = 0xF8
ROOM_MAP_CLOSED_DOOR = 0x02
ROOM_MAP_DEMON_MIRROR = 0x05
ROOM_MAP_KEY = 0x06
ROOM_MAP_DEFERRED_DOOR = 0x35
ROOM_MAP_DECORATION_BIT = 0x40
ROOM_MAP_SOLID_BIT = 0x80
ROOM_MAP_IMMUTABLE_MINIMUM = 0xF8

KEY_CLASS_BITS = {
    "normal": 0x00,
    "in_block": ROOM_MAP_SOLID_BIT,
    "hidden": ROOM_MAP_DECORATION_BIT,
}

# The first 16 bytes published by RoomLoadPaletteTemplate. The room loader
# replaces color 1 in every background subpalette with a room-group color.
ROOM_BACKGROUND_PALETTE = (
    0x0F,
    0x07,
    0x10,
    0x30,
    0x0F,
    0x07,
    0x27,
    0x30,
    0x0F,
    0x07,
    0x2C,
    0x30,
    0x0F,
    0x07,
    0x27,
    0x38,
)
ROOM_GROUP_COLORS = (
    0x07,
    0x1C,
    0x04,
    0x09,
    0x1C,
    0x07,
    0x04,
    0x07,
    0x09,
    0x1C,
    0x07,
    0x04,
    0x80,
    0x80,
)

# Four six-metatile constellation layouts. The decoder selects one layout
# with opcode bits 0-1 and applies a separate palette value to every record.
CONSTELLATION_PATTERN_BYTES = bytes(
    (
        0x28, 0xC1, 0x2A, 0xC3, 0xC0, 0xC5, 0xC2, 0xC7,
        0xC4, 0x29, 0xC6, 0x2B, 0x28, 0xC9, 0x2A, 0xCB,
        0xC8, 0xCD, 0xCA, 0xCF, 0xCC, 0x29, 0xCE, 0x2B,
        0x28, 0xD1, 0x2A, 0xD3, 0xD0, 0xD5, 0xD2, 0xD7,
        0xD4, 0x29, 0xD6, 0x2B, 0x28, 0xD9, 0x2A, 0xDB,
        0xD8, 0xDD, 0xDA, 0xDF, 0xDC, 0x29, 0xDE, 0x2B,
        0x28, 0xE1, 0x2A, 0xE3, 0xE0, 0xE5, 0xE2, 0xE7,
        0xE4, 0x29, 0xE6, 0x2B, 0x28, 0xE9, 0x2A, 0xEB,
        0xE8, 0xED, 0xEA, 0xEF, 0xEC, 0x29, 0xEE, 0x2B,
        0x28, 0xF1, 0x2A, 0xF3, 0xF0, 0xF5, 0xF2, 0xF7,
        0xF4, 0x29, 0xF6, 0x2B, 0x28, 0xF9, 0x2A, 0xFB,
        0xF8, 0xFD, 0xFA, 0xFF, 0xFC, 0x29, 0xFE, 0x2B,
    )
)
CONSTELLATION_PALETTES = (0x03, 0x03, 0x03, 0x03, 0x02, 0x03,
                          0x00, 0x02, 0x00, 0x01, 0x00, 0x01)

# A stable RGB rendering of the 64 NES palette indices. The room data retains
# indices, not RGB values; this table affects preview color only.
NES_RGB = (
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136),
    (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0),
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0),
    (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228),
    (136, 20, 176), (160, 20, 100), (152, 34, 32), (120, 60, 0),
    (84, 90, 0), (40, 114, 0), (8, 124, 0), (0, 118, 40),
    (0, 102, 120), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236),
    (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32),
    (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108),
    (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236),
    (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
    (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180),
    (160, 214, 228), (160, 162, 160), (0, 0, 0), (0, 0, 0),
)


class LevelPreviewError(ValueError):
    """The authored room cannot be converted into a native-art preview."""


@dataclass(frozen=True)
class PatternRecord:
    palette: int
    tiles: tuple[int, int, int, int]


@dataclass(frozen=True)
class RoomPreview:
    width: int
    height: int
    rgb: bytes
    chr_bank: int
    palette: tuple[int, ...]

    def ppm(self) -> bytes:
        header = f"P6\n{self.width} {self.height}\n255\n".encode("ascii")
        return header + self.rgb


def decode_chr_tiles(chr_data: bytes) -> tuple[tuple[tuple[int, ...], ...], ...]:
    if len(chr_data) != CHR_BANK_SIZE * 4:
        raise LevelPreviewError(
            f"Solomon's Key CHR must be 32768 bytes, got {len(chr_data)}"
        )
    tiles: list[tuple[tuple[int, ...], ...]] = []
    for offset in range(0, len(chr_data), CHR_TILE_SIZE):
        rows: list[tuple[int, ...]] = []
        for row in range(8):
            low = chr_data[offset + row]
            high = chr_data[offset + 8 + row]
            rows.append(
                tuple(
                    ((low >> (7 - column)) & 1)
                    | (((high >> (7 - column)) & 1) << 1)
                    for column in range(8)
                )
            )
        tiles.append(tuple(rows))
    return tuple(tiles)


def visible(position: object) -> bool:
    return (
        isinstance(position, dict)
        and isinstance(position.get("x"), int)
        and isinstance(position.get("y"), int)
        and 0 <= position["x"] < ROOM_WIDTH
        and 0 <= position["y"] < ROOM_HEIGHT
    )


def set_map_cell(values: list[list[int]], position: object, value: int) -> None:
    if visible(position):
        values[position["y"]][position["x"]] = value


def item_placements(commands: Iterable[dict[str, Any]]) -> Iterable[tuple[int, dict[str, int]]]:
    for command in commands:
        kind = command.get("kind")
        if kind == "item" and visible(command.get("position")):
            yield int(command["type"]), command["position"]
        elif kind == "repeat":
            for position in command.get("positions", ()):
                if visible(position):
                    yield int(command["type"]), position


def room_chr_bank(room: dict[str, Any]) -> int:
    commands = room.get("items", {}).get("commands", ())
    for command in reversed(commands):
        if command.get("kind") in {"end", "constellation"}:
            opcode = command.get("opcode")
            if isinstance(opcode, int) and (
                opcode == 0 or 0xE0 <= opcode <= 0xFB
            ):
                return (opcode >> 2) & 3
            break
    raise LevelPreviewError("room item stream has no CHR-bank terminator")


def room_palette(room_index: int) -> tuple[int, ...]:
    if not 0 <= room_index < 53:
        raise LevelPreviewError("room index is outside 0..52")
    palette = list(ROOM_BACKGROUND_PALETTE)
    color = ROOM_GROUP_COLORS[room_index // 4]
    if color & 0x80:
        palette[10] = 0x16
        color = 0
    for index in (1, 5, 9, 13):
        palette[index] = color
    return tuple(palette)


def room_map_values(room: dict[str, Any]) -> tuple[tuple[int, ...], ...]:
    values = [[ROOM_MAP_EMPTY for _ in range(ROOM_WIDTH)] for _ in range(ROOM_HEIGHT)]
    blocks = room.get("blocks", {})
    for position in blocks.get("brown", ()):
        set_map_cell(values, position, ROOM_MAP_BROWN_BLOCK)
    for position in blocks.get("white", ()):
        set_map_cell(values, position, ROOM_MAP_WHITE_BLOCK)

    items = room.get("items", {})
    metadata = items.get("metadata", {})
    door = metadata.get("door")
    key = metadata.get("key")
    set_map_cell(values, door, ROOM_MAP_CLOSED_DOOR)
    if visible(key):
        status = metadata.get("key_status")
        if status not in KEY_CLASS_BITS:
            raise LevelPreviewError(f"unknown room key status: {status!r}")
        set_map_cell(values, key, KEY_CLASS_BITS[status] | ROOM_MAP_KEY)
    elif visible(door):
        set_map_cell(values, door, ROOM_MAP_DEFERRED_DOOR)
    set_map_cell(values, metadata.get("mirror_1"), ROOM_MAP_DEMON_MIRROR)
    set_map_cell(values, metadata.get("mirror_2"), ROOM_MAP_DEMON_MIRROR)
    for item_type, position in item_placements(items.get("commands", ())):
        set_map_cell(values, position, item_type)
    return tuple(tuple(row) for row in values)


def classify_pattern(value: int) -> int:
    if value >= ROOM_MAP_IMMUTABLE_MINIMUM:
        return 3
    if value >= ROOM_MAP_SOLID_BIT:
        return 0
    if value >= ROOM_MAP_DECORATION_BIT:
        return ROOM_MAP_EMPTY
    return value


def document_pattern(document: dict[str, Any], index: int) -> PatternRecord:
    patterns = document.get("tile_patterns")
    if not isinstance(patterns, list) or not 0 <= index < len(patterns):
        raise LevelPreviewError(f"room tile pattern {index} is unavailable")
    pattern = patterns[index]
    try:
        palette = int(pattern["palette"])
        tiles = tuple(
            int(pattern[name])
            for name in ("top_left", "top_right", "bottom_left", "bottom_right")
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise LevelPreviewError(f"invalid room tile pattern {index}") from exc
    if not 0 <= palette <= 3 or len(tiles) != 4 or any(not 0 <= tile <= 0xFF for tile in tiles):
        raise LevelPreviewError(f"invalid room tile pattern {index}")
    return PatternRecord(palette, tiles)


def constellation_command(room: dict[str, Any]) -> dict[str, Any] | None:
    for command in room.get("items", {}).get("commands", ()):
        if command.get("kind") == "constellation":
            return command
    return None


def constellation_pattern(
    command: dict[str, Any] | None,
    x: int,
    y: int,
) -> PatternRecord | None:
    if command is None or not visible(command.get("position")):
        return None
    origin = command["position"]
    relative_x = x - origin["x"]
    relative_y = y - origin["y"]
    if not 0 <= relative_x < 3 or not 0 <= relative_y < 2:
        return None
    opcode = command.get("opcode")
    if not isinstance(opcode, int) or not 0xF0 <= opcode <= 0xFB:
        raise LevelPreviewError("invalid constellation opcode")
    record_index = relative_y * 3 + relative_x
    pattern_offset = (opcode & 3) * 24 + record_index * 4
    first, top_right, bottom_left, bottom_right = CONSTELLATION_PATTERN_BYTES[
        pattern_offset : pattern_offset + 4
    ]
    palette = CONSTELLATION_PALETTES[opcode & 0x0F]
    return PatternRecord(
        palette,
        (first & 0xFC, top_right, bottom_left, bottom_right),
    )


class LevelPreviewRenderer:
    """Decode CHR once and render any authored room into a 256x192 RGB frame."""

    def __init__(self, document: dict[str, Any], chr_data: bytes) -> None:
        self.document = document
        self.tiles = decode_chr_tiles(chr_data)

    def tile(self, bank: int, tile: int) -> tuple[tuple[int, ...], ...]:
        if not 0 <= bank < 4 or not 0 <= tile <= 0xFF:
            raise LevelPreviewError("CHR bank or tile is outside the background table")
        index = bank * CHR_TILES_PER_BANK + BACKGROUND_PATTERN_BASE + tile
        return self.tiles[index]

    def render(self, room_index: int) -> RoomPreview:
        rooms = self.document.get("rooms")
        if not isinstance(rooms, list) or not 0 <= room_index < len(rooms):
            raise LevelPreviewError("room index is outside the level document")
        room = rooms[room_index]
        bank = room_chr_bank(room)
        palette = room_palette(room_index)
        values = room_map_values(room)
        constellation = constellation_command(room)
        width = ROOM_WIDTH * METATILE_SIZE
        height = ROOM_HEIGHT * METATILE_SIZE
        rgb = bytearray(width * height * 3)

        for cell_y, row in enumerate(values):
            for cell_x, value in enumerate(row):
                pattern = None
                if value == ROOM_MAP_EMPTY:
                    pattern = constellation_pattern(constellation, cell_x, cell_y)
                if pattern is None:
                    pattern = document_pattern(self.document, classify_pattern(value))
                self._draw_metatile(rgb, width, cell_x, cell_y, bank, palette, pattern)
        return RoomPreview(width, height, bytes(rgb), bank, palette)

    def _draw_metatile(
        self,
        output: bytearray,
        output_width: int,
        cell_x: int,
        cell_y: int,
        bank: int,
        palette: tuple[int, ...],
        pattern: PatternRecord,
    ) -> None:
        for quadrant, tile_index in enumerate(pattern.tiles):
            tile = self.tile(bank, tile_index)
            origin_x = cell_x * METATILE_SIZE + (quadrant & 1) * 8
            origin_y = cell_y * METATILE_SIZE + (quadrant >> 1) * 8
            for pixel_y, row in enumerate(tile):
                for pixel_x, pixel in enumerate(row):
                    palette_index = pattern.palette * 4 + pixel
                    color = NES_RGB[palette[palette_index] & 0x3F]
                    offset = ((origin_y + pixel_y) * output_width + origin_x + pixel_x) * 3
                    output[offset : offset + 3] = bytes(color)
