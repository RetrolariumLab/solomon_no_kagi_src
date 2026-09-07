from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from scripts.item_handler_data import (
    collect_report,
    load_manifest,
    validate_manifest_profile,
    validate_report,
)


class ItemHandlerDataTests(unittest.TestCase):
    def test_committed_profiles_preserve_selectors_at_relocated_handlers(self) -> None:
        root = Path(__file__).resolve().parent.parent
        usa = load_manifest(root / "config" / "item_handlers.json")
        europe = load_manifest(root / "config" / "item_handlers_europe.json")
        validate_manifest_profile(usa, "usa")
        validate_manifest_profile(europe, "europe")
        self.assertEqual(
            [item["name"] for item in usa["handlers"]],
            [item["name"] for item in europe["handlers"]],
        )
        self.assertNotEqual(usa["table_address"], europe["table_address"])
        self.assertNotEqual(usa["table_sha1"], europe["table_sha1"])

    def manifest(self) -> dict[str, object]:
        encoded = bytes((0x63, 0xC5, 0x87, 0xC5))
        return {
            "table_address": "0xc4d3",
            "first_map_tile": "0x06",
            "table_sha1": hashlib.sha1(encoded).hexdigest(),
            "handlers": [
                {"name": "CollectRoomKey", "address": "0xc563"},
                {"name": "EnterRoomDoor", "address": "0xc587"},
            ],
        }

    def test_decodes_selector_tile_name_and_address(self) -> None:
        prg = bytearray(32_768)
        prg[0x44D3:0x44D7] = bytes((0x63, 0xC5, 0x87, 0xC5))
        report = collect_report(bytes(prg), self.manifest())
        self.assertEqual(report["handler_count"], 2)
        self.assertEqual(report["unique_handler_count"], 2)
        self.assertEqual(
            report["entries"],
            [
                {"selector": 0, "map_tile": 6, "name": "CollectRoomKey", "address": 0xC563},
                {"selector": 1, "map_tile": 7, "name": "EnterRoomDoor", "address": 0xC587},
            ],
        )
        self.assertEqual(validate_report(report, self.manifest()), [])

    def test_audit_detects_handler_and_hash_changes(self) -> None:
        manifest = self.manifest()
        report = {
            "table_sha1": "changed",
            "entries": [
                {"address": 0xC563},
                {"address": 0xC588},
            ],
        }
        errors = validate_report(report, manifest)
        self.assertTrue(any("SHA-1 differs" in error for error in errors))
        self.assertTrue(any("handler 1" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
