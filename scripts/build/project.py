#!/usr/bin/env python3
"""Build-support commands for the Solomon's Key preservation project."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shlex
import shutil
import subprocess
import sys
import zlib

from scripts.build.atomic_io import atomic_write_bytes


ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


class ProjectError(ValueError):
    """A validation error that should be shown without a traceback."""


def digest(data: bytes, algorithm: str = "sha1") -> str:
    return hashlib.new(algorithm, data).hexdigest()


def crc32(data: bytes) -> str:
    return f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"


def parse_number(value: object, field: str) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    raise ProjectError(f"invalid integer for {field}: {value!r}")


def load_manifest(path: Path) -> dict[str, object]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectError(f"cannot read manifest {path}: {exc}") from exc
    if manifest.get("schema_version") != 1:
        raise ProjectError("unsupported manifest schema")
    return manifest


def parse_ines(data: bytes) -> dict[str, object]:
    if len(data) < 16 or data[:4] != b"NES\x1a":
        raise ProjectError("image is not an iNES ROM")
    trainer_size = 512 if data[6] & 0x04 else 0
    prg_size = data[4] * 16_384
    chr_size = data[5] * 8_192
    prg_start = 16 + trainer_size
    chr_start = prg_start + prg_size
    expected_size = chr_start + chr_size
    if len(data) != expected_size:
        raise ProjectError(
            f"image size is {len(data)}, expected exactly {expected_size}"
        )
    return {
        "header": data[:prg_start],
        "prg": data[prg_start:chr_start],
        "chr": data[chr_start:],
        "payload": data[prg_start:],
        "trainer_size": trainer_size,
        "prg_size": prg_size,
        "chr_size": chr_size,
        "mapper": (data[6] >> 4) | (data[7] & 0xF0),
        "mirroring": "vertical" if data[6] & 0x01 else "horizontal",
    }


def validate_image(data: bytes, manifest: dict[str, object]) -> dict[str, object]:
    reference = manifest.get("reference_rom")
    if not isinstance(reference, dict):
        raise ProjectError("manifest has no reference_rom object")
    parsed = parse_ines(data)
    checks = {
        "file_size": len(data),
        "file_sha1": digest(data),
        "file_sha256": digest(data, "sha256"),
        "file_md5": digest(data, "md5"),
        "file_crc32": crc32(data),
        "payload_sha1": digest(parsed["payload"]),
        "payload_sha256": digest(parsed["payload"], "sha256"),
        "payload_crc32": crc32(parsed["payload"]),
        "header_sha1": digest(parsed["header"]),
        "header_sha256": digest(parsed["header"], "sha256"),
        "prg_sha1": digest(parsed["prg"]),
        "prg_sha256": digest(parsed["prg"], "sha256"),
        "prg_crc32": crc32(parsed["prg"]),
        "chr_sha1": digest(parsed["chr"]),
        "chr_sha256": digest(parsed["chr"], "sha256"),
        "chr_crc32": crc32(parsed["chr"]),
        "trainer_size": parsed["trainer_size"],
        "prg_size": parsed["prg_size"],
        "chr_size": parsed["chr_size"],
        "mapper": parsed["mapper"],
        "mirroring": parsed["mirroring"],
    }
    for field, actual in checks.items():
        expected = reference.get(field)
        if isinstance(actual, int):
            expected = parse_number(expected, field)
        elif isinstance(expected, str):
            expected = expected.lower()
        if actual != expected:
            raise ProjectError(
                f"{field} mismatch: got {actual!r}, expected {expected!r}"
            )
    return parsed


def safe_asset_path(root: Path, relative: str) -> Path:
    posix = PurePosixPath(relative)
    if posix.is_absolute() or not posix.parts or ".." in posix.parts:
        raise ProjectError(f"unsafe asset path: {relative!r}")
    destination = root.joinpath(*posix.parts)
    try:
        destination.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ProjectError(f"asset path escapes output directory: {relative!r}") from exc
    return destination


def write_if_changed(path: Path, data: bytes) -> str:
    if path.is_file() and path.read_bytes() == data:
        return "OK"
    atomic_write_bytes(path, data)
    return "WRITE"


def command_verify(args: argparse.Namespace) -> None:
    image = Path(args.image)
    if not image.is_file():
        raise ProjectError(f"image not found: {image}")
    manifest = load_manifest(Path(args.manifest))
    validate_image(image.read_bytes(), manifest)
    print(f"[OK] byte-identical Solomon's Key image: {image}")


def command_split(args: argparse.Namespace) -> None:
    image = Path(args.image)
    if not image.is_file():
        raise ProjectError(f"reference ROM not found: {image}")
    manifest = load_manifest(Path(args.manifest))
    parsed = validate_image(image.read_bytes(), manifest)
    assets = manifest.get("extracted_assets")
    if not isinstance(assets, list):
        raise ProjectError("manifest has no extracted_assets list")
    output_root = Path(args.output_dir)
    for entry in assets:
        if not isinstance(entry, dict):
            raise ProjectError("invalid asset entry")
        region = str(entry.get("region", ""))
        if region not in ("header", "prg", "chr"):
            raise ProjectError(f"unsupported asset region: {region!r}")
        payload = parsed[region]
        expected_size = parse_number(entry.get("size"), f"{region}.size")
        expected_sha1 = str(entry.get("sha1", "")).lower()
        expected_sha256 = str(entry.get("sha256", "")).lower()
        if (
            len(payload) != expected_size
            or digest(payload) != expected_sha1
            or digest(payload, "sha256") != expected_sha256
        ):
            raise ProjectError(f"manifest does not describe extracted {region}")
        destination = safe_asset_path(output_root, str(entry.get("path", "")))
        action = write_if_changed(destination, payload)
        print(f"[{action}] {destination} ({len(payload)} bytes)")


def command_mkdir(args: argparse.Namespace) -> None:
    Path(args.path).mkdir(parents=True, exist_ok=True)


def command_require(args: argparse.Namespace) -> None:
    path = Path(args.path)
    if not path.is_file():
        raise ProjectError(f"required generated asset not found: {path}; {args.hint}")


def command_clean(args: argparse.Namespace) -> None:
    target = Path(args.path).resolve()
    build_root = (ROOT / "build").resolve()
    if target != build_root and build_root not in target.parents:
        raise ProjectError(f"refusing to clean outside {build_root}: {target}")
    if target.exists():
        shutil.rmtree(target)
        print(f"[CLEAN] {target}")


def load_toolchain(path: Path) -> dict[str, object]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectError(f"cannot read toolchain manifest {path}: {exc}") from exc
    if manifest.get("schema_version") != 1:
        raise ProjectError("unsupported toolchain manifest schema")
    return manifest


def parse_path_overrides(values: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for value in values:
        component, separator, path = value.partition("=")
        if not separator or not component or not path:
            raise ProjectError(f"invalid component path override: {value!r}")
        if component in overrides:
            raise ProjectError(f"duplicate component path override: {component}")
        overrides[component] = path
    return overrides


def kit_tool_path(spec: str) -> Path:
    """A program Retrolarium Kit ships, as suite/tool (nes/ca65); RLTOOL
    names the kit command (default rltool)."""
    suite, _, tool = spec.partition("/")
    # On Windows the command keeps its quoted paths (they may hold spaces).
    kit = [part[1:-1] if len(part) > 1 and part[0] == part[-1] == '"' else part
           for part in shlex.split(os.environ.get("RLTOOL", "rltool"), posix=os.name != "nt")]
    try:
        completed = subprocess.run([*kit, "build-tools", "path", suite, tool],
                                   capture_output=True, text=True, check=False)
    except OSError as exc:
        raise ProjectError(f"cannot run Retrolarium Kit for {spec}: {exc}") from exc
    if completed.returncode:
        raise ProjectError(f"Retrolarium Kit has no {spec}: {completed.stderr.strip()}")
    return Path(completed.stdout.strip().splitlines()[-1])


def entry_path(entry: dict[str, object], overrides: dict[str, str]) -> Path:
    identifier = str(entry.get("id", ""))
    if identifier in overrides:
        return resolve_tool_path(overrides[identifier])
    if isinstance(entry.get("kit_tool"), str):
        return kit_tool_path(str(entry["kit_tool"]))
    return resolve_tool_path(str(entry.get("path", "")))


def resolve_tool_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        project_path = ROOT / path
        if project_path.is_file():
            return project_path.resolve()
        executable = shutil.which(value)
        if executable:
            return Path(executable).resolve()
    return path.resolve()


def verify_file_contract(path: Path, entry: dict[str, object], description: str) -> None:
    if not path.is_file():
        raise ProjectError(f"{description} not found: {path}")
    data = path.read_bytes()
    expected_size = parse_number(entry.get("size"), f"{description}.size")
    expected_sha256 = str(entry.get("binary_sha256", entry.get("sha256", ""))).lower()
    if len(data) != expected_size:
        raise ProjectError(
            f"{description} size mismatch: got {len(data)}, expected {expected_size}"
        )
    actual_sha256 = digest(data, "sha256")
    if actual_sha256 != expected_sha256:
        raise ProjectError(
            f"{description} SHA-256 mismatch: got {actual_sha256}, "
            f"expected {expected_sha256}"
        )


def verify_component(path: Path, entry: dict[str, object]) -> None:
    identifier = str(entry.get("id", ""))
    if not identifier:
        raise ProjectError("toolchain component has no id")
    verify_file_contract(path, entry, f"toolchain component {identifier}")
    arguments = entry.get("version_arguments")
    if not isinstance(arguments, list) or not all(isinstance(arg, str) for arg in arguments):
        raise ProjectError(f"toolchain component {identifier} has invalid version arguments")
    if arguments:
        try:
            result = subprocess.run(
                [str(path), *arguments],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ProjectError(f"cannot query {identifier} version: {exc}") from exc
        actual_version = (result.stdout + result.stderr).strip()
        if actual_version != entry.get("version"):
            raise ProjectError(
                f"{identifier} version mismatch: got {actual_version!r}, "
                f"expected {entry.get('version')!r}"
            )
    checkout = entry.get("source_checkout")
    source_commit = entry.get("source_commit")
    if checkout:
        checkout_path = (ROOT / str(checkout)).resolve()
        try:
            actual_commit = subprocess.run(
                ["git", "-C", str(checkout_path), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ProjectError(f"cannot inspect {identifier} source checkout: {exc}") from exc
        if actual_commit != source_commit:
            raise ProjectError(
                f"{identifier} source commit mismatch: got {actual_commit}, "
                f"expected {source_commit}"
            )


def verify_host(entry: dict[str, object]) -> None:
    versions = entry.get("language_versions")
    if not isinstance(versions, dict):
        raise ProjectError("supported host has no language_versions object")
    facts = {
        "os": platform.system(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
    }
    try:
        facts["make"] = subprocess.run(
            ["make", "--version"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()[0]
    except (OSError, subprocess.CalledProcessError, IndexError) as exc:
        raise ProjectError(f"cannot query GNU Make version: {exc}") from exc
    expected = {
        "os": entry.get("os"),
        "architecture": entry.get("architecture"),
        "python": versions.get("python"),
        "make": versions.get("make"),
    }
    for field, value in facts.items():
        if value != expected[field]:
            raise ProjectError(
                f"host {field} mismatch: got {value!r}, expected {expected[field]!r}"
            )


def command_toolchain(args: argparse.Namespace) -> None:
    manifest = load_toolchain(Path(args.manifest))
    overrides = parse_path_overrides(args.component_path)
    components = manifest.get("components")
    if not isinstance(components, list):
        raise ProjectError("toolchain manifest has no components list")
    verified = 0
    for entry in components:
        if not isinstance(entry, dict):
            raise ProjectError("invalid toolchain component entry")
        if args.scope != "all" and entry.get("scope") != args.scope:
            continue
        path = entry_path(entry, overrides)
        verify_component(path, entry)
        verified += 1
    if args.scope in ("private", "all"):
        private_inputs = manifest.get("private_inputs")
        if not isinstance(private_inputs, list):
            raise ProjectError("toolchain manifest has no private_inputs list")
        for entry in private_inputs:
            if not isinstance(entry, dict):
                raise ProjectError("invalid private input entry")
            identifier = str(entry.get("id", ""))
            path = resolve_tool_path(overrides.get(identifier, str(entry.get("path", ""))))
            verify_file_contract(path, entry, f"private input {identifier}")
            verified += 1
    if args.scope in ("host", "all"):
        hosts = manifest.get("hosts")
        if not isinstance(hosts, list) or len(hosts) != 1 or not isinstance(hosts[0], dict):
            raise ProjectError("toolchain manifest must declare one supported host")
        verify_host(hosts[0])
        verified += 1
    if not verified:
        raise ProjectError(f"toolchain scope has no entries: {args.scope}")
    print(f"[OK] verified {verified} pinned {args.scope} toolchain input(s)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="verify a complete built image")
    verify.add_argument("--image", required=True)
    verify.add_argument("--manifest", required=True)
    verify.set_defaults(handler=command_verify)

    split = subparsers.add_parser("split", help="validate and split a reference ROM")
    split.add_argument("--image", required=True)
    split.add_argument("--manifest", required=True)
    split.add_argument("--output-dir", required=True)
    split.set_defaults(handler=command_split)

    mkdir = subparsers.add_parser("mkdir", help="create a build directory")
    mkdir.add_argument("--path", required=True)
    mkdir.set_defaults(handler=command_mkdir)

    require = subparsers.add_parser("require", help="require a generated asset")
    require.add_argument("--path", required=True)
    require.add_argument("--hint", required=True)
    require.set_defaults(handler=command_require)

    clean = subparsers.add_parser("clean", help="remove a path below build/")
    clean.add_argument("--path", required=True)
    clean.set_defaults(handler=command_clean)


    toolchain = subparsers.add_parser("toolchain", help="verify pinned toolchain inputs")
    toolchain.add_argument("--manifest", required=True)
    toolchain.add_argument(
        "--scope", choices=("build", "runtime", "private", "host", "all"), required=True
    )
    toolchain.add_argument("--component-path", action="append", default=[])
    toolchain.set_defaults(handler=command_toolchain)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.handler(args)
    except ProjectError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
