#!/usr/bin/env python3
"""Decode and audit Solomon's Key audio tables, descriptors, and streams."""

from __future__ import annotations

import argparse
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
PERIOD_TABLE = 0xF368
PERIOD_COUNT = 12
DURATION_TABLE = 0xF380
DURATION_COUNT = 26
ENVELOPE_POINTER_TABLE = 0xF39A
ENVELOPE_COUNT = 8
ENVELOPE_DATA = 0xF3AA
SOUND_EFFECT_POINTER_TABLE = 0xF47C
SOUND_EFFECT_COUNT = 26
SOUND_EFFECT_DATA = 0xF4B0
AUDIO_STREAM_DATA = 0xF592
AUDIO_STREAM_END = 0xFFF9

COMMAND_ARGUMENT_SIZES = {
    0xF0: 1,
    0xF1: 1,
    0xF2: 2,
    0xF3: 2,
    0xF4: 0,
    0xF5: 1,
    0xF6: 0,
    0xF7: 1,
    0xF8: 1,
    0xF9: 0,
}
TERMINAL_COMMANDS = {0xF2, 0xF4, 0xF9}
POINTER_COMMANDS = {0xF2, 0xF3}


@dataclass(frozen=True)
class AudioLayout:
    period_table: int
    period_count: int
    duration_table: int
    duration_count: int
    envelope_pointer_table: int
    envelope_count: int
    envelope_data: int
    sound_effect_pointer_table: int
    sound_effect_count: int
    sound_effect_data: int
    stream_data: int
    stream_end: int


USA_LAYOUT = AudioLayout(
    period_table=PERIOD_TABLE,
    period_count=PERIOD_COUNT,
    duration_table=DURATION_TABLE,
    duration_count=DURATION_COUNT,
    envelope_pointer_table=ENVELOPE_POINTER_TABLE,
    envelope_count=ENVELOPE_COUNT,
    envelope_data=ENVELOPE_DATA,
    sound_effect_pointer_table=SOUND_EFFECT_POINTER_TABLE,
    sound_effect_count=SOUND_EFFECT_COUNT,
    sound_effect_data=SOUND_EFFECT_DATA,
    stream_data=AUDIO_STREAM_DATA,
    stream_end=AUDIO_STREAM_END,
)

EUROPE_LAYOUT = AudioLayout(
    period_table=0xF2E8,
    period_count=12,
    duration_table=0xF300,
    duration_count=26,
    envelope_pointer_table=0xF342,
    envelope_count=8,
    envelope_data=0xF352,
    sound_effect_pointer_table=0xF424,
    sound_effect_count=26,
    sound_effect_data=0xF458,
    stream_data=0xF53A,
    stream_end=0xFFDE,
)

AUDIO_LAYOUTS = {
    "usa": USA_LAYOUT,
    "europe": EUROPE_LAYOUT,
}


@dataclass(frozen=True)
class EnvelopeStep:
    duration: int
    volume: int


@dataclass(frozen=True)
class AudioChannelStart:
    selector: int
    stream_address: int


@dataclass(frozen=True)
class AudioCommand:
    cpu_address: int
    opcode: int
    arguments: bytes


@dataclass(frozen=True)
class AudioStream:
    cpu_address: int
    commands: tuple[AudioCommand, ...]
    encoded_size: int


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


def read_word(prg: bytes, cpu_address: int) -> int:
    data = cpu_slice(prg, cpu_address, cpu_address + 1, "audio pointer")
    return data[0] | (data[1] << 8)


def decode_pointer_table(prg: bytes, address: int, count: int) -> list[int]:
    pointers = [read_word(prg, address + index * 2) for index in range(count)]
    for pointer in pointers:
        prg_offset(pointer)
    return pointers


def decode_periods(prg: bytes, layout: AudioLayout = USA_LAYOUT) -> list[int]:
    return [
        read_word(prg, layout.period_table + index * 2)
        for index in range(layout.period_count)
    ]


def decode_durations(prg: bytes, layout: AudioLayout = USA_LAYOUT) -> list[int]:
    return list(
        cpu_slice(
            prg,
            layout.duration_table,
            layout.duration_table + layout.duration_count - 1,
            "duration table",
        )
    )


