from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import level_studio
import level_preview


def room_metadata() -> dict[str, object]:
    return {
        "mirror_2_schedule": 0,
        "mirror_1_schedule": 0,
        "mirror_2_enemy_set": 0,
        "mirror_1_enemy_set": 0,
        "key_status": "normal",
        "time_decrease_rate": 1,
        "door": {"x": 1, "y": 1},
        "key": {"x": 2, "y": 2},
        "player_start": {"x": 3, "y": 3},
        "mirror_1": {"x": 4, "y": 4},
        "mirror_2": {"x": 5, "y": 5},
    }


def studio_document() -> dict[str, object]:
    return {
        "schema_version": 1,
        "game": "solomons-key-nes",
        "source_profile": "usa",
        "source_rom_sha256": "0" * 64,
        "dimensions": {"width": 16, "height": 12},
        "tile_patterns": [],
        "mirror_schedules": [],
        "mirror_enemy_sets": [],
        "rooms": [
            {
                "number": 1,
                "blocks": {
                    "brown": [{"x": 1, "y": 2}],
                    "white": [{"x": 3, "y": 4}],
                },
                "enemies": {
                    "spawn_lifetime": 16,
                    "placements": [
                        {"type": 0x71, "position": {"x": 6, "y": 7}}
                    ],
                },
                "items": {
                    "metadata": room_metadata(),
                    "commands": [
                        {
                            "kind": "item",
                            "type": 0x18,
                            "position": {"x": 8, "y": 9},
                        },
                        {
                            "kind": "repeat",
                            "type": 0x88,
                            "positions": [
                                {"x": 10, "y": 3},
                                {"x": 11, "y": 3},
                            ],
                        },
                        {
                            "kind": "constellation",
                            "opcode": 0xF0,
                            "position": {"x": 12, "y": 5},
                        },
                    ],
                },
            }
        ],
    }


