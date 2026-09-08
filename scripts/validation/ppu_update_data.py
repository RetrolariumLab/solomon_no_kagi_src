#!/usr/bin/env python3
"""Decode and audit ROM-resident PPU update streams."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from scripts.authoring.room_data import RoomDataError, extract_prg


PRG_BASE = 0x8000

PPU_UPDATE_MANIFESTS = {
    "usa": "ppu_update_streams.json",
    "europe": "ppu_update_streams_europe.json",
}


@dataclass(frozen=True)
class PpuUpdateCommand:
    ppu_address: int
    increment: int
    literal: bool
    count: int
    payload: bytes


@dataclass(frozen=True)
class PpuUpdateStream:
    cpu_address: int
    commands: tuple[PpuUpdateCommand, ...]
    encoded_size: int


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


def decode_split_pointers(
    prg: bytes, low_address: int, high_address: int, count: int
) -> list[int]:
    if count <= 0:
        raise RoomDataError(f"invalid stream count: {count}")
    lows = cpu_slice(prg, low_address, low_address + count - 1, "pointer low table")
    highs = cpu_slice(prg, high_address, high_address + count - 1, "pointer high table")
    pointers = [low | (high << 8) for low, high in zip(lows, highs)]
    for pointer in pointers:
        prg_offset(pointer)
    return pointers


def decode_stream(prg: bytes, cpu_address: int) -> PpuUpdateStream:
    cursor = prg_offset(cpu_address)
    start = cursor
    commands: list[PpuUpdateCommand] = []
    while True:
        if cursor >= len(prg):
            raise RoomDataError(f"unterminated PPU update stream at ${cpu_address:04X}")
        address_high = prg[cursor]
        if address_high == 0:
            cursor += 1
            break
        if cursor + 3 > len(prg):
            raise RoomDataError(f"truncated PPU update command at ${cursor + PRG_BASE:04X}")
        ppu_address = (address_high << 8) | prg[cursor + 1]
        control = prg[cursor + 2]
        literal = bool(control & 0x40)
        increment = 32 if control & 0x80 else 1
        count = (control & 0x3F) + 1
        payload_size = count if literal else 1
        payload_start = cursor + 3
        payload_end = payload_start + payload_size
        if payload_end > len(prg):
            raise RoomDataError(f"truncated PPU update payload at ${cursor + PRG_BASE:04X}")
        commands.append(
            PpuUpdateCommand(
                ppu_address=ppu_address,
                increment=increment,
                literal=literal,
                count=count,
                payload=prg[payload_start:payload_end],
            )
        )
        cursor = payload_end
    return PpuUpdateStream(cpu_address, tuple(commands), cursor - start)


def encode_command(command: PpuUpdateCommand) -> bytes:
    if not 0x0100 <= command.ppu_address <= 0x3FFF:
        raise RoomDataError(f"invalid PPU address: ${command.ppu_address:04X}")
    if command.increment not in (1, 32):
        raise RoomDataError(f"invalid PPU increment: {command.increment}")
    if not 1 <= command.count <= 64:
        raise RoomDataError(f"invalid PPU write count: {command.count}")
    expected_payload_size = command.count if command.literal else 1
    if len(command.payload) != expected_payload_size:
        raise RoomDataError(
            f"payload has {len(command.payload)} bytes, expected {expected_payload_size}"
        )
    control = command.count - 1
    if command.literal:
        control |= 0x40
    if command.increment == 32:
        control |= 0x80
    return bytes((command.ppu_address >> 8, command.ppu_address & 0xFF, control)) + command.payload


def encode_stream(stream: PpuUpdateStream) -> bytes:
    return b"".join(encode_command(command) for command in stream.commands) + b"\x00"


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RoomDataError("unsupported PPU update manifest schema")
    pointers = value.get("stream_addresses")
    if not isinstance(pointers, list) or not pointers:
        raise RoomDataError("PPU update manifest needs stream_addresses")
    return value


def validate_manifest_profile(manifest: dict[str, Any], profile: str) -> None:
    actual = manifest.get("profile", "usa")
    if actual != profile:
        raise RoomDataError(
            f"PPU update profile mismatch: expected={profile}, manifest={actual}"
        )


def stream_report(stream: PpuUpdateStream) -> dict[str, object]:
    return {
        "address": stream.cpu_address,
        "end_address": stream.cpu_address + stream.encoded_size - 1,
        "encoded_size": stream.encoded_size,
        "command_count": len(stream.commands),
        "commands": [
            {
                "ppu_address": command.ppu_address,
                "increment": command.increment,
                "mode": "literal" if command.literal else "repeat",
                "count": command.count,
                "payload": list(command.payload),
            }
            for command in stream.commands
        ],
    }


def collect_report(prg: bytes, manifest: dict[str, Any]) -> dict[str, object]:
    low_address = parse_number(manifest.get("pointer_low_address"), "pointer_low_address")
    high_address = parse_number(manifest.get("pointer_high_address"), "pointer_high_address")
    data_start = parse_number(manifest.get("data_start"), "data_start")
    data_end = parse_number(manifest.get("data_end"), "data_end")
    expected_pointers = manifest["stream_addresses"]
    pointers = decode_split_pointers(prg, low_address, high_address, len(expected_pointers))
    streams = [decode_stream(prg, pointer) for pointer in pointers]
    coverage = Counter(
        address
        for stream in streams
        for address in range(stream.cpu_address, stream.cpu_address + stream.encoded_size)
    )
    expected_coverage = set(range(data_start, data_end + 1))
    actual_coverage = set(coverage)
    round_trip = all(
        encode_stream(stream)
        == cpu_slice(
            prg,
            stream.cpu_address,
            stream.cpu_address + stream.encoded_size - 1,
            "PPU update stream",
        )
        for stream in streams
    )
    pointer_data = cpu_slice(
        prg, low_address, low_address + len(pointers) - 1, "pointer low table"
    ) + cpu_slice(
        prg, high_address, high_address + len(pointers) - 1, "pointer high table"
    )
    stream_data = cpu_slice(prg, data_start, data_end, "PPU stream data")
    return {
        "pointer_low_address": low_address,
        "pointer_high_address": high_address,
        "stream_count": len(streams),
        "command_count": sum(len(stream.commands) for stream in streams),
        "data_start": data_start,
        "data_end": data_end,
        "data_size": len(stream_data),
        "pointer_sha1": hashlib.sha1(pointer_data).hexdigest(),
        "data_sha1": hashlib.sha1(stream_data).hexdigest(),
        "pointers": pointers,
        "coverage_exact": actual_coverage == expected_coverage
        and all(count == 1 for count in coverage.values()),
        "round_trip": round_trip,
        "streams": [stream_report(stream) for stream in streams],
    }


def validate_report(report: dict[str, object], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_pointers = [
        parse_number(value, "stream_addresses") for value in manifest["stream_addresses"]
    ]
    if report.get("pointers") != expected_pointers:
        errors.append("split pointer table differs from reviewed stream addresses")
    for report_field, manifest_field in (
        ("pointer_sha1", "pointer_sha1"),
        ("data_sha1", "data_sha1"),
    ):
        if report.get(report_field) != manifest.get(manifest_field):
            errors.append(
                f"{report_field} differs: got {report.get(report_field)!r}, "
                f"expected {manifest.get(manifest_field)!r}"
            )
    if not report.get("coverage_exact"):
        errors.append("stream entries do not cover the reviewed data range exactly once")
    if not report.get("round_trip"):
        errors.append("decoded PPU update streams do not round-trip byte-for-byte")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "audit"))
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--profile", choices=tuple(PPU_UPDATE_MANIFESTS), default="usa"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    manifest_path = args.manifest or (
        root / "config" / "validation" / PPU_UPDATE_MANIFESTS[args.profile]
    )
    try:
        manifest = load_manifest(manifest_path)
        validate_manifest_profile(manifest, args.profile)
        report = collect_report(extract_prg(args.image.read_bytes()), manifest)
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
        print(f"[FAIL] PPU update stream audit found {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(
        f"[OK] PPU update streams: {report['stream_count']} streams, "
        f"{report['command_count']} commands, {report['data_size']} bytes round-tripped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
