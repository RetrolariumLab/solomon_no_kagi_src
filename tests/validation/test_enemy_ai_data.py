from __future__ import annotations

import unittest

from scripts.validation.enemy_ai_data import decode_handler_table, validate_report


class EnemyAiDataTests(unittest.TestCase):
    def test_decodes_little_endian_handlers(self) -> None:
        prg = bytearray(32_768)
        prg[0x246E:0x2472] = bytes((0xB3, 0xA4, 0xDD, 0xA5))
        self.assertEqual(decode_handler_table(bytes(prg), 0xA46E, 2), [0xA4B3, 0xA5DD])

    def test_rejects_truncated_table(self) -> None:
        with self.assertRaisesRegex(ValueError, "truncated"):
            decode_handler_table(bytes(32_768), 0xFFFF, 1)

    def test_audit_detects_changed_handler(self) -> None:
        report = {"handlers": [0xA4B3, 0xA5DE]}
        manifest = {"handlers": ["0xa4b3", "0xa5dd"]}
        errors = validate_report(report, manifest)
        self.assertEqual(len(errors), 1)
        self.assertIn("handler 1 differs", errors[0])


if __name__ == "__main__":
    unittest.main()
