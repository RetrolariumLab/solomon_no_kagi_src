#!/usr/bin/env python3
"""Import, validate, and rebuild editable Solomon's Key audio documents."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

from audio_data import (
    AUDIO_LAYOUTS,
    POINTER_COMMANDS,
    AudioCommand,
    AudioLayout,
    collect_command_map,
    cpu_slice,
    decode_durations,
    decode_envelopes,
    decode_periods,
    decode_sound_effects,
    discover_streams,
)
from project import ProjectError, digest, parse_ines, write_if_changed
from revision_profiles import (
    ROOT,
    get_profile,
    load_profiles,
    resolve_reference,
    verify_reference,
)
from room_data import RoomDataError


DOCUMENT_SCHEMA = 1
DOCUMENT_GAME = "solomons-key-nes-audio"
STREAM_ENTRY_COUNT = 114
COMMAND_NAMES = {
    0xF0: "set_sequence",
    0xF1: "set_control",
    0xF2: "jump",
    0xF3: "call",
    0xF4: "return",
    0xF5: "begin_loop",
    0xF6: "end_loop",
    0xF7: "set_sweep",
    0xF8: "set_volume",
    0xF9: "stop",
}
VALUE_COMMANDS = {
    "set_sequence": 0xF0,
    "set_control": 0xF1,
    "begin_loop": 0xF5,
    "set_sweep": 0xF7,
    "set_volume": 0xF8,
}
POINTER_COMMAND_NAMES = {"jump": 0xF2, "call": 0xF3}
SIMPLE_COMMANDS = {"return": 0xF4, "end_loop": 0xF6, "stop": 0xF9}


class AudioEditorError(ValueError):
    """An invalid audio document or fixed audio-bank allocation."""


@dataclass(frozen=True)
class EncodedAudioDocument:
    timing: bytes
    envelope_pointers: bytes
    envelopes: bytes
    effect_pointers: bytes
    effects: bytes
    streams: bytes
    trailing: bytes


def stream_id(index: int) -> str:
    return f"stream_{index:03d}"


def byte_value(value: object, field: str) -> int:
    if not isinstance(value, int) or not 0 <= value <= 0xFF:
        raise AudioEditorError(f"{field} must be a byte")
    return value


def indexed_records(value: object, field: str, count: int) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != count:
        raise AudioEditorError(f"{field} must contain exactly {count} records")
    records: list[dict[str, Any]] = []
    identity = "number" if field == "effects" else "index"
    for index, record in enumerate(value):
        expected = index + 1 if identity == "number" else index
        if not isinstance(record, dict) or record.get(identity) != expected:
            raise AudioEditorError(f"{field} identity mismatch at record {index}")
        records.append(record)
    return records


def command_record(command: AudioCommand, labels: dict[int, str]) -> dict[str, Any]:
    opcode = command.opcode
    if opcode < 0x80:
        return {"kind": "note", "value": opcode}
    if opcode < 0xF0:
        return {"kind": "duration", "value": opcode}
    name = COMMAND_NAMES[opcode]
    if opcode in POINTER_COMMANDS:
        target = command.arguments[0] | (command.arguments[1] << 8)
        if target not in labels:
            raise AudioEditorError(f"unlabelled audio target ${target:04X}")
        return {"kind": name, "target": labels[target]}
    if command.arguments:
        return {"kind": name, "value": command.arguments[0]}
    return {"kind": name}


def profile_layout(profile: dict[str, Any]) -> AudioLayout:
    identifier = profile.get("id")
    if identifier not in AUDIO_LAYOUTS:
        raise AudioEditorError(f"profile {identifier!r} has no editable audio layout")
    return AUDIO_LAYOUTS[identifier]


def export_document(prg: bytes, profile: dict[str, Any]) -> dict[str, Any]:
    layout = profile_layout(profile)
    _, envelopes = decode_envelopes(prg, layout)
    _, effects = decode_sound_effects(prg, layout)
    streams = discover_streams(prg, effects, layout)
    labels = {
        stream.cpu_address: stream_id(index) for index, stream in enumerate(streams)
    }
    command_map = collect_command_map(streams)
    commands: list[dict[str, Any]] = []
    cursor = layout.stream_data
    while cursor <= layout.stream_end:
        command = command_map.get(cursor)
        if command is None:
            raise AudioEditorError(f"audio command coverage gap at ${cursor:04X}")
        record = command_record(command, labels)
        if cursor in labels:
            record["entry"] = labels[cursor]
        commands.append(record)
        cursor += 1 + len(command.arguments)

    timing_tail_start = layout.duration_table + layout.duration_count
    timing_tail = (
        list(
            cpu_slice(
                prg,
                timing_tail_start,
                layout.envelope_pointer_table - 1,
                "audio timing tail",
            )
        )
        if timing_tail_start < layout.envelope_pointer_table
        else []
    )
    trailing_start = layout.stream_end + 1
    trailing = (
        list(cpu_slice(prg, trailing_start, 0xFFF9, "audio trailing bytes"))
        if trailing_start < 0xFFFA
        else []
    )
    return {
        "schema_version": DOCUMENT_SCHEMA,
        "game": DOCUMENT_GAME,
        "source_profile": profile["id"],
        "source_rom_sha256": profile["rom"]["sha256"],
        "periods": decode_periods(prg, layout),
        "durations": decode_durations(prg, layout),
        "timing_tail": timing_tail,
        "envelopes": [
            {
                "index": index,
                "steps": [
                    {"duration": step.duration, "volume": step.volume}
                    for step in envelope
                ],
            }
            for index, envelope in enumerate(envelopes)
        ],
        "effects": [
            {
                "number": index + 1,
                "channels": [
                    {
                        "selector": channel.selector,
                        "stream": labels[channel.stream_address],
                    }
                    for channel in effect
                ],
            }
            for index, effect in enumerate(effects)
        ],
        "commands": commands,
        "trailing_bytes": trailing,
    }


def validate_header(value: object, profile: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AudioEditorError("audio document is not an object")
    if value.get("schema_version") != DOCUMENT_SCHEMA:
        raise AudioEditorError("unsupported audio document schema")
    if value.get("game") != DOCUMENT_GAME:
        raise AudioEditorError("audio document belongs to another game")
    if value.get("source_profile") != profile.get("id"):
        raise AudioEditorError("audio document profile does not match the build profile")
    if value.get("source_rom_sha256") != profile.get("rom", {}).get("sha256"):
        raise AudioEditorError("audio document source ROM identity differs")
    return value


def command_size(record: object) -> int:
    if not isinstance(record, dict):
        raise AudioEditorError("audio command is not an object")
    kind = record.get("kind")
    if kind in {"note", "duration"} or kind in SIMPLE_COMMANDS:
        return 1
    if kind in VALUE_COMMANDS:
        return 2
    if kind in POINTER_COMMAND_NAMES:
        return 3
    raise AudioEditorError(f"unknown audio command kind: {kind!r}")


def encode_commands(
    value: object,
    layout: AudioLayout,
) -> tuple[bytes, dict[str, int]]:
    if not isinstance(value, list) or not value:
        raise AudioEditorError("audio command list is empty")
    addresses: list[int] = []
    entries: dict[str, int] = {}
    cursor = layout.stream_data
    for record in value:
        size = command_size(record)
        addresses.append(cursor)
        entry = record.get("entry")
        if entry is not None:
            if not isinstance(entry, str) or entry in entries:
                raise AudioEditorError(f"invalid or duplicate stream entry: {entry!r}")
            entries[entry] = cursor
        cursor += size
    expected_entries = {stream_id(index) for index in range(STREAM_ENTRY_COUNT)}
    if set(entries) != expected_entries:
        raise AudioEditorError("audio stream entries must be contiguous stream_000..113")
    capacity = layout.stream_end - layout.stream_data + 1
    if cursor != layout.stream_end + 1:
        raise AudioEditorError(
            f"audio commands encode to {cursor - layout.stream_data}/{capacity} bytes"
        )

    output = bytearray()
    for index, record in enumerate(value):
        kind = record["kind"]
        if kind in {"note", "duration"}:
            token = byte_value(record.get("value"), f"command {index} value")
            valid = token < 0x80 if kind == "note" else 0x80 <= token < 0xF0
            if not valid:
                raise AudioEditorError(f"command {index} has invalid {kind} token")
            output.append(token)
        elif kind in VALUE_COMMANDS:
            output.extend(
                (
                    VALUE_COMMANDS[kind],
                    byte_value(record.get("value"), f"command {index} value"),
                )
            )
        elif kind in POINTER_COMMAND_NAMES:
            target = record.get("target")
            if not isinstance(target, str) or target not in entries:
                raise AudioEditorError(f"command {index} has unknown target {target!r}")
            output.append(POINTER_COMMAND_NAMES[kind])
            output.extend(entries[target].to_bytes(2, "little"))
        else:
            output.append(SIMPLE_COMMANDS[kind])
    if len(output) != capacity or addresses[-1] >= layout.stream_end + 1:
        raise AudioEditorError("audio command address calculation failed")
    return bytes(output), entries


def encode_document(
    value: object,
    profile: dict[str, Any],
) -> EncodedAudioDocument:
    document = validate_header(value, profile)
    layout = profile_layout(profile)
    periods = document.get("periods")
    if not isinstance(periods, list) or len(periods) != layout.period_count:
        raise AudioEditorError(f"periods must contain {layout.period_count} words")
    if any(not isinstance(period, int) or not 0 <= period <= 0xFFFF for period in periods):
        raise AudioEditorError("audio period is outside $0000..$FFFF")
    durations = document.get("durations")
    if not isinstance(durations, list) or len(durations) != layout.duration_count:
        raise AudioEditorError(f"durations must contain {layout.duration_count} bytes")
    duration_bytes = bytes(
        byte_value(duration, "duration") for duration in durations
    )
    timing_tail = document.get("timing_tail")
    tail_size = layout.envelope_pointer_table - (
        layout.duration_table + layout.duration_count
    )
    if not isinstance(timing_tail, list) or len(timing_tail) != tail_size:
        raise AudioEditorError(f"audio timing tail must contain {tail_size} bytes")
    timing = b"".join(period.to_bytes(2, "little") for period in periods)
    timing += duration_bytes + bytes(
        byte_value(item, "timing tail") for item in timing_tail
    )

    envelope_records = indexed_records(
        document.get("envelopes"), "envelopes", layout.envelope_count
    )
    envelope_data = bytearray()
    envelope_addresses: list[int] = []
    for index, envelope in enumerate(envelope_records):
        steps = envelope.get("steps")
        if not isinstance(steps, list) or not steps:
            raise AudioEditorError(f"envelope {index} has no steps")
        envelope_addresses.append(layout.envelope_data + len(envelope_data))
        for step in steps:
            if not isinstance(step, dict):
                raise AudioEditorError(f"envelope {index} step is not an object")
            envelope_data.extend(
                (
                    byte_value(step.get("duration"), "envelope duration"),
                    byte_value(step.get("volume"), "envelope volume"),
                )
            )
    envelope_capacity = layout.sound_effect_pointer_table - layout.envelope_data
    if len(envelope_data) != envelope_capacity:
        raise AudioEditorError(
            f"envelopes encode to {len(envelope_data)}/{envelope_capacity} bytes"
        )
    envelope_pointers = b"".join(
        address.to_bytes(2, "little") for address in envelope_addresses
    )

    stream_data, entries = encode_commands(document.get("commands"), layout)
    effect_records = indexed_records(
        document.get("effects"), "effects", layout.sound_effect_count
    )
    effect_data = bytearray()
    effect_addresses: list[int] = []
    for index, effect in enumerate(effect_records):
        channels = effect.get("channels")
        if not isinstance(channels, list) or not channels:
            raise AudioEditorError(f"effect {index + 1} has no channels")
        effect_addresses.append(layout.sound_effect_data + len(effect_data))
        for channel_index, channel in enumerate(channels):
            if not isinstance(channel, dict):
                raise AudioEditorError(f"effect {index + 1} channel is invalid")
            selector = byte_value(channel.get("selector"), "channel selector")
            if selector & 0x7F > 7:
                raise AudioEditorError("channel selector must address virtual channel 0..7")
            if (channel_index == 0) != bool(selector & 0x80):
                raise AudioEditorError(
                    "only the first channel selector in each effect may set bit 7"
                )
            target = channel.get("stream")
            if not isinstance(target, str) or target not in entries:
                raise AudioEditorError(f"unknown effect stream entry: {target!r}")
            effect_data.append(selector)
            effect_data.extend(entries[target].to_bytes(2, "little"))
    effect_capacity = layout.stream_data - 1 - layout.sound_effect_data
    if len(effect_data) != effect_capacity:
        raise AudioEditorError(
            f"effect descriptors encode to {len(effect_data)}/{effect_capacity} bytes"
        )
    effect_pointers = b"".join(
        address.to_bytes(2, "little") for address in effect_addresses
    )
    effect_data.append(0xFF)

    trailing = document.get("trailing_bytes")
    trailing_size = 0xFFFA - (layout.stream_end + 1)
    if not isinstance(trailing, list) or len(trailing) != trailing_size:
        raise AudioEditorError(f"audio trailing data must contain {trailing_size} bytes")
    trailing_data = bytes(byte_value(item, "trailing audio data") for item in trailing)
    return EncodedAudioDocument(
        timing,
        envelope_pointers,
        bytes(envelope_data),
        effect_pointers,
        bytes(effect_data),
        stream_data,
        trailing_data,
    )


def patch_cpu_range(prg: bytearray, address: int, data: bytes) -> None:
    offset = address - 0x8000
    if offset < 0 or offset + len(data) > len(prg):
        raise AudioEditorError(f"audio patch at ${address:04X} is outside PRG")
    prg[offset : offset + len(data)] = data


def build_audio_image(
    document: object,
    base_image: bytes,
    profile: dict[str, Any],
) -> bytes:
    encoded = encode_document(document, profile)
    if digest(base_image, "sha256") != profile["rom"]["sha256"]:
        raise AudioEditorError("base ROM does not match the audio profile")
    parsed = parse_ines(base_image)
    layout = profile_layout(profile)
    prg = bytearray(parsed["prg"])
    patch_cpu_range(prg, layout.period_table, encoded.timing)
    patch_cpu_range(prg, layout.envelope_pointer_table, encoded.envelope_pointers)
    patch_cpu_range(prg, layout.envelope_data, encoded.envelopes)
    patch_cpu_range(prg, layout.sound_effect_pointer_table, encoded.effect_pointers)
    patch_cpu_range(prg, layout.sound_effect_data, encoded.effects)
    patch_cpu_range(prg, layout.stream_data, encoded.streams)
    patch_cpu_range(prg, layout.stream_end + 1, encoded.trailing)
    return bytes(parsed["header"]) + bytes(prg) + bytes(parsed["chr"])


def canonical_document(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"))


def validate_rebuilt_document(
    document: dict[str, Any],
    image: bytes,
    profile: dict[str, Any],
) -> None:
    rebuilt = export_document(parse_ines(image)["prg"], profile)
    if canonical_document(rebuilt) != canonical_document(document):
        raise AudioEditorError("rebuilt ROM does not decode to the audio document")


def load_document(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AudioEditorError(f"cannot read audio document {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AudioEditorError("audio document is not an object")
    return value


def save_document(path: Path, document: dict[str, Any]) -> str:
    payload = (json.dumps(document, indent=2) + "\n").encode("utf-8")
    action = write_if_changed(path, payload)
    print(f"[{action}] audio document: {path}")
    return action


def document_summary(document: dict[str, Any]) -> str:
    commands = document["commands"]
    return (
        f"{len(document['effects'])} effects, {len(document['envelopes'])} envelopes, "
        f"{sum('entry' in command for command in commands)} stream entries, "
        f"{len(commands)} physical commands"
    )


def command_export(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    profile = get_profile(profiles, args.profile)
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    parsed = verify_reference(reference, profile)
    document = export_document(parsed["prg"], profile)
    save_document(args.output, document)
    print(f"[OK] {profile['id']}: {document_summary(document)}")


def command_validate(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    document = load_document(args.input)
    profile = get_profile(profiles, document.get("source_profile"))
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    verify_reference(reference, profile)
    image = build_audio_image(document, reference.read_bytes(), profile)
    validate_rebuilt_document(document, image, profile)
    print(f"[OK] valid {profile['id']} audio document: {document_summary(document)}")


def command_build(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    document = load_document(args.input)
    profile = get_profile(profiles, document.get("source_profile"))
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    verify_reference(reference, profile)
    image = build_audio_image(document, reference.read_bytes(), profile)
    validate_rebuilt_document(document, image, profile)
    action = write_if_changed(args.output, image)
    print(f"[{action}] audio ROM: {args.output}")


def command_roundtrip(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    profile = get_profile(profiles, args.profile)
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    parsed = verify_reference(reference, profile)
    document = export_document(parsed["prg"], profile)
    original = reference.read_bytes()
    rebuilt = build_audio_image(document, original, profile)
    validate_rebuilt_document(document, rebuilt, profile)
    if rebuilt != original:
        mismatch = next(
            index for index, pair in enumerate(zip(rebuilt, original)) if pair[0] != pair[1]
        )
        raise AudioEditorError(f"audio round trip differs at ROM offset ${mismatch:04X}")
    print(f"[OK] {profile['id']}: byte-identical audio round trip; {document_summary(document)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles", type=Path, default=ROOT / "config/revision_profiles.json")
    parser.add_argument("--private-root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    export = subparsers.add_parser("export")
    export.add_argument("--profile", required=True)
    export.add_argument("--base-rom", type=Path)
    export.add_argument("--output", required=True, type=Path)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--input", required=True, type=Path)
    validate.add_argument("--base-rom", type=Path)
    build = subparsers.add_parser("build")
    build.add_argument("--input", required=True, type=Path)
    build.add_argument("--base-rom", type=Path)
    build.add_argument("--output", required=True, type=Path)
    roundtrip = subparsers.add_parser("roundtrip")
    roundtrip.add_argument("--profile", required=True)
    roundtrip.add_argument("--base-rom", type=Path)
    summary = subparsers.add_parser("summary")
    summary.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    try:
        profiles = load_profiles(args.profiles)
        if args.command == "export":
            command_export(args, profiles)
        elif args.command == "validate":
            command_validate(args, profiles)
        elif args.command == "build":
            command_build(args, profiles)
        elif args.command == "roundtrip":
            command_roundtrip(args, profiles)
        else:
            document = load_document(args.input)
            print(document_summary(document))
    except (
        AudioEditorError,
        RoomDataError,
        ProjectError,
        OSError,
        KeyError,
        IndexError,
        json.JSONDecodeError,
    ) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
