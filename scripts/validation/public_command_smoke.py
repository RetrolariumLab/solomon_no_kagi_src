#!/usr/bin/env python3
"""Run a real public Make command from a disposable tracked-only clone."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]


class PublicCommandSmokeError(RuntimeError):
    """A disposable public command did not complete successfully."""


def run_disposable_make(
    project_root: Path,
    target: str = "lint",
    *,
    make_executable: str | None = None,
    prepare_clone: Callable[[Path], None] | None = None,
) -> str:
    """Clone tracked content, optionally prepare it, and run one public target."""
    make = make_executable or shutil.which("make")
    if not make:
        raise PublicCommandSmokeError("make executable not found")

    with tempfile.TemporaryDirectory(prefix="solomon-public-command-") as directory:
        clone = Path(directory) / "repository"
        clone_result = subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                "--shared",
                "--no-local",
                str(project_root.resolve()),
                str(clone),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if clone_result.returncode != 0:
            raise PublicCommandSmokeError(
                f"cannot create disposable clone: {clone_result.stderr.strip()}"
            )

        if prepare_clone is not None:
            prepare_clone(clone)

        result = subprocess.run(
            [make, target],
            cwd=clone,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            details = (result.stdout + result.stderr).strip()
            raise PublicCommandSmokeError(
                f"public command 'make {target}' failed in disposable clone:\n{details}"
            )

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=clone,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout.strip()
        if status:
            raise PublicCommandSmokeError(
                f"public command 'make {target}' changed the disposable worktree"
            )
        return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--target", default="lint")
    args = parser.parse_args()
    try:
        output = run_disposable_make(args.project_root, args.target)
    except (OSError, subprocess.SubprocessError, PublicCommandSmokeError) as exc:
        print(f"[ERROR] {exc}")
        return 1

    summary = next(
        (line for line in reversed(output.splitlines()) if line.startswith("[OK]")),
        "completed",
    )
    print(f"[OK] disposable 'make {args.target}': {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
