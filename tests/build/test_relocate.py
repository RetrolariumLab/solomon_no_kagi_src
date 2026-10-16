from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "build"))

import relocate  # noqa: E402


class RelocateTests(unittest.TestCase):
    def test_the_moved_segments_come_before_the_audio_filler(self) -> None:
        segments = relocate.moved_segments(ROOT / "config" / "linker" / "cnrom.cfg")
        self.assertIn("PRG_NMI", segments)
        self.assertNotIn(relocate.FILLER_SEGMENT, segments)
        self.assertFalse(relocate.FIXED & set(segments))

    def test_the_filler_shrinks_by_the_bytes_inserted(self) -> None:
        source = (ROOT / "src" / relocate.FILLER_MODULE).read_text(encoding="utf-8")
        shrunk = relocate.shrink_filler(source, 5)
        self.assertIn(f"= ${relocate.FILLER_SIZE - 5:04X}, error", shrunk)
        self.assertIn(f".res ${relocate.FILLER_SIZE - 5:04X}, $FF", shrunk)
        with self.assertRaises(relocate.RelocationError):
            relocate.shrink_filler(source, relocate.FILLER_SIZE + 1)


if __name__ == "__main__":
    unittest.main()
