#!/usr/bin/env python3
"""Capture and validate deterministic FCEUX runtime scenarios."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


REQUIRED_COLUMNS = {
    "frame",
    "event",
    "detail",
    "thread",
    "room",
    "timer",
    "dana_y",
    "dana_x",
    "active_enemies",
    "remaining_lives",
}
BUTTONS = frozenset({"a", "b", "select", "start", "up", "down", "left", "right"})


class RuntimeError(ValueError):
    """A runtime scenario or trace validation error."""


def sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_scenarios(path: Path) -> dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read {path}: {exc}") from exc
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise RuntimeError(f"unsupported runtime scenario schema: {path}")
    profile = document.get("profile")
    if profile is not None and (not isinstance(profile, str) or not profile):
        raise RuntimeError(f"invalid runtime profile in {path}: {profile!r}")
    scenarios = document.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise RuntimeError("runtime scenarios must be a non-empty list")
    identifiers: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise RuntimeError("runtime scenario must be an object")
        identifier = scenario.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in identifiers:
            raise RuntimeError(f"invalid or duplicate runtime scenario id: {identifier!r}")
        identifiers.add(identifier)
        max_frames = scenario.get("max_frames")
        if not isinstance(max_frames, int) or max_frames <= 0:
            raise RuntimeError(f"invalid max_frames for {identifier}")
        validate_inputs(scenario)
        validate_patches(scenario)
    return document


def validate_manifest_profile(
    document: dict[str, object], expected_profile: str | None
) -> None:
    """Bind regional traces explicitly while preserving the legacy USA manifest."""
    if expected_profile is None:
        return
    actual_profile = document.get("profile", "usa")
    if actual_profile != expected_profile:
        raise RuntimeError(
            f"runtime profile mismatch: expected={expected_profile}, "
            f"manifest={actual_profile}"
        )


def validate_inputs(scenario: dict[str, object]) -> None:
    inputs = scenario.get("inputs")
    if not isinstance(inputs, list):
        raise RuntimeError(f"inputs must be a list for {scenario.get('id')}")
    max_frames = int(scenario["max_frames"])
    previous_end = -1
    for input_range in inputs:
        if not isinstance(input_range, dict):
            raise RuntimeError(f"invalid input range for {scenario.get('id')}")
        first = input_range.get("start_frame")
        last = input_range.get("end_frame")
        buttons = input_range.get("buttons")
        if (
            not isinstance(first, int)
            or not isinstance(last, int)
            or first < 0
            or first > last
            or last >= max_frames
            or first <= previous_end
        ):
            raise RuntimeError(f"invalid or overlapping input frames for {scenario.get('id')}")
        if (
            not isinstance(buttons, list)
            or not buttons
            or not all(isinstance(button, str) and button in BUTTONS for button in buttons)
        ):
            raise RuntimeError(f"invalid buttons for {scenario.get('id')}")
        previous_end = last


def parse_byte(value: object, field: str) -> int:
    try:
        parsed = int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"invalid byte for {field}: {value!r}") from exc
    if not 0 <= parsed <= 0xFF:
        raise RuntimeError(f"byte outside range for {field}: {value!r}")
    return parsed


def validate_patches(scenario: dict[str, object]) -> None:
    patches = scenario.get("patches")
    if not isinstance(patches, list):
        raise RuntimeError(f"patches must be a list for {scenario.get('id')}")
    previous_frame = -1
    for patch in patches:
        if not isinstance(patch, dict):
            raise RuntimeError(f"invalid patch for {scenario.get('id')}")
        frame = patch.get("frame")
        symbol = patch.get("symbol")
        offset = patch.get("offset", 0)
        operation = patch.get("operation", "set")
        reason = patch.get("reason")
        expected_detail = patch.get("expected_detail")
        if (
            not isinstance(frame, int)
            or frame < previous_frame
            or frame >= int(scenario["max_frames"])
        ):
            raise RuntimeError(f"invalid patch frame for {scenario.get('id')}")
        if not isinstance(symbol, str) or not symbol:
            raise RuntimeError(f"invalid patch symbol for {scenario.get('id')}")
        if not isinstance(offset, int) or not 0 <= offset <= 0x7FF:
            raise RuntimeError(f"invalid patch offset for {scenario.get('id')}")
        if operation not in {"set", "or"}:
            raise RuntimeError(f"invalid patch operation for {scenario.get('id')}")
        if not isinstance(reason, str) or not reason or ":" in reason or ";" in reason:
            raise RuntimeError(f"invalid patch reason for {scenario.get('id')}")
        if (
            not isinstance(expected_detail, str)
            or not expected_detail.endswith(f":{reason}")
        ):
            raise RuntimeError(f"invalid expected patch detail for {scenario.get('id')}")
        parse_byte(patch.get("value"), f"{scenario.get('id')}.{reason}")
        previous_frame = frame


def encode_inputs(scenario: dict[str, object]) -> str:
    encoded: list[str] = []
    for input_range in scenario["inputs"]:  # type: ignore[index]
        encoded.append(
            f"{input_range['start_frame']}-{input_range['end_frame']}:"
            + "+".join(input_range["buttons"])
        )
    return ";".join(encoded)


def encode_patches(scenario: dict[str, object]) -> str:
    encoded: list[str] = []
    for patch in scenario["patches"]:  # type: ignore[index]
        encoded.append(
            f"{patch['frame']},{patch['symbol']},{patch.get('offset', 0)},"
            f"{patch.get('operation', 'set')},{parse_byte(patch['value'], 'patch')},"
            f"{patch['reason']}"
        )
    return ";".join(encoded)


def load_trace(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
    except OSError as exc:
        raise RuntimeError(f"cannot read runtime trace {path}: {exc}") from exc
    if not rows or not REQUIRED_COLUMNS.issubset(rows[0]):
        raise RuntimeError(f"trace is empty or uses an obsolete schema: {path}")
    if rows[0]["event"] != "trace_start" or rows[-1]["event"] != "trace_end":
        raise RuntimeError(f"trace did not complete cleanly: {path}")
    frames = [int(row["frame"]) for row in rows]
    if frames != sorted(frames):
        raise RuntimeError(f"trace frames are not monotonic: {path}")
    return rows


def first_events(rows: list[dict[str, str]]) -> dict[str, int]:
    events: dict[str, int] = {}
    for row in rows:
        events.setdefault(row["event"], int(row["frame"]))
    return events


def validate_trace(scenario: dict[str, object], rows: list[dict[str, str]]) -> None:
    identifier = str(scenario["id"])
    if rows[0]["detail"] != identifier or rows[-1]["detail"] != identifier:
        raise RuntimeError(f"trace scenario identity mismatch: {identifier}")
    expected_events = scenario.get("expected_events")
    if not isinstance(expected_events, dict) or not expected_events:
        raise RuntimeError(f"scenario has no expected_events: {identifier}")
    observed = first_events(rows)
    declared_patches = [
        str(patch["expected_detail"])
        for patch in scenario["patches"]  # type: ignore[index]
    ]
    observed_patches = [
        row["detail"] for row in rows if row["event"] == "controlled_patch"
    ]
    if observed_patches != declared_patches:
        raise RuntimeError(
            f"controlled patch scope differs for {identifier}: "
            f"expected={declared_patches}, observed={observed_patches}"
        )
    for event, expected_frame in expected_events.items():
        if observed.get(str(event)) != expected_frame:
            raise RuntimeError(
                f"unexpected {event} frame for {identifier}: "
                f"expected={expected_frame}, observed={observed.get(str(event))}"
            )
    expected_details = scenario.get("expected_event_details", {})
    if not isinstance(expected_details, dict):
        raise RuntimeError(f"expected_event_details must be an object for {identifier}")
    observed_details: dict[str, str] = {}
    for row in rows:
        observed_details.setdefault(row["event"], row["detail"])
    for event, expected_detail in expected_details.items():
        if observed_details.get(str(event)) != expected_detail:
            raise RuntimeError(
                f"unexpected {event} detail for {identifier}: "
                f"expected={expected_detail}, observed={observed_details.get(str(event))}"
            )
    expected_series = scenario.get("expected_event_series", {})
    if not isinstance(expected_series, dict):
        raise RuntimeError(f"expected_event_series must be an object for {identifier}")
    for event, expected_values in expected_series.items():
        if not isinstance(expected_values, list) or not all(
            isinstance(value, str) for value in expected_values
        ):
            raise RuntimeError(f"invalid {event} event series for {identifier}")
        observed_values = [
            f"{row['frame']}:{row['detail']}"
            for row in rows
            if row["event"] == event
        ]
        if observed_values != expected_values:
            raise RuntimeError(
                f"unexpected {event} series for {identifier}: "
                f"expected={expected_values}, observed={observed_values}"
            )
    forbidden = scenario.get("forbidden_events", [])
    if not isinstance(forbidden, list):
        raise RuntimeError(f"forbidden_events must be a list for {identifier}")
    present = sorted(set(map(str, forbidden)) & observed.keys())
    if present:
        raise RuntimeError(f"forbidden events in {identifier}: {', '.join(present)}")
    expected_final = scenario.get("expected_final", {})
    if not isinstance(expected_final, dict):
        raise RuntimeError(f"expected_final must be an object for {identifier}")
    final = rows[-1]
    for field, expected in expected_final.items():
        if final.get(str(field)) != expected:
            raise RuntimeError(
                f"unexpected final {field} for {identifier}: "
                f"expected={expected}, observed={final.get(str(field))}"
            )


def command_trace(args: argparse.Namespace, document: dict[str, object]) -> None:
    required = (args.fceux, args.rom, args.lua)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("missing runtime input: " + ", ".join(missing))
    expected_sha1 = document.get("rom_sha1")
    actual_sha1 = sha1(args.rom)
    if actual_sha1 != expected_sha1:
        raise RuntimeError(
            f"runtime ROM SHA-1 mismatch: expected={expected_sha1}, actual={actual_sha1}"
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for scenario in document["scenarios"]:  # type: ignore[index]
        output = args.output_dir / f"{scenario['id']}.csv"
        output.unlink(missing_ok=True)
        environment = os.environ.copy()
        environment.update(
            SOLOMON_RUNTIME_TRACE=output.resolve().as_posix(),
            SOLOMON_RUNTIME_SCENARIO=str(scenario["id"]),
            SOLOMON_RUNTIME_MAX_FRAMES=str(scenario["max_frames"]),
            SOLOMON_RUNTIME_INPUTS=encode_inputs(scenario),
            SOLOMON_RUNTIME_PATCHES=encode_patches(scenario),
        )
        command = [
            str(args.fceux.resolve()),
            "-lua",
            str(args.lua.resolve()),
            "-max-frames",
            str(int(scenario["max_frames"]) + 2),
            "-turbo",
            "1",
            "-nothrottle",
            "1",
            str(args.rom.resolve()),
        ]
        print(f"[RUN] {scenario['id']}: {scenario['method']}", flush=True)
        subprocess.run(command, check=True, env=environment, cwd=args.rom.parent)
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"runtime trace was not created: {output}")
        print(f"[OK] runtime trace: {output}")


def command_validate(args: argparse.Namespace, document: dict[str, object]) -> None:
    for scenario in document["scenarios"]:  # type: ignore[index]
        rows = load_trace(args.trace_dir / f"{scenario['id']}.csv")
        validate_trace(scenario, rows)
        print(f"[OK] {scenario['id']}: {scenario['method']}")
    print(f"[OK] all {len(document['scenarios'])} runtime scenarios passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    trace = subparsers.add_parser("trace")
    trace.add_argument("--fceux", required=True, type=Path)
    trace.add_argument("--rom", required=True, type=Path)
    trace.add_argument("--lua", required=True, type=Path)
    trace.add_argument("--scenarios", required=True, type=Path)
    trace.add_argument("--output-dir", required=True, type=Path)
    trace.add_argument("--profile")
    validate = subparsers.add_parser("validate")
    validate.add_argument("--scenarios", required=True, type=Path)
    validate.add_argument("--trace-dir", required=True, type=Path)
    validate.add_argument("--profile")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        document = load_scenarios(args.scenarios)
        validate_manifest_profile(document, args.profile)
        if args.command == "trace":
            command_trace(args, document)
        else:
            command_validate(args, document)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
