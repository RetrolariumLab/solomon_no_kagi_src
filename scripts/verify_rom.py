#!/usr/bin/env python3
"""Compare built Solomon's Key images and generated assets with the original."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from project import ProjectError, crc32, digest, load_manifest, parse_ines, validate_image


REGIONS = ("header", "prg", "chr", "payload")


def read_file(path: Path, description: str) -> bytes:
    if not path.is_file():
        raise ProjectError(f"{description} not found: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ProjectError(f"cannot read {description} {path}: {exc}") from exc


def first_difference(actual: bytes, expected: bytes) -> tuple[int, int | None, int | None] | None:
    for offset, (actual_byte, expected_byte) in enumerate(zip(actual, expected)):
        if actual_byte != expected_byte:
            return offset, actual_byte, expected_byte
    if len(actual) != len(expected):
        offset = min(len(actual), len(expected))
        actual_byte = actual[offset] if offset < len(actual) else None
        expected_byte = expected[offset] if offset < len(expected) else None
        return offset, actual_byte, expected_byte
    return None


def byte_text(value: int | None) -> str:
    return "EOF" if value is None else f"${value:02X}"


def location_text(region: str, offset: int, parsed: dict[str, object]) -> str:
    if region == "prg":
        return f"PRG offset ${offset:04X}, CPU ${0x8000 + offset:04X}"
    if region == "chr":
        return f"CHR offset ${offset:04X}, bank {offset // 0x2000} + ${offset % 0x2000:04X}"
    if region == "header":
        return f"header offset ${offset:02X}"
    if region == "payload":
        return f"payload offset ${offset:04X}"
    if region == "rom":
        header_size = len(parsed["header"])
        prg_size = len(parsed["prg"])
        if offset < header_size:
            detail = f"header + ${offset:02X}"
        elif offset < header_size + prg_size:
            prg_offset = offset - header_size
            detail = f"PRG + ${prg_offset:04X}, CPU ${0x8000 + prg_offset:04X}"
        else:
            chr_offset = offset - header_size - prg_size
            detail = f"CHR + ${chr_offset:04X}, bank {chr_offset // 0x2000}"
        return f"file offset ${offset:05X} ({detail})"
    raise AssertionError(region)


def compare_bytes(
    region: str,
    actual: bytes,
    expected: bytes,
    parsed: dict[str, object],
) -> None:
    mismatch = first_difference(actual, expected)
    if mismatch is not None:
        offset, actual_byte, expected_byte = mismatch
        raise ProjectError(
            f"{region} differs at {location_text(region, offset, parsed)}: "
            f"built {byte_text(actual_byte)}, original {byte_text(expected_byte)}; "
            f"sizes {len(actual)} and {len(expected)}"
        )
    print(
        f"[OK] {region}: {len(actual)} bytes identical "
        f"(sha1={digest(actual)}, sha256={digest(actual, 'sha256')}, "
        f"crc32={crc32(actual)})"
    )


def compare_images(
    built_data: bytes,
    reference_data: bytes,
    manifest: dict[str, object],
    region: str,
) -> None:
    reference = validate_image(reference_data, manifest)
    built = parse_ines(built_data)
    print("[OK] original image matches the manifest")
    regions = (*REGIONS, "rom") if region == "all" else (region,)
    for name in regions:
        actual = built_data if name == "rom" else built[name]
        expected = reference_data if name == "rom" else reference[name]
        compare_bytes(name, actual, expected, built)
    if region in ("all", "rom"):
        validate_image(built_data, manifest)
        print("[OK] built image matches the manifest")


def verify_asset(
    asset_data: bytes,
    reference_data: bytes,
    manifest: dict[str, object],
    region: str,
) -> None:
    reference = validate_image(reference_data, manifest)
    if region not in REGIONS:
        raise ProjectError(f"unsupported asset region: {region}")
    compare_bytes(region, asset_data, reference[region], reference)


def report_image(data: bytes, manifest: dict[str, object] | None = None) -> None:
    parsed = parse_ines(data)
    print(
        f"mapper={parsed['mapper']} mirroring={parsed['mirroring']} "
        f"trainer={parsed['trainer_size']}"
    )
    for name, payload in (
        ("rom", data),
        ("payload", parsed["payload"]),
        ("header", parsed["header"]),
        ("prg", parsed["prg"]),
        ("chr", parsed["chr"]),
    ):
        print(
            f"{name:7} size={len(payload):5} sha1={digest(payload)} "
            f"sha256={digest(payload, 'sha256')} crc32={crc32(payload)}"
        )
    if manifest is not None:
        validate_image(data, manifest)
        print("[OK] image matches the manifest")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare = subparsers.add_parser("compare", help="compare built and original images")
    compare.add_argument("--built", required=True)
    compare.add_argument("--reference", required=True)
    compare.add_argument("--manifest", required=True)
    compare.add_argument("--region", choices=(*REGIONS, "rom", "all"), default="all")

    asset = subparsers.add_parser("asset", help="compare an extracted asset")
    asset.add_argument("--asset", required=True)
    asset.add_argument("--reference", required=True)
    asset.add_argument("--manifest", required=True)
    asset.add_argument("--region", choices=REGIONS, required=True)

    report = subparsers.add_parser("report", help="print image identity and layout")
    report.add_argument("--image", required=True)
    report.add_argument("--manifest")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "compare":
            compare_images(
                read_file(Path(args.built), "built image"),
                read_file(Path(args.reference), "original image"),
                load_manifest(Path(args.manifest)),
                args.region,
            )
        elif args.command == "asset":
            verify_asset(
                read_file(Path(args.asset), "generated asset"),
                read_file(Path(args.reference), "original image"),
                load_manifest(Path(args.manifest)),
                args.region,
            )
        else:
            manifest = load_manifest(Path(args.manifest)) if args.manifest else None
            report_image(read_file(Path(args.image), "image"), manifest)
    except ProjectError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
