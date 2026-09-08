"""Validate release commit structure directly from Git objects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


EXPECTED_AUTHOR = "Daniel Oranguthang <75395800+oranguthang@users.noreply.github.com>"
EXPECTED_CODEX_TRAILER = "Co-Authored-By: Codex <noreply@openai.com>"
FORBIDDEN_SUBJECTS = {"changes", "fix", "update", "wip"}


@dataclass(frozen=True)
class CommitRecord:
    object_id: str
    parents: tuple[str, ...]
    tree: str
    author: str
    message: str


def git(project_root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def read_commits(project_root: Path, revision_range: str) -> list[CommitRecord]:
    output = git(
        project_root,
        "log",
        "--reverse",
        "--format=%H%x1f%P%x1f%T%x1f%an <%ae>%x1f%B%x1e",
        revision_range,
    )
    records: list[CommitRecord] = []
    for raw_record in output.split("\x1e"):
        raw_record = raw_record.strip()
        if not raw_record:
            continue
        fields = raw_record.split("\x1f", 4)
        if len(fields) != 5:
            raise ValueError("cannot parse commit history record")
        object_id, parents, tree, author, message = fields
        records.append(
            CommitRecord(
                object_id=object_id,
                parents=tuple(parents.split()),
                tree=tree,
                author=author,
                message=message.strip(),
            )
        )
    return records


def tree(project_root: Path, commit: str) -> str:
    return git(project_root, "show", "-s", "--format=%T", commit).strip()


def validate_nonempty_commits(
    project_root: Path, records: list[CommitRecord]
) -> list[str]:
    errors: list[str] = []
    for record in records:
        if not record.parents:
            continue
        parent_trees = [tree(project_root, parent) for parent in record.parents]
        if all(record.tree == parent_tree for parent_tree in parent_trees):
            errors.append(
                f"commit {record.object_id[:12]} is empty relative to every parent"
            )
    return errors


def body_paragraphs(lines: list[str], has_trailer: bool) -> list[str]:
    body_lines = lines[2:]
    if has_trailer:
        body_lines = body_lines[:-2] if body_lines[-2:-1] == [""] else body_lines[:-1]
    return [part for part in "\n".join(body_lines).split("\n\n") if part.strip()]


def validate_commit_messages(records: list[CommitRecord]) -> list[str]:
    errors: list[str] = []
    for record in records:
        lines = record.message.splitlines()
        subject = lines[0].strip() if lines else ""
        short = record.object_id[:12]
        if (
            not subject
            or not subject.isascii()
            or subject.endswith(".")
            or subject.lower() in FORBIDDEN_SUBJECTS
        ):
            errors.append(f"commit {short} has an invalid English subject")
        if record.author != EXPECTED_AUTHOR:
            errors.append(f"commit {short} has unexpected author {record.author!r}")
        if len(lines) < 3 or lines[1] != "":
            errors.append(f"commit {short} must separate subject and body")
        has_trailer = lines[-1:] == [EXPECTED_CODEX_TRAILER]
        if not has_trailer:
            errors.append(f"commit {short} lacks the exact Codex co-author trailer")
        elif len(lines) < 2 or lines[-2] != "":
            errors.append(f"commit {short} must separate its trailer from the body")
        paragraphs = body_paragraphs(lines, has_trailer)
        if len(paragraphs) not in {2, 3}:
            errors.append(f"commit {short} must have two or three body paragraphs")
    return errors


def validate_release_history(
    project_root: Path, predecessor: str, terminal: str = "HEAD"
) -> list[str]:
    records = read_commits(project_root, f"{predecessor}..{terminal}")
    errors = validate_nonempty_commits(project_root, records)
    errors.extend(validate_commit_messages(records))
    return errors
