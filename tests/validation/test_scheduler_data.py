from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validation.scheduler_data import (
    INITIAL_STACK_POINTERS,
    THREAD_ENTRY_TABLE_BASES,
    decode_thread_code,
    discover_start_calls,
    load_manifest,
    prg_offset,
    validate_context_roles,
    validate_manifest_profile,
    validate_report,
)


class SchedulerDataTests(unittest.TestCase):
    def test_committed_profiles_preserve_codes_at_native_table_addresses(self) -> None:
        root = Path(__file__).resolve().parents[2]
        usa = load_manifest(root / "config" / "validation" / "scheduler_entries.json")
        europe = load_manifest(root / "config" / "validation" / "scheduler_entries_europe.json")
        validate_manifest_profile(usa, "usa")
        validate_manifest_profile(europe, "europe")
        self.assertEqual(
            [entry["code"] for entry in usa["static_entries"]],
            [entry["code"] for entry in europe["static_entries"]],
        )
        self.assertEqual(
            [entry["code"] for entry in usa["reviewed_dynamic_entries"]],
            [entry["code"] for entry in europe["reviewed_dynamic_entries"]],
        )
        self.assertEqual(europe["initial_stack_pointer_address"], "0x8e10")
        self.assertEqual(europe["thread_entry_table_bases_address"], "0x8e18")

    def test_decodes_packed_thread_code(self) -> None:
        prg = bytearray(32_768)
        base = 0x9000
        prg[prg_offset(THREAD_ENTRY_TABLE_BASES + 2) : prg_offset(THREAD_ENTRY_TABLE_BASES + 2) + 2] = bytes((0x00, 0x90))
        prg[prg_offset(base + 6) : prg_offset(base + 8)] = bytes((0x34, 0xA2))
        self.assertEqual(
            decode_thread_code(bytes(prg), 0x13),
            {
                "code": 0x13,
                "context": 1,
                "selector": 3,
                "base": 0x9000,
                "pointer_address": 0x9006,
                "return_address": 0xA234,
                "entry": 0xA235,
            },
        )

    def test_discovers_immediate_and_dynamic_calls(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "src").mkdir()
        (root / "src" / "main.asm").write_text(
            "    LDA #$17\n"
            "    JSR StartThread\n"
            "    TXA\n"
            "    JSR StartThread\n"
            "    JMP StartThread\n",
            encoding="utf-8",
        )
        static, dynamic = discover_start_calls(root)
        self.assertEqual([call["code"] for call in static], [0x17])
        self.assertEqual(len(dynamic), 2)

    def test_discovers_named_numeric_thread_code(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "src").mkdir()
        (root / "src" / "main.asm").write_text(
            "RoomClearThreadCode = $14\n"
            "    LDA #RoomClearThreadCode\n"
            "    JSR StartThread\n",
            encoding="utf-8",
        )
        static, dynamic = discover_start_calls(root)
        self.assertEqual([call["code"] for call in static], [0x14])
        self.assertEqual(dynamic, [])

    def test_unresolved_named_thread_code_remains_dynamic(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "src").mkdir()
        (root / "src" / "main.asm").write_text(
            "    LDA #RuntimeThreadCode\n    JSR StartThread\n",
            encoding="utf-8",
        )
        static, dynamic = discover_start_calls(root)
        self.assertEqual(static, [])
        self.assertEqual(len(dynamic), 1)

    def test_table_addresses_are_inside_prg(self) -> None:
        self.assertEqual(prg_offset(INITIAL_STACK_POINTERS), 0x0E01)
        self.assertEqual(prg_offset(THREAD_ENTRY_TABLE_BASES), 0x0E09)

    def test_audit_accepts_registered_entry_and_counts(self) -> None:
        entry = {
            "code": 0x30,
            "context": 3,
            "selector": 0,
            "base": 0x8E2F,
            "pointer_address": 0x8E2F,
            "return_address": 0x9FFF,
            "entry": 0xA000,
        }
        report = {
            "initial_stack_pointers": [0xFC, 0xDC, 0xBC, 0x9C, 0x7C, 0x5C, 0x3C, 0x1C],
            "static_call_count": 2,
            "dynamic_call_count": 1,
            "entries": [entry],
        }
        manifest = {
            "initial_stack_pointers": report["initial_stack_pointers"],
            "static_call_count": 2,
            "dynamic_call_count": 1,
            "static_entries": [entry],
        }
        self.assertEqual(validate_report(report, manifest), [])

    def test_audit_rejects_changed_entry(self) -> None:
        report = {
            "initial_stack_pointers": [0xFC],
            "static_call_count": 1,
            "dynamic_call_count": 0,
            "entries": [{
                "code": 0x30,
                "context": 3,
                "selector": 0,
                "base": 0x8E2F,
                "pointer_address": 0x8E2F,
                "return_address": 0x9FFF,
                "entry": 0xA000,
            }],
        }
        manifest = {
            "initial_stack_pointers": [0xFC],
            "static_call_count": 1,
            "dynamic_call_count": 0,
            "static_entries": [{**report["entries"][0], "entry": 0xA001}],
        }
        errors = validate_report(report, manifest)
        self.assertTrue(any("entry differs" in error for error in errors))

    def test_audit_accepts_reviewed_dynamic_entry(self) -> None:
        prg = bytearray(32_768)
        table_base = 0x9000
        base_offset = prg_offset(THREAD_ENTRY_TABLE_BASES + 4)
        prg[base_offset : base_offset + 2] = bytes((0x00, 0x90))
        pointer_offset = prg_offset(table_base + 2)
        prg[pointer_offset : pointer_offset + 2] = bytes((0x46, 0x8E))
        reviewed = {
            "code": 0x21,
            "context": 2,
            "selector": 1,
            "base": table_base,
            "pointer_address": table_base + 2,
            "return_address": 0x8E46,
            "entry": 0x8E47,
        }
        report = {
            "initial_stack_pointers": [0xFC],
            "static_call_count": 0,
            "dynamic_call_count": 1,
            "entries": [],
        }
        manifest = {
            "initial_stack_pointers": [0xFC],
            "static_call_count": 0,
            "dynamic_call_count": 1,
            "static_entries": [],
            "reviewed_dynamic_entries": [reviewed],
        }
        self.assertEqual(validate_report(report, manifest, bytes(prg)), [])

    def test_audit_rejects_changed_reviewed_dynamic_entry(self) -> None:
        prg = bytearray(32_768)
        table_base = 0x9000
        base_offset = prg_offset(THREAD_ENTRY_TABLE_BASES + 4)
        prg[base_offset : base_offset + 2] = bytes((0x00, 0x90))
        pointer_offset = prg_offset(table_base + 2)
        prg[pointer_offset : pointer_offset + 2] = bytes((0x45, 0x8E))
        report = {
            "initial_stack_pointers": [0xFC],
            "static_call_count": 0,
            "dynamic_call_count": 1,
            "entries": [],
        }
        manifest = {
            "initial_stack_pointers": [0xFC],
            "static_call_count": 0,
            "dynamic_call_count": 1,
            "static_entries": [],
            "reviewed_dynamic_entries": [{
                "code": 0x21,
                "context": 2,
                "selector": 1,
                "base": table_base,
                "pointer_address": table_base + 2,
                "return_address": 0x8E46,
                "entry": 0x8E47,
            }],
        }
        errors = validate_report(report, manifest, bytes(prg))
        self.assertTrue(
            any("reviewed dynamic thread code $21 return_address differs" in error for error in errors)
        )

    def test_context_roles_cover_all_contexts_and_known_codes(self) -> None:
        manifest = {
            "context_roles": [
                {
                    "context": context,
                    "role": f"context {context} role",
                    "entry_codes": (
                        [f"0x{code:02x}"]
                        if (code := {1: 0x10, 3: 0x30}.get(context)) is not None
                        else []
                    ),
                }
                for context in range(8)
            ]
        }
        self.assertEqual(validate_context_roles(manifest, {0x10, 0x30}), [])

    def test_context_roles_reject_missing_context_and_code(self) -> None:
        manifest = {
            "context_roles": [
                {
                    "context": context,
                    "role": f"context {context} role",
                    "entry_codes": [],
                }
                for context in range(7)
            ]
        }
        errors = validate_context_roles(manifest, {0x10})
        self.assertTrue(any("contexts missing roles: 7" in error for error in errors))
        self.assertTrue(any("codes missing context roles: $10" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
