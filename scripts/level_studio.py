#!/usr/bin/env python3
"""Visual 16x12 room editor backed by the byte-exact level document codec."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

from level_editor import (
    KEY_STATUS_BITS,
    POSITION_FIELDS,
    ROOM_COUNT,
    ROOM_HEIGHT,
    ROOM_WIDTH,
    LevelEditorError,
    build_level_image,
    canonical_document,
    clean_position,
    export_document,
    load_document,
    save_document,
    validate_rebuilt_document,
)
from level_preview import LevelPreviewError, LevelPreviewRenderer, METATILE_SIZE
from project import ProjectError, parse_ines, write_if_changed
from revision_profiles import (
    ROOT,
    get_profile,
    load_profiles,
    resolve_reference,
    verify_reference,
)
from room_data import ENEMY_TYPE_MAXIMUM, ENEMY_TYPE_MINIMUM, RoomDataError


PIXEL_SCALE = 2
CELL = METATILE_SIZE * PIXEL_SCALE
CANVAS_WIDTH = ROOM_WIDTH * CELL
CANVAS_HEIGHT = ROOM_HEIGHT * CELL
MIRROR_ENEMY_SET_BUDGET = 42
LEVEL_PLAYTEST_LUA = ROOT / "scripts" / "level_playtest.lua"
EDIT_MODES = (
    "select",
    "brown block",
    "white block",
    "brown + white block",
    "erase cell",
    "player start",
    "key",
    "door",
    "mirror 1",
    "mirror 2",
    "enemy",
    "item",
)
ANCHOR_MODES = {
    "player start": "player_start",
    "key": "key",
    "door": "door",
    "mirror 1": "mirror_1",
    "mirror 2": "mirror_2",
}

ITEM_IDENTITY_NAMES = {
    0x00: "Brown block (glitch)",
    0x01: "Broken block (glitch)",
    0x02: "Door (glitch)",
    0x03: "White block (glitch)",
    0x04: "Bat symbol",
    0x05: "Demon Mirror",
    0x06: "Key (glitch)",
    0x07: "Open door (glitch)",
    0x08: "Blue diamond",
    0x09: "Blue fire jar",
    0x0A: "Gold double coin",
    0x0B: "Orange jewels / red Tzo",
    0x0C: "Orange diamond",
    0x0D: "Orange fire jar",
    0x0E: "Scroll",
    0x0F: "Bell",
    0x10: "Nothing",
    0x11: "Half time bottle",
    0x12: "Full time bottle",
    0x13: "Blue hourglass",
    0x14: "Orange hourglass",
    0x15: "Blue fire jar",
    0x16: "Orange fire jar",
    0x17: "Scroll",
    0x18: "Bell",
    0x19: "Explosion jar",
    0x1A: "Blue key",
    0x1B: "Blue jewels / blue Tzo",
    0x1C: "Shrine 1",
    0x1D: "Shrine 2",
    0x1E: "Shrine 3",
    0x1F: "Shrine 4",
    0x20: "Solomon's Seal",
    0x21: "Solomon page / Egyptian head",
    0x22: "Golden Wings / warp item",
    0x23: "Open door (out-of-table glitch 1)",
    0x24: "Open door (out-of-table glitch 2)",
    0x25: "Silver coin",
    0x26: "Silver double coin",
    0x27: "Blue opal",
    0x28: "Gold coin",
    0x29: "Gold double coin",
    0x2A: "Orange opal",
    0x2B: "Star coin",
    0x2C: "Double star coin",
    0x2D: "Dark orange opal",
    0x2E: "Origami swan",
    0x2F: "Demonhead coin",
    0x30: "Sphinx",
    0x31: "Egyptian head",
    0x32: "Magic lamp / Tecmo Bunny reward",
    0x33: "E-bottle",
    0x34: "Extra life (glitch 1)",
    0x35: "Extra life (glitch 2)",
    0x36: "Extra life (glitch 3)",
    0x37: "Mini-Dana",
    0x38: "White Tecmo Bunny",
    0x39: "Orange Tecmo Bunny",
    0x3A: "Unclassified graphics 1",
    0x3B: "Unclassified graphics 2",
    0x3C: "Unclassified graphics 3",
    0x3D: "Unclassified graphics 4",
    0x3E: "Unclassified graphics 5",
    0x3F: "Unclassified graphics 6",
}
CONSTELLATION_NAMES = (
    "Aries",
    "Gemini",
    "Virgo",
    "Aquarius",
    "Cancer",
    "Scorpio",
    "Capricorn",
    "Pisces",
    "Taurus",
    "Leo",
    "Libra",
    "Sagittarius",
)


@dataclass(frozen=True)
class ItemPlacement:
    command_index: int
    position_index: int | None
    item_type: int
    position: dict[str, int]


def profile_integer(value: object, field: str) -> int:
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise LevelEditorError(f"invalid profile playtest {field}: {value!r}") from exc


def parse_hex_byte_list(value: str, field: str, count: int | None = None) -> list[int]:
    tokens = value.replace(",", " ").split()
    try:
        result = [
            int(token.removeprefix("$").removeprefix("0x"), 16)
            for token in tokens
        ]
    except ValueError as exc:
        raise LevelEditorError(f"invalid {field} byte list: {value!r}") from exc
    if count is not None and len(result) != count:
        raise LevelEditorError(f"{field} must contain exactly {count} bytes")
    if any(not 0 <= item <= 0xFF for item in result):
        raise LevelEditorError(f"{field} contains a value outside $00..$FF")
    return result


def format_hex_byte_list(values: list[int]) -> str:
    return " ".join(f"{value:02X}" for value in values)


def enemy_type_name(value: int) -> str:
    if not ENEMY_TYPE_MINIMUM <= value <= ENEMY_TYPE_MAXIMUM:
        return "Outside enemy configuration table"
    if value < 0x1C:
        variant = value - 0x18
        return "Mighty Bomb Jack" + (f" variant {variant + 1}" if variant else "")
    if value < 0x20:
        return (
            "Fairy",
            "Fairy Princess",
            "Erratic Fairy (glitch)",
            "Erratic Fairy Princess (glitch)",
        )[value - 0x1C]
    if value < 0x24:
        return f"Bullet ({('right', 'left', 'up', 'down')[value - 0x20]})"
    if value < 0x28:
        return f"Panel Monster ({('right', 'left', 'up', 'down')[value - 0x24]})"
    if value < 0x30:
        offset = value - 0x28
        direction = (
            "right, counterclockwise",
            "left, clockwise",
            "up, clockwise",
            "down, counterclockwise",
        )[offset & 3]
        return f"Fireball ({direction}, speed {offset // 4 + 1})"
    if value < 0x50:
        offset = value - 0x30
        group = offset // 4
        variant = offset & 3
        family = "Neul" if group % 2 == 0 else "Ghost"
        speed = group // 2 % 2 + 1
        no_slow = ", no-slow flag" if group >= 4 else ""
        if family == "Neul":
            direction = "up" if variant < 2 else "down"
        else:
            direction = "right" if variant < 2 else "left"
        duplicate = " variant 2" if variant & 1 else ""
        return f"{family} ({direction}, speed {speed}{no_slow}){duplicate}"
    if value < 0x68:
        family = "Demonhead" if value < 0x5C else "Saramandor"
        offset = value - (0x50 if family == "Demonhead" else 0x5C)
        variant = offset & 3
        direction = "right" if variant in (0, 2) else "left"
        duplicate = " variant 2" if variant >= 2 else ""
        return f"{family} ({direction}, speed {offset // 4 + 1}){duplicate}"
    if value < 0x80:
        family_base = ((0x68, "Dragon"), (0x70, "Golem"), (0x78, "Gargoyle"))
        base, family = next(
            (base, name) for base, name in reversed(family_base) if value >= base
        )
        offset = value - base
        variant = offset & 3
        direction = "right" if variant in (0, 2) else "left"
        duplicate = " variant 2" if variant >= 2 else ""
        return f"{family} ({direction}, speed {offset // 4 + 1}){duplicate}"
    return (
        "Red flame",
        "White flame",
        "Red flame variant 2",
        "White flame variant 2",
    )[value - 0x80]


def item_type_name(value: int, constellation: bool = False) -> str:
    if constellation and 0xF0 <= value <= 0xFB:
        return f"Constellation: {CONSTELLATION_NAMES[value - 0xF0]}"
    name = ITEM_IDENTITY_NAMES.get(value & 0x3F, "Unclassified item")
    flags = []
    if value & 0x40:
        flags.append("hidden")
    if value & 0x80:
        flags.append("embedded in brown block")
    return name + (f" [{', '.join(flags)}]" if flags else "")


def type_choice(value: int, description: str) -> str:
    return f"${value:02X} - {description}"


def parse_type_choice(value: str, description: str) -> int:
    tokens = value.strip().split(maxsplit=1)
    if not tokens:
        raise LevelEditorError(f"invalid {description}: {value!r}")
    token = tokens[0]
    try:
        return int(token.removeprefix("$").removeprefix("0x"), 16)
    except ValueError as exc:
        raise LevelEditorError(f"invalid {description}: {value!r}") from exc


ENEMY_TYPE_CHOICES = tuple(
    type_choice(value, enemy_type_name(value))
    for value in range(ENEMY_TYPE_MINIMUM, ENEMY_TYPE_MAXIMUM + 1)
)
DIRECT_ITEM_TYPE_CHOICES = tuple(
    type_choice(value, item_type_name(value))
    for value in (*range(1, 0xC0), *range(0xFC, 0x100))
)
REPEATED_ITEM_TYPE_CHOICES = tuple(
    type_choice(value, item_type_name(value)) for value in range(0x100)
)
CONSTELLATION_TYPE_CHOICES = tuple(
    type_choice(value, item_type_name(value, constellation=True))
    for value in range(0xF0, 0xFC)
)


def combined_block_positions(blocks: dict[str, Any]) -> set[tuple[int, int]]:
    brown = {(position["x"], position["y"]) for position in blocks["brown"]}
    white = {(position["x"], position["y"]) for position in blocks["white"]}
    return brown & white


def terminal_chr_bank(command: dict[str, Any]) -> int:
    kind = command.get("kind")
    opcode = command.get("opcode")
    if kind not in {"end", "constellation"} or not isinstance(opcode, int):
        raise LevelEditorError("room item stream has no valid terminating command")
    return opcode >> 2 & 3


def level_playtest_environment(
    profile: dict[str, Any],
    room_index: int,
    result_path: Path | None = None,
    exit_after_ready: bool = False,
) -> dict[str, str]:
    if not 0 <= room_index < ROOM_COUNT:
        raise LevelEditorError(f"playtest room must be 0..{ROOM_COUNT - 1}")
    contract = profile.get("playtest")
    if not isinstance(contract, dict):
        raise LevelEditorError(f"profile {profile.get('id')} has no playtest contract")
    environment = os.environ.copy()
    environment.update(
        SOLOMON_LEVEL_ROOM=str(room_index),
        SOLOMON_LEVEL_ROOM_LOAD_ADDRESS=str(
            profile_integer(contract.get("room_load_address"), "room_load_address")
        ),
        SOLOMON_LEVEL_GAMEPLAY_ADDRESS=str(
            profile_integer(contract.get("gameplay_address"), "gameplay_address")
        ),
        SOLOMON_LEVEL_CURRENT_ROOM_ADDRESS=str(
            profile_integer(
                contract.get("current_room_address"), "current_room_address"
            )
        ),
        SOLOMON_LEVEL_START_FRAME=str(
            profile_integer(contract.get("start_frame"), "start_frame")
        ),
        SOLOMON_LEVEL_READY_FRAMES=str(
            profile_integer(contract.get("ready_frames"), "ready_frames")
        ),
        SOLOMON_LEVEL_EXIT="1" if exit_after_ready else "0",
    )
    if result_path is not None:
        environment["SOLOMON_LEVEL_RESULT"] = result_path.resolve().as_posix()
    return environment


def level_playtest_command(
    fceux: Path,
    image: Path,
    smoke_frames: int | None = None,
) -> list[str]:
    command = [str(fceux.resolve()), "-lua", str(LEVEL_PLAYTEST_LUA.resolve())]
    if smoke_frames is not None:
        command.extend(
            ("-max-frames", str(smoke_frames + 2), "-turbo", "1", "-nothrottle", "1")
        )
    command.append(str(image.resolve()))
    return command


def validate_playtest_result(path: Path, room_index: int) -> str:
    try:
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        fields = dict(field.split("=", 1) for field in first_line.split())
    except (OSError, IndexError, ValueError) as exc:
        raise LevelEditorError(f"cannot read playtest result {path}: {exc}") from exc
    expected = f"{room_index:02x}"
    if fields.get("status") != "ready" or fields.get("current_room") != expected:
        raise LevelEditorError(f"selected room playtest failed: {first_line}")
    return first_line


def run_playtest_smoke(
    fceux: Path,
    image: Path,
    profile: dict[str, Any],
    room_index: int,
    result_path: Path,
) -> str:
    contract = profile["playtest"]
    ready_frames = profile_integer(contract["ready_frames"], "ready_frames")
    process = subprocess.Popen(
        level_playtest_command(fceux, image, ready_frames),
        cwd=image.parent,
        env=level_playtest_environment(
            profile,
            room_index,
            result_path=result_path,
            exit_after_ready=True,
        ),
    )
    deadline = time.monotonic() + 120
    try:
        while time.monotonic() < deadline:
            if result_path.is_file():
                return validate_playtest_result(result_path, room_index)
            return_code = process.poll()
            if return_code is not None:
                raise LevelEditorError(
                    f"FCEUX playtest exited with code {return_code} before reporting"
                )
            time.sleep(0.1)
        raise LevelEditorError("FCEUX playtest did not report within 120 seconds")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()


class StudioDocument:
    def __init__(self, document: dict[str, Any]) -> None:
        self.document = document
        self.original = canonical_document(document)
        self.undo_stack: list[dict[str, Any]] = []

    @property
    def dirty(self) -> bool:
        return canonical_document(self.document) != self.original

    def mark_saved(self) -> None:
        self.original = canonical_document(self.document)

    def room(self, room_index: int) -> dict[str, Any]:
        if not 0 <= room_index < ROOM_COUNT:
            raise LevelEditorError(f"room index outside 0..{ROOM_COUNT - 1}")
        return self.document["rooms"][room_index]

    def mutate(self, callback: Callable[[], bool]) -> bool:
        before = copy.deepcopy(self.document)
        changed = callback()
        if changed:
            self.undo_stack.append(before)
            if len(self.undo_stack) > 100:
                del self.undo_stack[0]
        return changed

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        self.document = self.undo_stack.pop()
        return True

    @staticmethod
    def same_position(value: dict[str, int], x: int, y: int) -> bool:
        return value.get("x") == x and value.get("y") == y

    def set_block(self, room_index: int, kind: str, x: int, y: int) -> bool:
        memberships = {
            "brown": frozenset(("brown",)),
            "white": frozenset(("white",)),
            "brown_white": frozenset(("brown", "white")),
        }
        if kind not in memberships:
            raise LevelEditorError(f"unknown block kind: {kind}")

        def apply() -> bool:
            blocks = self.room(room_index)["blocks"]
            changed = False
            for plane in ("brown", "white"):
                values = blocks[plane]
                existing = next(
                    (value for value in values if self.same_position(value, x, y)),
                    None,
                )
                enabled = plane in memberships[kind]
                if enabled and existing is None:
                    values.append({"x": x, "y": y})
                    values.sort(key=lambda value: (value["y"], value["x"]))
                    changed = True
                elif not enabled and existing is not None:
                    values.remove(existing)
                    changed = True
            return changed

        return self.mutate(apply)

    def set_anchor(self, room_index: int, field: str, x: int, y: int) -> bool:
        if field not in POSITION_FIELDS:
            raise LevelEditorError(f"unknown room anchor: {field}")

        def apply() -> bool:
            metadata = self.room(room_index)["items"]["metadata"]
            value = {"x": x, "y": y}
            if metadata[field] == value:
                return False
            metadata[field] = value
            return True

        return self.mutate(apply)

    def set_room_properties(
        self,
        room_index: int,
        spawn_lifetime: int,
        key_status: str,
        time_rate: int,
        schedules: tuple[int, int],
        enemy_sets: tuple[int, int],
    ) -> bool:
        if not 0 <= spawn_lifetime <= 0xFF:
            raise LevelEditorError("spawn lifetime must be 0..255")
        if key_status not in KEY_STATUS_BITS:
            raise LevelEditorError(f"unknown key status: {key_status}")
        if not 0 <= time_rate <= 0x0F:
            raise LevelEditorError("time decrease rate must be 0..15")
        if any(not 0 <= value < 16 for value in schedules):
            raise LevelEditorError("mirror schedule index must be 0..15")
        if any(not 0 <= value < 17 for value in enemy_sets):
            raise LevelEditorError("mirror enemy-set index must be 0..16")

        def apply() -> bool:
            room = self.room(room_index)
            metadata = room["items"]["metadata"]
            new_values = {
                "spawn_lifetime": spawn_lifetime,
                "key_status": key_status,
                "time_decrease_rate": time_rate,
                "mirror_1_schedule": schedules[0],
                "mirror_2_schedule": schedules[1],
                "mirror_1_enemy_set": enemy_sets[0],
                "mirror_2_enemy_set": enemy_sets[1],
            }
            old_values = {
                "spawn_lifetime": room["enemies"]["spawn_lifetime"],
                **{key: metadata[key] for key in new_values if key != "spawn_lifetime"},
            }
            if old_values == new_values:
                return False
            room["enemies"]["spawn_lifetime"] = spawn_lifetime
            for key, value in new_values.items():
                if key != "spawn_lifetime":
                    metadata[key] = value
            return True

        return self.mutate(apply)

    def set_mirror_schedule(
        self,
        schedule_index: int,
        initial_phase: list[int],
        loop_phase: list[int],
    ) -> bool:
        schedules = self.document["mirror_schedules"]
        if not 0 <= schedule_index < len(schedules):
            raise LevelEditorError("Demon Mirror schedule index is outside 0..15")
        if len(initial_phase) != 4 or len(loop_phase) != 4:
            raise LevelEditorError("Demon Mirror schedule phases need four bytes each")
        if any(not 0 <= value <= 0xFF for value in initial_phase + loop_phase):
            raise LevelEditorError("Demon Mirror schedule byte is outside $00..$FF")

        def apply() -> bool:
            schedule = schedules[schedule_index]
            replacement = {
                "index": schedule_index,
                "initial_phase": list(initial_phase),
                "loop_phase": list(loop_phase),
            }
            if schedule == replacement:
                return False
            schedules[schedule_index] = replacement
            return True

        return self.mutate(apply)

    def set_mirror_enemy_set(
        self,
        enemy_set_index: int,
        enemy_types: list[int],
        loop_offset: int,
    ) -> bool:
        enemy_sets = self.document["mirror_enemy_sets"]
        if not 0 <= enemy_set_index < len(enemy_sets):
            raise LevelEditorError("Demon Mirror enemy-set index is outside 0..16")
        if not enemy_types:
            raise LevelEditorError("Demon Mirror enemy set cannot be empty")
        if any(
            not ENEMY_TYPE_MINIMUM <= value <= ENEMY_TYPE_MAXIMUM
            for value in enemy_types
        ):
            raise LevelEditorError("Demon Mirror enemy type must be $18..$83")
        if not 0 <= loop_offset < len(enemy_types):
            raise LevelEditorError(
                "Demon Mirror loop offset must select an enemy in this set"
            )
        used = sum(len(record["enemy_types"]) + 1 for record in enemy_sets)
        replacement_size = len(enemy_types) + 1
        current_size = len(enemy_sets[enemy_set_index]["enemy_types"]) + 1
        if used - current_size + replacement_size > MIRROR_ENEMY_SET_BUDGET:
            raise LevelEditorError(
                "Demon Mirror enemy sets exceed their shared 42-byte budget"
            )

        def apply() -> bool:
            enemy_set = enemy_sets[enemy_set_index]
            replacement = {
                "index": enemy_set_index,
                "enemy_types": list(enemy_types),
                "loop_offset": loop_offset,
            }
            if enemy_set == replacement:
                return False
            enemy_sets[enemy_set_index] = replacement
            return True

        return self.mutate(apply)

    def set_room_terminator(
        self,
        room_index: int,
        kind: str,
        chr_bank: int,
        constellation_index: int,
        x: int,
        y: int,
    ) -> bool:
        if kind not in {"end", "constellation"}:
            raise LevelEditorError(f"unknown room terminator kind: {kind!r}")
        if not 0 <= chr_bank <= 3:
            raise LevelEditorError("room CHR bank must be 0..3")
        if not 0 <= constellation_index < len(CONSTELLATION_NAMES):
            raise LevelEditorError("constellation index must be 0..11")
        if kind == "constellation" and chr_bank != constellation_index >> 2:
            raise LevelEditorError("constellation opcode and CHR bank disagree")
        commands = self.room(room_index)["items"]["commands"]
        if not commands or commands[-1].get("kind") not in {"end", "constellation"}:
            raise LevelEditorError("room item stream has no terminating command")
        current = commands[-1]
        if kind == "constellation":
            replacement = {
                "kind": kind,
                "opcode": 0xF0 + constellation_index,
                "position": clean_position({"x": x, "y": y}),
            }
        else:
            current_opcode = current.get("opcode")
            low_bits = (
                current_opcode & 3
                if current.get("kind") == "end" and isinstance(current_opcode, int)
                else 0
            )
            opcode = 0xE0 | chr_bank << 2 | low_bits
            if current_opcode == 0 and chr_bank == 0:
                opcode = 0
            replacement = {"kind": kind, "opcode": opcode}

        def apply() -> bool:
            if current == replacement:
                return False
            commands[-1] = replacement
            return True

        return self.mutate(apply)

    def add_enemy(
        self,
        room_index: int,
        enemy_type: int,
        x: int,
        y: int,
    ) -> bool:
        if not ENEMY_TYPE_MINIMUM <= enemy_type <= ENEMY_TYPE_MAXIMUM:
            raise LevelEditorError("enemy type must be $18..$83")

        def apply() -> bool:
            self.room(room_index)["enemies"]["placements"].append(
                {"type": enemy_type, "position": {"x": x, "y": y}}
            )
            return True

        return self.mutate(apply)

    def add_item(
        self,
        room_index: int,
        item_type: int,
        x: int,
        y: int,
    ) -> bool:
        if not (1 <= item_type < 0xC0 or 0xFC <= item_type <= 0xFF):
            raise LevelEditorError("item type must be $01..$BF or $FC..$FF")

        def apply() -> bool:
            commands = self.room(room_index)["items"]["commands"]
            insertion = len(commands)
            if commands and commands[-1]["kind"] in {"end", "constellation"}:
                insertion -= 1
            commands.insert(
                insertion,
                {"kind": "item", "type": item_type, "position": {"x": x, "y": y}},
            )
            return True

        return self.mutate(apply)

    def update_enemy(
        self,
        room_index: int,
        enemy_index: int,
        enemy_type: int,
        x: int,
        y: int,
    ) -> bool:
        if not ENEMY_TYPE_MINIMUM <= enemy_type <= ENEMY_TYPE_MAXIMUM:
            raise LevelEditorError("enemy type must be $18..$83")
        position = clean_position({"x": x, "y": y})
        placements = self.room(room_index)["enemies"]["placements"]
        if not 0 <= enemy_index < len(placements):
            raise LevelEditorError("selected enemy no longer exists")

        def apply() -> bool:
            replacement = {"type": enemy_type, "position": position}
            if placements[enemy_index] == replacement:
                return False
            placements[enemy_index] = replacement
            return True

        return self.mutate(apply)

    def remove_enemy(self, room_index: int, enemy_index: int) -> bool:
        placements = self.room(room_index)["enemies"]["placements"]
        if not 0 <= enemy_index < len(placements):
            raise LevelEditorError("selected enemy no longer exists")

        def apply() -> bool:
            del placements[enemy_index]
            return True

        return self.mutate(apply)

    def update_item_placement(
        self,
        room_index: int,
        command_index: int,
        position_index: int | None,
        item_type: int,
        x: int,
        y: int,
    ) -> bool:
        position = clean_position({"x": x, "y": y})
        commands = self.room(room_index)["items"]["commands"]
        if not 0 <= command_index < len(commands):
            raise LevelEditorError("selected item command no longer exists")
        command = commands[command_index]
        kind = command["kind"]
        if kind == "item":
            if position_index is not None:
                raise LevelEditorError("direct item has no repeated position index")
            if not (1 <= item_type < 0xC0 or 0xFC <= item_type <= 0xFF):
                raise LevelEditorError("item type must be $01..$BF or $FC..$FF")
        elif kind == "repeat":
            positions = command["positions"]
            if position_index is None or not 0 <= position_index < len(positions):
                raise LevelEditorError("selected repeated item no longer exists")
            if not 0 <= item_type <= 0xFF:
                raise LevelEditorError("repeated item type must be $00..$FF")
        elif kind == "constellation":
            if position_index is not None:
                raise LevelEditorError("constellation has no repeated position index")
            if not 0xF0 <= item_type <= 0xFB:
                raise LevelEditorError("constellation opcode must be $F0..$FB")
        else:
            raise LevelEditorError(f"cannot edit item command {kind!r}")

        def apply() -> bool:
            if kind == "repeat":
                old_position = command["positions"][position_index]
                if command["type"] == item_type and old_position == position:
                    return False
                command["type"] = item_type
                command["positions"][position_index] = position
            else:
                type_field = "opcode" if kind == "constellation" else "type"
                if command[type_field] == item_type and command["position"] == position:
                    return False
                command[type_field] = item_type
                command["position"] = position
            return True

        return self.mutate(apply)

    def remove_item_placement(
        self,
        room_index: int,
        command_index: int,
        position_index: int | None,
    ) -> bool:
        commands = self.room(room_index)["items"]["commands"]
        if not 0 <= command_index < len(commands):
            raise LevelEditorError("selected item command no longer exists")
        command = commands[command_index]
        kind = command["kind"]
        if kind == "repeat":
            positions = command["positions"]
            if position_index is None or not 0 <= position_index < len(positions):
                raise LevelEditorError("selected repeated item no longer exists")
        elif kind not in {"item", "constellation"} or position_index is not None:
            raise LevelEditorError(f"cannot remove item command {kind!r}")

        def apply() -> bool:
            if kind == "repeat" and len(command["positions"]) > 1:
                del command["positions"][position_index]
            elif kind == "constellation":
                commands[command_index] = {
                    "kind": "end",
                    "opcode": 0xE0 | (command["opcode"] & 0x0C),
                }
            else:
                del commands[command_index]
            return True

        return self.mutate(apply)

    def item_placements(self, room_index: int) -> list[ItemPlacement]:
        result: list[ItemPlacement] = []
        commands = self.room(room_index)["items"]["commands"]
        for command_index, command in enumerate(commands):
            kind = command["kind"]
            if kind == "item":
                result.append(
                    ItemPlacement(
                        command_index,
                        None,
                        command["type"],
                        command["position"],
                    )
                )
            elif kind == "repeat":
                result.extend(
                    ItemPlacement(command_index, index, command["type"], position)
                    for index, position in enumerate(command["positions"])
                )
            elif kind == "constellation":
                result.append(
                    ItemPlacement(
                        command_index,
                        None,
                        command["opcode"],
                        command["position"],
                    )
                )
        return result

    def erase_cell(self, room_index: int, x: int, y: int) -> bool:
        def apply() -> bool:
            room = self.room(room_index)
            changed = False
            for kind in ("brown", "white"):
                values = room["blocks"][kind]
                kept = [value for value in values if not self.same_position(value, x, y)]
                if len(kept) != len(values):
                    values[:] = kept
                    changed = True
            placements = room["enemies"]["placements"]
            kept_enemies = [
                value
                for value in placements
                if not self.same_position(value["position"], x, y)
            ]
            if len(kept_enemies) != len(placements):
                placements[:] = kept_enemies
                changed = True
            commands = room["items"]["commands"]
            for command in list(commands):
                if command["kind"] in {"item", "constellation"}:
                    if self.same_position(command["position"], x, y):
                        commands.remove(command)
                        changed = True
                elif command["kind"] == "repeat":
                    values = command["positions"]
                    kept = [
                        value for value in values
                        if not self.same_position(value, x, y)
                    ]
                    if len(kept) != len(values):
                        changed = True
                        if kept:
                            command["positions"] = kept
                        else:
                            commands.remove(command)
            return changed

        return self.mutate(apply)


class RoomTerminatorDialog(tk.Toplevel):
    """Edit the item-stream terminator which owns tileset and constellation."""

    def __init__(self, studio: "LevelStudio") -> None:
        super().__init__(studio)
        self.studio = studio
        self.room_index = studio.room_index.get()
        self.kind = tk.StringVar(value="end")
        self.chr_bank = tk.IntVar(value=0)
        self.constellation = tk.StringVar(value=CONSTELLATION_TYPE_CHOICES[0])
        self.x = tk.IntVar(value=0)
        self.y = tk.IntVar(value=0)
        self.summary = tk.StringVar()
        self.title(
            f"Room {self.room_index + 1:02d} tileset / constellation "
            f"[{studio.profile['id']}]"
        )
        self.resizable(False, False)
        self.transient(studio)
        self.build_ui()
        self.load()

    def build_ui(self) -> None:
        body = ttk.Frame(self, padding=10)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Ending kind").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            body,
            textvariable=self.kind,
            values=("end", "constellation"),
            state="readonly",
            width=18,
        ).grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Label(body, text="CHR bank / tileset").grid(
            row=1, column=0, sticky="w", pady=(7, 0)
        )
        ttk.Spinbox(
            body,
            from_=0,
            to=3,
            textvariable=self.chr_bank,
            width=6,
        ).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(7, 0))
        ttk.Label(body, text="Constellation").grid(
            row=2, column=0, sticky="w", pady=(7, 0)
        )
        constellation_box = ttk.Combobox(
            body,
            textvariable=self.constellation,
            values=CONSTELLATION_TYPE_CHOICES,
            state="readonly",
            width=34,
        )
        constellation_box.grid(row=2, column=1, padx=(8, 0), pady=(7, 0))
        constellation_box.bind("<<ComboboxSelected>>", self.select_constellation)
        ttk.Label(body, text="Position X / Y").grid(
            row=3, column=0, sticky="w", pady=(7, 0)
        )
        position = ttk.Frame(body)
        position.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(7, 0))
        ttk.Spinbox(position, from_=0, to=15, textvariable=self.x, width=5).pack(
            side="left"
        )
        ttk.Spinbox(position, from_=-1, to=13, textvariable=self.y, width=5).pack(
            side="left", padx=(6, 0)
        )
        ttk.Label(
            body,
            textvariable=self.summary,
            wraplength=430,
            justify="left",
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(9, 0))
        ttk.Button(body, text="Apply", command=self.apply).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )

    def terminal(self) -> dict[str, Any]:
        return self.studio.model.room(self.room_index)["items"]["commands"][-1]

    def load(self) -> None:
        terminal = self.terminal()
        kind = terminal["kind"]
        bank = terminal_chr_bank(terminal)
        self.kind.set(kind)
        self.chr_bank.set(bank)
        if kind == "constellation":
            index = terminal["opcode"] - 0xF0
            self.constellation.set(CONSTELLATION_TYPE_CHOICES[index])
            self.x.set(terminal["position"]["x"])
            self.y.set(terminal["position"]["y"])
            detail = CONSTELLATION_NAMES[index]
        else:
            detail = "no constellation"
        self.summary.set(
            f"Stored opcode ${terminal['opcode']:02X}: CHR bank {bank}, {detail}. "
            "For a constellation, its zodiac opcode determines the CHR bank."
        )

    def select_constellation(self, _event: object = None) -> None:
        opcode = parse_type_choice(self.constellation.get(), "constellation")
        self.chr_bank.set((opcode >> 2) & 3)

    def apply(self) -> None:
        try:
            constellation_index = (
                parse_type_choice(self.constellation.get(), "constellation") - 0xF0
            )
            if self.kind.get() == "constellation":
                self.chr_bank.set(constellation_index >> 2)
            changed = self.studio.model.set_room_terminator(
                self.room_index,
                self.kind.get(),
                self.chr_bank.get(),
                constellation_index,
                self.x.get(),
                self.y.get(),
            )
            self.load()
            if self.studio.room_index.get() == self.room_index:
                self.studio.redraw()
            self.studio.set_status(
                "Room tileset/constellation updated" if changed else "No change"
            )
        except (tk.TclError, LevelEditorError) as exc:
            messagebox.showerror("Invalid room ending", str(exc), parent=self)


class MirrorDataDialog(tk.Toplevel):
    """Edit the shared schedule and cyclic enemy-set tables used by rooms."""

    def __init__(self, studio: "LevelStudio") -> None:
        super().__init__(studio)
        self.studio = studio
        self.schedule_index = tk.IntVar(value=0)
        self.schedule_initial = tk.StringVar()
        self.schedule_loop = tk.StringVar()
        self.schedule_references = tk.StringVar()
        self.enemy_set_index = tk.IntVar(value=0)
        self.enemy_types = tk.StringVar()
        self.enemy_loop_offset = tk.IntVar(value=0)
        self.enemy_set_references = tk.StringVar()
        self.enemy_set_usage = tk.StringVar()
        self.title(f"Demon Mirror data [{studio.profile['id']}]")
        self.resizable(False, False)
        self.transient(studio)
        self.build_ui()
        self.load_schedule()
        self.load_enemy_set()

    def build_ui(self) -> None:
        body = ttk.Frame(self, padding=10)
        body.pack(fill="both", expand=True)

        schedules = ttk.LabelFrame(body, text="Spawn schedule", padding=8)
        schedules.pack(fill="x")
        ttk.Label(schedules, text="Index").grid(row=0, column=0, sticky="w")
        schedule_box = ttk.Combobox(
            schedules,
            textvariable=self.schedule_index,
            values=tuple(range(16)),
            state="readonly",
            width=5,
        )
        schedule_box.grid(row=0, column=1, sticky="w", padx=(7, 0))
        schedule_box.bind("<<ComboboxSelected>>", self.load_schedule)
        ttk.Label(schedules, text="Initial four bytes").grid(
            row=1, column=0, sticky="w", pady=(7, 0)
        )
        ttk.Entry(schedules, textvariable=self.schedule_initial, width=28).grid(
            row=1, column=1, padx=(7, 0), pady=(7, 0)
        )
        ttk.Label(schedules, text="Loop four bytes").grid(
            row=2, column=0, sticky="w", pady=(5, 0)
        )
        ttk.Entry(schedules, textvariable=self.schedule_loop, width=28).grid(
            row=2, column=1, padx=(7, 0), pady=(5, 0)
        )
        ttk.Label(
            schedules,
            textvariable=self.schedule_references,
            wraplength=390,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(7, 0))
        ttk.Button(
            schedules,
            text="Apply schedule",
            command=self.apply_schedule,
        ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        enemy_sets = ttk.LabelFrame(body, text="Cyclic enemy set", padding=8)
        enemy_sets.pack(fill="x", pady=(10, 0))
        ttk.Label(enemy_sets, text="Index").grid(row=0, column=0, sticky="w")
        enemy_set_box = ttk.Combobox(
            enemy_sets,
            textvariable=self.enemy_set_index,
            values=tuple(range(17)),
            state="readonly",
            width=5,
        )
        enemy_set_box.grid(row=0, column=1, sticky="w", padx=(7, 0))
        enemy_set_box.bind("<<ComboboxSelected>>", self.load_enemy_set)
        ttk.Label(enemy_sets, text="Enemy type bytes").grid(
            row=1, column=0, sticky="w", pady=(7, 0)
        )
        ttk.Entry(enemy_sets, textvariable=self.enemy_types, width=28).grid(
            row=1, column=1, padx=(7, 0), pady=(7, 0)
        )
        ttk.Label(enemy_sets, text="Loop offset").grid(
            row=2, column=0, sticky="w", pady=(5, 0)
        )
        ttk.Spinbox(
            enemy_sets,
            from_=0,
            to=0x6F,
            textvariable=self.enemy_loop_offset,
            width=7,
        ).grid(row=2, column=1, sticky="w", padx=(7, 0), pady=(5, 0))
        ttk.Label(
            enemy_sets,
            textvariable=self.enemy_set_references,
            wraplength=390,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(7, 0))
        ttk.Label(
            enemy_sets,
            textvariable=self.enemy_set_usage,
            wraplength=390,
            justify="left",
        ).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(3, 0)
        )
        ttk.Button(
            enemy_sets,
            text="Apply enemy set",
            command=self.apply_enemy_set,
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def referenced_rooms(self, fields: tuple[str, str], index: int) -> str:
        rooms = []
        for room_index, room in enumerate(self.studio.model.document["rooms"]):
            metadata = room["items"]["metadata"]
            if any(metadata[field] == index for field in fields):
                rooms.append(room_index + 1)
        return "Rooms using this record: " + (
            ", ".join(f"{room:02d}" for room in rooms) if rooms else "none"
        )

    def load_schedule(self, _event: object = None) -> None:
        index = self.schedule_index.get()
        schedule = self.studio.model.document["mirror_schedules"][index]
        self.schedule_initial.set(format_hex_byte_list(schedule["initial_phase"]))
        self.schedule_loop.set(format_hex_byte_list(schedule["loop_phase"]))
        self.schedule_references.set(
            self.referenced_rooms(("mirror_1_schedule", "mirror_2_schedule"), index)
        )

    def load_enemy_set(self, _event: object = None) -> None:
        index = self.enemy_set_index.get()
        enemy_set = self.studio.model.document["mirror_enemy_sets"][index]
        self.enemy_types.set(format_hex_byte_list(enemy_set["enemy_types"]))
        self.enemy_loop_offset.set(enemy_set["loop_offset"])
        self.enemy_set_references.set(
            self.referenced_rooms(("mirror_1_enemy_set", "mirror_2_enemy_set"), index)
        )
        used = sum(
            len(record["enemy_types"]) + 1
            for record in self.studio.model.document["mirror_enemy_sets"]
        )
        self.enemy_set_usage.set(
            f"Shared encoded budget: {used}/{MIRROR_ENEMY_SET_BUDGET} bytes\n"
            "Sequence: "
            + ", ".join(
                type_choice(value, enemy_type_name(value))
                for value in enemy_set["enemy_types"]
            )
        )

    def apply_schedule(self) -> None:
        try:
            changed = self.studio.model.set_mirror_schedule(
                self.schedule_index.get(),
                parse_hex_byte_list(
                    self.schedule_initial.get(), "initial schedule phase", 4
                ),
                parse_hex_byte_list(
                    self.schedule_loop.get(), "loop schedule phase", 4
                ),
            )
            self.load_schedule()
            self.studio.set_status("Mirror schedule updated" if changed else "No change")
        except (tk.TclError, LevelEditorError) as exc:
            messagebox.showerror("Invalid Demon Mirror schedule", str(exc), parent=self)

    def apply_enemy_set(self) -> None:
        try:
            changed = self.studio.model.set_mirror_enemy_set(
                self.enemy_set_index.get(),
                parse_hex_byte_list(self.enemy_types.get(), "enemy-set type"),
                self.enemy_loop_offset.get(),
            )
            self.load_enemy_set()
            self.studio.set_status("Mirror enemy set updated" if changed else "No change")
        except (tk.TclError, LevelEditorError) as exc:
            messagebox.showerror("Invalid Demon Mirror enemy set", str(exc), parent=self)


class LevelStudio(tk.Tk):
    def __init__(
        self,
        model: StudioDocument,
        profile: dict[str, Any],
        reference: Path,
        document_path: Path,
        output_path: Path,
        fceux: Path,
        chr_data: bytes,
        prg_data: bytes,
    ) -> None:
        super().__init__()
        self.model = model
        self.profile = profile
        self.reference = reference
        self.document_path = document_path
        self.output_path = output_path
        self.fceux = fceux
        self.preview_renderer = LevelPreviewRenderer(
            model.document,
            chr_data,
            prg_data,
            profile["level_preview"],
        )
        self.preview_image: tk.PhotoImage | None = None
        self.playtest_process: subprocess.Popen[bytes] | None = None
        self.selection: tuple[str, int, int | None] | None = None
        self.record_refs: dict[str, tuple[str, int, int | None]] = {}
        self.room_index = tk.IntVar(value=0)
        self.room_choice = tk.StringVar(value="Room 01")
        self.mode = tk.StringVar(value="select")
        self.enemy_type = tk.StringVar(value=ENEMY_TYPE_CHOICES[0x71 - 0x18])
        self.item_type = tk.StringVar(
            value=type_choice(0x18, item_type_name(0x18))
        )
        self.status = tk.StringVar()
        self.selected_record = tk.StringVar(value="No record selected")
        self.selected_type = tk.StringVar(value="")
        self.selected_x = tk.IntVar(value=0)
        self.selected_y = tk.IntVar(value=0)
        self.property_vars = {
            "spawn_lifetime": tk.IntVar(),
            "time_decrease_rate": tk.IntVar(),
            "key_status": tk.StringVar(),
            "mirror_1_schedule": tk.IntVar(),
            "mirror_2_schedule": tk.IntVar(),
            "mirror_1_enemy_set": tk.IntVar(),
            "mirror_2_enemy_set": tk.IntVar(),
        }
        self.title(f"Solomon's Key Level Studio [{profile['id']}]")
        self.geometry("1260x760")
        self.minsize(1050, 680)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.build_ui()
        self.load_properties()
        self.redraw()

    def build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=7)
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="Room").pack(side="left")
        room_box = ttk.Combobox(
            toolbar,
            textvariable=self.room_choice,
            values=[f"Room {number:02d}" for number in range(1, ROOM_COUNT + 1)],
            state="readonly",
            width=10,
        )
        room_box.pack(side="left", padx=(4, 12))
        room_box.bind("<<ComboboxSelected>>", self.select_room)
        ttk.Label(toolbar, text="Tool").pack(side="left")
        mode_box = ttk.Combobox(
            toolbar,
            textvariable=self.mode,
            values=EDIT_MODES,
            state="readonly",
            width=15,
        )
        mode_box.pack(side="left", padx=4)
        for text, command in (
            ("Undo", self.undo),
            ("Save", self.save),
            ("Build ROM", self.build_rom),
            ("Tileset", self.open_room_terminator),
            ("Mirror data", self.open_mirror_data),
            ("Play", self.play),
            ("Stop", self.stop_playtest),
        ):
            ttk.Button(toolbar, text=text, command=command).pack(side="left", padx=3)
        ttk.Label(toolbar, textvariable=self.status).pack(side="right")

        body = ttk.Frame(self, padding=(7, 0, 7, 7))
        body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(
            body,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg="#101820",
            highlightthickness=0,
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.canvas.bind("<Button-3>", self.erase_click)

        side = ttk.Frame(body, padding=(10, 0))
        side.pack(side="right", fill="y")
        type_box = ttk.LabelFrame(side, text="Placed object", padding=7)
        type_box.pack(fill="x", pady=(0, 8))
        ttk.Label(type_box, text="Enemy type").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            type_box,
            textvariable=self.enemy_type,
            values=ENEMY_TYPE_CHOICES,
            width=39,
        ).grid(row=0, column=1)
        ttk.Label(type_box, text="Item type").grid(row=1, column=0, sticky="w")
        ttk.Combobox(
            type_box,
            textvariable=self.item_type,
            values=DIRECT_ITEM_TYPE_CHOICES,
            width=39,
        ).grid(row=1, column=1)

        properties = ttk.LabelFrame(side, text="Room properties", padding=7)
        properties.pack(fill="x")
        rows = (
            ("spawn_lifetime", "Enemy lifetime", 0, 255),
            ("time_decrease_rate", "Time rate", 0, 15),
            ("mirror_1_schedule", "Mirror 1 schedule", 0, 15),
            ("mirror_2_schedule", "Mirror 2 schedule", 0, 15),
            ("mirror_1_enemy_set", "Mirror 1 set", 0, 16),
            ("mirror_2_enemy_set", "Mirror 2 set", 0, 16),
        )
        for row, (name, label, low, high) in enumerate(rows):
            ttk.Label(properties, text=label).grid(row=row, column=0, sticky="w")
            ttk.Spinbox(
                properties,
                from_=low,
                to=high,
                textvariable=self.property_vars[name],
                width=7,
            ).grid(row=row, column=1, padx=(8, 0), pady=2)
        ttk.Label(properties, text="Key status").grid(row=len(rows), column=0, sticky="w")
        ttk.Combobox(
            properties,
            textvariable=self.property_vars["key_status"],
            values=tuple(KEY_STATUS_BITS),
            state="readonly",
            width=10,
        ).grid(row=len(rows), column=1, padx=(8, 0), pady=2)
        ttk.Button(
            properties,
            text="Apply properties",
            command=self.apply_properties,
        ).grid(row=len(rows) + 1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        records = ttk.LabelFrame(side, text="Room records", padding=7)
        records.pack(fill="both", expand=True, pady=(8, 0))
        self.record_tree = ttk.Treeview(
            records,
            columns=("kind", "type", "x", "y", "source"),
            show="headings",
            height=8,
            selectmode="browse",
        )
        for name, label, width in (
            ("kind", "Kind", 80),
            ("type", "Type", 190),
            ("x", "X", 28),
            ("y", "Y", 28),
            ("source", "Source", 92),
        ):
            self.record_tree.heading(name, text=label)
            self.record_tree.column(
                name, width=width, stretch=name in {"kind", "source"}
            )
        self.record_tree.pack(fill="both", expand=True)
        self.record_tree.bind("<<TreeviewSelect>>", self.select_record_row)

        inspector = ttk.Frame(records, padding=(0, 7, 0, 0))
        inspector.pack(fill="x")
        ttk.Label(inspector, textvariable=self.selected_record).grid(
            row=0, column=0, columnspan=6, sticky="w"
        )
        for column, (label, variable, width) in enumerate(
            (
                ("Type", self.selected_type, 7),
                ("X", self.selected_x, 4),
                ("Y", self.selected_y, 4),
            )
        ):
            ttk.Label(inspector, text=label).grid(row=1, column=column * 2, sticky="e")
            if label == "Type":
                self.selected_type_box = ttk.Combobox(
                    inspector,
                    textvariable=variable,
                    values=REPEATED_ITEM_TYPE_CHOICES,
                    width=32,
                )
                self.selected_type_box.grid(
                    row=1, column=column * 2 + 1, padx=(3, 7)
                )
            else:
                ttk.Entry(inspector, textvariable=variable, width=width).grid(
                    row=1, column=column * 2 + 1, padx=(3, 7)
                )
        ttk.Button(inspector, text="Apply", command=self.apply_selected_record).grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0), padx=(0, 3)
        )
        ttk.Button(inspector, text="Delete", command=self.delete_selected_record).grid(
            row=2, column=3, columnspan=3, sticky="ew", pady=(6, 0), padx=(3, 0)
        )

        legend = ttk.LabelFrame(side, text="Legend", padding=7)
        legend.pack(fill="x", pady=(8, 0))
        ttk.Label(
            legend,
            justify="left",
            text=(
                "Brown / white / B+W: block planes\n"
                "P player, K key, D door\n"
                "M1/M2 Demon Mirrors\n"
                "Red circles: enemies\n"
                "Gold diamonds: items\n\n"
                "Left click applies selected tool.\n"
                "Right click erases the cell."
            ),
        ).pack(anchor="w")

    def open_mirror_data(self) -> None:
        MirrorDataDialog(self)

    def open_room_terminator(self) -> None:
        RoomTerminatorDialog(self)

    def current_room(self) -> dict[str, Any]:
        return self.model.room(self.room_index.get())

    def select_room(self, _event: object = None) -> None:
        self.room_index.set(int(self.room_choice.get().split()[-1]) - 1)
        self.selection = None
        self.load_properties()
        self.redraw()

    def load_properties(self) -> None:
        room = self.current_room()
        metadata = room["items"]["metadata"]
        self.property_vars["spawn_lifetime"].set(room["enemies"]["spawn_lifetime"])
        for name in self.property_vars:
            if name != "spawn_lifetime":
                self.property_vars[name].set(metadata[name])

    def apply_properties(self) -> None:
        try:
            changed = self.model.set_room_properties(
                self.room_index.get(),
                self.property_vars["spawn_lifetime"].get(),
                self.property_vars["key_status"].get(),
                self.property_vars["time_decrease_rate"].get(),
                (
                    self.property_vars["mirror_1_schedule"].get(),
                    self.property_vars["mirror_2_schedule"].get(),
                ),
                (
                    self.property_vars["mirror_1_enemy_set"].get(),
                    self.property_vars["mirror_2_enemy_set"].get(),
                ),
            )
            self.set_status("Room properties updated" if changed else "No change")
        except (tk.TclError, LevelEditorError) as exc:
            messagebox.showerror("Invalid room properties", str(exc))
        self.redraw()

    @staticmethod
    def parse_hex(value: str, description: str) -> int:
        return parse_type_choice(value, description)

    def canvas_cell(self, event: tk.Event) -> tuple[int, int]:
        x = min(max(int(self.canvas.canvasx(event.x)) // CELL, 0), ROOM_WIDTH - 1)
        y = min(max(int(self.canvas.canvasy(event.y)) // CELL, 0), ROOM_HEIGHT - 1)
        return x, y

    @staticmethod
    def record_iid(reference: tuple[str, int, int | None]) -> str:
        kind, record_index, position_index = reference
        suffix = "direct" if position_index is None else str(position_index)
        return f"{kind}:{record_index}:{suffix}"

    def refresh_record_table(self) -> None:
        selected = self.selection
        self.record_tree.delete(*self.record_tree.get_children())
        self.record_refs.clear()
        room = self.current_room()
        for index, enemy in enumerate(room["enemies"]["placements"]):
            reference = ("enemy", index, None)
            iid = self.record_iid(reference)
            position = enemy["position"]
            self.record_refs[iid] = reference
            self.record_tree.insert(
                "",
                "end",
                iid=iid,
                values=(
                    "enemy",
                    type_choice(enemy["type"], enemy_type_name(enemy["type"])),
                    position["x"],
                    position["y"],
                    f"placement {index + 1}",
                ),
            )
        for placement in self.model.item_placements(self.room_index.get()):
            reference = (
                "item",
                placement.command_index,
                placement.position_index,
            )
            iid = self.record_iid(reference)
            command = room["items"]["commands"][placement.command_index]
            source = f"command {placement.command_index + 1}"
            if placement.position_index is not None:
                source += f" / {placement.position_index + 1}"
            self.record_refs[iid] = reference
            self.record_tree.insert(
                "",
                "end",
                iid=iid,
                values=(
                    command["kind"],
                    type_choice(
                        placement.item_type,
                        item_type_name(
                            placement.item_type,
                            constellation=command["kind"] == "constellation",
                        ),
                    ),
                    placement.position["x"],
                    placement.position["y"],
                    source,
                ),
            )
        if selected is not None:
            iid = self.record_iid(selected)
            if iid in self.record_refs:
                self.record_tree.selection_set(iid)
                self.record_tree.focus(iid)
                self.record_tree.see(iid)
                self.load_selected_record()
                return
        self.selection = None
        self.selected_record.set("No record selected")
        self.selected_type.set("")

    def select_record_row(self, _event: object = None) -> None:
        rows = self.record_tree.selection()
        if not rows:
            return
        self.selection = self.record_refs.get(rows[0])
        self.load_selected_record()

    def selected_item(self) -> tuple[dict[str, Any], dict[str, int], str]:
        if self.selection is None or self.selection[0] != "item":
            raise LevelEditorError("no item record is selected")
        _, command_index, position_index = self.selection
        commands = self.current_room()["items"]["commands"]
        if not 0 <= command_index < len(commands):
            raise LevelEditorError("selected item command no longer exists")
        command = commands[command_index]
        kind = command["kind"]
        if kind == "repeat":
            positions = command["positions"]
            if position_index is None or not 0 <= position_index < len(positions):
                raise LevelEditorError("selected repeated item no longer exists")
            return command, positions[position_index], kind
        if kind not in {"item", "constellation"} or position_index is not None:
            raise LevelEditorError("selected item record no longer exists")
        return command, command["position"], kind

    def load_selected_record(self) -> None:
        if self.selection is None:
            return
        kind, record_index, position_index = self.selection
        if kind == "enemy":
            placements = self.current_room()["enemies"]["placements"]
            if not 0 <= record_index < len(placements):
                self.selection = None
                return
            record = placements[record_index]
            item_type = record["type"]
            position = record["position"]
            description = f"Enemy placement {record_index + 1}"
            type_values = ENEMY_TYPE_CHOICES
            type_description = enemy_type_name(item_type)
        else:
            command, position, command_kind = self.selected_item()
            item_type = (
                command["opcode"]
                if command_kind == "constellation"
                else command["type"]
            )
            description = f"{command_kind.title()} command {record_index + 1}"
            type_values = {
                "item": DIRECT_ITEM_TYPE_CHOICES,
                "repeat": REPEATED_ITEM_TYPE_CHOICES,
                "constellation": CONSTELLATION_TYPE_CHOICES,
            }[command_kind]
            type_description = item_type_name(
                item_type,
                constellation=command_kind == "constellation",
            )
            if position_index is not None:
                description += (
                    f", position {position_index + 1}/{len(command['positions'])}"
                )
                description += " (type is shared)"
        self.selected_record.set(description)
        self.selected_type_box.configure(values=type_values)
        self.selected_type.set(type_choice(item_type, type_description))
        self.selected_x.set(position["x"])
        self.selected_y.set(position["y"])

    def select_canvas_record(self, x: int, y: int) -> bool:
        matches: list[tuple[str, int, int | None]] = []
        for index, enemy in enumerate(self.current_room()["enemies"]["placements"]):
            if self.model.same_position(enemy["position"], x, y):
                matches.append(("enemy", index, None))
        for placement in self.model.item_placements(self.room_index.get()):
            if self.model.same_position(placement.position, x, y):
                matches.append(
                    ("item", placement.command_index, placement.position_index)
                )
        if not matches:
            self.record_tree.selection_remove(*self.record_tree.selection())
            self.selection = None
            self.selected_record.set("No record selected")
            self.selected_type.set("")
            return False
        selection_index = 0
        if self.selection in matches:
            selection_index = (matches.index(self.selection) + 1) % len(matches)
        self.selection = matches[selection_index]
        iid = self.record_iid(self.selection)
        self.record_tree.selection_set(iid)
        self.record_tree.focus(iid)
        self.record_tree.see(iid)
        self.load_selected_record()
        return True

    def apply_selected_record(self) -> None:
        if self.selection is None:
            self.set_status("Select an enemy or item first")
            return
        try:
            kind, record_index, position_index = self.selection
            item_type = self.parse_hex(self.selected_type.get(), f"{kind} type")
            x = self.selected_x.get()
            y = self.selected_y.get()
            if kind == "enemy":
                changed = self.model.update_enemy(
                    self.room_index.get(), record_index, item_type, x, y
                )
            else:
                changed = self.model.update_item_placement(
                    self.room_index.get(),
                    record_index,
                    position_index,
                    item_type,
                    x,
                    y,
                )
            self.redraw()
            self.set_status("Record updated" if changed else "No change")
        except (tk.TclError, LevelEditorError) as exc:
            messagebox.showerror("Invalid record", str(exc))

    def delete_selected_record(self) -> None:
        if self.selection is None:
            self.set_status("Select an enemy or item first")
            return
        try:
            kind, record_index, position_index = self.selection
            if kind == "enemy":
                self.model.remove_enemy(self.room_index.get(), record_index)
            else:
                self.model.remove_item_placement(
                    self.room_index.get(), record_index, position_index
                )
            self.selection = None
            self.redraw()
            self.set_status("Record deleted")
        except LevelEditorError as exc:
            messagebox.showerror("Cannot delete record", str(exc))

    def canvas_click(self, event: tk.Event) -> None:
        x, y = self.canvas_cell(event)
        mode = self.mode.get()
        try:
            if mode == "brown block":
                changed = self.model.set_block(self.room_index.get(), "brown", x, y)
            elif mode == "white block":
                changed = self.model.set_block(self.room_index.get(), "white", x, y)
            elif mode == "brown + white block":
                changed = self.model.set_block(
                    self.room_index.get(), "brown_white", x, y
                )
            elif mode == "erase cell":
                changed = self.model.erase_cell(self.room_index.get(), x, y)
            elif mode in ANCHOR_MODES:
                changed = self.model.set_anchor(
                    self.room_index.get(), ANCHOR_MODES[mode], x, y
                )
            elif mode == "enemy":
                changed = self.model.add_enemy(
                    self.room_index.get(),
                    self.parse_hex(self.enemy_type.get(), "enemy type"),
                    x,
                    y,
                )
            elif mode == "item":
                changed = self.model.add_item(
                    self.room_index.get(),
                    self.parse_hex(self.item_type.get(), "item type"),
                    x,
                    y,
                )
            else:
                found = self.select_canvas_record(x, y)
                self.set_status(
                    f"Selected record at ({x}, {y})"
                    if found
                    else f"Cell ({x}, {y}) has no enemy or item"
                )
                return
            self.selection = None
            self.set_status(f"Updated ({x}, {y})" if changed else "No change")
            self.redraw()
        except LevelEditorError as exc:
            messagebox.showerror("Invalid edit", str(exc))

    def erase_click(self, event: tk.Event) -> None:
        x, y = self.canvas_cell(event)
        if self.model.erase_cell(self.room_index.get(), x, y):
            self.selection = None
            self.set_status(f"Erased ({x}, {y})")
            self.redraw()

    def undo(self) -> None:
        if self.model.undo():
            self.load_properties()
            self.redraw()
            self.set_status("Undid last edit")
        else:
            self.set_status("Nothing to undo")

    def set_status(self, text: str) -> None:
        suffix = " *" if self.model.dirty else ""
        self.status.set(text + suffix)

    def draw_label(self, position: dict[str, int], text: str, color: str) -> None:
        x, y = position["x"], position["y"]
        if y < 0 or y >= ROOM_HEIGHT:
            return
        self.canvas.create_text(
            x * CELL + CELL // 2,
            y * CELL + CELL // 2,
            text=text,
            fill=color,
            font=("Consolas", 10, "bold"),
        )

    def redraw(self) -> None:
        self.canvas.delete("all")
        room = self.current_room()
        self.preview_renderer.document = self.model.document
        preview = self.preview_renderer.render(self.room_index.get())
        base = tk.PhotoImage(data=preview.ppm(), format="PPM")
        self.preview_image = base.zoom(PIXEL_SCALE, PIXEL_SCALE)
        self.canvas.create_image(0, 0, image=self.preview_image, anchor="nw")
        for x in range(ROOM_WIDTH + 1):
            self.canvas.create_line(
                x * CELL, 0, x * CELL, CANVAS_HEIGHT, fill="#405060"
            )
        for y in range(ROOM_HEIGHT + 1):
            self.canvas.create_line(0, y * CELL, CANVAS_WIDTH, y * CELL, fill="#405060")
        for x, y in sorted(combined_block_positions(room["blocks"])):
            self.canvas.create_text(
                (x + 1) * CELL - 2,
                y * CELL + 2,
                text="B+W",
                fill="#ffcc66",
                font=("Consolas", 7, "bold"),
                anchor="ne",
            )
        metadata = room["items"]["metadata"]
        for field, text, color in (
            ("player_start", "P", "#66ddff"),
            ("key", "K", "#ffff55"),
            ("door", "D", "#66ff77"),
            ("mirror_1", "M1", "#dd88ff"),
            ("mirror_2", "M2", "#bb66ff"),
        ):
            self.draw_label(metadata[field], text, color)
        rendered_enemies = set(preview.rendered_enemy_indices)
        for enemy_index, enemy in enumerate(room["enemies"]["placements"]):
            position = enemy["position"]
            x, y = position["x"], position["y"]
            if y < 0 or y >= ROOM_HEIGHT:
                continue
            if enemy_index not in rendered_enemies:
                self.canvas.create_oval(
                    x * CELL + 5,
                    y * CELL + 5,
                    (x + 1) * CELL - 5,
                    (y + 1) * CELL - 5,
                    fill="#bb3344",
                    outline="#ff99aa",
                )
                self.draw_label(position, f"{enemy['type']:02X}", "white")
            else:
                self.canvas.create_text(
                    x * CELL + 3,
                    y * CELL + 3,
                    text=f"{enemy['type']:02X}",
                    fill="white",
                    font=("Consolas", 8, "bold"),
                    anchor="nw",
                )
        for item in self.model.item_placements(self.room_index.get()):
            x, y = item.position["x"], item.position["y"]
            if y < 0 or y >= ROOM_HEIGHT:
                continue
            self.canvas.create_polygon(
                x * CELL + CELL // 2,
                y * CELL + 4,
                (x + 1) * CELL - 4,
                y * CELL + CELL // 2,
                x * CELL + CELL // 2,
                (y + 1) * CELL - 4,
                x * CELL + 4,
                y * CELL + CELL // 2,
                fill="#d6a900",
                outline="#fff099",
            )
            self.draw_label(item.position, f"{item.item_type:02X}", "#201800")
        self.refresh_record_table()
        self.set_status(
            f"Room {self.room_index.get() + 1:02d}: "
            f"CHR {preview.chr_bank}, "
            f"{len(room['enemies']['placements'])} enemies, "
            f"{len(self.model.item_placements(self.room_index.get()))} items"
        )

    def validate_and_build(self) -> bytes:
        base = self.reference.read_bytes()
        image, _ = build_level_image(self.model.document, base, self.profile)
        validate_rebuilt_document(self.model.document, image, self.profile)
        return image

    def save(self) -> bool:
        try:
            self.validate_and_build()
            save_document(self.document_path, self.model.document)
            self.model.mark_saved()
            self.set_status("Saved and validated")
            return True
        except (OSError, LevelEditorError, RoomDataError, ProjectError) as exc:
            messagebox.showerror("Cannot save level document", str(exc))
            return False

    def build_rom(self) -> bool:
        try:
            image = self.validate_and_build()
            save_document(self.document_path, self.model.document)
            write_if_changed(self.output_path, image)
            self.model.mark_saved()
            self.set_status(f"Built {self.output_path}")
            return True
        except (OSError, LevelEditorError, RoomDataError, ProjectError) as exc:
            messagebox.showerror("Cannot build level ROM", str(exc))
            return False

    def play(self) -> None:
        if not self.build_rom():
            return
        if not self.fceux.is_file():
            messagebox.showerror("FCEUX not found", str(self.fceux))
            return
        if not LEVEL_PLAYTEST_LUA.is_file():
            messagebox.showerror("Level playtest script not found", str(LEVEL_PLAYTEST_LUA))
            return
        try:
            self.stop_playtest(update_status=False)
            environment = level_playtest_environment(
                self.profile, self.room_index.get()
            )
            self.playtest_process = subprocess.Popen(
                level_playtest_command(self.fceux, self.output_path),
                cwd=self.output_path.parent,
                env=environment,
            )
            self.set_status(f"Launching Room {self.room_index.get() + 1:02d}")
        except (OSError, LevelEditorError) as exc:
            messagebox.showerror("Cannot start FCEUX", str(exc))

    def stop_playtest(self, update_status: bool = True) -> None:
        if self.playtest_process is not None and self.playtest_process.poll() is None:
            self.playtest_process.terminate()
            try:
                self.playtest_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.playtest_process.kill()
            if update_status:
                self.set_status("Stopped Level Studio playtest")
        elif update_status:
            self.set_status("No Level Studio playtest is running")
        self.playtest_process = None

    def close(self) -> None:
        if self.model.dirty and not messagebox.askyesno(
            "Unsaved edits", "Discard unsaved level edits?"
        ):
            return
        self.stop_playtest(update_status=False)
        self.destroy()


def load_studio_document(
    profile: dict[str, Any],
    reference: Path,
    document_path: Path,
) -> dict[str, Any]:
    parsed = verify_reference(reference, profile)
    if document_path.is_file():
        document = load_document(document_path)
        if document["source_profile"] != profile["id"]:
            raise LevelEditorError("workspace profile does not match selected profile")
        return document
    document = export_document(parsed, profile)
    save_document(document_path, document)
    return document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="usa")
    parser.add_argument(
        "--profiles",
        type=Path,
        default=ROOT / "config" / "revision_profiles.json",
    )
    parser.add_argument("--private-root", type=Path, default=ROOT)
    parser.add_argument("--base-rom", type=Path)
    parser.add_argument("--document", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--fceux",
        type=Path,
        default=ROOT.parent / "fceux_automation" / "vc" / "x64" / "Release" / "fceux64.exe",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the workspace and codec without opening a window",
    )
    parser.add_argument(
        "--check-playtest",
        action="store_true",
        help="run a bounded FCEUX smoke test for the selected room",
    )
    parser.add_argument(
        "--playtest-room",
        type=int,
        default=1,
        help="one-based room selected by --check-playtest (default: 1)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        profiles = load_profiles(args.profiles)
        profile = get_profile(profiles, args.profile)
        reference = resolve_reference(profile, args.private_root, args.base_rom)
        document_path = args.document or (
            ROOT / "content" / "workspace" / profile["id"] / "levels.json"
        )
        output_path = args.output or (
            ROOT / "build" / "content" / profile["id"] / "solomons_key_levels.nes"
        )
        document = load_studio_document(profile, reference, document_path)
        model = StudioDocument(document)
        base_image = reference.read_bytes()
        parsed_image = parse_ines(base_image)
        rebuilt, usage = build_level_image(document, base_image, profile)
        validate_rebuilt_document(document, rebuilt, profile)
        preview_renderer = LevelPreviewRenderer(
            document,
            parsed_image["chr"],
            parsed_image["prg"],
            profile["level_preview"],
        )
        if args.check:
            previews = [preview_renderer.render(index) for index in range(ROOM_COUNT)]
            combined_blocks = sum(
                len(combined_block_positions(room["blocks"]))
                for room in document["rooms"]
            )
            placed_enemies = sum(
                len(room["enemies"]["placements"])
                for room in document["rooms"]
            )
            native_enemies = sum(
                len(preview.rendered_enemy_indices) for preview in previews
            )
            print(
                f"[OK] Level Studio {profile['id']}: {ROOM_COUNT} rooms, "
                f"{sum(used for used, _ in usage.values())} encoded bytes, "
                f"{sum(len(preview.rgb) for preview in previews)} preview RGB bytes, "
                f"{combined_blocks} combined block cells, "
                f"{native_enemies}/{placed_enemies} native enemy sprites"
            )
            return 0
        if args.check_playtest:
            if not args.fceux.is_file() or not LEVEL_PLAYTEST_LUA.is_file():
                raise LevelEditorError("FCEUX or the level playtest Lua script is missing")
            room_index = args.playtest_room - 1
            result_path = output_path.with_suffix(".playtest.txt")
            result_path.unlink(missing_ok=True)
            write_if_changed(output_path, rebuilt)
            result = run_playtest_smoke(
                args.fceux,
                output_path,
                profile,
                room_index,
                result_path,
            )
            print(f"[OK] Level Studio playtest {profile['id']}: {result}")
            return 0
        studio = LevelStudio(
            model,
            profile,
            reference,
            document_path,
            output_path,
            args.fceux,
            parsed_image["chr"],
            parsed_image["prg"],
        )
        studio.mainloop()
    except (
        OSError,
        KeyError,
        TypeError,
        tk.TclError,
        ProjectError,
        RoomDataError,
        LevelEditorError,
        LevelPreviewError,
    ) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