def decode_envelopes(
    prg: bytes, layout: AudioLayout = USA_LAYOUT
) -> tuple[list[int], list[tuple[EnvelopeStep, ...]]]:
    pointers = decode_pointer_table(
        prg, layout.envelope_pointer_table, layout.envelope_count
    )
    boundaries = pointers[1:] + [layout.sound_effect_pointer_table]
    envelopes: list[tuple[EnvelopeStep, ...]] = []
    for index, (start, end) in enumerate(zip(pointers, boundaries)):
        data = cpu_slice(prg, start, end - 1, f"envelope {index}")
        if len(data) % 2:
            raise RoomDataError(f"envelope {index} has an odd byte count")
        envelopes.append(
            tuple(EnvelopeStep(data[offset], data[offset + 1]) for offset in range(0, len(data), 2))
        )
    return pointers, envelopes


def decode_sound_effects(
    prg: bytes,
    layout: AudioLayout = USA_LAYOUT,
) -> tuple[list[int], list[tuple[AudioChannelStart, ...]]]:
    pointers = decode_pointer_table(
        prg, layout.sound_effect_pointer_table, layout.sound_effect_count
    )
    boundaries = pointers[1:] + [layout.stream_data - 1]
    effects: list[tuple[AudioChannelStart, ...]] = []
    for index, (start, end) in enumerate(zip(pointers, boundaries)):
        if start >= end or (end - start) % 3:
            raise RoomDataError(f"invalid sound-effect descriptor {index + 1}")
        records: list[AudioChannelStart] = []
        cursor = start
        while cursor < end:
            selector = cpu_slice(prg, cursor, cursor, "channel selector")[0]
            if cursor != start and selector >= 0x80:
                raise RoomDataError(
                    f"early descriptor boundary at ${cursor:04X}"
                )
            stream_address = read_word(prg, cursor + 1)
            if not layout.stream_data <= stream_address <= layout.stream_end:
                raise RoomDataError(
                    f"sound-effect stream outside data range: ${stream_address:04X}"
                )
            records.append(AudioChannelStart(selector, stream_address))
            cursor += 3
        effects.append(tuple(records))
    if cpu_slice(
        prg, layout.stream_data - 1, layout.stream_data - 1, "descriptor terminator"
    ) != b"\xFF":
        raise RoomDataError("sound-effect descriptors lack final $FF terminator")
    return pointers, effects


def decode_stream(
    prg: bytes, cpu_address: int, layout: AudioLayout = USA_LAYOUT
) -> AudioStream:
    if not layout.stream_data <= cpu_address <= layout.stream_end:
        raise RoomDataError(f"audio stream outside data range: ${cpu_address:04X}")
    cursor = cpu_address
    commands: list[AudioCommand] = []
    while cursor <= layout.stream_end:
        opcode = cpu_slice(prg, cursor, cursor, "audio opcode")[0]
        if opcode >= 0xFA:
            raise RoomDataError(f"unknown audio opcode ${opcode:02X} at ${cursor:04X}")
        argument_size = COMMAND_ARGUMENT_SIZES.get(opcode, 0)
        end = cursor + argument_size
        arguments = cpu_slice(prg, cursor + 1, end, "audio command arguments") if argument_size else b""
        command = AudioCommand(cursor, opcode, arguments)
        commands.append(command)
        cursor = end + 1
        if opcode in TERMINAL_COMMANDS:
            return AudioStream(cpu_address, tuple(commands), cursor - cpu_address)
    raise RoomDataError(f"unterminated audio stream at ${cpu_address:04X}")


def encode_stream(stream: AudioStream) -> bytes:
    return b"".join(
        bytes((command.opcode,)) + command.arguments for command in stream.commands
    )


