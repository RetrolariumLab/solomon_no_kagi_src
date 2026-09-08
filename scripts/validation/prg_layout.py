#!/usr/bin/env python3
"""Classify every PRG byte from ld65 source spans and reviewed overrides."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys

from scripts.validation.debug_symbols import parse_record


MNEMONICS = frozenset(
    """
    ADC AND ASL BCC BCS BEQ BIT BMI BNE BPL BRK BVC BVS CLC CLD CLI CLV
    CMP CPX CPY DEC DEX DEY EOR INC INX INY JMP JSR LDA LDX LDY LSR NOP
    ORA PHA PHP PLA PLP ROL ROR RTI RTS SBC SEC SED SEI STA STX STY TAX
    TAY TSX TXA TXS TYA
    """.split()
)
LABEL_RE = re.compile(r"^[A-Za-z_@.?][A-Za-z0-9_@.?]*:\s*")
CATEGORY_CODES = {"code": 1, "data": 2, "stream": 3, "padding": 4, "vector": 5}


class LayoutError(ValueError):
    """A PRG layout validation error."""


@dataclass(frozen=True)
class Segment:
    identifier: int
    name: str
    start: int
    size: int


@dataclass(frozen=True)
class Span:
    identifier: int
    segment: int
    start: int
    size: int


@dataclass(frozen=True)
class SourceLine:
    file: int
    line: int


def parse_number(value: object, field: str) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    raise LayoutError(f"invalid integer for {field}: {value!r}")


def load_config(path: Path) -> dict[str, object]:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LayoutError(f"cannot read {path}: {exc}") from exc
    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise LayoutError(f"unsupported PRG layout schema: {path}")
    return config


def load_debug_records(
    path: Path,
) -> tuple[
    dict[int, Segment],
    dict[int, Span],
    dict[int, str],
    dict[int, SourceLine],
    dict[int, set[int]],
]:
    segments: dict[int, Segment] = {}
    spans: dict[int, Span] = {}
    files: dict[int, str] = {}
    lines: dict[int, SourceLine] = {}
    span_lines: dict[int, set[int]] = defaultdict(set)
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        kind, fields = parse_record(raw_line)
        if kind == "seg" and {"id", "name", "start", "size"} <= fields.keys():
            identifier = int(fields["id"], 0)
            segments[identifier] = Segment(
                identifier,
                fields["name"],
                int(fields["start"], 0),
                int(fields["size"], 0),
            )
        elif kind == "span" and {"id", "seg", "start", "size"} <= fields.keys():
            identifier = int(fields["id"], 0)
            spans[identifier] = Span(
                identifier,
                int(fields["seg"], 0),
                int(fields["start"], 0),
                int(fields["size"], 0),
            )
        elif kind == "file" and {"id", "name"} <= fields.keys():
            files[int(fields["id"], 0)] = fields["name"]
        elif kind == "line" and {"id", "file", "line"} <= fields.keys():
            identifier = int(fields["id"], 0)
            lines[identifier] = SourceLine(
                int(fields["file"], 0), int(fields["line"], 0)
            )
            for span_id in fields.get("span", "").split("+"):
                if span_id:
                    span_lines[int(span_id, 0)].add(identifier)
    if not segments or not spans or not files or not lines:
        raise LayoutError(f"incomplete ld65 debug records: {path}")
    return segments, spans, files, lines, dict(span_lines)


def classify_statement(line: str) -> str:
    """Classify one source statement as machine code or emitted data."""

    statement = line.split(";", 1)[0].strip()
    statement = LABEL_RE.sub("", statement, count=1).lstrip()
    if not statement:
        return "data"
    token = statement.split(None, 1)[0].upper()
    return "code" if token in MNEMONICS else "data"


def source_cache(files: dict[int, str]) -> dict[int, list[str]]:
    cache: dict[int, list[str]] = {}
    for identifier, name in files.items():
        path = Path(name)
        if path.suffix.lower() not in {".asm", ".inc"}:
            cache[identifier] = []
            continue
        if not path.is_file():
            raise LayoutError(f"debug source file does not exist: {name}")
        cache[identifier] = path.read_text(encoding="utf-8").splitlines()
    return cache


def load_overrides(
    config: dict[str, object], segments: dict[int, Segment]
) -> dict[str, str]:
    document = config.get("segment_overrides")
    if not isinstance(document, dict):
        raise LayoutError("segment_overrides must be an object")
    known_names = {segment.name for segment in segments.values()}
    overrides: dict[str, str] = {}
    for category, names in document.items():
        if category not in {"stream", "padding", "vector"}:
            raise LayoutError(f"unsupported segment override category: {category}")
        if not isinstance(names, list) or not all(
            isinstance(name, str) for name in names
        ):
            raise LayoutError(f"segment override {category} must be a list of names")
        for name in names:
            if name not in known_names:
                raise LayoutError(f"unknown overridden segment: {name}")
            if name in overrides:
                raise LayoutError(f"segment has multiple classifications: {name}")
            overrides[name] = category
    return overrides


def collect_stream_codec_coverage(
    config: dict[str, object],
    segment_counts: dict[str, dict[str, int]],
    overrides: dict[str, str],
) -> dict[str, object]:
    declarations = config.get("stream_codecs")
    if not isinstance(declarations, dict) or not declarations:
        return {
            "exact": False,
            "covered_bytes": 0,
            "codec_count": 0,
            "segment_count": 0,
            "errors": ["stream_codecs must be a nonempty object"],
            "codecs": {},
        }
    expected_segments = sorted(
        name for name, category in overrides.items() if category == "stream"
    )
    ownership: dict[str, list[str]] = defaultdict(list)
    codecs: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    for codec, names in declarations.items():
        if not isinstance(codec, str) or not codec:
            errors.append("stream codec name must be a nonempty string")
            continue
        if not isinstance(names, list) or not all(
            isinstance(name, str) for name in names
        ):
            errors.append(f"stream codec {codec} must contain segment names")
            continue
        byte_count = 0
        for name in names:
            ownership[name].append(codec)
            counts = segment_counts.get(name)
            if counts is None:
                errors.append(f"stream codec {codec} references unknown segment {name}")
                continue
            non_stream = {
                category: count
                for category, count in counts.items()
                if category != "stream"
            }
            if non_stream:
                errors.append(f"stream codec {codec} owns non-stream segment {name}")
            byte_count += counts.get("stream", 0)
        codecs[codec] = {"segments": names, "bytes": byte_count}
    for name in expected_segments:
        owners = ownership.get(name, [])
        if not owners:
            errors.append(f"stream segment has no codec owner: {name}")
        elif len(owners) > 1:
            errors.append(f"stream segment has multiple codec owners: {name}")
    for name in sorted(set(ownership) - set(expected_segments)):
        errors.append(f"codec ownership includes non-stream segment: {name}")
    covered_bytes = sum(
        segment_counts[name].get("stream", 0)
        for name in expected_segments
        if len(ownership.get(name, [])) == 1
    )
    return {
        "exact": not errors,
        "covered_bytes": covered_bytes,
        "codec_count": len(codecs),
        "segment_count": len(expected_segments),
        "errors": errors,
        "codecs": dict(sorted(codecs.items())),
    }


def classify_layout(debug_path: Path, config: dict[str, object]) -> dict[str, object]:
    segments, spans, files, lines, span_lines = load_debug_records(debug_path)
    overrides = load_overrides(config, segments)
    sources = source_cache(files)
    prg_start = parse_number(config.get("prg_start"), "prg_start")
    prg_end = parse_number(config.get("prg_end"), "prg_end")
    prg_size = prg_end - prg_start + 1
    if prg_size <= 0:
        raise LayoutError("invalid PRG address range")
    layout: list[str | None] = [None] * prg_size
    prg_segments = {
        identifier: segment
        for identifier, segment in segments.items()
        if segment.size and prg_start <= segment.start <= prg_end
    }
    for span in spans.values():
        segment = prg_segments.get(span.segment)
        if segment is None or span.size == 0:
            continue
        absolute_start = segment.start + span.start
        absolute_end = absolute_start + span.size - 1
        if absolute_start < segment.start or absolute_end >= segment.start + segment.size:
            raise LayoutError(f"span {span.identifier} escapes segment {segment.name}")
        category = overrides.get(segment.name)
        if category is None:
            line_ids = span_lines.get(span.identifier, set())
            statements: list[str] = []
            for line_id in line_ids:
                source_line = lines[line_id]
                source = sources[source_line.file]
                if 1 <= source_line.line <= len(source):
                    statements.append(source[source_line.line - 1])
            category = (
                "code"
                if any(classify_statement(statement) == "code" for statement in statements)
                else "data"
            )
        for address in range(absolute_start, absolute_end + 1):
            index = address - prg_start
            previous = layout[index]
            if previous is None or previous == category:
                layout[index] = category
            elif {previous, category} == {"code", "data"}:
                # ld65 emits nested operand-expression spans inside the span
                # for the complete instruction. The instruction classification
                # owns those shared bytes.
                layout[index] = "code"
            else:
                raise LayoutError(
                    f"conflicting source spans at ${address:04X}: "
                    f"{previous} and {category}"
                )
    gaps = [prg_start + index for index, category in enumerate(layout) if category is None]
    if gaps:
        preview = ", ".join(f"${address:04X}" for address in gaps[:8])
        raise LayoutError(f"unclassified PRG bytes: {preview}")
    byte_counts = {
        category: layout.count(category)
        for category in CATEGORY_CODES
    }
    encoded = bytes(CATEGORY_CODES[str(category)] for category in layout)
    range_counts: dict[str, int] = defaultdict(int)
    previous: str | None = None
    for category in layout:
        if category != previous:
            range_counts[str(category)] += 1
            previous = category
    segment_counts: dict[str, dict[str, int]] = {}
    for segment in prg_segments.values():
        counts: dict[str, int] = defaultdict(int)
        for address in range(segment.start, segment.start + segment.size):
            counts[str(layout[address - prg_start])] += 1
        segment_counts[segment.name] = counts
    stream_codec_coverage = collect_stream_codec_coverage(
        config, segment_counts, overrides
    )
    return {
        "prg_start": f"0x{prg_start:04x}",
        "prg_end": f"0x{prg_end:04x}",
        "classified_bytes": len(layout),
        "layout_sha1": hashlib.sha1(encoded).hexdigest(),
        "byte_counts": byte_counts,
        "range_counts": dict(sorted(range_counts.items())),
        "segments": {
            name: dict(sorted(counts.items()))
            for name, counts in sorted(segment_counts.items())
        },
        "stream_codec_coverage": stream_codec_coverage,
    }


def audit_expected(report: dict[str, object], config: dict[str, object]) -> list[str]:
    expected = config.get("expected")
    if not isinstance(expected, dict):
        return ["layout config has no expected audit values"]
    errors: list[str] = []
    for field in ("classified_bytes", "layout_sha1", "byte_counts", "range_counts"):
        if report.get(field) != expected.get(field):
            errors.append(
                f"{field} mismatch: got {report.get(field)!r}, "
                f"expected {expected.get(field)!r}"
            )
    errors.extend(audit_stream_codec_coverage(report, config))
    return errors


def audit_stream_codec_coverage(
    report: dict[str, object], config: dict[str, object]
) -> list[str]:
    coverage = report.get("stream_codec_coverage")
    if not isinstance(coverage, dict):
        return ["layout report has no stream codec coverage"]
    errors = list(coverage.get("errors", []))
    expected = config.get("expected")
    if not isinstance(expected, dict):
        errors.append("layout config has no expected audit values")
        return errors
    expected_bytes = expected.get("stream_codec_bytes")
    if coverage.get("covered_bytes") != expected_bytes:
        errors.append(
            f"stream codec byte count mismatch: got {coverage.get('covered_bytes')!r}, "
            f"expected {expected_bytes!r}"
        )
    byte_counts = report.get("byte_counts")
    if not isinstance(byte_counts, dict) or coverage.get(
        "covered_bytes"
    ) != byte_counts.get("stream"):
        errors.append("stream codecs do not cover every classified stream byte")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "audit", "format-audit"))
    parser.add_argument("--debug", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        report = classify_layout(args.debug, config)
        if args.command == "report":
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0
        errors = (
            audit_stream_codec_coverage(report, config)
            if args.command == "format-audit"
            else audit_expected(report, config)
        )
    except (OSError, LayoutError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    if args.command == "format-audit":
        coverage = report["stream_codec_coverage"]
        print(
            f"[OK] Stream codec coverage: {coverage['segment_count']} segments, "
            f"{coverage['covered_bytes']} bytes across "
            f"{coverage['codec_count']} codecs"
        )
        return 0
    counts = report["byte_counts"]
    print(
        f"[OK] PRG layout: {report['classified_bytes']} bytes, "
        f"{counts['code']} code, {counts['data']} data, "
        f"{counts['stream']} stream, {counts['padding']} padding, "
        f"{counts['vector']} vector"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
