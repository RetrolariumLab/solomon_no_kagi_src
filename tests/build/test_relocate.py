from __future__ import annotations

from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "build"))

import relocate  # noqa: E402

LINKER_CONFIG = ROOT / "config" / "linker" / "cnrom.cfg"


class RelocateTests(unittest.TestCase):
    def test_the_moved_segments_come_before_the_audio_filler(self) -> None:
        segments = relocate.moved_segments(LINKER_CONFIG)
        self.assertIn("PRG_NMI", segments)
        self.assertNotIn(relocate.FILLER_SEGMENT, segments)
        self.assertFalse(relocate.FIXED & set(segments))
        # More candidates than the filler can absorb: every n-th of them.
        candidates = relocate.candidate_segments(LINKER_CONFIG)
        self.assertLessEqual(len(segments), relocate.MOST_PROBES)
        step = candidates.index(segments[1]) - candidates.index(segments[0])
        self.assertEqual(candidates[::step], segments)

    def test_the_filler_shrinks_by_the_bytes_inserted(self) -> None:
        source = (ROOT / "src" / relocate.FILLER_MODULE).read_text(encoding="utf-8")
        shrunk = relocate.shrink_filler(source, 5)
        self.assertIn(f"= ${relocate.FILLER_SIZE - 5:04X}, error", shrunk)
        self.assertIn(f".res ${relocate.FILLER_SIZE - 5:04X}, $FF", shrunk)
        with self.assertRaises(relocate.RelocationError):
            relocate.shrink_filler(source, relocate.FILLER_SIZE + 1)

    def test_the_relocated_entry_includes_the_relocated_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "europe"
            count = relocate.relocate(ROOT / "src" / "revisions" / "europe.asm", LINKER_CONFIG, output)
            entry = (output / "europe.asm").read_text(encoding="utf-8")
            main = (output / "main.asm").read_text(encoding="utf-8")
            self.assertIn('.include "main.asm"', entry)
            self.assertIn("SolomonRevision = 1", entry)
            self.assertEqual(count, main.count("    .byte $EA"))
            # Every include resolves from the copy; the filler is the shrunk one.
            for path in re.findall(r'\.include "([^"]+)"', main):
                self.assertTrue((output / path).is_file(), path)
            self.assertIn('.include "items.asm"', main)
            with self.assertRaises(relocate.RelocationError):
                relocate.relocate(ROOT / "src" / "revisions" / "europe.asm", LINKER_CONFIG, output, only=count)


if __name__ == "__main__":
    unittest.main()
