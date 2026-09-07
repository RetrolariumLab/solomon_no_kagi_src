#!/usr/bin/env python3
"""Render Solomon's Key room documents with the original NES background art."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


ROOM_WIDTH = 16
ROOM_HEIGHT = 12
PRG_BASE = 0x8000
CHR_BANK_SIZE = 8192
CHR_TILE_SIZE = 16
CHR_TILES_PER_BANK = CHR_BANK_SIZE // CHR_TILE_SIZE
BACKGROUND_PATTERN_BASE = 0x100
METATILE_SIZE = 16

ROOM_MAP_EMPTY = 0x10
ROOM_MAP_BROWN_BLOCK = 0x90
ROOM_MAP_WHITE_BLOCK = 0xF8
ROOM_MAP_CLOSED_DOOR = 0x02
ROOM_MAP_BAT_SYMBOL = 0x04
ROOM_MAP_DEMON_MIRROR = 0x05
ROOM_MAP_KEY = 0x06
ROOM_MAP_DEFERRED_DOOR = 0x35
ROOM_MAP_SOLOMON_SEAL = 0x20
ROOM_MAP_BLUE_OPAL = 0x27
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
ROOM_SPRITE_PALETTE = (
    0x0F, 0x26, 0x29, 0x30,
    0x0F, 0x30, 0x16, 0x27,
    0x0F, 0x16, 0x10, 0x30,
    0x0F, 0x2C, 0x26, 0x30,
)
ENEMY_TYPE_CONFIGURATION_COUNT = 27
OBJECT_ANIMATION_POINTER_COUNT = 33
DANA_IDLE_ACTION_RIGHT = 0x16
DANA_IDLE_ACTION_LEFT = 0x17
HIDDEN_OBJECT_OPACITY = 128
EMBEDDED_BLOCK_OPACITY = 80
EMBEDDED_OBJECT_OPACITY = 192
COMBINED_BLOCK_OPACITY = 128
GROUND_ENEMY_TYPE_MINIMUM = 0x50
GROUND_ENEMY_TYPE_LIMIT = 0x80

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
    rendered_enemy_indices: tuple[int, ...]
    rendered_player: bool = False

    def ppm(self) -> bytes:
        header = f"P6\n{self.width} {self.height}\n255\n".encode("ascii")
        return header + self.rgb


@dataclass(frozen=True)
class SpriteFrame:
    left_tile: int
    right_tile: int
    flags: int


@dataclass(frozen=True)
class PreviewLayers:
    """Select logical foreground families without changing room data."""

    metadata: bool = True
    items: bool = True
    enemies: bool = True
    special: bool = True


def manifest_address(value: object, field: str) -> int:
    try:
        address = int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise LevelPreviewError(f"invalid level preview {field}: {value!r}") from exc
    if not PRG_BASE <= address <= 0xFFFF:
        raise LevelPreviewError(f"level preview {field} is outside PRG")
    return address


def cpu_offset(address: int, size: int, prg_size: int) -> int:
    offset = address - PRG_BASE
    if address < PRG_BASE or size < 0 or offset + size > prg_size:
        raise LevelPreviewError(
            f"level preview read ${address:04X}+${size:X} is outside PRG"
        )
    return offset


def sprite_attributes(flags: int) -> tuple[int, int]:
    """Project packed object flags through the game's two OAM transforms."""
    left = (
        ((flags & 0x20) << 2)
        | ((flags & 0x10) << 2)
        | ((flags & 0x80) >> 7)
        | ((flags & 0x40) >> 5)
    )
    right = (
        ((flags & 0x01) << 7)
        | ((flags & 0x02) << 5)
        | ((flags & 0x08) >> 2)
        | ((flags & 0x04) >> 2)
    )
    return left, right


