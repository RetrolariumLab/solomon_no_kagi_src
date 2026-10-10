#!/usr/bin/env python3
"""Run a published release's own audit in a checkout of its tag.

A release manifest describes the tree it was tagged with. Once the repository
moves on (Source Reconstruction 3.0 retired the editors the 2.0 and 2.1
manifests audit), the audit runs where that tree still is: a disposable clone
of this repository, with its tags, checked out at the release tag. The command
is the tag's own: a Python script there (2.0 still had flat scripts, 2.1 has
`scripts/run.py`) or a program such as make with the tag's Make targets.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]


class TagAuditError(RuntimeError):
    """The tag cannot be checked out or no command was given."""


def run_at_tag(project_root: Path, tag: str, command: list[str]) -> int:
    if not command:
        raise TagAuditError("no audit command given")
    with tempfile.TemporaryDirectory(prefix="tag-audit-") as directory:
        clone = Path(directory) / "repository"
        for step in (
            ["git", "clone", "--quiet", "--no-hardlinks", str(project_root), str(clone)],
            ["git", "-C", str(clone), "checkout", "--quiet", "--detach", f"refs/tags/{tag}"],
        ):
            completed = subprocess.run(step, capture_output=True, text=True, check=False)
            if completed.returncode:
                raise TagAuditError(f"cannot check out {tag}: {completed.stderr.strip()}")
        print(f"[RUN] at {tag}: " + " ".join(command), flush=True)
        program = [sys.executable] if command[0].endswith(".py") else []
        return subprocess.run([*program, *command], cwd=clone, check=False).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="after --: a script of the tag (or a program) and its arguments",
    )
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        return run_at_tag(ROOT, args.tag, command)
    except TagAuditError as error:
        print(f"[FAIL] {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
