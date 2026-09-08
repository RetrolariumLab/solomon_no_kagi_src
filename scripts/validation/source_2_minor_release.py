"""Audit the compatible Solomon's Key Source Reconstruction 2.1 release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from scripts.validation import release_history
from scripts.validation.reconstruction_status import (
    parse_make_targets,
    remote_tag_lines,
    run_git,
)


ROOT = Path(__file__).resolve().parents[2]
INHERITED_SECTION_IDS = {
    "profiles",
    "runtime_coverage",
    "toolchain",
    "artifacts",
    "authoring",
    "structured_data_contracts",
    "licensing",
    "provenance",
}
VALID_STATUSES = {"development", "tag-ready", "tagged"}
VALID_REQUIREMENT_STATUSES = {
    "satisfied",
    "not_applicable",
    "partial",
    "unsupported",
    "planned",
}
EVIDENCE_FIELDS = {"targets", "files", "scenarios", "artifacts"}
EXPLICIT_INHERITED_FIELDS = {
    "profiles",
    "runtime_coverage",
    "toolchain",
    "artifacts",
    "licensing",
}
MINOR_METADATA_PATHS = {
    "config/source_reconstruction_2_1.json",
    "docs/source_reconstruction_2_1.md",
}


class Source2MinorReleaseError(ValueError):
    """Report an inconsistent compatible-minor release without a traceback."""


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Source2MinorReleaseError(f"JSON root must be an object: {path}")
    return value


def section_digest(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def git_lines(project_root: Path, *arguments: str) -> list[str]:
    result = subprocess.run(
        ["git", *arguments],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line for line in result.stdout.splitlines() if line]


def validate_release_header(release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if release.get("schema_version") != 2:
        errors.append("unsupported Source Reconstruction 2.1 manifest schema")
    if release.get("release_line") != "2.x":
        errors.append("release_line must be 2.x")
    if "contract" in release:
        errors.append("release manifest must contain only project-owned metadata")
    return errors


def project_release_view(release: dict[str, Any]) -> dict[str, Any]:
    """Return fields whose meaning belongs to this public project."""
    return {
        key: value
        for key, value in release.items()
        if key not in {"schema_version", "release_line", "contract"}
    }


def validate_predecessor(
    project_root: Path, release: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    predecessor = release.get("predecessor", {})
    if not isinstance(predecessor, dict):
        return {}, ["predecessor must be an object"]
    manifest = predecessor.get("manifest")
    tag = predecessor.get("tag")
    commit = predecessor.get("commit")
    if manifest != "config/source_reconstruction_2_0.json":
        errors.append("predecessor manifest must identify Source 2.0")
    path = project_root / str(manifest or "")
    if not path.is_file():
        return {}, errors + ["predecessor manifest is missing"]
    document = load_json(path)
    if document.get("release") != {
        "name": "Source Reconstruction 2.0",
        "version": "2.0",
    }:
        errors.append("predecessor manifest does not identify Source 2.0")
    if tag != document.get("tag"):
        errors.append("predecessor tag disagrees with its manifest")
    tag_ref = f"refs/tags/{tag}"
    if git_lines(project_root, "cat-file", "-t", tag_ref) != ["tag"]:
        errors.append("accepted Source 2.0 tag is not annotated")
    if git_lines(project_root, "rev-parse", f"{tag_ref}^{{commit}}") != [commit]:
        errors.append("predecessor tag and commit disagree")
    tagged = subprocess.run(
        ["git", "show", f"{tag_ref}:{manifest}"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    tagged_document = json.loads(tagged)
    if project_release_view(tagged_document) != project_release_view(document):
        errors.append("working predecessor project metadata differs from the accepted tag")
    return document, errors


def validate_inheritance(
    predecessor: dict[str, Any], release: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    records = release.get("inherited_sections", [])
    if not isinstance(records, list):
        return ["inherited_sections must be a list"]
    by_id = {
        item.get("id"): item
        for item in records
        if isinstance(item, dict) and item.get("id")
    }
    if set(by_id) != INHERITED_SECTION_IDS or len(records) != len(by_id):
        errors.append("inherited section inventory differs from Source 2.x policy")
    for identifier in sorted(INHERITED_SECTION_IDS):
        item = by_id.get(identifier)
        if item and item.get("sha256") != section_digest(predecessor.get(identifier)):
            errors.append(f"inherited Source 2.0 section changed: {identifier}")
    return errors


def validate_explicit_inheritance(
    project_root: Path,
    predecessor: dict[str, Any],
    release: dict[str, Any],
) -> list[str]:
    """Require the compatible manifest to expose its effective 2.0 surface."""
    errors: list[str] = []
    for field in sorted(EXPLICIT_INHERITED_FIELDS):
        if release.get(field) != predecessor.get(field):
            errors.append(f"compatible minor must explicitly inherit Source 2.0 {field}")
    revision_manifest = release.get("revision_manifest")
    if revision_manifest != predecessor.get("revision_manifest"):
        errors.append("compatible minor must explicitly inherit revision_manifest")
    elif not (project_root / str(revision_manifest)).is_file():
        errors.append(f"revision manifest is missing: {revision_manifest}")

    toolchain = release.get("toolchain", {})
    toolchain_path = project_root / str(toolchain.get("manifest", ""))
    if not toolchain_path.is_file():
        errors.append(f"toolchain manifest is missing: {toolchain.get('manifest')}")
    else:
        details = load_json(toolchain_path)
        component_ids = [
            item.get("id")
            for item in details.get("components", [])
            if isinstance(item, dict)
        ]
        host_ids = {
            item.get("id")
            for item in details.get("hosts", [])
            if isinstance(item, dict)
        }
        if toolchain.get("components") != component_ids:
            errors.append("toolchain component inventory disagrees with its manifest")
        if toolchain.get("host") not in host_ids:
            errors.append("toolchain host is absent from its manifest")
    return errors


def validate_requirements(
    project_root: Path,
    release: dict[str, Any],
    targets: set[str],
) -> list[str]:
    """Validate the structured evidence attached to requirements."""
    errors: list[str] = []
    requirements = release.get("requirements", {})
    if not isinstance(requirements, dict) or not requirements:
        return ["requirements must be a non-empty object"]

    artifact_ids = {
        item.get("id")
        for item in release.get("artifacts", [])
        if isinstance(item, dict) and item.get("id")
    }
    scenario_ids = {
        scenario
        for coverage in release.get("runtime_coverage", [])
        if isinstance(coverage, dict)
        for scenario in coverage.get("scenarios", [])
    }
    for identifier, requirement in requirements.items():
        if not isinstance(requirement, dict):
            errors.append(f"requirement {identifier} must be an object")
            continue
        status = requirement.get("status")
        if status not in VALID_REQUIREMENT_STATUSES:
            errors.append(f"requirement {identifier} has invalid status")
        evidence = requirement.get("evidence")
        if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_FIELDS:
            errors.append(f"requirement {identifier} evidence must use structured fields")
            continue
        if any(not isinstance(evidence[field], list) for field in EVIDENCE_FIELDS):
            errors.append(f"requirement {identifier} evidence fields must be lists")
            continue
        if not any(evidence.values()):
            errors.append(f"requirement {identifier} has no evidence")
        for target in evidence["targets"]:
            if target not in targets:
                errors.append(f"requirement {identifier} names missing target: {target}")
        for relative in evidence["files"]:
            if not (project_root / str(relative)).is_file():
                errors.append(f"requirement {identifier} names missing file: {relative}")
        for scenario in evidence["scenarios"]:
            if scenario not in scenario_ids and not (project_root / str(scenario)).is_file():
                errors.append(f"requirement {identifier} names missing scenario: {scenario}")
        for artifact in evidence["artifacts"]:
            if artifact not in artifact_ids:
                errors.append(f"requirement {identifier} names missing artifact: {artifact}")
        if status == "not_applicable" and not requirement.get("reason"):
            errors.append(f"requirement {identifier} is not_applicable without a reason")
    return errors


def validate_delta_history(
    project_root: Path, release: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    predecessor = release.get("predecessor", {}).get("commit")
    history = release.get("delta_history", {})
    if not isinstance(history, dict):
        return ["delta_history must be an object"]
    if history.get("from_exclusive") != predecessor:
        errors.append("delta_history does not start at the predecessor commit")
    through = history.get("through_inclusive")
    count = history.get("commit_count")
    if through is None and release.get("status") == "development":
        errors.extend(release_history.validate_release_history(project_root, predecessor))
        return errors
    if not isinstance(through, str) or not re.fullmatch(r"[0-9a-f]{40}", through):
        return errors + ["delta_history has no valid terminal commit"]
    commits = git_lines(project_root, "rev-list", "--reverse", f"{predecessor}..{through}")
    if not isinstance(count, int) or count != len(commits):
        errors.append(f"delta_history covers {len(commits)} commits, expected {count}")
    if not commits or commits[-1] != through:
        errors.append("delta_history terminal commit is not reachable from predecessor")
    errors.extend(release_history.validate_release_history(project_root, predecessor, through))
    trailing = git_lines(project_root, "rev-list", "--reverse", f"{through}..HEAD")
    for commit in trailing:
        changed = set(
            git_lines(
                project_root,
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                commit,
            )
        )
        if not changed or not changed.issubset(MINOR_METADATA_PATHS):
            errors.append(f"delta_history does not cover substantive commit {commit[:12]}")
    errors.extend(release_history.validate_release_history(project_root, through))
    return errors


def validate_paths_and_commands(
    project_root: Path, release: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    targets = parse_make_targets(project_root / "Makefile")
    for field in ("required_documents", "required_files"):
        values = release.get(field, [])
        if not isinstance(values, list) or not values:
            errors.append(f"{field} must be a non-empty list")
            continue
        for relative in values:
            if not (project_root / str(relative)).is_file():
                errors.append(f"required release path is missing: {relative}")
    for target in release.get("release_commands", []):
        if target not in targets:
            errors.append(f"release command names missing target: {target}")
    gates = release.get("aggregate_gates")
    expected_gates = {
        "pre_tag": ["make source-2-minor-pre-tag-check"],
        "post_tag": ["make source-2-minor-tag-check"],
    }
    if gates != expected_gates:
        errors.append("aggregate gates differ from the Source 2.1 interface")
    errors.extend(validate_requirements(project_root, release, targets))
    for item in release.get("delta", []):
        if not isinstance(item, dict) or not all(
            item.get(field) for field in ("id", "kind", "summary", "evidence")
        ):
            errors.append("delta entry is incomplete")
            continue
        for evidence in item["evidence"]:
            if evidence not in targets and not (project_root / str(evidence)).exists():
                errors.append(f"delta {item['id']} names missing evidence: {evidence}")
    return errors


def validate_manifest(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors = validate_release_header(release)
    if release.get("release") != {
        "name": "Source Reconstruction 2.1",
        "version": "2.1",
    }:
        errors.append("release identity must name Source Reconstruction 2.1")
    if release.get("release_kind") != "compatible_minor":
        errors.append("release_kind must be compatible_minor")
    if release.get("tag") != "source-reconstruction-2.1":
        errors.append("release tag must be source-reconstruction-2.1")
    if release.get("status") not in VALID_STATUSES:
        errors.append("release status is invalid")
    predecessor, predecessor_errors = validate_predecessor(project_root, release)
    errors.extend(predecessor_errors)
    if predecessor:
        errors.extend(validate_inheritance(predecessor, release))
        errors.extend(validate_explicit_inheritance(project_root, predecessor, release))
    if not release.get("included_scope") or not release.get("excluded_scope"):
        errors.append("included_scope and excluded_scope must both be non-empty")
    errors.extend(validate_delta_history(project_root, release))
    errors.extend(validate_paths_and_commands(project_root, release))
    provenance = release.get("provenance", {})
    if provenance.get("private_inputs_tracked") is not False:
        errors.append("provenance must reject tracked private inputs")
    if provenance.get("generated_outputs_tracked") is not False:
        errors.append("provenance must reject tracked generated outputs")
    return errors


def validate_lifecycle(
    project_root: Path, release: dict[str, Any], command: str
) -> list[str]:
    if command == "audit":
        return []
    if release.get("status") != "tag-ready":
        return [f"{command} requires status tag-ready"]
    if command == "pre-tag-audit":
        errors = []
        if git_lines(project_root, "status", "--porcelain", "--untracked-files=all"):
            errors.append("pre-tag audit requires a clean worktree")
        requirements = release.get("requirements", {})
        if any(
            not isinstance(value, dict) or value.get("status") != "satisfied"
            for value in requirements.values()
        ):
            errors.append("pre-tag audit requires every requirement to be satisfied")
        if release.get("delta_history", {}).get("through_inclusive") is None:
            errors.append("pre-tag audit requires a pinned delta terminal")
        tag = release["tag"]
        result = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
            cwd=project_root,
            check=False,
        )
        if result.returncode == 0:
            errors.append("future release tag already exists")
        remote = str(release.get("publish_remote", ""))
        lines, remote_error = remote_tag_lines(project_root, remote, tag)
        if remote_error:
            errors.append(f"cannot verify publish remote tag state: {remote_error}")
        elif lines:
            errors.append(f"future release tag already exists on {remote}: {tag}")
        return errors
    tag_ref = f"refs/tags/{release['tag']}"
    tag_type = run_git(project_root, "cat-file", "-t", tag_ref)
    if tag_type.returncode or tag_type.stdout.strip() != "tag":
        return ["release tag is not annotated"]
    head = git_lines(project_root, "rev-parse", "HEAD")[0]
    if git_lines(project_root, "rev-parse", f"{tag_ref}^{{commit}}") != [head]:
        return ["release tag does not point at HEAD"]
    remote = str(release.get("publish_remote", ""))
    lines, remote_error = remote_tag_lines(project_root, remote, release["tag"])
    if remote_error:
        return [f"cannot verify published tag: {remote_error}"]
    peeled = [
        line.split()[0]
        for line in lines
        if line.endswith(f"refs/tags/{release['tag']}^{{}}")
    ]
    return [] if peeled == [head] else [f"published tag on {remote} does not peel to HEAD"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "pre-tag-audit", "post-tag-audit"))
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument(
        "--release",
        type=Path,
        default=ROOT / "config" / "source_reconstruction_2_1.json",
    )
    args = parser.parse_args()
    try:
        release = load_json(args.release)
        project_root = args.project_root.resolve()
        errors = validate_manifest(project_root, release)
        errors.extend(validate_lifecycle(project_root, release, args.command))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        print(f"[FAIL] Source Reconstruction 2.1 audit found {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(
        "[OK] Source Reconstruction 2.1 contract, predecessor, inherited "
        "sections, profiles, evidence, delta history, and command surface agree"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
