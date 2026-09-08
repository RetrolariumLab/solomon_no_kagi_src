#!/usr/bin/env python3
"""Edit packed title graphics and the attract-demo controller program."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from scripts.build.project import ProjectError, digest, parse_ines, write_if_changed
from scripts.build.revision_profiles import (
    ROOT,
    get_profile,
    load_profiles,
    resolve_reference,
    verify_reference,
)
from scripts.authoring.room_data import RoomDataError
from scripts.authoring import title_data


DOCUMENT_SCHEMA = 1
DOCUMENT_GAME = "solomons-key-nes-presentation"


class PresentationEditorError(ValueError):
    """An invalid presentation document or fixed data allocation."""


def profile_manifest(profile: dict[str, Any]) -> dict[str, Any]:
    profile_id = profile.get("id")
    filename = title_data.TITLE_DATA_MANIFESTS.get(str(profile_id))
    if filename is None:
        raise PresentationEditorError(
            f"profile {profile_id!r} has no presentation manifest"
        )
    manifest = title_data.load_manifest(ROOT / "config" / "authoring" / filename)
    title_data.validate_manifest_profile(manifest, str(profile_id))
    return manifest


def integer(value: object, field: str) -> int:
    try:
        return title_data.parse_number(value, field)
    except RoomDataError as exc:
        raise PresentationEditorError(str(exc)) from exc


def stream_layout(manifest: dict[str, Any]) -> list[dict[str, object]]:
    return [
        {
            "name": declaration["name"],
            "address": integer(declaration["address"], "stream address"),
            "encoded_size": int(declaration["encoded_size"]),
        }
        for declaration in manifest["streams"]
    ]


def document_layout(manifest: dict[str, Any]) -> dict[str, object]:
    demo = manifest["demo_input"]
    return {
        "streams": stream_layout(manifest),
        "demo": {
            "duration_address": integer(
                demo["duration_address"], "demo duration address"
            ),
            "input_address": integer(demo["input_address"], "demo input address"),
            "step_count": int(demo["input_count"]),
        },
    }


def token_to_document(
    token: title_data.TitleCursorCommand | title_data.TitleLiteralRun,
) -> dict[str, object]:
    if isinstance(token, title_data.TitleLiteralRun):
        return {"kind": "literal", "tiles": list(token.tiles)}
    record: dict[str, object] = {"kind": token.kind}
    if token.value is not None:
        record["value"] = token.value
    return record


def export_document(image: bytes, profile: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_ines(image)
    prg = bytes(parsed["prg"])
    manifest = profile_manifest(profile)
    streams: list[dict[str, object]] = []
    for declaration in manifest["streams"]:
        name = str(declaration["name"])
        address = integer(declaration["address"], f"{name}.address")
        stream = title_data.decode_stream(prg, address)
        streams.append(
            {
                "name": name,
                "tokens": [token_to_document(token) for token in stream.tokens],
            }
        )
    demo = manifest["demo_input"]
    steps = title_data.decode_demo_input(
        prg,
        integer(demo["duration_address"], "demo duration address"),
        integer(demo["input_address"], "demo input address"),
        int(demo["input_count"]),
    )
    return {
        "schema_version": DOCUMENT_SCHEMA,
        "game": DOCUMENT_GAME,
        "source_profile": profile["id"],
        "source_rom_sha256": profile["rom"]["sha256"],
        "layout": document_layout(manifest),
        "streams": streams,
        "demo_steps": [
            {
                "index": step.index,
                "duration": step.duration,
                "buttons": list(step.buttons),
            }
            for step in steps
        ],
    }


def validate_header(
    document: object, profile: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise PresentationEditorError("presentation document is not an object")
    if document.get("schema_version") != DOCUMENT_SCHEMA:
        raise PresentationEditorError("unsupported presentation document schema")
    if document.get("game") != DOCUMENT_GAME:
        raise PresentationEditorError("presentation document belongs to another game")
    if document.get("source_profile") != profile.get("id"):
        raise PresentationEditorError("presentation document profile differs")
    if document.get("source_rom_sha256") != profile.get("rom", {}).get("sha256"):
        raise PresentationEditorError("presentation source ROM identity differs")
    if document.get("layout") != document_layout(manifest):
        raise PresentationEditorError("presentation fixed layout differs")
    return document


def token_from_document(value: object, field: str) -> object:
    if not isinstance(value, dict):
        raise PresentationEditorError(f"{field} is not an object")
    kind = value.get("kind")
    if kind == "literal":
        tiles = value.get("tiles")
        if not isinstance(tiles, list) or not tiles:
            raise PresentationEditorError(f"{field} literal run is empty")
        if any(not isinstance(tile, int) or not 0x80 <= tile <= 0xFF for tile in tiles):
            raise PresentationEditorError(
                f"{field} literal tiles must remain in $80-$FF"
            )
        return title_data.TitleLiteralRun(0, bytes(tiles))
    if kind not in {"set_column", "set_row", "add_row", "terminate"}:
        raise PresentationEditorError(f"{field} has unknown kind {kind!r}")
    command = title_data.TitleCursorCommand(str(kind), value.get("value"))
    try:
        title_data.encode_cursor_command(command)
    except RoomDataError as exc:
        raise PresentationEditorError(str(exc)) from exc
    return command


def encode_streams(
    document: object, profile: dict[str, Any], manifest: dict[str, Any]
) -> list[tuple[int, bytes]]:
    checked = validate_header(document, profile, manifest)
    records = checked.get("streams")
    declarations = manifest["streams"]
    if not isinstance(records, list) or len(records) != len(declarations):
        raise PresentationEditorError("presentation stream count differs")
    writes: list[tuple[int, bytes]] = []
    for index, (record, declaration) in enumerate(zip(records, declarations)):
        if not isinstance(record, dict) or record.get("name") != declaration["name"]:
            raise PresentationEditorError(f"presentation stream {index} identity differs")
        tokens = record.get("tokens")
        if not isinstance(tokens, list) or not tokens:
            raise PresentationEditorError(f"presentation stream {index} has no tokens")
        stream = title_data.TitlePackedStream(
            integer(declaration["address"], f"stream {index} address"),
            tuple(
                token_from_document(token, f"streams[{index}].tokens[{token_index}]")
                for token_index, token in enumerate(tokens)
            ),
            int(declaration["encoded_size"]),
        )
        try:
            payload = title_data.encode_stream(stream)
        except RoomDataError as exc:
            raise PresentationEditorError(str(exc)) from exc
        expected = int(declaration["encoded_size"])
        if len(payload) != expected:
            raise PresentationEditorError(
                f"{declaration['name']} must encode to exactly {expected} bytes, got {len(payload)}"
            )
        writes.append((title_data.prg_offset(stream.cpu_address), payload))
    return writes


def encode_demo(
    document: object, profile: dict[str, Any], manifest: dict[str, Any]
) -> list[tuple[int, bytes]]:
    checked = validate_header(document, profile, manifest)
    values = checked.get("demo_steps")
    count = int(manifest["demo_input"]["input_count"])
    if not isinstance(values, list) or len(values) != count:
        raise PresentationEditorError(f"demo_steps must contain exactly {count} records")
    steps: list[title_data.DemoInputStep] = []
    for index, value in enumerate(values):
        if not isinstance(value, dict) or value.get("index") != index:
            raise PresentationEditorError(f"demo_steps[{index}] has a non-contiguous index")
        duration = value.get("duration")
        buttons = value.get("buttons")
        if not isinstance(duration, int) or not 0 <= duration <= 0xFF:
            raise PresentationEditorError(f"demo_steps[{index}] duration is outside byte range")
        if not isinstance(buttons, list) or any(not isinstance(item, str) for item in buttons):
            raise PresentationEditorError(f"demo_steps[{index}] buttons are invalid")
        steps.append(title_data.DemoInputStep(index, duration, tuple(buttons)))
    try:
        durations, inputs = title_data.encode_demo_input(steps)
    except RoomDataError as exc:
        raise PresentationEditorError(str(exc)) from exc
    demo = manifest["demo_input"]
    return [
        (title_data.prg_offset(integer(demo["duration_address"], "demo durations")), durations),
        (title_data.prg_offset(integer(demo["input_address"], "demo inputs")), inputs),
    ]


def build_presentation_image(
    document: object, base_image: bytes, profile: dict[str, Any]
) -> bytes:
    if digest(base_image, "sha256") != profile["rom"]["sha256"]:
        raise PresentationEditorError("base ROM does not match the presentation profile")
    parsed = parse_ines(base_image)
    manifest = profile_manifest(profile)
    prg = bytearray(parsed["prg"])
    writes = encode_streams(document, profile, manifest) + encode_demo(
        document, profile, manifest
    )
    occupied: set[int] = set()
    for offset, payload in writes:
        target = set(range(offset, offset + len(payload)))
        if occupied & target or offset < 0 or offset + len(payload) > len(prg):
            raise PresentationEditorError("presentation writes overlap or exceed PRG")
        occupied.update(target)
        prg[offset : offset + len(payload)] = payload
    return bytes(parsed["header"]) + bytes(prg) + bytes(parsed["chr"])


def canonical_document(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"))


def validate_rebuilt_document(
    document: dict[str, Any], image: bytes, profile: dict[str, Any]
) -> None:
    rebuilt = export_document(image, profile)
    if canonical_document(rebuilt) != canonical_document(document):
        raise PresentationEditorError(
            "rebuilt ROM does not decode to the presentation document"
        )


def load_document(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PresentationEditorError(f"cannot read presentation document {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PresentationEditorError("presentation document is not an object")
    return value


def save_document(path: Path, document: dict[str, Any]) -> str:
    action = write_if_changed(
        path, (json.dumps(document, indent=2) + "\n").encode("utf-8")
    )
    print(f"[{action}] presentation document: {path}")
    return action


def document_summary(document: dict[str, Any]) -> str:
    streams = document.get("streams", [])
    literal_tiles = sum(
        len(token.get("tiles", []))
        for stream in streams
        for token in stream.get("tokens", [])
        if token.get("kind") == "literal"
    )
    return (
        f"{len(streams)} title streams, {literal_tiles} literal tiles, "
        f"{len(document.get('demo_steps', []))} demo steps"
    )


def command_export(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    profile = get_profile(profiles, args.profile)
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    verify_reference(reference, profile)
    document = export_document(reference.read_bytes(), profile)
    save_document(args.output, document)
    print(f"[OK] {profile['id']}: {document_summary(document)}")


def document_context(
    args: argparse.Namespace, profiles: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    document = load_document(args.input)
    profile = get_profile(profiles, document.get("source_profile"))
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    verify_reference(reference, profile)
    return document, profile, reference


def command_validate(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    document, profile, reference = document_context(args, profiles)
    image = build_presentation_image(document, reference.read_bytes(), profile)
    validate_rebuilt_document(document, image, profile)
    print(f"[OK] valid {profile['id']} presentation: {document_summary(document)}")


def command_build(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    document, profile, reference = document_context(args, profiles)
    image = build_presentation_image(document, reference.read_bytes(), profile)
    validate_rebuilt_document(document, image, profile)
    action = write_if_changed(args.output, image)
    print(f"[{action}] presentation ROM: {args.output}")


def command_roundtrip(args: argparse.Namespace, profiles: dict[str, Any]) -> None:
    profile = get_profile(profiles, args.profile)
    reference = resolve_reference(profile, args.private_root, args.base_rom)
    verify_reference(reference, profile)
    original = reference.read_bytes()
    document = export_document(original, profile)
    rebuilt = build_presentation_image(document, original, profile)
    validate_rebuilt_document(document, rebuilt, profile)
    if rebuilt != original:
        mismatch = next(
            index
            for index, (actual, expected) in enumerate(zip(rebuilt, original))
            if actual != expected
        )
        raise PresentationEditorError(
            f"presentation round trip differs at ROM offset ${mismatch:04X}"
        )
    print(
        f"[OK] {profile['id']}: byte-identical presentation round trip; "
        f"{document_summary(document)}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profiles", type=Path, default=ROOT / "config" / "revision_profiles.json"
    )
    parser.add_argument("--private-root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("--profile", required=True)
    export.add_argument("--output", required=True, type=Path)
    export.add_argument("--base-rom", type=Path)
    for name in ("validate", "build"):
        command = commands.add_parser(name)
        command.add_argument("--input", required=True, type=Path)
        command.add_argument("--base-rom", type=Path)
        if name == "build":
            command.add_argument("--output", required=True, type=Path)
    roundtrip = commands.add_parser("roundtrip")
    roundtrip.add_argument("--profile", required=True)
    roundtrip.add_argument("--base-rom", type=Path)
    summary = commands.add_parser("summary")
    summary.add_argument("--input", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
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
            print(document_summary(load_document(args.input)))
    except (
        PresentationEditorError,
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
