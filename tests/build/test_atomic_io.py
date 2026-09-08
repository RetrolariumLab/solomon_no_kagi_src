from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.build import atomic_io


class AtomicIoTests(unittest.TestCase):
    def test_bytes_replace_existing_output_without_temp_residue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "nested" / "output.bin"
            atomic_io.atomic_write_bytes(output, b"first")
            atomic_io.atomic_write_bytes(output, b"second")
            self.assertEqual(output.read_bytes(), b"second")
            self.assertEqual(list(output.parent.glob("*.tmp")), [])

    def test_json_has_stable_indentation_and_terminal_newline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            atomic_io.atomic_write_json(output, {"value": "solomon"})
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                '{\n  "value": "solomon"\n}\n',
            )

    def test_failed_replace_cleans_up_unique_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "output.bin"
            with mock.patch("os.replace", side_effect=OSError("replace failed")):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    atomic_io.atomic_write_bytes(output, b"payload")
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
