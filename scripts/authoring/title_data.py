#!/usr/bin/env python3
"""Decode, encode, and audit packed title graphics and attract-demo input."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

try:
    from .room_data import RoomDataError, extract_prg
except ImportError:
    from scripts.authoring.room_data import RoomDataError, extract_prg


PRG_BASE = 0x8000
TITLE_DATA_MANIFESTS = {
    "usa": "title_data.json",
    "europe": "title_data_europe.json",
}
TERMINATOR = 0x7F
BUTTON_BITS = (
    (0x80, "A"),
    (0x40, "B"),
    (0x20, "SELECT"),
    (0x10, "START"),
    (0x08, "UP"),
    (0x04, "DOWN"),
    (0x02, "LEFT"),
    (0x01, "RIGHT"),
)


@dataclass(frozen=True)
class TitleCursorCommand:
    kind: str
    value: int | None = None


@dataclass(frozen=True)
class TitleLiteralRun:
    ppu_address: int
    tiles: bytes


@dataclass(frozen=True)
class TitlePackedStream:
    cpu_address: int
    tokens: tuple[TitleCursorCommand | TitleLiteralRun, ...]
    encoded_size: int


@dataclass(frozen=True)
class DemoInputStep:
    index: int
    duration: int
    buttons: tuple[str, ...]


def parse_number(value: object, field: str) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    raise RoomDataError(f"invalid integer for {field}: {value!r}")


def prg_offset(cpu_address: int) -> int:
    if not PRG_BASE <= cpu_address <= 0xFFFF:
        raise RoomDataError(f"CPU address outside PRG: ${cpu_address:04X}")
    return cpu_address - PRG_BASE


def cpu_slice(prg: bytes, start: int, end: int, label: str) -> bytes:
    if end < start:
        raise RoomDataError(f"invalid {label} range: ${start:04X}-${end:04X}")
    offset = prg_offset(start)
    stop = prg_offset(end) + 1
    if stop > len(prg):
        raise RoomDataError(f"truncated {label} at ${start:04X}")
    return prg[offset:stop]


def title_ppu_address(row: int, column: int) -> int:
    """Reproduce SetPackedTitlePpuAddress, including its carry-fed rotates."""
    if not 0 <= row <= 0xFF or not 0 <= column < 0x40:
        raise RoomDataError(f"invalid packed title cursor: row={row}, column={column}")
    biased_row = (row + 0x10) & 0xFF
    address_high = ((biased_row >> 2) & 0x2B) | 0x20
    carry = (biased_row >> 1) & 1
    address_low = row
    for _ in range(3):
        next_carry = address_low & 1
        address_low = (carry << 7) | (address_low >> 1)
        carry = next_carry
    address_low = (address_low & 0xC0) | column
    return (address_high << 8) | address_low


def decode_cursor_command(opcode: int) -> TitleCursorCommand:
    if not 0 <= opcode < 0x80:
        raise RoomDataError(f"packed title command is not nonnegative: ${opcode:02X}")
    if opcode < 0x40:
        return TitleCursorCommand("set_column", opcode)
    if opcode < 0x60:
        return TitleCursorCommand("set_row", opcode)
    if opcode < TERMINATOR:
        return TitleCursorCommand("add_row", (opcode & 0x1F) + 1)
    return TitleCursorCommand("terminate")


def encode_cursor_command(command: TitleCursorCommand) -> int:
    if command.kind == "terminate":
        if command.value is not None:
            raise RoomDataError("packed title terminator cannot have an operand")
        return TERMINATOR
    if not isinstance(command.value, int):
        raise RoomDataError(f"packed title {command.kind} command needs an operand")
    if command.kind == "set_column" and 0 <= command.value < 0x40:
        return command.value
    if command.kind == "set_row" and 0x40 <= command.value < 0x60:
        return command.value
    if command.kind == "add_row" and 1 <= command.value <= 31:
        return 0x60 | (command.value - 1)
    raise RoomDataError(
        f"invalid packed title command: kind={command.kind!r}, value={command.value}"
    )


def decode_stream(prg: bytes, cpu_address: int) -> TitlePackedStream:
    cursor = prg_offset(cpu_address)
    start = cursor
    row = 0
    column = 0
    tokens: list[TitleCursorCommand | TitleLiteralRun] = []
    while cursor < len(prg):
        opcode = prg[cursor]
        if opcode >= 0x80:
            literal_start = cursor
            while cursor < len(prg) and prg[cursor] >= 0x80:
                cursor += 1
            tokens.append(
                TitleLiteralRun(
                    ppu_address=title_ppu_address(row, column),
                    tiles=prg[literal_start:cursor],
                )
            )
            continue

        command = decode_cursor_command(opcode)
        tokens.append(command)
        cursor += 1
        if command.kind == "set_column":
            column = command.value if command.value is not None else column
        elif command.kind == "set_row":
            row = command.value if command.value is not None else row
        elif command.kind == "add_row":
            row = (row + (command.value or 0)) & 0xFF
        else:
            return TitlePackedStream(cpu_address, tuple(tokens), cursor - start)
    raise RoomDataError(f"unterminated packed title stream at ${cpu_address:04X}")


def encode_stream(stream: TitlePackedStream) -> bytes:
    encoded = bytearray()
    saw_terminator = False
    for index, token in enumerate(stream.tokens):
        if isinstance(token, TitleCursorCommand):
            opcode = encode_cursor_command(token)
            encoded.append(opcode)
            if opcode == TERMINATOR:
                if index != len(stream.tokens) - 1:
                    raise RoomDataError("packed title terminator is not the final token")
                saw_terminator = True
        else:
            if not token.tiles or any(tile < 0x80 for tile in token.tiles):
                raise RoomDataError("packed title literal run contains a command byte")
            encoded.extend(token.tiles)
    if not saw_terminator:
        raise RoomDataError("packed title stream has no terminator")
    return bytes(encoded)


def decode_buttons(value: int) -> tuple[str, ...]:
    if not 0 <= value <= 0xFF:
        raise RoomDataError(f"controller value is outside byte range: {value}")
    return tuple(name for mask, name in BUTTON_BITS if value & mask)


def encode_buttons(buttons: tuple[str, ...]) -> int:
    if len(set(buttons)) != len(buttons):
        raise RoomDataError("demo input contains a duplicate button")
    known = {name: mask for mask, name in BUTTON_BITS}
    unknown = [name for name in buttons if name not in known]
    if unknown:
        raise RoomDataError(f"unknown demo input button: {unknown[0]}")
    return sum(known[name] for name in buttons)


def decode_demo_input(
    prg: bytes, duration_address: int, input_address: int, count: int
) -> list[DemoInputStep]:
    if count <= 0:
        raise RoomDataError(f"invalid demo input count: {count}")
    durations = cpu_slice(
        prg, duration_address, duration_address + count - 1, "demo input durations"
    )
    inputs = cpu_slice(prg, input_address, input_address + count - 1, "demo inputs")
    return [
        DemoInputStep(index, duration, decode_buttons(buttons))
        for index, (duration, buttons) in enumerate(zip(durations, inputs))
    ]


def encode_demo_input(steps: list[DemoInputStep]) -> tuple[bytes, bytes]:
    if [step.index for step in steps] != list(range(len(steps))):
        raise RoomDataError("demo input indices are not contiguous")
    if any(not 0 <= step.duration <= 0xFF for step in steps):
        raise RoomDataError("demo input duration is outside byte range")
    return (
        bytes(step.duration for step in steps),
        bytes(encode_buttons(step.buttons) for step in steps),
    )


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RoomDataError("unsupported packed title manifest schema")
    streams = value.get("streams")
    if not isinstance(streams, list) or not streams:
        raise RoomDataError("packed title manifest needs streams")
    if not isinstance(value.get("demo_input"), dict):
        raise RoomDataError("packed title manifest needs demo_input")
    return value


def validate_manifest_profile(manifest: dict[str, Any], profile: str) -> None:
    actual = manifest.get("profile", "usa")
    if actual != profile:
        raise RoomDataError(
            f"title data profile mismatch: expected={profile}, manifest={actual}"
        )


def token_report(token: TitleCursorCommand | TitleLiteralRun) -> dict[str, object]:
    if isinstance(token, TitleCursorCommand):
        report: dict[str, object] = {"kind": token.kind}
        if token.value is not None:
            report["value"] = token.value
        return report
    return {
        "kind": "literal",
        "ppu_address": token.ppu_address,
        "tile_count": len(token.tiles),
        "tiles": token.tiles.hex(),
    }


def collect_report(prg: bytes, manifest: dict[str, Any]) -> dict[str, object]:
    stream_reports: list[dict[str, object]] = []
    coverage: Counter[int] = Counter()
    all_round_trip = True
    for index, declaration in enumerate(manifest["streams"]):
        if not isinstance(declaration, dict):
            raise RoomDataError(f"packed title stream {index} must be an object")
        name = declaration.get("name")
        if not isinstance(name, str) or not name:
            raise RoomDataError(f"packed title stream {index} needs a name")
        address = parse_number(declaration.get("address"), f"{name}.address")
        stream = decode_stream(prg, address)
        end_address = address + stream.encoded_size - 1
        encoded = encode_stream(stream)
        original = cpu_slice(prg, address, end_address, f"{name} packed title stream")
        commands = [
            token for token in stream.tokens if isinstance(token, TitleCursorCommand)
        ]
        literals = [
            token for token in stream.tokens if isinstance(token, TitleLiteralRun)
        ]
        coverage.update(range(address, end_address + 1))
        round_trip = encoded == original
        all_round_trip &= round_trip
        stream_reports.append(
            {
                "name": name,
                "address": address,
                "end_address": end_address,
                "encoded_size": stream.encoded_size,
                "command_count": len(commands),
                "literal_run_count": len(literals),
                "literal_tile_count": sum(len(run.tiles) for run in literals),
                "literal_ppu_addresses": [run.ppu_address for run in literals],
                "round_trip": round_trip,
                "sha1": hashlib.sha1(original).hexdigest(),
                "tokens": [token_report(token) for token in stream.tokens],
            }
        )

    data_start = parse_number(manifest.get("data_start"), "data_start")
    data_end = parse_number(manifest.get("data_end"), "data_end")
    expected_coverage = set(range(data_start, data_end + 1))
    demo_manifest = manifest["demo_input"]
    if not isinstance(demo_manifest, dict):
        raise RoomDataError("demo_input must be an object")
    duration_address = parse_number(
        demo_manifest.get("duration_address"), "demo_input.duration_address"
    )
    input_address = parse_number(
        demo_manifest.get("input_address"), "demo_input.input_address"
    )
    input_count = parse_number(demo_manifest.get("input_count"), "demo_input.input_count")
    steps = decode_demo_input(prg, duration_address, input_address, input_count)
    encoded_durations, encoded_inputs = encode_demo_input(steps)
    original_durations = cpu_slice(
        prg, duration_address, duration_address + input_count - 1, "demo input durations"
    )
    original_inputs = cpu_slice(
        prg, input_address, input_address + input_count - 1, "demo inputs"
    )
    demo_round_trip = (
        encoded_durations == original_durations and encoded_inputs == original_inputs
    )
    terminal_duration = original_inputs[0]
    demo_report = {
        "duration_address": duration_address,
        "input_address": input_address,
        "end_address": input_address + input_count - 1,
        "input_count": input_count,
        "encoded_size": input_count * 2,
        "terminal_duration_alias": terminal_duration,
        "duration_sha1": hashlib.sha1(original_durations).hexdigest(),
        "input_sha1": hashlib.sha1(original_inputs).hexdigest(),
        "data_sha1": hashlib.sha1(original_durations + original_inputs).hexdigest(),
        "round_trip": demo_round_trip,
        "steps": [
            {
                "index": step.index,
                "duration": step.duration,
                "effective_wait": step.duration + 1,
                "buttons": list(step.buttons),
                "button_mask": encode_buttons(step.buttons),
            }
            for step in steps
        ],
    }
    title_round_trip = all_round_trip
    return {
        "stream_count": len(stream_reports),
        "encoded_size": sum(item["encoded_size"] for item in stream_reports),
        "command_count": sum(item["command_count"] for item in stream_reports),
        "literal_run_count": sum(
            item["literal_run_count"] for item in stream_reports
        ),
        "literal_tile_count": sum(
            item["literal_tile_count"] for item in stream_reports
        ),
        "coverage_exact": set(coverage) == expected_coverage
        and all(count == 1 for count in coverage.values()),
        "round_trip": title_round_trip and demo_round_trip,
        "title_round_trip": title_round_trip,
        "data_sha1": hashlib.sha1(
            cpu_slice(prg, data_start, data_end, "packed title data")
        ).hexdigest(),
        "streams": stream_reports,
        "demo_input": demo_report,
        "audited_size": sum(item["encoded_size"] for item in stream_reports)
        + input_count * 2,
    }


def validate_report(report: dict[str, object], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_streams = manifest["streams"]
    actual_streams = report.get("streams")
    if not isinstance(actual_streams, list):
        return ["packed title report has no stream list"]
    if len(actual_streams) != len(expected_streams):
        errors.append("packed title stream count differs from manifest")
        return errors
    for expected, actual in zip(expected_streams, actual_streams):
        if not isinstance(expected, dict) or not isinstance(actual, dict):
            errors.append("packed title stream entry is not an object")
            continue
        name = expected.get("name", "unnamed")
        expected_ppu_addresses = [
            parse_number(value, f"{name}.literal_ppu_addresses")
            for value in expected.get("literal_ppu_addresses", [])
        ]
        if actual.get("literal_ppu_addresses") != expected_ppu_addresses:
            errors.append(f"{name}.literal_ppu_addresses differ from manifest")
        for field in (
            "address",
            "end_address",
            "encoded_size",
            "command_count",
            "literal_run_count",
            "literal_tile_count",
            "sha1",
        ):
            expected_value = expected.get(field)
            if field in {"address", "end_address"}:
                expected_value = parse_number(expected_value, f"{name}.{field}")
            if actual.get(field) != expected_value:
                errors.append(
                    f"{name}.{field} differs: got {actual.get(field)!r}, "
                    f"expected {expected_value!r}"
                )
    if report.get("data_sha1") != manifest.get("data_sha1"):
        errors.append("packed title aggregate SHA-1 differs from manifest")
    if not report.get("coverage_exact"):
        errors.append("packed title streams do not cover their data range exactly once")
    if not report.get("title_round_trip"):
        errors.append("packed title streams do not round-trip byte-for-byte")
    expected_demo = manifest.get("demo_input")
    actual_demo = report.get("demo_input")
    if not isinstance(expected_demo, dict) or not isinstance(actual_demo, dict):
        errors.append("demo input report or manifest is missing")
    else:
        for field in (
            "duration_address",
            "input_address",
            "end_address",
            "input_count",
            "encoded_size",
            "terminal_duration_alias",
            "duration_sha1",
            "input_sha1",
            "data_sha1",
        ):
            expected_value = expected_demo.get(field)
            if field.endswith("address"):
                expected_value = parse_number(expected_value, f"demo_input.{field}")
            if actual_demo.get(field) != expected_value:
                errors.append(
                    f"demo_input.{field} differs: got {actual_demo.get(field)!r}, "
                    f"expected {expected_value!r}"
                )
        if not actual_demo.get("round_trip"):
            errors.append("demo input tables do not round-trip byte-for-byte")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "audit"))
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--profile", choices=tuple(TITLE_DATA_MANIFESTS), default="usa"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    manifest_path = args.manifest or (
        root / "config" / "authoring" / TITLE_DATA_MANIFESTS[args.profile]
    )
    try:
        manifest = load_manifest(manifest_path)
        validate_manifest_profile(manifest, args.profile)
        prg = extract_prg(args.image.read_bytes())
        report = collect_report(prg, manifest)
        if args.command == "report":
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0
        errors = validate_report(report, manifest)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, RoomDataError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        print(f"[FAIL] Packed title audit found {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(
        "[OK] Packed title data: "
        f"{report['stream_count']} streams, {report['command_count']} commands, "
        f"{report['literal_run_count']} literal runs, "
        f"{report['encoded_size']} title bytes and "
        f"{report['demo_input']['encoded_size']} demo bytes round-tripped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