def discover_streams(
    prg: bytes,
    effects: list[tuple[AudioChannelStart, ...]],
    layout: AudioLayout = USA_LAYOUT,
) -> list[AudioStream]:
    pending = {
        record.stream_address for effect in effects for record in effect
    }
    streams: dict[int, AudioStream] = {}
    while pending:
        address = min(pending)
        pending.remove(address)
        if address in streams:
            continue
        stream = decode_stream(prg, address, layout)
        streams[address] = stream
        for command in stream.commands:
            if command.opcode in POINTER_COMMANDS:
                target = command.arguments[0] | (command.arguments[1] << 8)
                if not layout.stream_data <= target <= layout.stream_end:
                    raise RoomDataError(
                        f"audio command target outside data range: ${target:04X}"
                    )
                if target not in streams:
                    pending.add(target)
    return [streams[address] for address in sorted(streams)]


def audio_stream_labels(streams: list[AudioStream]) -> dict[int, str]:
    return {
        stream.cpu_address: f"AudioStream{index:03d}"
        for index, stream in enumerate(streams)
    }


def collect_command_map(streams: list[AudioStream]) -> dict[int, AudioCommand]:
    commands: dict[int, AudioCommand] = {}
    for stream in streams:
        for command in stream.commands:
            previous = commands.get(command.cpu_address)
            if previous is not None and previous != command:
                raise RoomDataError(
                    f"conflicting audio decode at ${command.cpu_address:04X}"
                )
            commands[command.cpu_address] = command
    return commands


