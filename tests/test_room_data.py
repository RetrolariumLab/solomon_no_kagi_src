from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import room_data
import level_editor


class RoomDataTests(unittest.TestCase):
    def test_europe_layout_moves_room_data_earlier(self) -> None:
        usa = room_data.USA_ROOM_DATA_LAYOUT
        japan = room_data.JAPAN_ROOM_DATA_LAYOUT
        europe = room_data.EUROPE_ROOM_DATA_LAYOUT
        fields = (
            "room_tile_pattern_data",
            "mirror_schedule_table",
            "mirror_enemy_set_table",
            "mirror_schedule_data",
            "enemy_pointer_table",
            "block_data",
            "item_pointer_table",
            "item_data_end",
            "audio_engine",
        )
        for field in fields:
            self.assertEqual(getattr(japan, field), getattr(usa, field))
            self.assertEqual(getattr(europe, field), getattr(usa, field) - 0x80)

    def test_block_decoder_uses_selected_regional_layout(self) -> None:
        prg = bytearray(32_768)
        data = bytes([0x80]) + bytes(room_data.BLOCK_BYTES_PER_ROOM - 1)
        start = room_data.EUROPE_ROOM_DATA_LAYOUT.block_data
        prg[start : start + len(data)] = data
        europe = room_data.decode_blocks(
            bytes(prg), 0, room_data.EUROPE_ROOM_DATA_LAYOUT
        )
        usa = room_data.decode_blocks(bytes(prg), 0)
        self.assertEqual(europe["brown"], [{"x": 0, "y": 0}])
        self.assertEqual(usa["brown"], [])

    def test_position_encoding(self) -> None:
        self.assertEqual(room_data.position(0xB5), {"x": 5, "y": 10, "raw": 0xB5})
        self.assertEqual(room_data.position(0x05)["y"], -1)

    def test_spawn_lifetime_rotation(self) -> None:
        self.assertEqual(room_data.rotate_left_3(0x20), 1)
        self.assertEqual(room_data.rotate_left_3(0xFF), 0xFF)

    def test_level_codec_rejects_more_enemies_than_the_runtime_pool(self) -> None:
        placements = [
            {"type": 0x71, "position": {"x": index % 16, "y": index % 12}}
            for index in range(level_editor.ROOM_ENEMY_SLOT_COUNT + 1)
        ]
        with self.assertRaisesRegex(level_editor.LevelEditorError, "17 slots"):
            level_editor.encode_room_enemies(
                {"spawn_lifetime": 1, "placements": placements}
            )

    def test_groups_rooms_by_chr_bank(self) -> None:
        self.assertEqual(
            room_data.group_room_chr_banks((0, 2, 0, 3)),
            {0: [1, 3], 1: [], 2: [2], 3: [4]},
        )

    def test_rejects_invalid_room_chr_bank(self) -> None:
        with self.assertRaisesRegex(room_data.RoomDataError, "invalid CHR bank 4"):
            room_data.group_room_chr_banks((0, 4))

    def test_room_tile_patterns_split_palette_from_top_left_tile(self) -> None:
        prg = bytearray(32_768)
        pattern_bytes = bytes((0x91, 0x91, 0x92, 0x93)) * 58
        start = room_data.ROOM_TILE_PATTERN_DATA
        prg[start : start + len(pattern_bytes)] = pattern_bytes
        patterns = room_data.decode_room_tile_patterns(bytes(prg))
        self.assertEqual(
            patterns[0],
            {
                "index": 0,
                "palette": 1,
                "top_left": 0x90,
                "top_right": 0x91,
                "bottom_left": 0x92,
                "bottom_right": 0x93,
            },
        )
        self.assertEqual(room_data.encode_room_tile_patterns(patterns), pattern_bytes)

    def test_room_tile_pattern_encoder_rejects_palette_overlap(self) -> None:
        patterns = [
            {
                "index": index,
                "palette": 0,
                "top_left": 0,
                "top_right": 0,
                "bottom_left": 0,
                "bottom_right": 0,
            }
            for index in range(room_data.ROOM_TILE_PATTERN_COUNT)
        ]
        patterns[0]["top_left"] = 1
        with self.assertRaisesRegex(ValueError, "overlaps palette"):
            room_data.encode_room_tile_patterns(patterns)

    def test_bitplane_is_row_major_and_msb_first(self) -> None:
        data = bytes([0x80, 0x01]) + bytes(room_data.BITPLANE_SIZE - 2)
        rows = room_data.decode_bitplane(data)
        self.assertTrue(rows[0][0])
        self.assertTrue(rows[0][15])
        self.assertEqual(sum(map(sum, rows)), 2)
        self.assertEqual(room_data.encode_bitplane(room_data.true_positions(rows)), data)

        prg = bytearray(32_768)
        prg[room_data.BLOCK_DATA : room_data.BLOCK_DATA + len(data)] = data
        source = room_data.emit_block_source(bytes(prg))
        self.assertIn("RoomBlockData:", source)
        self.assertIn(".byte $80, $01", source)
        self.assertIn("RoomBlockDataRoom53:", source)

    def test_enemy_stream_round_trip(self) -> None:
        prg = bytearray(32_768)
        offset = 0x1000
        cpu_address = offset + 0x8000
        prg[room_data.ENEMY_POINTER_TABLE] = cpu_address & 0xFF
        prg[room_data.ENEMY_POINTER_TABLE + room_data.ROOM_COUNT] = cpu_address >> 8
        encoded = bytes((0x20, 0x1C, 0xB5, 0x27, 0x31, 0x00))
        prg[offset : offset + len(encoded)] = encoded
        decoded = room_data.decode_enemies(bytes(prg), 0)
        self.assertEqual(room_data.encode_enemies(decoded), encoded)

        low = bytes((cpu_address & 0xFF,)) * room_data.ROOM_COUNT
        high = bytes((cpu_address >> 8,)) * room_data.ROOM_COUNT
        table = room_data.ENEMY_POINTER_TABLE
        prg[table : table + room_data.ROOM_COUNT] = low
        prg[table + room_data.ROOM_COUNT : table + room_data.ROOM_COUNT * 2] = high
        source = room_data.emit_enemy_source(bytes(prg))
        self.assertIn("RoomEnemyStream01:", source)
        self.assertIn("RoomEnemyRecord $1C, $B5", source)
        self.assertIn("RoomEnemyStream53:", source)

    def test_rejects_enemy_outside_configuration_table(self) -> None:
        for enemy_type in (0x17, 0x84):
            with self.subTest(enemy_type=enemy_type):
                with self.assertRaisesRegex(room_data.RoomDataError, "enemy type"):
                    room_data.encode_enemies(
                        {
                            "spawn_lifetime_encoded": 0,
                            "enemies": [
                                {
                                    "type": enemy_type,
                                    "position": {"x": 0, "y": 0},
                                }
                            ],
                        }
                    )

    def test_item_stream_round_trip_preserves_rle_commands(self) -> None:
        prg = bytearray(32_768)
        offset = 0x1100
        cpu_address = offset + 0x8000
        prg[room_data.ITEM_POINTER_TABLE] = cpu_address & 0xFF
        prg[room_data.ITEM_POINTER_TABLE + room_data.ROOM_COUNT] = cpu_address >> 8
        encoded = bytes(
            (
                1, 2, 3, 4, 0x8F, 0x21, 0x32, 0x43, 0x54, 0x65,
                0xC1, 0x22, 0x76, 0x87,
                0xF0, 0x98,
            )
        )
        prg[offset : offset + len(encoded)] = encoded
        decoded = room_data.decode_items(bytes(prg), 0)
        self.assertEqual(decoded["commands"][0]["kind"], "repeat")
        self.assertEqual(room_data.encode_items(decoded), encoded)

        low = bytes((cpu_address & 0xFF,)) * room_data.ROOM_COUNT
        high = bytes((cpu_address >> 8,)) * room_data.ROOM_COUNT
        table = room_data.ITEM_POINTER_TABLE
        prg[table : table + room_data.ROOM_COUNT] = low
        prg[table + room_data.ROOM_COUNT : table + room_data.ROOM_COUNT * 2] = high
        source = room_data.emit_item_source(bytes(prg))
        self.assertIn("RoomItemStream01:", source)
        self.assertIn("BeginRoomItemRepeat $22, 2", source)
        self.assertIn("RoomConstellationItem $F0, $98", source)
        self.assertIn("RoomItemStream53:", source)

    def test_split_pointer_round_trip(self) -> None:
        offsets = [0x0100, 0x1234, 0x7FFF]
        encoded = room_data.encode_split_pointers(offsets)
        self.assertEqual(encoded, bytes((0x00, 0x34, 0xFF, 0x81, 0x92, 0xFF)))

    def test_mirror_schedule_round_trip(self) -> None:
        prg = bytearray(32_768)
        offset = 0x1000
        cpu_address = offset + 0x8000
        table = room_data.MIRROR_SCHEDULE_TABLE
        count = room_data.MIRROR_SCHEDULE_COUNT
        prg[table : table + count] = bytes((cpu_address & 0xFF,)) * count
        prg[table + count : table + count * 2] = bytes((cpu_address >> 8,)) * count
        encoded = bytes((0x84, 0x21, 0x08, 0x42, 0x08, 0x42, 0x10, 0x84))
        prg[offset : offset + len(encoded)] = encoded
        schedule = room_data.decode_mirror_schedules(bytes(prg))[0]
        self.assertEqual(schedule["initial_phase"], [0x84, 0x21, 0x08, 0x42])
        self.assertEqual(room_data.encode_mirror_schedule(schedule), encoded)

    def test_mirror_enemy_set_round_trip(self) -> None:
        prg = bytearray(32_768)
        offset = 0x1000
        cpu_address = offset + 0x8000
        table = room_data.MIRROR_ENEMY_SET_TABLE
        count = room_data.MIRROR_ENEMY_SET_COUNT
        prg[table : table + count] = bytes((cpu_address & 0xFF,)) * count
        prg[table + count : table + count * 2] = bytes((cpu_address >> 8,)) * count
        encoded = bytes((0x50, 0x51, 0x5C, 0x90))
        prg[offset : offset + len(encoded)] = encoded
        enemy_set = room_data.decode_mirror_enemy_sets(bytes(prg))[0]
        self.assertEqual(enemy_set["enemy_types"], [0x50, 0x51, 0x5C])
        self.assertEqual(enemy_set["loop_offset"], 0)
        self.assertEqual(room_data.encode_mirror_enemy_set(enemy_set), encoded)

    def test_rejects_empty_or_out_of_range_mirror_enemy_set(self) -> None:
        for enemy_types in ([], [0x17], [0x84]):
            with self.subTest(enemy_types=enemy_types):
                with self.assertRaisesRegex(room_data.RoomDataError, "enemy types"):
                    room_data.encode_mirror_enemy_set(
                        {"enemy_types": enemy_types, "loop_offset": 0}
                    )

    def test_rejects_mirror_loop_outside_its_payload(self) -> None:
        with self.assertRaisesRegex(room_data.RoomDataError, "loop offset"):
            room_data.encode_mirror_enemy_set(
                {"enemy_types": [0x50, 0x51], "loop_offset": 2}
            )

    def test_extracts_prg_from_ines(self) -> None:
        header = b"NES\x1a" + bytes((2, 4, 0x30, 0)) + bytes(8)
        prg = bytes([0xA5]) * 32_768
        image = header + prg + bytes(32_768)
        self.assertEqual(room_data.extract_prg(image), prg)

    def test_rejects_bad_bare_image(self) -> None:
        with self.assertRaisesRegex(room_data.RoomDataError, "expected"):
            room_data.extract_prg(b"not a ROM")


if __name__ == "__main__":
    unittest.main()