class EnemySpriteDecoder:
    """Resolve room spawn types through the original animation tables."""

    def __init__(self, prg: bytes, preview_contract: dict[str, Any]) -> None:
        if len(prg) != 0x8000:
            raise LevelPreviewError(
                f"Solomon's Key PRG must be 32768 bytes, got {len(prg)}"
            )
        self.prg = prg
        self.pointer_address = manifest_address(
            preview_contract.get("object_animation_pointer_address"),
            "object_animation_pointer_address",
        )
        self.configuration_address = manifest_address(
            preview_contract.get("enemy_type_configuration_address"),
            "enemy_type_configuration_address",
        )
        cpu_offset(
            self.pointer_address,
            OBJECT_ANIMATION_POINTER_COUNT * 2,
            len(prg),
        )
        cpu_offset(
            self.configuration_address,
            ENEMY_TYPE_CONFIGURATION_COUNT,
            len(prg),
        )

    def byte(self, address: int) -> int:
        return self.prg[cpu_offset(address, 1, len(self.prg))]

    def word(self, address: int) -> int:
        offset = cpu_offset(address, 2, len(self.prg))
        return self.prg[offset] | (self.prg[offset + 1] << 8)

    def initial_action(self, enemy_type: int) -> int | None:
        if not 0x18 <= enemy_type < 0x18 + ENEMY_TYPE_CONFIGURATION_COUNT * 4:
            return None
        configuration_index = (enemy_type - 0x18) >> 2
        flags = self.byte(self.configuration_address + configuration_index)
        action = enemy_type & 3
        return action if flags & 0x08 else action | 0x18

    @staticmethod
    def initial_frame_offset(initial_phase: int) -> int:
        phase_sum = initial_phase + 0xF0
        phase = phase_sum & 0xFF
        if phase_sum <= 0xFF:
            phase = (phase & 0x0F) * 0x11
        return (phase >> 3) + (phase >> 4)

    def action_frame(
        self, pointer_index: int, action: int, variant: int = 0
    ) -> SpriteFrame | None:
        if (
            not 0 <= pointer_index < OBJECT_ANIMATION_POINTER_COUNT
            or not 0 <= action <= 0xFF
            or not 0 <= variant <= 3
        ):
            return None
        descriptor_group = self.word(self.pointer_address + pointer_index * 2)
        descriptor = descriptor_group + action * 4
        initial_phase = self.byte(descriptor)
        flags = self.byte(descriptor + 1)
        frame_pointer = self.word(descriptor + 2)
        if flags & 1:
            frame_pointer = self.word(frame_pointer + variant * 2)
        frame_pointer += self.initial_frame_offset(initial_phase)
        return SpriteFrame(
            self.byte(frame_pointer),
            self.byte(frame_pointer + 1),
            self.byte(frame_pointer + 2),
        )

    def frame(self, enemy_type: int) -> SpriteFrame | None:
        action = self.initial_action(enemy_type)
        if action is None:
            return None
        return self.action_frame(enemy_type >> 2, action, enemy_type & 3)

    def dana_frame(self, faces_left: bool) -> SpriteFrame | None:
        action = DANA_IDLE_ACTION_LEFT if faces_left else DANA_IDLE_ACTION_RIGHT
        return self.action_frame(0, action)


def flip_ground_enemy_vertical(enemy_type: int) -> bool:
    """Turn the lateral ground-enemy families upright in editor previews."""
    return GROUND_ENEMY_TYPE_MINIMUM <= enemy_type < GROUND_ENEMY_TYPE_LIMIT


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


def room_map_values(
    room: dict[str, Any], layers: PreviewLayers | None = None
) -> tuple[tuple[int, ...], ...]:
    layers = layers or PreviewLayers()
    values = [[ROOM_MAP_EMPTY for _ in range(ROOM_WIDTH)] for _ in range(ROOM_HEIGHT)]
    blocks = room.get("blocks", {})
    for position in blocks.get("brown", ()):
        set_map_cell(values, position, ROOM_MAP_BROWN_BLOCK)
    for position in blocks.get("white", ()):
        set_map_cell(values, position, ROOM_MAP_WHITE_BLOCK)

    items = room.get("items", {})
    metadata = items.get("metadata", {})
    if layers.metadata:
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
    if layers.items:
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


def special_room_pattern_placements(
    document: dict[str, Any], room_index: int
) -> tuple[tuple[dict[str, int], int], ...]:
    """Return special-script cells that have a native RoomMap pattern."""
    special = document.get("special_room_data")
    if not isinstance(special, dict):
        return ()
    room_number = room_index + 1
    placements: list[tuple[dict[str, int], int]] = []
    seals = special.get("solomon_seals", ())
    if isinstance(seals, list):
        for record in seals:
            if (
                isinstance(record, dict)
                and record.get("room") == room_number
                and visible(record.get("position"))
            ):
                placements.append((record["position"], ROOM_MAP_SOLOMON_SEAL))
    family: object = ()
    pattern_index: int | None = None
    if room_number == 20:
        family = special.get("room_20_bat_symbols", ())
        pattern_index = ROOM_MAP_BAT_SYMBOL
    elif room_number == 30:
        family = special.get("room_30_blue_opals", ())
        pattern_index = ROOM_MAP_BLUE_OPAL
    if pattern_index is not None and isinstance(family, list):
        placements.extend(
            (position, pattern_index) for position in family if visible(position)
        )
    return tuple(placements)