def emit_source(prg: bytes, layout: AudioLayout = USA_LAYOUT) -> str:
    """Render all audio tables, descriptors, streams, and vectors as ca65."""
    periods = decode_periods(prg, layout)
    durations = decode_durations(prg, layout)
    envelope_pointers, envelopes = decode_envelopes(prg, layout)
    effect_pointers, effects = decode_sound_effects(prg, layout)
    streams = discover_streams(prg, effects, layout)
    labels = audio_stream_labels(streams)
    commands = collect_command_map(streams)
    lines = [
        "; Audio lookup tables, effects, bytecode streams, and CPU vectors",
        "",
        ".macro AudioChannelStart selector, stream",
        "    .byte selector",
        "    .word stream",
        ".endmacro",
        "",
        ".macro AudioJump stream",
        "    .byte $F2",
        "    .word stream",
        ".endmacro",
        "",
        ".macro AudioCall stream",
        "    .byte $F3",
        "    .word stream",
        ".endmacro",
        "",
        '.segment "PRG_AUDIO_TIMING_TABLES"',
        "",
        "AudioPeriodTable:",
    ]
    for offset in range(0, len(periods), 6):
        row = periods[offset : offset + 6]
        lines.append("    .word " + ", ".join(f"${value:04X}" for value in row))
    lines.extend(("", "AudioDurationTable:"))
    for offset in range(0, len(durations), 13):
        row = durations[offset : offset + 13]
        lines.append("    .byte " + ", ".join(f"${value:02X}" for value in row))
    timing_tail_start = layout.duration_table + layout.duration_count
    timing_tail = cpu_slice(
        prg,
        timing_tail_start,
        layout.envelope_pointer_table - 1,
        "audio timing tail",
    ) if timing_tail_start < layout.envelope_pointer_table else b""
    if timing_tail:
        lines.extend(("", "; Profile-specific timing tail"))
        for offset in range(0, len(timing_tail), 16):
            row = timing_tail[offset : offset + 16]
            lines.append("    .byte " + ", ".join(f"${value:02X}" for value in row))
    timing_size = layout.envelope_pointer_table - layout.period_table
    lines.extend(
        (
            "",
            f".assert * - AudioPeriodTable = ${timing_size:04X}, error, "
            '"unexpected audio timing table size"',
            "",
            '.segment "PRG_AUDIO_ENVELOPES"',
            "",
            "AudioEnvelopePointerTable:",
        )
    )
    envelope_labels = [f"AudioEnvelope{index:02d}" for index in range(len(envelopes))]
    for offset in range(0, len(envelope_labels), 2):
        row = envelope_labels[offset : offset + 2]
        lines.append("    .word " + ", ".join(row))
    for label, pointer, envelope in zip(
        envelope_labels, envelope_pointers, envelopes
    ):
        if pointer < layout.envelope_data:
            raise RoomDataError(f"invalid envelope pointer: ${pointer:04X}")
        lines.extend(("", f"{label}:"))
        lines.append("; (duration, volume) pairs")
        encoded_envelope = [
            value
            for step in envelope
            for value in (step.duration, step.volume)
        ]
        for offset in range(0, len(encoded_envelope), 16):
            row = encoded_envelope[offset : offset + 16]
            lines.append("    .byte " + ", ".join(f"${value:02X}" for value in row))
    lines.extend(
        (
            "",
            f".assert * - AudioEnvelopePointerTable = "
            f"${layout.sound_effect_pointer_table - layout.envelope_pointer_table:04X}, error, "
            '"unexpected audio envelope data size"',
            "",
            '.segment "PRG_SOUND_EFFECT_DATA"',
            "",
            "SoundEffectPointerTable:",
        )
    )
    effect_labels = [
        f"SoundEffectDescriptor{index + 1:02d}" for index in range(len(effects))
    ]
    for offset in range(0, len(effect_labels), 2):
        row = effect_labels[offset : offset + 2]
        lines.append("    .word " + ", ".join(row))
    for label, pointer, effect in zip(effect_labels, effect_pointers, effects):
        if pointer < layout.sound_effect_data:
            raise RoomDataError(f"invalid sound-effect pointer: ${pointer:04X}")
        lines.extend(("", f"{label}:"))
        for record in effect:
            stream_label = labels.get(record.stream_address)
            if stream_label is None:
                raise RoomDataError(
                    f"missing label for audio stream ${record.stream_address:04X}"
                )
            lines.append(
                f"    AudioChannelStart ${record.selector:02X}, {stream_label}"
            )
    lines.extend(
        (
            "    .byte $FF",
            "",
            f".assert * - SoundEffectPointerTable = "
            f"${layout.stream_data - layout.sound_effect_pointer_table:04X}, error, "
            '"unexpected sound-effect data size"',
            "",
            '.segment "PRG_AUDIO_STREAMS"',
            "",
        )
    )
    labels_by_address = {address: label for address, label in labels.items()}
    cursor = layout.stream_data
    raw = bytearray()

    def flush_raw() -> None:
        if not raw:
            return
        lines.append("    .byte " + ", ".join(f"${value:02X}" for value in raw))
        raw.clear()

    while cursor <= layout.stream_end:
        label = labels_by_address.get(cursor)
        if label is not None:
            flush_raw()
            lines.append(f"{label}:")
        command = commands.get(cursor)
        if command is None:
            raise RoomDataError(f"unmapped audio byte at ${cursor:04X}")
        encoded = bytes((command.opcode,)) + command.arguments
        if command.opcode in POINTER_COMMANDS:
            flush_raw()
            target = command.arguments[0] | (command.arguments[1] << 8)
            target_label = labels.get(target)
            if target_label is None:
                raise RoomDataError(f"missing command target label at ${target:04X}")
            macro = "AudioJump" if command.opcode == 0xF2 else "AudioCall"
            lines.append(f"    {macro} {target_label}")
        else:
            if len(raw) + len(encoded) > 16:
                flush_raw()
            raw.extend(encoded)
        cursor += len(encoded)
    flush_raw()
    tail_start = layout.stream_end + 1
    if tail_start < 0xFFFA:
        tail = cpu_slice(prg, tail_start, 0xFFF9, "audio bank tail")
        lines.extend(("", "; Profile-specific tail before CPU vectors"))
        for offset in range(0, len(tail), 16):
            row = tail[offset : offset + 16]
            lines.append("    .byte " + ", ".join(f"${value:02X}" for value in row))
    lines.extend(
        (
            "",
            f".assert * - AudioStream000 = "
            f"${0xFFFA - layout.stream_data:04X}, error, "
            '"unexpected audio stream data size"',
            "",
            '.segment "VECTORS"',
            "",
            "CpuVectors:",
            "    .word NMI, Reset, $00FF",
            "",
            ".assert * - CpuVectors = 6, error, \"unexpected CPU vector size\"",
            "",
        )
    )
    return "\n".join(lines)


def parse_number(value: object, field: str) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    raise RoomDataError(f"invalid integer for {field}: {value!r}")


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RoomDataError("unsupported audio-data manifest schema")
    return value


