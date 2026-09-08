from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]

from scripts.validation import debug_symbols


def write_json(path: Path, document: dict[str, object]) -> None:
    path.write_text(json.dumps(document), encoding="utf-8")


class RecordTests(unittest.TestCase):
    def test_parses_quoted_debug_fields(self) -> None:
        kind, fields = debug_symbols.parse_record(
            'file\tid=3,name="src/game/flow/runtime.asm",size=10'
        )
        self.assertEqual(kind, "file")
        self.assertEqual(fields["id"], "3")
        self.assertEqual(fields["name"], "src/game/flow/runtime.asm")

    def test_loads_code_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "game.lbl"
            path.write_text("al 008000 .NMI\nal 00A000 .MainGameplayThread\n")
            self.assertEqual(
                debug_symbols.load_vice_labels(path),
                {"NMI": 0x8000, "MainGameplayThread": 0xA000},
            )

    def test_rejects_unknown_label_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "game.lbl"
            path.write_text("not a label\n")
            with self.assertRaisesRegex(debug_symbols.SymbolError, "unsupported"):
                debug_symbols.load_vice_labels(path)


class ConfigTests(unittest.TestCase):
    def test_profile_address_overrides_the_preservation_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "breakpoints.json"
            write_json(
                path,
                {
                    "schema_version": 1,
                    "breakpoints": [
                        {
                            "address": "0x8000",
                            "profile_addresses": {"europe": "0x8010"},
                            "symbol": "NMI",
                            "name": "NMI",
                            "kind": "execute",
                            "confidence": "confirmed",
                        }
                    ],
                },
            )
            resolved = debug_symbols.resolve_config(
                path,
                "breakpoints",
                {"NMI": 0x8010},
                {"NMI": 0x8010},
                "europe",
            )
            self.assertEqual(resolved[0]["address"], 0x8010)
            with self.assertRaisesRegex(debug_symbols.SymbolError, "stale address"):
                debug_symbols.resolve_config(
                    path, "breakpoints", {"NMI": 0x8010}, {"NMI": 0x8010}
                )

    def test_rejects_malformed_profile_address_map(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "watches.json"
            write_json(
                path,
                {
                    "schema_version": 1,
                    "watches": [
                        {
                            "address": "0x0008",
                            "profile_addresses": ["0x0009"],
                            "symbol": "Pointer",
                            "name": "Pointer",
                            "size": 2,
                            "confidence": "confirmed",
                        }
                    ],
                },
            )
            with self.assertRaisesRegex(debug_symbols.SymbolError, "profile_addresses"):
                debug_symbols.resolve_config(
                    path, "watches", {"Pointer": 0x0008}, {}
                )

    def test_resolves_breakpoint_against_both_symbol_sets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "breakpoints.json"
            write_json(
                path,
                {
                    "schema_version": 1,
                    "breakpoints": [
                        {
                            "address": "0x8000",
                            "symbol": "NMI",
                            "name": "NMI",
                            "kind": "execute",
                            "confidence": "confirmed",
                        }
                    ],
                },
            )
            resolved = debug_symbols.resolve_config(
                path, "breakpoints", {"NMI": 0x8000}, {"NMI": 0x8000}
            )
            self.assertEqual(resolved[0]["address"], 0x8000)
            self.assertEqual(resolved[0]["address_hex"], "$8000")

    def test_rejects_stale_config_address(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "breakpoints.json"
            write_json(
                path,
                {
                    "schema_version": 1,
                    "breakpoints": [
                        {
                            "address": "0x8001",
                            "symbol": "NMI",
                            "name": "NMI",
                            "kind": "execute",
                            "confidence": "confirmed",
                        }
                    ],
                },
            )
            with self.assertRaisesRegex(debug_symbols.SymbolError, "stale address"):
                debug_symbols.resolve_config(
                    path, "breakpoints", {"NMI": 0x8000}, {"NMI": 0x8000}
                )

    def test_accepts_distinct_overlapping_watch_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "watches.json"
            write_json(
                path,
                {
                    "schema_version": 1,
                    "watches": [
                        {
                            "address": "0x04f7",
                            "size": 136,
                            "symbol": "EnemyAiState",
                            "name": "Enemy AI state",
                            "confidence": "tentative",
                        },
                        {
                            "address": "0x04f7",
                            "size": 25,
                            "symbol": "EnemyAiState",
                            "name": "Transition state",
                            "confidence": "confirmed",
                        },
                    ],
                },
            )
            resolved = debug_symbols.resolve_config(
                path, "watches", {"EnemyAiState": 0x04F7}, {}
            )
            self.assertEqual([entry["size"] for entry in resolved], [136, 25])

    def test_rejects_watch_outside_internal_ram(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "watches.json"
            write_json(
                path,
                {
                    "schema_version": 1,
                    "watches": [
                        {
                            "address": "0x07ff",
                            "size": 2,
                            "symbol": "LastRamByte",
                            "name": "Bad range",
                            "confidence": "tentative",
                        }
                    ],
                },
            )
            with self.assertRaisesRegex(debug_symbols.SymbolError, "outside internal RAM"):
                debug_symbols.resolve_config(
                    path, "watches", {"LastRamByte": 0x07FF}, {}
                )


class ExportTests(unittest.TestCase):
    def test_fceux_export_chooses_one_name_per_address(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            rom_path, ram_path = debug_symbols.write_fceux_labels(
                output,
                "game.nes",
                {"LongResetName": 0x8000, "Reset": 0x8000},
                {"LongRamAlias": 0x12, "Stack": 0x12},
                {"LongRamAlias", "Stack"},
            )
            self.assertEqual(rom_path.read_text(), "$8000#Reset#\n")
            self.assertEqual(ram_path.read_text(), "$0012#Stack#\n")

    def test_debug_loader_includes_equates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "game.dbg"
            path.write_text(
                'file\tid=0,name="src/main.asm"\n'
                'sym\tid=0,name="ThreadIndex",val=0x302,type=equ\n'
            )
            counts, symbols, files = debug_symbols.load_debug_file(path)
            self.assertEqual(counts["sym"], 1)
            self.assertEqual(symbols["ThreadIndex"], 0x0302)
            self.assertEqual(files[0], "src/main.asm")


if __name__ == "__main__":
    unittest.main()
