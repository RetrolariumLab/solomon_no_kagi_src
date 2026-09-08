from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validation.asm_style import format_file, lint_file


class AssemblyStyleTests(unittest.TestCase):
    def test_valid_nested_source_passes(self) -> None:
        source = ".if ENABLE_DEMO\nhandler:\n    LDA #$01  ; Select mode\n.endif\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "valid.asm")
            path.write_text(source, encoding="utf-8", newline="\n")
            self.assertEqual(lint_file(path), [])

    def test_common_violations_are_reported(self) -> None:
        source = ";Bad heading\nBad: lda #$00 ;bad comment\n\n\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "invalid.asm")
            path.write_text(source, encoding="utf-8", newline="\n")
            codes = {issue.code for issue in lint_file(path)}
        self.assertTrue({"blank-lines", "comment-space", "final-newline", "label-line"}.issubset(codes))

    def test_formatter_is_idempotent(self) -> None:
        source = "\n;Header.\nentry: lda #$00 ;comment.\n\n\n"
        expected = "; Header\nentry:\n    LDA #$00  ; comment\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "format.asm")
            path.write_text(source, encoding="utf-8", newline="\n")
            self.assertTrue(format_file(path))
            self.assertEqual(path.read_text(encoding="utf-8"), expected)
            self.assertEqual(lint_file(path), [])
            self.assertFalse(format_file(path))

    def test_comment_semicolon_inside_string_is_preserved(self) -> None:
        source = '    .byte "a;b"  ; Text\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "string.asm")
            path.write_text(source, encoding="utf-8", newline="\n")
            self.assertEqual(lint_file(path), [])
            self.assertFalse(format_file(path))

    def test_machine_code_only_comment_is_rejected_and_removed(self) -> None:
        source = "    BNE target  ; $82AD D0 01\ntarget:\n    RTS\n"
        expected = "    BNE target\ntarget:\n    RTS\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "dump.asm")
            path.write_text(source, encoding="utf-8", newline="\n")
            self.assertIn(
                "machine-code-comment",
                {issue.code for issue in lint_file(path)},
            )
            self.assertTrue(format_file(path))
            self.assertEqual(path.read_text(encoding="utf-8"), expected)
            self.assertEqual(lint_file(path), [])

    def test_address_only_comment_is_rejected_and_removed(self) -> None:
        source = "    .byte $00, $0f  ; $B173\n"
        expected = "    .byte $00, $0f\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "address.asm")
            path.write_text(source, encoding="utf-8", newline="\n")
            self.assertIn(
                "machine-code-comment",
                {issue.code for issue in lint_file(path)},
            )
            self.assertTrue(format_file(path))
            self.assertEqual(path.read_text(encoding="utf-8"), expected)
            self.assertEqual(lint_file(path), [])

    def test_machine_code_with_explanation_is_allowed(self) -> None:
        source = "    BNE target  ; $82AD D0 01 skips the fallback\ntarget:\n    RTS\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "explained.asm")
            path.write_text(source, encoding="utf-8", newline="\n")
            self.assertEqual(lint_file(path), [])


if __name__ == "__main__":
    unittest.main()