class DirtyStateTests(unittest.TestCase):
    def test_new_model_is_clean(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        self.assertFalse(model.dirty)

    def test_successful_mutation_marks_dirty_and_can_undo(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        self.assertTrue(model.set_block(0, "brown", 2, 3))
        self.assertTrue(model.dirty)
        self.assertEqual(len(model.undo_stack), 1)
        self.assertTrue(model.undo())
        self.assertFalse(model.dirty)

    def test_noop_does_not_create_undo_record(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        self.assertFalse(model.set_block(0, "brown", 1, 2))
        self.assertEqual(model.undo_stack, [])

    def test_mark_saved_resets_dirty_baseline(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        model.add_enemy(0, 0x40, 1, 1)
        model.mark_saved()
        self.assertFalse(model.dirty)

    def test_undo_stack_is_bounded(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        for index in range(120):
            model.set_anchor(0, "key", index % 16, (index // 16) % 12)
        self.assertLessEqual(len(model.undo_stack), 100)


class BlockEditingTests(unittest.TestCase):
    def test_adds_block_in_grid_order(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        model.set_block(0, "brown", 0, 0)
        model.set_block(0, "brown", 15, 11)
        self.assertEqual(
            model.room(0)["blocks"]["brown"],
            [{"x": 0, "y": 0}, {"x": 1, "y": 2}, {"x": 15, "y": 11}],
        )

    def test_block_planes_are_mutually_exclusive(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        model.set_block(0, "white", 1, 2)
        self.assertNotIn({"x": 1, "y": 2}, model.room(0)["blocks"]["brown"])
        self.assertIn({"x": 1, "y": 2}, model.room(0)["blocks"]["white"])

    def test_rejects_unknown_block_kind(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        with self.assertRaisesRegex(level_studio.LevelEditorError, "block kind"):
            model.set_block(0, "glass", 1, 1)


class EntityEditingTests(unittest.TestCase):
    def test_moves_room_anchor(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        model.set_anchor(0, "player_start", 14, 10)
        self.assertEqual(
            model.room(0)["items"]["metadata"]["player_start"],
            {"x": 14, "y": 10},
        )

    def test_rejects_unknown_anchor(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        with self.assertRaisesRegex(level_studio.LevelEditorError, "anchor"):
            model.set_anchor(0, "exit", 1, 1)

    def test_adds_enemy_with_hex_type(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        model.add_enemy(0, 0x42, 4, 5)
        self.assertEqual(
            model.room(0)["enemies"]["placements"][-1],
            {"type": 0x42, "position": {"x": 4, "y": 5}},
        )

    def test_rejects_zero_enemy_type(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        with self.assertRaisesRegex(level_studio.LevelEditorError, "enemy type"):
            model.add_enemy(0, 0, 4, 5)

    def test_inserts_item_before_terminating_command(self) -> None:
        document = studio_document()
        document["rooms"][0]["items"]["commands"] = [
            {"kind": "end", "opcode": 0}
        ]
        model = level_studio.StudioDocument(document)
        model.add_item(0, 0x18, 4, 5)
        commands = model.room(0)["items"]["commands"]
        self.assertEqual(commands[0]["kind"], "item")
        self.assertEqual(commands[1]["kind"], "end")

    def test_inserts_item_before_constellation_terminator(self) -> None:
        document = studio_document()
        model = level_studio.StudioDocument(document)
        model.add_item(0, 0x19, 1, 2)
        commands = model.room(0)["items"]["commands"]
        self.assertEqual(commands[-2]["type"], 0x19)
        self.assertEqual(commands[-1]["kind"], "constellation")

    def test_rejects_reserved_item_opcode_range(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        with self.assertRaisesRegex(level_studio.LevelEditorError, "item type"):
            model.add_item(0, 0xC0, 1, 2)

    def test_flattens_direct_repeat_and_constellation_items(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        placements = model.item_placements(0)
        self.assertEqual(len(placements), 4)
        self.assertEqual(
            [placement.item_type for placement in placements],
            [0x18, 0x88, 0x88, 0xF0],
        )
        self.assertEqual(placements[2].position_index, 1)


class RecordInspectorTests(unittest.TestCase):
    def test_updates_existing_enemy_type_and_position(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        self.assertTrue(model.update_enemy(0, 0, 0x42, 9, 10))
        self.assertEqual(
            model.room(0)["enemies"]["placements"][0],
            {"type": 0x42, "position": {"x": 9, "y": 10}},
        )

    def test_removes_existing_enemy_as_one_undoable_change(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        self.assertTrue(model.remove_enemy(0, 0))
        self.assertEqual(model.room(0)["enemies"]["placements"], [])
        self.assertTrue(model.undo())
        self.assertEqual(len(model.room(0)["enemies"]["placements"]), 1)

    def test_updates_direct_item_without_recreating_command(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        self.assertTrue(model.update_item_placement(0, 0, None, 0x19, 7, 8))
        command = model.room(0)["items"]["commands"][0]
        self.assertEqual(
            command,
            {"kind": "item", "type": 0x19, "position": {"x": 7, "y": 8}},
        )

    def test_repeat_type_change_is_shared_but_position_change_is_local(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        self.assertTrue(model.update_item_placement(0, 1, 1, 0x89, 14, 2))
        command = model.room(0)["items"]["commands"][1]
        self.assertEqual(command["type"], 0x89)
        self.assertEqual(command["positions"][0], {"x": 10, "y": 3})
        self.assertEqual(command["positions"][1], {"x": 14, "y": 2})

    def test_removes_only_selected_repeat_position(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        self.assertTrue(model.remove_item_placement(0, 1, 0))
        repeat = model.room(0)["items"]["commands"][1]
        self.assertEqual(repeat["positions"], [{"x": 11, "y": 3}])

    def test_removes_last_repeat_position_and_its_command(self) -> None:
        document = studio_document()
        document["rooms"][0]["items"]["commands"][1]["positions"] = [
            {"x": 10, "y": 3}
        ]
        model = level_studio.StudioDocument(document)
        self.assertTrue(model.remove_item_placement(0, 1, 0))
        self.assertFalse(
            any(
                command["kind"] == "repeat"
                for command in model.room(0)["items"]["commands"]
            )
        )

    def test_removing_constellation_retains_chr_bank_terminator(self) -> None:
        document = studio_document()
        document["rooms"][0]["items"]["commands"][-1]["opcode"] = 0xFB
        model = level_studio.StudioDocument(document)
        self.assertTrue(model.remove_item_placement(0, 2, None))
        self.assertEqual(
            model.room(0)["items"]["commands"][-1],
            {"kind": "end", "opcode": 0xE8},
        )

    def test_rejects_direct_item_reserved_opcode(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        with self.assertRaisesRegex(level_studio.LevelEditorError, "item type"):
            model.update_item_placement(0, 0, None, 0xC0, 7, 8)


class EraseTests(unittest.TestCase):
    def test_erases_blocks_enemy_and_direct_item_in_cell(self) -> None:
        document = studio_document()
        room = document["rooms"][0]
        room["blocks"]["brown"].append({"x": 6, "y": 7})
        room["items"]["commands"].insert(
            0,
            {"kind": "item", "type": 0x20, "position": {"x": 6, "y": 7}},
        )
        model = level_studio.StudioDocument(document)
        self.assertTrue(model.erase_cell(0, 6, 7))
        self.assertNotIn({"x": 6, "y": 7}, room["blocks"]["brown"])
        self.assertEqual(room["enemies"]["placements"], [])
        self.assertFalse(
            any(
                command.get("position") == {"x": 6, "y": 7}
                for command in room["items"]["commands"]
            )
        )

    def test_erases_one_position_from_repeat(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        model.erase_cell(0, 10, 3)
        repeat = model.room(0)["items"]["commands"][1]
        self.assertEqual(repeat["positions"], [{"x": 11, "y": 3}])

    def test_erases_repeat_command_when_last_position_is_removed(self) -> None:
        document = studio_document()
        repeat = document["rooms"][0]["items"]["commands"][1]
        repeat["positions"] = [{"x": 10, "y": 3}]
        model = level_studio.StudioDocument(document)
        model.erase_cell(0, 10, 3)
        self.assertFalse(
            any(
                command["kind"] == "repeat"
                for command in model.room(0)["items"]["commands"]
            )
        )

    def test_empty_cell_is_noop(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        self.assertFalse(model.erase_cell(0, 15, 0))
        self.assertEqual(model.undo_stack, [])


class PropertyEditingTests(unittest.TestCase):
    def test_updates_profile_sensitive_room_properties(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        model.set_room_properties(0, 13, "hidden", 2, (1, 2), (3, 4))
        room = model.room(0)
        metadata = room["items"]["metadata"]
        self.assertEqual(room["enemies"]["spawn_lifetime"], 13)
        self.assertEqual(metadata["key_status"], "hidden")
        self.assertEqual(metadata["time_decrease_rate"], 2)
        self.assertEqual(metadata["mirror_1_schedule"], 1)
        self.assertEqual(metadata["mirror_2_enemy_set"], 4)

    def test_property_noop_does_not_dirty_document(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        self.assertFalse(
            model.set_room_properties(0, 16, "normal", 1, (0, 0), (0, 0))
        )
        self.assertFalse(model.dirty)

    def test_rejects_schedule_outside_table(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        with self.assertRaisesRegex(level_studio.LevelEditorError, "schedule"):
            model.set_room_properties(0, 16, "normal", 1, (16, 0), (0, 0))

    def test_rejects_enemy_set_outside_table(self) -> None:
        model = level_studio.StudioDocument(studio_document())
        with self.assertRaisesRegex(level_studio.LevelEditorError, "enemy-set"):
            model.set_room_properties(0, 16, "normal", 1, (0, 0), (17, 0))


class StudioLoadingTests(unittest.TestCase):
    def test_loads_existing_matching_workspace(self) -> None:
        document = studio_document()
        profile = {"id": "usa"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "levels.json"
            path.write_text(__import__("json").dumps(document), encoding="utf-8")
            with patch.object(level_studio, "verify_reference", return_value={}):
                loaded = level_studio.load_studio_document(
                    profile, Path(directory) / "base.nes", path
                )
        self.assertEqual(loaded, document)

    def test_rejects_workspace_for_another_profile(self) -> None:
        document = studio_document()
        document["source_profile"] = "europe"
        profile = {"id": "usa"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "levels.json"
            path.write_text(__import__("json").dumps(document), encoding="utf-8")
            with patch.object(level_studio, "verify_reference", return_value={}):
                with self.assertRaisesRegex(level_studio.LevelEditorError, "profile"):
                    level_studio.load_studio_document(
                        profile, Path(directory) / "base.nes", path
                    )

    def test_hex_parser_accepts_dollar_and_0x_prefixes(self) -> None:
        self.assertEqual(level_studio.LevelStudio.parse_hex("$71", "type"), 0x71)
        self.assertEqual(level_studio.LevelStudio.parse_hex("0x88", "type"), 0x88)

    def test_hex_parser_rejects_invalid_value(self) -> None:
        with self.assertRaisesRegex(level_studio.LevelEditorError, "invalid type"):
            level_studio.LevelStudio.parse_hex("enemy", "type")


def preview_patterns() -> list[dict[str, int]]:
    return [
        {
            "index": index,
            "palette": 0,
            "top_left": index,
            "top_right": index,
            "bottom_left": index,
            "bottom_right": index,
        }
        for index in range(58)
    ]


def write_uniform_chr_tile(
    chr_data: bytearray,
    bank: int,
    tile: int,
    pixel: int,
) -> None:
    offset = bank * level_preview.CHR_BANK_SIZE + tile * level_preview.CHR_TILE_SIZE
    low = 0xFF if pixel & 1 else 0
    high = 0xFF if pixel & 2 else 0
    chr_data[offset : offset + 8] = bytes((low,)) * 8
    chr_data[offset + 8 : offset + 16] = bytes((high,)) * 8


def chr_with_uniform_tiles(values: dict[tuple[int, int], int]) -> bytes:
    chr_data = bytearray(level_preview.CHR_BANK_SIZE * 4)
    for (bank, tile), pixel in values.items():
        write_uniform_chr_tile(
            chr_data,
            bank,
            level_preview.BACKGROUND_PATTERN_BASE + tile,
            pixel,
        )
    return bytes(chr_data)


def enemy_preview_data() -> tuple[bytes, bytes, dict[str, str]]:
    prg = bytearray(0x8000)
    pointer_address = 0xD000
    configuration_address = 0xA400
    enemy_type = 0x1C
    pointer_offset = pointer_address - level_preview.PRG_BASE + (enemy_type >> 2) * 2
    prg[pointer_offset : pointer_offset + 2] = bytes((0x00, 0xD2))
    prg[configuration_address - level_preview.PRG_BASE + 1] = 0x0A
    descriptor_offset = 0xD200 - level_preview.PRG_BASE
    prg[descriptor_offset : descriptor_offset + 4] = bytes(
        (0x10, 0x08, 0x00, 0xD3)
    )
    frame_offset = 0xD300 - level_preview.PRG_BASE
    prg[frame_offset : frame_offset + 3] = bytes((0x02, 0x04, 0x00))

    chr_data = bytearray(level_preview.CHR_BANK_SIZE * 4)
    for tile in (0x02, 0x03, 0x04, 0x05):
        write_uniform_chr_tile(chr_data, 1, tile, 1)
    contract = {
        "object_animation_pointer_address": hex(pointer_address),
        "enemy_type_configuration_address": hex(configuration_address),
    }
    return bytes(prg), bytes(chr_data), contract


def preview_room() -> dict[str, object]:
    metadata = room_metadata()
    for field in ("player_start", "key", "door", "mirror_1", "mirror_2"):
        metadata[field] = {"x": 0, "y": -1}
    return {
        "number": 1,
        "blocks": {
            "brown": [{"x": 0, "y": 0}],
            "white": [{"x": 1, "y": 0}],
        },
        "enemies": {"spawn_lifetime": 0, "placements": []},
        "items": {
            "metadata": metadata,
            "commands": [
                {"kind": "item", "type": 8, "position": {"x": 2, "y": 0}},
                {"kind": "end", "opcode": 0xE4},
            ],
        },
    }


class NativePreviewTests(unittest.TestCase):
    def test_decodes_both_chr_bitplanes(self) -> None:
        chr_data = chr_with_uniform_tiles({(1, 4): 3})
        tiles = level_preview.decode_chr_tiles(chr_data)
        tile_index = (
            level_preview.CHR_TILES_PER_BANK
            + level_preview.BACKGROUND_PATTERN_BASE
            + 4
        )
        self.assertEqual(tiles[tile_index][0], (3,) * 8)

    def test_derives_chr_bank_from_the_terminator(self) -> None:
        self.assertEqual(level_preview.room_chr_bank(preview_room()), 1)
        room = preview_room()
        room["items"]["commands"][-1] = {
            "kind": "constellation",
            "opcode": 0xF8,
            "position": {"x": 1, "y": 1},
        }
        self.assertEqual(level_preview.room_chr_bank(room), 2)

    def test_room_map_matches_loader_precedence(self) -> None:
        room = preview_room()
        room["blocks"]["brown"].append({"x": 1, "y": 0})
        values = level_preview.room_map_values(room)
        self.assertEqual(values[0][0], level_preview.ROOM_MAP_BROWN_BLOCK)
        self.assertEqual(values[0][1], level_preview.ROOM_MAP_WHITE_BLOCK)
        self.assertEqual(values[0][2], 8)

    def test_hidden_key_uses_the_decorated_map_class(self) -> None:
        room = preview_room()
        metadata = room["items"]["metadata"]
        metadata["key"] = {"x": 3, "y": 4}
        metadata["key_status"] = "hidden"
        values = level_preview.room_map_values(room)
        self.assertEqual(values[4][3], 0x46)
        self.assertEqual(
            level_preview.classify_pattern(values[4][3]),
            level_preview.ROOM_MAP_EMPTY,
        )

    def test_special_room_palette_branch_is_reproduced(self) -> None:
        palette = level_preview.room_palette(48)
        self.assertEqual(tuple(palette[index] for index in (1, 5, 9, 13)), (0,) * 4)
        self.assertEqual(palette[10], 0x16)

    def test_constellation_selects_its_six_native_records(self) -> None:
        command = {
            "kind": "constellation",
            "opcode": 0xF5,
            "position": {"x": 4, "y": 3},
        }
        first = level_preview.constellation_pattern(command, 4, 3)
        last = level_preview.constellation_pattern(command, 6, 4)
        self.assertIsNotNone(first)
        self.assertIsNotNone(last)
        self.assertEqual(first.palette, level_preview.CONSTELLATION_PALETTES[5])
        self.assertEqual(first.tiles[0] & 3, 0)
        self.assertIsNone(level_preview.constellation_pattern(command, 7, 4))

    def test_renders_native_patterns_from_the_selected_chr_bank(self) -> None:
        document = {"tile_patterns": preview_patterns(), "rooms": [preview_room()]}
        chr_data = chr_with_uniform_tiles(
            {(1, 0): 1, (1, 3): 2, (1, 8): 3, (1, 16): 0}
        )
        preview = level_preview.LevelPreviewRenderer(document, chr_data).render(0)
        self.assertEqual((preview.width, preview.height), (256, 192))
        self.assertEqual(preview.chr_bank, 1)

        def pixel(x: int, y: int) -> tuple[int, int, int]:
            offset = (y * preview.width + x) * 3
            return tuple(preview.rgb[offset : offset + 3])

        palette = level_preview.room_palette(0)
        self.assertEqual(pixel(0, 0), level_preview.NES_RGB[palette[1]])
        self.assertEqual(pixel(16, 0), level_preview.NES_RGB[palette[2]])
        self.assertEqual(pixel(32, 0), level_preview.NES_RGB[palette[3]])

    def test_projects_packed_flags_to_both_oam_attributes(self) -> None:
        self.assertEqual(level_preview.sprite_attributes(0xF0), (0xC3, 0x00))
        self.assertEqual(level_preview.sprite_attributes(0x0F), (0x00, 0xC3))

    def test_enemy_decoder_follows_type_action_and_frame_pointers(self) -> None:
        prg, _, contract = enemy_preview_data()
        decoder = level_preview.EnemySpriteDecoder(prg, contract)
        self.assertEqual(decoder.initial_action(0x1C), 0)
        self.assertEqual(decoder.initial_frame_offset(0x10), 0)
        self.assertEqual(
            decoder.frame(0x1C),
            level_preview.SpriteFrame(0x02, 0x04, 0x00),
        )

    def test_renders_enemy_as_two_native_8_by_16_sprites(self) -> None:
        prg, chr_data, contract = enemy_preview_data()
        room = preview_room()
        room["enemies"]["placements"] = [
            {"type": 0x1C, "position": {"x": 0, "y": 0}}
        ]
        document = {"tile_patterns": preview_patterns(), "rooms": [room]}
        preview = level_preview.LevelPreviewRenderer(
            document, chr_data, prg, contract
        ).render(0)
        sprite_color = bytes(
            level_preview.NES_RGB[level_preview.ROOM_SPRITE_PALETTE[1]]
        )
        self.assertEqual(preview.rgb[0:3], sprite_color)
        self.assertEqual(preview.rgb[8 * 3 : 9 * 3], sprite_color)
        self.assertEqual(preview.rendered_enemy_indices, (0,))

    def test_unknown_enemy_type_remains_available_for_editor_fallback(self) -> None:
        prg, chr_data, contract = enemy_preview_data()
        room = preview_room()
        room["enemies"]["placements"] = [
            {"type": 0xFF, "position": {"x": 0, "y": 0}}
        ]
        document = {"tile_patterns": preview_patterns(), "rooms": [room]}
        preview = level_preview.LevelPreviewRenderer(
            document, chr_data, prg, contract
        ).render(0)
        self.assertEqual(preview.rendered_enemy_indices, ())

    def test_rejects_missing_chr_terminator(self) -> None:
        room = preview_room()
        room["items"]["commands"] = []
        with self.assertRaisesRegex(level_preview.LevelPreviewError, "terminator"):
            level_preview.room_chr_bank(room)


class PointPlaytestTests(unittest.TestCase):
    @staticmethod
    def profile() -> dict[str, object]:
        return {
            "id": "europe",
            "playtest": {
                "room_load_address": "0x9030",
                "gameplay_address": "0xa000",
                "current_room_address": "0x0428",
                "start_frame": 300,
                "ready_frames": 1000,
            },
        }

    def test_environment_selects_profile_addresses_and_zero_based_room(self) -> None:
        environment = level_studio.level_playtest_environment(self.profile(), 29)
        self.assertEqual(environment["SOLOMON_LEVEL_ROOM"], "29")
        self.assertEqual(environment["SOLOMON_LEVEL_ROOM_LOAD_ADDRESS"], "36912")
        self.assertEqual(environment["SOLOMON_LEVEL_GAMEPLAY_ADDRESS"], "40960")
        self.assertEqual(environment["SOLOMON_LEVEL_CURRENT_ROOM_ADDRESS"], "1064")
        self.assertEqual(environment["SOLOMON_LEVEL_EXIT"], "0")

    def test_smoke_environment_requests_result_and_exit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.txt"
            environment = level_studio.level_playtest_environment(
                self.profile(), 0, result_path=result, exit_after_ready=True
            )
        self.assertEqual(environment["SOLOMON_LEVEL_RESULT"], result.resolve().as_posix())
        self.assertEqual(environment["SOLOMON_LEVEL_EXIT"], "1")

    def test_command_adds_bounded_smoke_options_only_when_requested(self) -> None:
        interactive = level_studio.level_playtest_command(
            Path("fceux.exe"), Path("room.nes")
        )
        smoke = level_studio.level_playtest_command(
            Path("fceux.exe"), Path("room.nes"), 1000
        )
        self.assertNotIn("-max-frames", interactive)
        self.assertIn("-max-frames", smoke)
        self.assertEqual(smoke[-1], str(Path("room.nes").resolve()))

    def test_accepts_ready_result_for_selected_room(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.txt"
            line = (
                "status=ready requested_room=1d current_room=1d "
                "room_loads=1 gameplay_hits=1 frame=610 pc=a000"
            )
            result.write_text(line + "\ntrace=\n", encoding="utf-8")
            self.assertEqual(level_studio.validate_playtest_result(result, 29), line)

    def test_rejects_result_for_another_room(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = Path(directory) / "result.txt"
            result.write_text(
                "status=ready requested_room=00 current_room=00\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(level_studio.LevelEditorError, "failed"):
                level_studio.validate_playtest_result(result, 29)


if __name__ == "__main__":
    unittest.main()