def sha1_range(prg: bytes, start: int, end: int) -> str:
    return hashlib.sha1(cpu_slice(prg, start, end, "audio data")).hexdigest()


def collect_report(
    prg: bytes, layout: AudioLayout = USA_LAYOUT
) -> dict[str, object]:
    envelope_pointers, envelopes = decode_envelopes(prg, layout)
    effect_pointers, effects = decode_sound_effects(prg, layout)
    streams = discover_streams(prg, effects, layout)
    coverage = {
        command.cpu_address + offset
        for stream in streams
        for command in stream.commands
        for offset in range(1 + len(command.arguments))
    }
    round_trip = all(
        encode_stream(stream)
        == cpu_slice(
            prg,
            stream.cpu_address,
            stream.cpu_address + stream.encoded_size - 1,
            "audio stream",
        )
        for stream in streams
    )
    return {
        "period_count": len(decode_periods(prg, layout)),
        "duration_count": len(decode_durations(prg, layout)),
        "envelope_count": len(envelopes),
        "envelope_step_count": sum(len(value) for value in envelopes),
        "envelope_pointers": envelope_pointers,
        "sound_effect_count": len(effects),
        "sound_effect_channel_count": sum(len(value) for value in effects),
        "sound_effect_pointers": effect_pointers,
        "stream_entry_count": len(streams),
        "stream_command_count": sum(len(stream.commands) for stream in streams),
        "stream_addresses": [stream.cpu_address for stream in streams],
        "stream_data_size": layout.stream_end - layout.stream_data + 1,
        "stream_coverage_size": len(coverage),
        "coverage_complete": coverage
        == set(range(layout.stream_data, layout.stream_end + 1)),
        "round_trip": round_trip,
        "table_sha1": sha1_range(
            prg, layout.period_table, layout.sound_effect_data - 1
        ),
        "stream_sha1": sha1_range(prg, layout.stream_data, layout.stream_end),
    }


def validate_report(report: dict[str, object], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scalar_fields = (
        "period_count",
        "duration_count",
        "envelope_count",
        "envelope_step_count",
        "sound_effect_count",
        "sound_effect_channel_count",
        "stream_entry_count",
        "stream_command_count",
        "stream_data_size",
        "stream_coverage_size",
        "table_sha1",
        "stream_sha1",
    )
    for field in scalar_fields:
        expected = manifest.get(field)
        if field.endswith("_count") or field.endswith("_size"):
            expected = parse_number(expected, field)
        if report.get(field) != expected:
            errors.append(
                f"{field} differs: got {report.get(field)!r}, expected {expected!r}"
            )
    for field in ("envelope_pointers", "sound_effect_pointers", "stream_addresses"):
        expected_values = manifest.get(field)
        if not isinstance(expected_values, list):
            raise RoomDataError(f"manifest field {field} must be a list")
        expected = [parse_number(value, field) for value in expected_values]
        if report.get(field) != expected:
            errors.append(f"{field} differs from reviewed addresses")
    if not report.get("coverage_complete"):
        errors.append("reachable audio commands do not cover the stream-data range")
    if not report.get("round_trip"):
        errors.append("decoded audio streams do not round-trip byte-for-byte")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "audit", "source"))
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--profile", choices=tuple(AUDIO_LAYOUTS), default="usa")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    default_manifest = (
        "audio_data.json" if args.profile == "usa" else "audio_data_europe.json"
    )
    manifest_path = args.manifest or root / "config" / "authoring" / default_manifest
    layout = AUDIO_LAYOUTS[args.profile]
    try:
        prg = extract_prg(args.image.read_bytes())
        if args.command == "source":
            print(emit_source(prg, layout), end="")
            return 0
        report = collect_report(prg, layout)
        if args.command == "report":
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0
        errors = validate_report(report, load_manifest(manifest_path))
    except (OSError, ValueError, KeyError, IndexError, json.JSONDecodeError, RoomDataError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print(
        f"[OK] Audio data ({args.profile}): "
        f"{report['sound_effect_count']} effects, "
        f"{report['stream_entry_count']} stream entries, "
        f"{report['stream_data_size']} payload bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
