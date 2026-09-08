#!/usr/bin/env python3
"""Reject non-English letters in the public project and reachable history."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import subprocess
import unicodedata


ROOT = Path(__file__).resolve().parents[2]
TEXT_SUFFIXES = {
    ".asm",
    ".cfg",
    ".csv",
    ".inc",
    ".json",
    ".lua",
    ".md",
    ".mk",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "CONTRIBUTING",
    "CONTRIBUTING.md",
    "LICENSE",
    "Makefile",
    "README",
    "README.md",
}


@dataclass(frozen=True)
class TextViolation:
    owner: str
    line: int
    column: int
    character: str
    unicode_name: str

    def render(self) -> str:
        return (
            f"{self.owner}:{self.line}:{self.column}: non-Latin letter "
            f"U+{ord(self.character):04X} {self.unicode_name}"
        )


def run_git(root: Path, *arguments: str, input_data: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        input=input_data,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def is_public_text_path(relative: str) -> bool:
    path = Path(relative)
    return path.name in TEXT_FILENAMES or path.suffix.lower() in TEXT_SUFFIXES


def decode_text(owner: str, data: bytes) -> tuple[str | None, list[str]]:
    try:
        return data.decode("utf-8"), []
    except UnicodeDecodeError as exc:
        return None, [f"{owner}: public text is not valid UTF-8: {exc}"]


def find_non_latin_letters(owner: str, text: str) -> list[str]:
    errors: list[str] = []
    line = 1
    column = 1
    for character in text:
        name = unicodedata.name(character, "")
        if character.isalpha() and not name.startswith("LATIN"):
            errors.append(
                TextViolation(owner, line, column, character, name or "UNNAMED").render()
            )
        if character == "\n":
            line += 1
            column = 1
        else:
            column += 1
    return errors


def validate_current_tree(root: Path) -> list[str]:
    errors: list[str] = []
    paths = run_git(root, "ls-files", "-z").decode("utf-8").split("\0")
    for relative in paths:
        if not relative:
            continue
        errors.extend(find_non_latin_letters(f"path {relative}", relative))
        if not is_public_text_path(relative):
            continue
        path = root / relative
        text, decode_errors = decode_text(relative, path.read_bytes())
        errors.extend(decode_errors)
        if text is not None:
            errors.extend(find_non_latin_letters(relative, text))
    return errors


def history_objects(root: Path, revision: str) -> list[tuple[str, str]]:
    output = run_git(root, "rev-list", "--objects", revision).decode("utf-8")
    objects: list[tuple[str, str]] = []
    for line in output.splitlines():
        object_id, separator, relative = line.partition(" ")
        if separator and is_public_text_path(relative):
            objects.append((object_id, relative))
    return objects


def read_objects(root: Path, object_ids: list[str]) -> list[tuple[str, bytes]]:
    if not object_ids:
        return []
    payload = run_git(
        root,
        "cat-file",
        "--batch",
        input_data=("\n".join(object_ids) + "\n").encode("ascii"),
    )
    offset = 0
    objects: list[tuple[str, bytes]] = []
    for expected in object_ids:
        header_end = payload.index(b"\n", offset)
        header = payload[offset:header_end].decode("ascii").split()
        if len(header) != 3 or header[0] != expected:
            raise ValueError(f"unexpected git cat-file response for {expected}")
        size = int(header[2])
        start = header_end + 1
        end = start + size
        objects.append((header[1], payload[start:end]))
        offset = end + 1
    return objects


def validate_history(root: Path, revision: str) -> list[str]:
    errors: list[str] = []
    metadata = run_git(
        root,
        "log",
        "-z",
        "--format=commit %H%n%an <%ae>%n%cn <%ce>%n%B",
        revision,
    )
    text, decode_errors = decode_text(f"history {revision}", metadata)
    errors.extend(decode_errors)
    if text is not None:
        errors.extend(find_non_latin_letters(f"history {revision}", text))

    entries = history_objects(root, revision)
    unique: dict[str, str] = {}
    for object_id, relative in entries:
        unique.setdefault(object_id, relative)
        errors.extend(find_non_latin_letters(f"historical path {relative}", relative))
    for (object_id, relative), (kind, data) in zip(
        unique.items(), read_objects(root, list(unique)), strict=True
    ):
        if kind != "blob":
            continue
        owner = f"historical blob {object_id[:12]} ({relative})"
        blob_text, blob_errors = decode_text(owner, data)
        errors.extend(blob_errors)
        if blob_text is not None:
            errors.extend(find_non_latin_letters(owner, blob_text))
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument(
        "--history-ref",
        help="also inspect commit metadata, paths, and public-text blobs reachable from this ref",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.project_root.resolve()
    errors = validate_current_tree(root)
    if args.history_ref:
        errors.extend(validate_history(root, args.history_ref))
    if errors:
        print("[FAIL] public English-text policy")
        for error in errors:
            print(f"  - {error}")
        return 1
    scope = "current tree and reachable history" if args.history_ref else "current tree"
    print(f"[OK] public English-text policy: {scope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
