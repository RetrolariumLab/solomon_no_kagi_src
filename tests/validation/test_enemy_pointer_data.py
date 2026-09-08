from __future__ import annotations

from pathlib import Path
import unittest

from scripts.validation.enemy_pointer_data import (
    decode_split_pointer_table,
    load_manifest,
    validate_manifest_profile,
    validate_report,
)


class EnemyPointerDataTests(unittest.TestCase):
    def test_committed_profiles_record_one_byte_shifted_ram_pools(self) -> None:
        root = Path(__file__).resolve().parents[2]
        usa = load_manifest(root / "config" / "validation" / "enemy_record_pointers.json")
        europe = load_manifest(
            root / "config" / "validation" / "enemy_record_pointers_europe.json"
        )
        validate_manifest_profile(usa, "usa")
        validate_manifest_profile(europe, "europe")
        self.assertEqual(
            [table["low_address"] for table in usa["tables"]],
            [table["low_address"] for table in europe["tables"]],
        )
        for usa_table, europe_table in zip(usa["tables"], europe["tables"]):
            self.assertEqual(
                int(europe_table["base_address"], 0),
                int(usa_table["base_address"], 0) + 1,
            )

    def test_decodes_split_pointer_table(self) -> None:
        prg = bytearray(32_768)
        prg[0x3446:0x3449] = bytes((0xF7, 0xFF, 0x07))
        prg[0x3457:0x345A] = bytes((0x04, 0x04, 0x05))
        self.assertEqual(
            decode_split_pointer_table(bytes(prg), 0xB446, 0xB457, 3),
            [0x04F7, 0x04FF, 0x0507],
        )

    def test_rejects_truncated_table(self) -> None:
        with self.assertRaisesRegex(ValueError, "truncated"):
            decode_split_pointer_table(bytes(32_768), 0xFFFF, 0xB457, 2)

    def test_audit_detects_stride_mismatch(self) -> None:
        report = {"tables": [{"id": "enemy_ai", "pointers": [0x04F7, 0x0500]}]}
        manifest = {
            "tables": [
                {
                    "id": "enemy_ai",
                    "base_address": "0x04f7",
                    "stride": 8,
                    "count": 2,
                }
            ]
        }
        errors = validate_report(report, manifest)
        self.assertEqual(len(errors), 1)
        self.assertIn("enemy_ai pointers differ", errors[0])


if __name__ == "__main__":
    unittest.main()
