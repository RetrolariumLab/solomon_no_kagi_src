"""The pinned assemblers of config/toolchain.json: ca65 and ld65 from
Retrolarium Kit (RLTOOL names the kit command, default rltool), checked by
SHA-256 and version before a build."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
from pathlib import Path

COMPONENTS = {"ca65", "ld65"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_toolchain_manifest(path: Path) -> dict[str, dict[str, object]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    components = document.get("components")
    if document.get("format") != 1 or not isinstance(components, dict):
        raise ValueError("unsupported toolchain manifest")
    if set(components) != COMPONENTS:
        raise ValueError("toolchain components must be exactly: " + ", ".join(sorted(COMPONENTS)))
    for component_id, component in components.items():
        digest = component.get("binary_sha256") if isinstance(component, dict) else None
        if not isinstance(digest, str) or len(digest) != 64 or any(
                char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"invalid binary_sha256 for {component_id}")
        for field in ("version", "suite", "tool", "kit_release"):
            if not isinstance(component.get(field), str) or not component[field]:
                raise ValueError(f"missing {field} for {component_id}")
    return components


def tool_path(project_root: Path, component_id: str, component: dict[str, object]) -> Path:
    """Where the kit keeps a toolchain component's program."""
    # On Windows the command keeps its quoted paths (they may hold spaces).
    kit = [part[1:-1] if len(part) > 1 and part[0] == part[-1] == '"' else part
           for part in shlex.split(os.environ.get("RLTOOL", "rltool"), posix=os.name != "nt")]
    command = [*kit, "build-tools", "path", str(component["suite"]), str(component["tool"])]
    try:
        completed = subprocess.run(command, cwd=str(project_root), capture_output=True,
                                   text=True, check=False)
    except OSError as error:
        raise ValueError(f"cannot run Retrolarium Kit for {component_id}: {error}") from error
    if completed.returncode:
        raise ValueError(f"Retrolarium Kit has no {component_id}: {completed.stderr.strip()}")
    return Path(completed.stdout.strip().splitlines()[-1])


def verify_bundled_tool(project_root: Path, component_id: str, component: dict[str, object]) -> None:
    path = tool_path(project_root, component_id, component)
    if not path.is_file():
        raise ValueError(f"missing {component_id} binary: {path}")
    actual = file_sha256(path)
    if actual != component["binary_sha256"]:
        raise ValueError(f"{component_id} SHA256 {actual}, expected {component['binary_sha256']}")
    completed = subprocess.run([str(path), "--version"], cwd=str(project_root), capture_output=True,
                               text=True, check=False)
    version = (completed.stdout + completed.stderr).strip().splitlines()[0]
    if version != component.get("version"):
        raise ValueError(f"{component_id} version {version!r}, expected {component.get('version')!r}")


def main() -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Check the kit's ca65 and ld65 against config/toolchain.json.")
    parser.add_argument("--manifest", type=Path, default=Path("config/toolchain.json"))
    args = parser.parse_args()
    root = Path.cwd()
    try:
        for component_id, component in load_toolchain_manifest(args.manifest).items():
            verify_bundled_tool(root, component_id, component)
    except ValueError as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print(f"[OK] ca65 and ld65 match {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
