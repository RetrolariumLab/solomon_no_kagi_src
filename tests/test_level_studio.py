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


if __name__ == "__main__":
    unittest.main()