class LevelPreviewRenderer:
    """Decode CHR once and render any authored room into a 256x192 RGB frame."""

    def __init__(
        self,
        document: dict[str, Any],
        chr_data: bytes,
        prg_data: bytes | None = None,
        preview_contract: dict[str, Any] | None = None,
    ) -> None:
        self.document = document
        self.tiles = decode_chr_tiles(chr_data)
        if (prg_data is None) != (preview_contract is None):
            raise LevelPreviewError(
                "enemy previews require both PRG data and a preview contract"
            )
        self.enemy_decoder = (
            EnemySpriteDecoder(prg_data, preview_contract)
            if prg_data is not None and preview_contract is not None
            else None
        )

    def tile(self, bank: int, tile: int) -> tuple[tuple[int, ...], ...]:
        if not 0 <= bank < 4 or not 0 <= tile <= 0xFF:
            raise LevelPreviewError("CHR bank or tile is outside the background table")
        index = bank * CHR_TILES_PER_BANK + BACKGROUND_PATTERN_BASE + tile
        return self.tiles[index]

    def render_pattern(self, room_index: int, pattern_index: int) -> RoomPreview:
        """Render one shared RoomMap pattern with a room's CHR and palette."""
        rooms = self.document.get("rooms")
        if not isinstance(rooms, list) or not 0 <= room_index < len(rooms):
            raise LevelPreviewError("room index is outside the level document")
        bank = room_chr_bank(rooms[room_index])
        palette = room_palette(room_index)
        rgb = bytearray(METATILE_SIZE * METATILE_SIZE * 3)
        self._draw_metatile(
            rgb,
            METATILE_SIZE,
            0,
            0,
            bank,
            palette,
            document_pattern(self.document, pattern_index),
        )
        return RoomPreview(
            METATILE_SIZE,
            METATILE_SIZE,
            bytes(rgb),
            bank,
            palette,
            (),
        )

    def render_item_icon(self, room_index: int, item_type: int) -> RoomPreview:
        """Render the collectible identity behind a possibly flagged item byte."""
        if not 0 <= item_type <= 0xFF:
            raise LevelPreviewError("item icon type is outside byte range")
        identity = item_type & 0x3F
        patterns = self.document.get("tile_patterns")
        if not isinstance(patterns, list):
            raise LevelPreviewError("room tile patterns are unavailable")
        pattern_index = identity if identity < len(patterns) else ROOM_MAP_EMPTY
        return self.render_pattern(room_index, pattern_index)

    def render_enemy_icon(self, room_index: int, enemy_type: int) -> RoomPreview:
        """Render one native initial enemy frame on the selected room's bank."""
        rooms = self.document.get("rooms")
        if not isinstance(rooms, list) or not 0 <= room_index < len(rooms):
            raise LevelPreviewError("room index is outside the level document")
        if self.enemy_decoder is None:
            raise LevelPreviewError("enemy icon rendering needs PRG animation data")
        bank = room_chr_bank(rooms[room_index])
        palette = room_palette(room_index)
        background = bytes(NES_RGB[ROOM_SPRITE_PALETTE[0] & 0x3F])
        rgb = bytearray(background * (METATILE_SIZE * METATILE_SIZE))
        frame = self.enemy_decoder.frame(enemy_type)
        if frame is None:
            return RoomPreview(
                METATILE_SIZE, METATILE_SIZE, bytes(rgb), bank, palette, ()
            )
        self._draw_enemy_sprite(
            rgb,
            METATILE_SIZE,
            0,
            0,
            bank,
            frame,
            mirror_y=flip_ground_enemy_vertical(enemy_type),
        )
        return RoomPreview(
            METATILE_SIZE, METATILE_SIZE, bytes(rgb), bank, palette, (0,)
        )

    def render(
        self, room_index: int, layers: PreviewLayers | None = None
    ) -> RoomPreview:
        layers = layers or PreviewLayers()
        rooms = self.document.get("rooms")
        if not isinstance(rooms, list) or not 0 <= room_index < len(rooms):
            raise LevelPreviewError("room index is outside the level document")
        room = rooms[room_index]
        bank = room_chr_bank(room)
        palette = room_palette(room_index)
        values = room_map_values(room, layers)
        constellation = constellation_command(room) if layers.metadata else None
        width = ROOM_WIDTH * METATILE_SIZE
        height = ROOM_HEIGHT * METATILE_SIZE
        rgb = bytearray(width * height * 3)
        combined_blocks = {
            (position["x"], position["y"])
            for position in room.get("blocks", {}).get("brown", ())
            if position in room.get("blocks", {}).get("white", ())
        }
        embedded_values: dict[tuple[int, int], int] = {}
        metadata = room.get("items", {}).get("metadata", {})
        if layers.metadata and metadata.get("key_status") == "in_block":
            key = metadata.get("key")
            if visible(key):
                embedded_values[(key["x"], key["y"])] = (
                    ROOM_MAP_SOLID_BIT | ROOM_MAP_KEY
                )
        if layers.items:
            for item_type, position in item_placements(
                room.get("items", {}).get("commands", ())
            ):
                if item_type & ROOM_MAP_SOLID_BIT:
                    embedded_values[(position["x"], position["y"])] = item_type

        for cell_y, row in enumerate(values):
            for cell_x, value in enumerate(row):
                pattern = None
                translucent_block = (
                    (cell_x, cell_y) in combined_blocks
                    and value == ROOM_MAP_WHITE_BLOCK
                )
                embedded_block = (
                    embedded_values.get((cell_x, cell_y)) == value
                )
                if value == ROOM_MAP_EMPTY or translucent_block or embedded_block:
                    pattern = constellation_pattern(constellation, cell_x, cell_y)
                if pattern is None:
                    pattern_index = (
                        ROOM_MAP_EMPTY
                        if translucent_block or embedded_block
                        else classify_pattern(value)
                    )
                    pattern = document_pattern(self.document, pattern_index)
                self._draw_metatile(rgb, width, cell_x, cell_y, bank, palette, pattern)
                if translucent_block or embedded_block:
                    self._draw_metatile(
                        rgb,
                        width,
                        cell_x,
                        cell_y,
                        bank,
                        palette,
                        document_pattern(
                            self.document, 0 if embedded_block else 3
                        ),
                        opacity=(
                            EMBEDDED_BLOCK_OPACITY
                            if embedded_block
                            else COMBINED_BLOCK_OPACITY
                        ),
                        transparent_zero=True,
                    )

        if layers.special:
            for position, pattern_index in special_room_pattern_placements(
                self.document, room_index
            ):
                self._draw_metatile(
                    rgb,
                    width,
                    position["x"],
                    position["y"],
                    bank,
                    palette,
                    document_pattern(self.document, pattern_index),
                )

        if layers.items:
            patterns = self.document.get("tile_patterns", ())
            for item_type, position in item_placements(
                room.get("items", {}).get("commands", ())
            ):
                if not item_type & (ROOM_MAP_DECORATION_BIT | ROOM_MAP_SOLID_BIT):
                    continue
                if values[position["y"]][position["x"]] != item_type:
                    continue
                identity = item_type & 0x3F
                pattern_index = identity if identity < len(patterns) else ROOM_MAP_EMPTY
                self._draw_metatile(
                    rgb,
                    width,
                    position["x"],
                    position["y"],
                    bank,
                    palette,
                    document_pattern(self.document, pattern_index),
                    opacity=(
                        EMBEDDED_OBJECT_OPACITY
                        if item_type & ROOM_MAP_SOLID_BIT
                        else HIDDEN_OBJECT_OPACITY
                    ),
                    transparent_zero=True,
                )

        if layers.metadata and metadata.get("key_status") in {"hidden", "in_block"}:
            key = metadata.get("key")
            expected = KEY_CLASS_BITS[metadata["key_status"]] | ROOM_MAP_KEY
            if visible(key) and values[key["y"]][key["x"]] == expected:
                self._draw_metatile(
                    rgb,
                    width,
                    key["x"],
                    key["y"],
                    bank,
                    palette,
                    document_pattern(self.document, ROOM_MAP_KEY),
                    opacity=(
                        EMBEDDED_OBJECT_OPACITY
                        if metadata["key_status"] == "in_block"
                        else HIDDEN_OBJECT_OPACITY
                    ),
                    transparent_zero=True,
                )

        rendered_player = False
        player_start = metadata.get("player_start")
        if layers.metadata and visible(player_start) and self.enemy_decoder is not None:
            frame = self.enemy_decoder.dana_frame(player_start["x"] >= ROOM_WIDTH // 2)
            if frame is not None:
                self._draw_enemy_sprite(
                    rgb,
                    width,
                    player_start["x"],
                    player_start["y"],
                    bank,
                    frame,
                )
                rendered_player = True
        rendered_enemy_indices: list[int] = []
        if layers.enemies and self.enemy_decoder is not None:
            placements = room.get("enemies", {}).get("placements", ())
            for index, enemy in enumerate(placements):
                position = enemy.get("position") if isinstance(enemy, dict) else None
                enemy_type = enemy.get("type") if isinstance(enemy, dict) else None
                if not visible(position) or not isinstance(enemy_type, int):
                    continue
                frame = self.enemy_decoder.frame(enemy_type)
                if frame is None:
                    continue
                self._draw_enemy_sprite(
                    rgb,
                    width,
                    position["x"],
                    position["y"],
                    bank,
                    frame,
                    mirror_y=flip_ground_enemy_vertical(enemy_type),
                )
                rendered_enemy_indices.append(index)
        return RoomPreview(
            width,
            height,
            bytes(rgb),
            bank,
            palette,
            tuple(rendered_enemy_indices),
            rendered_player,
        )

    def _draw_metatile(
        self,
        output: bytearray,
        output_width: int,
        cell_x: int,
        cell_y: int,
        bank: int,
        palette: tuple[int, ...],
        pattern: PatternRecord,
        opacity: int = 255,
        transparent_zero: bool = False,
    ) -> None:
        if not 0 <= opacity <= 255:
            raise LevelPreviewError("preview opacity is outside byte range")
        for quadrant, tile_index in enumerate(pattern.tiles):
            tile = self.tile(bank, tile_index)
            origin_x = cell_x * METATILE_SIZE + (quadrant & 1) * 8
            origin_y = cell_y * METATILE_SIZE + (quadrant >> 1) * 8
            for pixel_y, row in enumerate(tile):
                for pixel_x, pixel in enumerate(row):
                    if transparent_zero and pixel == 0:
                        continue
                    palette_index = pattern.palette * 4 + pixel
                    color = NES_RGB[palette[palette_index] & 0x3F]
                    offset = ((origin_y + pixel_y) * output_width + origin_x + pixel_x) * 3
                    if opacity == 255:
                        output[offset : offset + 3] = bytes(color)
                    else:
                        output[offset : offset + 3] = bytes(
                            (
                                output[offset + channel] * (255 - opacity)
                                + color[channel] * opacity
                                + 127
                            )
                            // 255
                            for channel in range(3)
                        )

    def _draw_enemy_sprite(
        self,
        output: bytearray,
        output_width: int,
        cell_x: int,
        cell_y: int,
        bank: int,
        frame: SpriteFrame,
        mirror_x: bool = False,
        mirror_y: bool = False,
    ) -> None:
        attributes = sprite_attributes(frame.flags)
        for half, tile_byte in enumerate((frame.left_tile, frame.right_tile)):
            attribute = attributes[half]
            horizontal_flip = bool(attribute & 0x40)
            vertical_flip = bool(attribute & 0x80)
            palette_offset = (attribute & 3) * 4
            pattern_base = (tile_byte & 1) * 0x100
            top_tile = tile_byte & 0xFE
            for source_y in range(16):
                tile_index = pattern_base + top_tile + source_y // 8
                tile = self.tiles[bank * CHR_TILES_PER_BANK + tile_index]
                row = tile[source_y & 7]
                output_y = 15 - source_y if vertical_flip else source_y
                for source_x, pixel in enumerate(row):
                    if pixel == 0:
                        continue
                    output_x = 7 - source_x if horizontal_flip else source_x
                    relative_x = half * 8 + output_x
                    if mirror_x:
                        relative_x = METATILE_SIZE - 1 - relative_x
                    x = cell_x * METATILE_SIZE + relative_x
                    relative_y = (
                        METATILE_SIZE - 1 - output_y if mirror_y else output_y
                    )
                    y = cell_y * METATILE_SIZE + relative_y
                    color = NES_RGB[
                        ROOM_SPRITE_PALETTE[palette_offset + pixel] & 0x3F
                    ]
                    offset = (y * output_width + x) * 3
                    output[offset : offset + 3] = bytes(color)
