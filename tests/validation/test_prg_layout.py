from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]

from scripts.validation import prg_layout


def synthetic_debug(source: Path) -> str:
    return "\n".join(
        (
            'seg\tid=0,name="PRG_TEST",start=0x8000,size=0x0004',
            "span\tid=0,seg=0,start=0,size=2",
            "span\tid=1,seg=0,start=1,size=1",
            "span\tid=2,seg=0,start=2,size=2",
            f'file\tid=0,name="{source.as_posix()}"',
            "line\tid=0,file=0,line=1,span=0",
            "line\tid=1,file=0,line=2,span=1+2",
        )
    )


class StatementTests(unittest.TestCase):
    def test_instruction_is_code(self) -> None:
        self.assertEqual(prg_layout.classify_statement("    LDA #$01"), "code")

    def test_data_directive_is_data(self) -> None:
        self.assertEqual(prg_layout.classify_statement("Table: .byte $01"), "data")


class LayoutTests(unittest.TestCase):
    def test_nested_operand_span_remains_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.asm"
            source.write_text("    LDA #$01\n    .byte $02, $03\n")
            debug = root / "game.dbg"
            debug.write_text(synthetic_debug(source))
            config = {
                "prg_start": "0x8000",
                "prg_end": "0x8003",
                "segment_overrides": {},
            }
            report = prg_layout.classify_layout(debug, config)
            self.assertEqual(report["byte_counts"]["code"], 2)
            self.assertEqual(report["byte_counts"]["data"], 2)
            self.assertEqual(report["classified_bytes"], 4)

    def test_segment_override_owns_complete_span(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.asm"
            source.write_text("    LDA #$01\n    .byte $02, $03\n")
            debug = root / "game.dbg"
            debug.write_text(synthetic_debug(source))
            config = {
                "prg_start": "0x8000",
                "prg_end": "0x8003",
                "segment_overrides": {"stream": ["PRG_TEST"]},
                "stream_codecs": {"test-codec": ["PRG_TEST"]},
            }
            report = prg_layout.classify_layout(debug, config)
            self.assertEqual(report["byte_counts"]["stream"], 4)
            self.assertEqual(report["range_counts"]["stream"], 1)
            self.assertEqual(report["stream_codec_coverage"]["covered_bytes"], 4)
            self.assertTrue(report["stream_codec_coverage"]["exact"])

    def test_stream_codec_coverage_rejects_duplicate_owner(self) -> None:
        counts = {"PRG_TEST": {"stream": 4}}
        config = {
            "stream_codecs": {
                "first": ["PRG_TEST"],
                "second": ["PRG_TEST"],
            }
        }
        coverage = prg_layout.collect_stream_codec_coverage(
            config, counts, {"PRG_TEST": "stream"}
        )
        self.assertFalse(coverage["exact"])
        self.assertEqual(coverage["covered_bytes"], 0)
        self.assertIn("multiple codec owners", coverage["errors"][0])

    def test_audit_detects_changed_layout_fingerprint(self) -> None:
        report = {
            "classified_bytes": 4,
            "layout_sha1": "actual",
            "byte_counts": {"code": 4, "stream": 0},
            "range_counts": {"code": 1},
            "stream_codec_coverage": {"errors": [], "covered_bytes": 0},
        }
        config = {
            "stream_codecs": {},
            "expected": {
                "classified_bytes": 4,
                "layout_sha1": "expected",
                "byte_counts": {"code": 4, "stream": 0},
                "range_counts": {"code": 1},
                "stream_codec_bytes": 0,
            }
        }
        self.assertEqual(len(prg_layout.audit_expected(report, config)), 1)


if __name__ == "__main__":
    unittest.main()
