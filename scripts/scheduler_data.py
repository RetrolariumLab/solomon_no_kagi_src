#!/usr/bin/env python3
"""Decode and audit Solomon's Key cooperative-scheduler tables."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .room_data import RoomDataError, extract_prg
except ImportError:
    from room_data import RoomDataError, extract_prg


INITIAL_STACK_POINTERS = 0x8E01
THREAD_ENTRY_TABLE_BASES = 0x8E09
THREAD_COUNT = 8
SCHEDULER_MANIFESTS = {
    "usa": "scheduler_entries.json",
    "europe": "scheduler_entries_europe.json",
}
START_CALL_RE = re.compile(r"^\s*(?:JSR|JMP)\s+StartThread\s*$")
IMMEDIATE_A_RE = re.compile(
    r"^\s*LDA\s+#(?:\$([0-9A-Fa-f]{1,2})|([A-Za-z_][A-Za-z0-9_]*))\s*$"
)
NUMERIC_CONSTANT_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\$[0-9A-Fa-f]+|%[01]+|[0-9]+)\s*$"
)
LABEL_RE = re.compile(r"^[A-Za-z_@.?][A-Za-z0-9_@.?]*:\s*$")


def prg_offset(cpu_address: int) -> int:
    if not 0x8000 <= cpu_address <= 0xFFFF:
        raise RoomDataError(f"CPU address outside PRG: ${cpu_address:04X}")
    return cpu_address - 0x8000


def read_word(prg: bytes, cpu_address: int) -> int:
    offset = prg_offset(cpu_address)
    if offset + 1 >= len(prg):
        raise RoomDataError(f"truncated word at ${cpu_address:04X}")
    return prg[offset] | (prg[offset + 1] << 8)


def decode_thread_code(
    prg: bytes,
    code: int,
    table_bases_address: int = THREAD_ENTRY_TABLE_BASES,
) -> dict[str, int]:
    if not 0 <= code <= 0xFF:
        raise RoomDataError(f"thread code outside byte range: {code}")
    context = code >> 4
    selector = code & 0x0F
    if context >= THREAD_COUNT:
        raise RoomDataError(f"thread code selects invalid context: ${code:02X}")
    base = read_word(prg, table_bases_address + context * 2)
    pointer_address = base + selector * 2
    return_address = read_word(prg, pointer_address)
    return {
        "code": code,
        "context": context,
        "selector": selector,
        "base": base,
        "pointer_address": pointer_address,
        "return_address": return_address,
        "entry": (return_address + 1) & 0xFFFF,
    }


def assembly_paths(project_root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in (project_root / "src").rglob("*")
            if path.is_file() and path.suffix.lower() in {".asm", ".inc"}
        ),
        key=lambda path: path.as_posix().lower(),
    )


def numeric_constants(paths: list[Path]) -> dict[str, int]:
    constants: dict[str, int] = {}
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            match = NUMERIC_CONSTANT_RE.match(line)
            if match is None:
                continue
            name, encoded = match.groups()
            if encoded.startswith("$"):
                value = int(encoded[1:], 16)
            elif encoded.startswith("%"):
                value = int(encoded[1:], 2)
            else:
                value = int(encoded, 10)
            previous = constants.get(name)
            if previous is not None and previous != value:
                raise RoomDataError(
                    f"conflicting numeric constant {name}: ${previous:X} and ${value:X}"
                )
            constants[name] = value
    return constants


def discover_start_calls(project_root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    static: list[dict[str, object]] = []
    dynamic: list[dict[str, object]] = []
    paths = assembly_paths(project_root)
    constants = numeric_constants(paths)
    for path in paths:
        lines = path.read_text(encoding="utf-8").splitlines()
        relative = path.relative_to(project_root).as_posix()
        for index, line in enumerate(lines):
            if START_CALL_RE.match(line) is None:
                continue
            previous_index = index - 1
            while previous_index >= 0 and (
                not lines[previous_index].strip()
                or lines[previous_index].lstrip().startswith(";")
                or LABEL_RE.match(lines[previous_index]) is not None
            ):
                previous_index -= 1
            immediate = (
                IMMEDIATE_A_RE.match(lines[previous_index])
                if previous_index >= 0
                else None
            )
            record: dict[str, object] = {"path": relative, "line": index + 1}
            code: int | None = None
            if immediate is not None:
                hexadecimal, name = immediate.groups()
                if hexadecimal is not None:
                    code = int(hexadecimal, 16)
                elif name in constants:
                    code = constants[name]
            if code is None or not 0 <= code <= 0xFF:
                dynamic.append(record)
            else:
                record["code"] = code
                static.append(record)
    return static, dynamic


def collect_report(
    project_root: Path,
    prg: bytes,
    initial_stack_pointer_address: int = INITIAL_STACK_POINTERS,
    table_bases_address: int = THREAD_ENTRY_TABLE_BASES,
) -> dict[str, object]:
    table_offset = prg_offset(initial_stack_pointer_address)
    stack_pointers = list(prg[table_offset : table_offset + THREAD_COUNT])
    static_calls, dynamic_calls = discover_start_calls(project_root)
    codes = sorted({int(call["code"]) for call in static_calls})
    return {
        "initial_stack_pointer_address": initial_stack_pointer_address,
        "thread_entry_table_bases_address": table_bases_address,
        "initial_stack_pointers": stack_pointers,
        "static_call_count": len(static_calls),
        "dynamic_call_count": len(dynamic_calls),
        "static_codes": codes,
        "entries": [
            decode_thread_code(prg, code, table_bases_address) for code in codes
        ],
        "dynamic_calls": dynamic_calls,
    }


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RoomDataError("unsupported scheduler manifest schema")
    return value


def validate_manifest_profile(manifest: dict[str, Any], profile: str) -> None:
    actual = manifest.get("profile", "usa")
    if actual != profile:
        raise RoomDataError(
            f"scheduler profile mismatch: expected={profile}, manifest={actual}"
        )


def manifest_address(manifest: dict[str, Any], field: str, default: int) -> int:
    value = manifest.get(field, default)
    try:
        address = int(str(value), 0)
    except (TypeError, ValueError) as exc:
        raise RoomDataError(f"invalid scheduler {field}: {value!r}") from exc
    prg_offset(address)
    return address


def compare_entry(
    actual: dict[str, int],
    expected: dict[str, Any],
    description: str,
) -> list[str]:
    errors: list[str] = []
    code = int(str(expected.get("code")), 0)
    for field in (
        "context",
        "selector",
        "base",
        "pointer_address",
        "return_address",
        "entry",
    ):
        expected_value = int(str(expected.get(field)), 0)
        if actual[field] != expected_value:
            errors.append(
                f"{description} ${code:02X} {field} differs: "
                f"got ${actual[field]:X}, expected ${expected_value:X}"
            )
    return errors


def validate_context_roles(
    manifest: dict[str, Any],
    known_codes: set[int],
) -> list[str]:
    roles = manifest.get("context_roles")
    if roles is None:
        return []
    if not isinstance(roles, list):
        return ["context_roles must be a list"]

    errors: list[str] = []
    seen_contexts: set[int] = set()
    listed_codes: set[int] = set()
    for index, record in enumerate(roles):
        if not isinstance(record, dict):
            errors.append(f"context_roles[{index}] must be an object")
            continue
        try:
            context = int(str(record.get("context")), 0)
        except (TypeError, ValueError):
            errors.append(f"context_roles[{index}] has an invalid context")
            continue
        if not 0 <= context < THREAD_COUNT:
            errors.append(f"scheduler context outside range: {context}")
            continue
        if context in seen_contexts:
            errors.append(f"duplicate scheduler context role: {context}")
            continue
        seen_contexts.add(context)

        role = record.get("role")
        if not isinstance(role, str) or not role.strip():
            errors.append(f"scheduler context {context} must have a role")

        entry_codes = record.get("entry_codes")
        if not isinstance(entry_codes, list):
            errors.append(f"scheduler context {context} entry_codes must be a list")
            continue
        for encoded_code in entry_codes:
            try:
                code = int(str(encoded_code), 0)
            except (TypeError, ValueError):
                errors.append(
                    f"scheduler context {context} has an invalid entry code"
                )
                continue
            if code >> 4 != context:
                errors.append(
                    f"scheduler code ${code:02X} is listed under context {context}"
                )
            if code in listed_codes:
                errors.append(f"duplicate scheduler context entry code: ${code:02X}")
            listed_codes.add(code)

    missing_contexts = set(range(THREAD_COUNT)) - seen_contexts
    if missing_contexts:
        errors.append(
            "scheduler contexts missing roles: "
            + ", ".join(str(context) for context in sorted(missing_contexts))
        )
    extra_contexts = seen_contexts - set(range(THREAD_COUNT))
    if extra_contexts:
        errors.append(
            "unexpected scheduler context roles: "
            + ", ".join(str(context) for context in sorted(extra_contexts))
        )

    missing_codes = known_codes - listed_codes
    if missing_codes:
        errors.append(
            "known scheduler codes missing context roles: "
            + ", ".join(f"${code:02X}" for code in sorted(missing_codes))
        )
    extra_codes = listed_codes - known_codes
    if extra_codes:
        errors.append(
            "context roles contain unknown scheduler codes: "
            + ", ".join(f"${code:02X}" for code in sorted(extra_codes))
        )
    return errors


def validate_report(
    report: dict[str, object],
    manifest: dict[str, Any],
    prg: bytes | None = None,
) -> list[str]:
    errors: list[str] = []
    expected_stacks = manifest.get("initial_stack_pointers")
    if report["initial_stack_pointers"] != expected_stacks:
        errors.append(
            f"initial stack pointers differ: got {report['initial_stack_pointers']}, "
            f"expected {expected_stacks}"
        )
    expected_entries = manifest.get("static_entries")
    if not isinstance(expected_entries, list):
        return errors + ["static_entries must be a list"]
    actual_entries = {entry["code"]: entry for entry in report["entries"]}
    expected_codes: set[int] = set()
    for expected in expected_entries:
        code = int(str(expected.get("code")), 0)
        expected_codes.add(code)
        actual = actual_entries.get(code)
        if actual is None:
            errors.append(f"expected static thread code is absent from source: ${code:02X}")
            continue
        errors.extend(compare_entry(actual, expected, "thread code"))
    extra_codes = set(actual_entries) - expected_codes
    if extra_codes:
        errors.append(
            "unregistered static thread codes: "
            + ", ".join(f"${code:02X}" for code in sorted(extra_codes))
        )
    expected_dynamic = int(manifest.get("dynamic_call_count", -1))
    expected_static = int(manifest.get("static_call_count", -1))
    if report["static_call_count"] != expected_static:
        errors.append(
            f"immediate StartThread call count differs: got {report['static_call_count']}, "
            f"expected {expected_static}"
        )
    if report["dynamic_call_count"] != expected_dynamic:
        errors.append(
            f"dynamic StartThread call count differs: got {report['dynamic_call_count']}, "
            f"expected {expected_dynamic}"
        )
    reviewed_entries = manifest.get("reviewed_dynamic_entries", [])
    reviewed_codes: set[int] = set()
    if not isinstance(reviewed_entries, list):
        errors.append("reviewed_dynamic_entries must be a list")
    elif reviewed_entries and prg is None:
        errors.append("PRG is required to validate reviewed dynamic entries")
    elif prg is not None:
        for expected in reviewed_entries:
            code = int(str(expected.get("code")), 0)
            if code in reviewed_codes:
                errors.append(f"duplicate reviewed dynamic thread code: ${code:02X}")
                continue
            reviewed_codes.add(code)
            try:
                table_bases_address = int(
                    report.get(
                        "thread_entry_table_bases_address", THREAD_ENTRY_TABLE_BASES
                    )
                )
                actual = decode_thread_code(prg, code, table_bases_address)
            except RoomDataError as exc:
                errors.append(f"cannot decode reviewed dynamic thread code ${code:02X}: {exc}")
                continue
            errors.extend(compare_entry(actual, expected, "reviewed dynamic thread code"))
    errors.extend(validate_context_roles(manifest, expected_codes | reviewed_codes))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "audit"))
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--profile", choices=tuple(SCHEDULER_MANIFESTS), default="usa"
    )
    args = parser.parse_args()
    root = args.project_root.resolve()
    try:
        manifest_path = args.manifest or (
            root / "config" / SCHEDULER_MANIFESTS[args.profile]
        )
        manifest = load_manifest(manifest_path)
        validate_manifest_profile(manifest, args.profile)
        initial_stack_pointer_address = manifest_address(
            manifest, "initial_stack_pointer_address", INITIAL_STACK_POINTERS
        )
        table_bases_address = manifest_address(
            manifest, "thread_entry_table_bases_address", THREAD_ENTRY_TABLE_BASES
        )
        prg = extract_prg(args.image.read_bytes())
        report = collect_report(
            root, prg, initial_stack_pointer_address, table_bases_address
        )
        if args.command == "report":
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0
        errors = validate_report(report, manifest, prg)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, RoomDataError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        print(f"[FAIL] Scheduler data audit found {len(errors)} error(s)", file=sys.stderr)
        return 1
    reviewed_count = len(manifest.get("reviewed_dynamic_entries", []))
    reviewed_noun = "entry" if reviewed_count == 1 else "entries"
    context_role_count = len(manifest.get("context_roles", []))
    context_noun = "role" if context_role_count == 1 else "roles"
    print(
        f"[OK] Scheduler tables: {len(report['entries'])} static codes, "
        f"{report['static_call_count']} immediate calls, "
        f"{report['dynamic_call_count']} dynamic calls, "
        f"{reviewed_count} reviewed dynamic {reviewed_noun}, "
        f"{context_role_count} context {context_noun}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
