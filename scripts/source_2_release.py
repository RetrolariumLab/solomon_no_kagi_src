"""Validate the additive Source Reconstruction 2.0 release contract.

The Source 1.0 release validator remains intentionally frozen in
``reconstruction_status.py``.  This module verifies only the contracts added
after that tag: revision identity, direct runtime evidence, authoring codecs,
regional data audits, and the reusable publication gates for 2.0.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .reconstruction_status import (
        makefile_sources,
        parse_make_targets,
        validate_post_tag,
        validate_pre_tag,
    )
except ImportError:  # Direct ``python scripts/source_2_release.py`` execution.
    from reconstruction_status import (
        makefile_sources,
        parse_make_targets,
        validate_post_tag,
        validate_pre_tag,
    )


ROOT = Path(__file__).resolve().parent.parent
RELEASE_LINE = "2.0"
RELEASE_TAG = "source-reconstruction-2.0"
SUPPORTED_PROFILES = {"usa", "europe"}
REQUIRED_REQUIREMENTS = {
    "predecessor_preservation",
    "revision_identity_matrix",
    "regional_source_ownership",
    "runtime_profile_matrix",
    "debugger_profile_matrix",
    "level_authoring",
    "audio_authoring",
    "graphics_authoring",
    "presentation_authoring",
    "structured_data_contracts",
    "private_inputs",
    "generated_outputs",
    "documentation",
    "release_contract",
    "licensing_and_provenance",
    "tag_integrity",
    "commit_history",
}
REQUIRED_AUTHORING_ROLES = {
    "export",
    "validate",
    "build",
    "roundtrip",
    "headless_check",
}
VALID_EXCLUDED_STATUSES = {"planned", "partial", "unsupported"}


class Source2ReleaseError(ValueError):
    """Report an invalid release-contract value without a traceback."""


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Source2ReleaseError(f"JSON root must be an object: {path}")
    return value


def as_object(value: object, description: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{description} must be an object")
        return {}
    return value


def as_object_list(
    value: object, description: str, errors: list[str]
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        errors.append(f"{description} must be a list of objects")
        return []
    return value


def unique_objects(
    entries: list[dict[str, Any]], description: str, errors: list[str]
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"{description} entry has no id")
        elif identifier in result:
            errors.append(f"duplicate {description} id: {identifier}")
        else:
            result[identifier] = entry
    return result


def valid_digest(value: object, digits: int) -> bool:
    if not isinstance(value, str) or len(value) != digits:
        return False
    return all(character in "0123456789abcdef" for character in value)


def run_git(project_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def make_recipe(makefile: Path, target: str) -> list[str]:
    commands: list[str] = []
    for source in makefile_sources(makefile):
        collecting = False
        for line in source.read_text(encoding="utf-8").splitlines():
            if not line.startswith((" ", "\t")):
                collecting = line.startswith(f"{target}:")
                continue
            if collecting and line.startswith("\t"):
                commands.append(line.strip())
    return commands


def validate_contract_header(release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if release.get("schema_version") != 2:
        errors.append("unsupported Source Reconstruction 2.0 manifest schema")
    if release.get("release_line") != RELEASE_LINE:
        errors.append("release_line must be 2.0")
    if "contract" in release:
        errors.append("release manifest must contain only project-owned metadata")
    if release.get("release") != {
        "name": "Source Reconstruction 2.0",
        "version": "2.0",
    }:
        errors.append("release name or version differs")
    if release.get("release_kind") != "baseline":
        errors.append("release_kind must be baseline")
    if release.get("tag") != RELEASE_TAG:
        errors.append("Source Reconstruction 2.0 tag name differs")
    if release.get("status") not in {"development", "tag-ready", "tagged"}:
        errors.append("Source Reconstruction 2.0 status is invalid")
    return errors


def validate_predecessor(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    predecessor = as_object(release.get("predecessor"), "predecessor", errors)
    expected_manifest = "config/source_reconstruction_1_0.json"
    expected_tag = "source-reconstruction-1.0"
    if predecessor.get("manifest") != expected_manifest:
        errors.append("predecessor manifest must be the accepted Source 1.0 contract")
    if predecessor.get("tag") != expected_tag:
        errors.append("predecessor tag must be source-reconstruction-1.0")
    commit = predecessor.get("commit")
    if not valid_digest(commit, 40):
        errors.append("predecessor commit must be a full lowercase SHA-1")

    manifest_path = project_root / expected_manifest
    if not manifest_path.is_file():
        errors.append("accepted Source 1.0 manifest is missing")
    else:
        accepted = load_json(manifest_path)
        if accepted.get("tag") != expected_tag or accepted.get("status") not in {
            "tag-ready",
            "tagged",
        }:
            errors.append("accepted Source 1.0 manifest is not a releasable predecessor")

    tag_result = run_git(project_root, "rev-parse", f"{expected_tag}^{{}}")
    if tag_result.returncode:
        errors.append("accepted Source 1.0 tag is unavailable")
    elif tag_result.stdout.strip() != commit:
        errors.append("predecessor commit differs from the peeled Source 1.0 tag")
    return errors


def validate_scope(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    included = release.get("included_scope")
    if not isinstance(included, list) or not all(
        isinstance(identifier, str) and identifier for identifier in included
    ):
        errors.append("included_scope must be a list of capability ids")
    elif len(included) != len(set(included)):
        errors.append("included_scope contains duplicate capability ids")

    excluded_entries = as_object_list(
        release.get("excluded_scope"), "excluded_scope", errors
    )
    excluded = unique_objects(excluded_entries, "excluded_scope", errors)
    for identifier, entry in excluded.items():
        if entry.get("status") not in VALID_EXCLUDED_STATUSES:
            errors.append(f"excluded_scope {identifier} has invalid status")
        if not entry.get("reason"):
            errors.append(f"excluded_scope {identifier} has no reason")
        evidence = entry.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"excluded_scope {identifier} has no evidence")
            continue
        for relative in evidence:
            if not (project_root / str(relative)).exists():
                errors.append(
                    f"excluded_scope {identifier} names missing evidence: {relative}"
                )
    if "japanese_release_profile" not in excluded:
        errors.append("excluded_scope must classify the Japanese profile")
    return errors


def validate_artifact(
    artifact: dict[str, Any], profile: dict[str, Any], targets: set[str]
) -> list[str]:
    errors: list[str] = []
    identifier = str(artifact.get("id", "<unknown>"))
    if artifact.get("profile") != profile.get("id"):
        errors.append(f"artifact {identifier} profile binding differs")
    if artifact.get("build_target") not in targets:
        errors.append(f"artifact {identifier} has no build target")
    rom = profile.get("rom", {})
    for field in ("size", "sha1", "sha256"):
        if artifact.get(field) != rom.get(field):
            errors.append(f"artifact {identifier} {field} differs from revision profile")
    regions = as_object(artifact.get("regions"), f"artifact {identifier} regions", errors)
    for region_name in ("header", "prg", "chr"):
        actual = as_object(
            regions.get(region_name), f"artifact {identifier} {region_name}", errors
        )
        expected = as_object(
            profile.get(region_name), f"revision profile {region_name}", errors
        )
        for field in ("size", "sha1", "sha256"):
            if actual.get(field) != expected.get(field):
                errors.append(
                    f"artifact {identifier} {region_name} {field} differs from profile"
                )
    return errors


def validate_profiles(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    revision_path = project_root / str(release.get("revision_manifest", ""))
    revisions = load_json(revision_path)
    if revisions.get("schema_version") != 1:
        errors.append("unsupported revision profile manifest schema")
    if set(revisions.get("source_2_required_profiles", [])) != SUPPORTED_PROFILES:
        errors.append("revision manifest Source 2.0 profile set differs")
    revision_entries = as_object_list(revisions.get("profiles"), "revision profiles", errors)
    revisions_by_id = unique_objects(revision_entries, "revision profile", errors)

    release_entries = as_object_list(release.get("profiles"), "release profiles", errors)
    release_by_id = unique_objects(release_entries, "release profile", errors)
    artifact_entries = as_object_list(release.get("artifacts"), "artifacts", errors)
    artifacts = unique_objects(artifact_entries, "artifact", errors)
    targets = parse_make_targets(project_root / "Makefile")

    for profile_id in sorted(SUPPORTED_PROFILES):
        revision = revisions_by_id.get(profile_id)
        profile = release_by_id.get(profile_id)
        artifact_id = f"{profile_id}_nes_rom"
        artifact = artifacts.get(artifact_id)
        if revision is None:
            errors.append(f"required revision profile is missing: {profile_id}")
            continue
        if revision.get("source_status") != "complete":
            errors.append(f"required revision source is not complete: {profile_id}")
        if not isinstance(profile, dict) or (
            profile.get("status"),
            profile.get("identity"),
            profile.get("runtime"),
            profile.get("artifact"),
        ) != ("supported", "byte-identical", "direct", artifact_id):
            errors.append(
                f"{profile_id} release profile does not bind source, identity, runtime, and artifact"
            )
        if artifact is None:
            errors.append(f"required artifact is missing: {artifact_id}")
        else:
            errors.extend(validate_artifact(artifact, revision, targets))

    japan = release_by_id.get("japan")
    if not isinstance(japan, dict) or (
        japan.get("status"), japan.get("excluded_scope")
    ) != ("planned", "japanese_release_profile"):
        errors.append("Japan profile must remain tied to planned excluded scope")
    return errors


def validate_runtime(project_root: Path, release: dict[str, Any]) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    scenario_keys: set[str] = set()
    coverage_entries = as_object_list(
        release.get("runtime_coverage"), "runtime_coverage", errors
    )
    coverage = unique_objects(
        [dict(entry, id=entry.get("profile_id")) for entry in coverage_entries],
        "runtime profile",
        errors,
    )
    if set(coverage) != SUPPORTED_PROFILES:
        errors.append("runtime_coverage must contain direct USA and Europe records")
    artifact_by_profile = {
        str(entry.get("profile")): entry
        for entry in release.get("artifacts", [])
        if isinstance(entry, dict) and entry.get("profile")
    }
    for profile_id in sorted(SUPPORTED_PROFILES):
        entry = coverage.get(profile_id)
        if entry is None:
            continue
        if entry.get("mode") != "direct":
            errors.append(f"runtime profile {profile_id} must use direct evidence")
        manifest_path = project_root / str(entry.get("manifest", ""))
        runtime = load_json(manifest_path)
        if runtime.get("schema_version") != 1:
            errors.append(f"runtime profile {profile_id} has unsupported schema")
        if runtime.get("profile", "usa") != profile_id:
            errors.append(f"runtime manifest profile differs for {profile_id}")
        artifact = artifact_by_profile.get(profile_id, {})
        if runtime.get("rom_sha1") != artifact.get("sha1"):
            errors.append(f"runtime ROM SHA-1 differs for {profile_id}")
        actual = [
            scenario.get("id")
            for scenario in runtime.get("scenarios", [])
            if isinstance(scenario, dict)
        ]
        if entry.get("scenarios") != actual:
            errors.append(f"runtime scenario order differs for {profile_id}")
        if not actual:
            errors.append(f"runtime profile {profile_id} has no scenarios")
        scenario_keys.update(f"{profile_id}:{identifier}" for identifier in actual)
    return scenario_keys, errors


def validate_authoring(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    targets = parse_make_targets(project_root / "Makefile")
    entries = as_object_list(release.get("authoring"), "authoring", errors)
    authoring = unique_objects(entries, "authoring capability", errors)
    if set(authoring) != {"levels", "audio", "graphics", "presentation"}:
        errors.append(
            "authoring must declare exactly the accepted level, audio, graphics, and presentation tools"
        )
    for identifier, entry in authoring.items():
        if set(entry.get("profiles", [])) != SUPPORTED_PROFILES:
            errors.append(f"authoring {identifier} profile set differs")
        if not isinstance(entry.get("schema_version"), int):
            errors.append(f"authoring {identifier} has no document schema version")
        for field in ("codec", "model"):
            relative = entry.get(field)
            if not isinstance(relative, str) or not (project_root / relative).is_file():
                errors.append(f"authoring {identifier} names missing {field}: {relative}")
        capabilities = entry.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities:
            errors.append(f"authoring {identifier} has no typed capabilities")
        capacity = as_object(
            entry.get("capacity_contract"),
            f"authoring {identifier} capacity_contract",
            errors,
        )
        if capacity.get("owner") != "profile":
            errors.append(f"authoring {identifier} capacities are not profile-owned")
        evidence = capacity.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"authoring {identifier} has no capacity evidence")
        else:
            for relative in evidence:
                if not (project_root / str(relative)).exists():
                    errors.append(
                        f"authoring {identifier} names missing capacity evidence: {relative}"
                    )
        target_map = as_object(
            entry.get("targets"), f"authoring {identifier} targets", errors
        )
        if set(target_map) != REQUIRED_AUTHORING_ROLES:
            errors.append(f"authoring {identifier} target roles differ")
        for role, target in target_map.items():
            if target not in targets:
                errors.append(
                    f"authoring {identifier} {role} names missing target: {target}"
                )
        for field in ("workspace_pattern", "output_pattern"):
            pattern = entry.get(field)
            if not isinstance(pattern, str) or "{profile}" not in pattern:
                errors.append(f"authoring {identifier} has no profile-aware {field}")
                continue
            for profile_id in SUPPORTED_PROFILES:
                path = pattern.format(profile=profile_id)
                ignored = run_git(project_root, "check-ignore", "-q", path)
                if ignored.returncode:
                    errors.append(
                        f"authoring {identifier} {field} is not ignored: {path}"
                    )
    return errors


def validate_structured_data(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    targets = parse_make_targets(project_root / "Makefile")
    entries = as_object_list(
        release.get("structured_data_contracts"), "structured_data_contracts", errors
    )
    contracts = unique_objects(entries, "structured-data contract", errors)
    required = {
        "rooms",
        "scheduler",
        "enemy_ai",
        "enemy_record_pointers",
        "item_handlers",
        "ppu_updates",
        "object_animations",
        "object_motion",
        "title_and_demo",
        "audio",
    }
    if set(contracts) != required:
        errors.append("structured-data contract inventory differs")
    for identifier, entry in contracts.items():
        if set(entry.get("profiles", [])) != SUPPORTED_PROFILES:
            errors.append(f"structured-data {identifier} profile set differs")
        target = entry.get("audit_target")
        if target not in targets:
            errors.append(f"structured-data {identifier} names missing target: {target}")
        manifests = entry.get("manifests")
        if not isinstance(manifests, list) or not manifests:
            errors.append(f"structured-data {identifier} has no profile manifests")
            continue
        for relative in manifests:
            if not (project_root / str(relative)).is_file():
                errors.append(
                    f"structured-data {identifier} names missing manifest: {relative}"
                )
    return errors


def validate_toolchain(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    contract = as_object(release.get("toolchain"), "toolchain", errors)
    manifest_path = project_root / str(contract.get("manifest", ""))
    manifest = load_json(manifest_path)
    if manifest.get("schema_version") != 1:
        errors.append("unsupported toolchain manifest schema")
    component_ids = {
        str(entry.get("id"))
        for entry in manifest.get("components", [])
        if isinstance(entry, dict) and entry.get("id")
    }
    if set(contract.get("components", [])) != component_ids:
        errors.append("Source 2.0 toolchain component selection differs")
    host_ids = {
        str(entry.get("id"))
        for entry in manifest.get("hosts", [])
        if isinstance(entry, dict) and entry.get("id")
    }
    if contract.get("host") not in host_ids:
        errors.append("Source 2.0 toolchain host is not pinned")
    private_profiles = contract.get("private_profile_inputs")
    if not isinstance(private_profiles, list) or set(private_profiles) != SUPPORTED_PROFILES:
        errors.append("toolchain must bind private inputs for USA and Europe")
    if contract.get("private_input_owner") != release.get("revision_manifest"):
        errors.append("revision manifest must own Source 2.0 private input identities")
    return errors


def validate_requirements(
    project_root: Path,
    release: dict[str, Any],
    scenario_keys: set[str],
) -> list[str]:
    errors: list[str] = []
    targets = parse_make_targets(project_root / "Makefile")
    artifact_ids = {
        str(entry.get("id"))
        for entry in release.get("artifacts", [])
        if isinstance(entry, dict) and entry.get("id")
    }
    requirements = as_object(release.get("requirements"), "requirements", errors)
    if set(requirements) != REQUIRED_REQUIREMENTS:
        missing = sorted(REQUIRED_REQUIREMENTS - set(requirements))
        extra = sorted(set(requirements) - REQUIRED_REQUIREMENTS)
        errors.append(f"Source 2.0 requirement IDs differ: missing={missing}, extra={extra}")
    for identifier, value in requirements.items():
        requirement = as_object(value, f"requirement {identifier}", errors)
        if requirement.get("status") != "satisfied":
            errors.append(f"requirement {identifier} is not satisfied")
        evidence = as_object(
            requirement.get("evidence"), f"requirement {identifier} evidence", errors
        )
        count = 0
        for target in evidence.get("targets", []):
            count += 1
            if target not in targets:
                errors.append(f"requirement {identifier} names missing target: {target}")
        for relative in evidence.get("files", []):
            count += 1
            if not (project_root / str(relative)).exists():
                errors.append(f"requirement {identifier} names missing file: {relative}")
        for scenario in evidence.get("scenarios", []):
            count += 1
            if scenario not in scenario_keys:
                errors.append(f"requirement {identifier} names unknown scenario: {scenario}")
        for artifact in evidence.get("artifacts", []):
            count += 1
            if artifact not in artifact_ids:
                errors.append(f"requirement {identifier} names unknown artifact: {artifact}")
        if not count:
            errors.append(f"requirement {identifier} has no concrete evidence")
    return errors


def validate_paths_and_gates(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    targets = parse_make_targets(project_root / "Makefile")
    for field in ("required_documents", "required_files"):
        paths = release.get(field)
        if not isinstance(paths, list) or not paths:
            errors.append(f"{field} must be a non-empty path list")
            continue
        for relative in paths:
            if not (project_root / str(relative)).exists():
                errors.append(f"required release path is missing: {relative}")
    required_targets = release.get("required_make_targets")
    if not isinstance(required_targets, list) or not required_targets:
        errors.append("required_make_targets must be a non-empty list")
    else:
        for target in required_targets:
            if target not in targets:
                errors.append(f"required Make target is missing: {target}")
    if release.get("aggregate_gates") != {
        "pre_tag": ["make source-2-check"],
        "post_tag": ["make source-2-post-tag-audit"],
    }:
        errors.append("aggregate_gates differ from the Source 2.0 interface")
    makefile = project_root / "Makefile"
    source_1_recipe = make_recipe(makefile, "release-check")
    if not source_1_recipe or "source-1-regression-check" not in source_1_recipe[0]:
        errors.append("release-check no longer begins with the reusable Source 1.0 gate")
    regression_recipe = make_recipe(makefile, "source-2-regression-check")
    if not regression_recipe or "source-1-regression-check" not in regression_recipe[0]:
        errors.append("Source 2.0 regression gate does not begin with Source 1.0")
    release_recipe = make_recipe(makefile, "source-2-check")
    if not release_recipe or "source-2-regression-check" not in release_recipe[0]:
        errors.append("Source 2.0 release gate does not begin with its regression gate")
    return errors


def validate_policy(release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    provenance = as_object(release.get("provenance"), "provenance", errors)
    if provenance.get("private_inputs_tracked") is not False:
        errors.append("provenance must reject tracked private inputs")
    if provenance.get("generated_outputs_tracked") is not False:
        errors.append("provenance must reject tracked generated outputs")
    licensing = as_object_list(release.get("licensing"), "licensing", errors)
    categories = {entry.get("category") for entry in licensing}
    required = {
        "project_authored",
        "reconstructed_game_source",
        "imported_material",
        "bundled_external_tools",
        "external_tool",
        "private_input",
    }
    if categories != required:
        errors.append("licensing categories do not cover every Source 2.0 component")
    for entry in licensing:
        if not all(
            entry.get(field)
            for field in (
                "component",
                "origin",
                "license_id_or_status",
                "redistribution",
                "notes",
            )
        ):
            errors.append("licensing entry lacks origin, status, or redistribution notes")
    history = as_object(release.get("history"), "history", errors)
    for field in ("base_commit", "release_subject", "expected_author", "codex_trailer"):
        if not history.get(field):
            errors.append(f"history contract lacks {field}")
    deviations = as_object_list(
        release.get("layout_deviations"), "layout_deviations", errors
    )
    for entry in deviations:
        if not all(
            entry.get(field)
            for field in ("rule_id", "actual_path", "reason", "equivalent_control")
        ):
            errors.append("layout deviation lacks rule, path, reason, or control")
    return errors


def validate_delta(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    targets = parse_make_targets(project_root / "Makefile")
    artifacts = {
        str(entry.get("id"))
        for entry in release.get("artifacts", [])
        if isinstance(entry, dict) and entry.get("id")
    }
    entries = as_object_list(release.get("delta"), "delta", errors)
    delta = unique_objects(entries, "delta", errors)
    if not delta:
        errors.append("delta must describe changes since Source 1.0")
    for identifier, entry in delta.items():
        if entry.get("kind") not in {
            "source",
            "tooling",
            "evidence",
            "documentation",
            "release",
        }:
            errors.append(f"delta {identifier} has invalid kind")
        if not entry.get("summary"):
            errors.append(f"delta {identifier} has no summary")
        evidence = entry.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"delta {identifier} has no evidence")
            continue
        for value in evidence:
            if value not in targets and value not in artifacts and not (
                project_root / str(value)
            ).exists():
                errors.append(f"delta {identifier} names missing evidence: {value}")
    return errors


def validate_source_2_release(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors = validate_contract_header(release)
    errors.extend(validate_predecessor(project_root, release))
    errors.extend(validate_scope(project_root, release))
    errors.extend(validate_profiles(project_root, release))
    scenario_keys, runtime_errors = validate_runtime(project_root, release)
    errors.extend(runtime_errors)
    errors.extend(validate_authoring(project_root, release))
    errors.extend(validate_structured_data(project_root, release))
    errors.extend(validate_toolchain(project_root, release))
    errors.extend(validate_requirements(project_root, release, scenario_keys))
    errors.extend(validate_paths_and_gates(project_root, release))
    errors.extend(validate_policy(release))
    errors.extend(validate_delta(project_root, release))
    return errors


def validate_lifecycle_status(release: dict[str, Any], command: str) -> list[str]:
    """Keep the immutable tagged manifest in its pre-publication ready state."""
    if command in {"pre-tag-audit", "post-tag-audit"} and release.get(
        "status"
    ) != "tag-ready":
        return [f"{command} requires status tag-ready"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "pre-tag-audit", "post-tag-audit"))
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument(
        "--release",
        type=Path,
        default=ROOT / "config" / "source_reconstruction_2_0.json",
    )
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    try:
        release = load_json(args.release)
        errors = validate_source_2_release(project_root, release)
        errors.extend(validate_lifecycle_status(release, args.command))
        if args.command == "pre-tag-audit":
            errors.extend(validate_pre_tag(project_root, release))
        elif args.command == "post-tag-audit":
            errors.extend(validate_post_tag(project_root, release))
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        print(f"[FAIL] Source Reconstruction 2.0 audit found {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(
        "[OK] Source Reconstruction 2.0 release contract: "
        "2 source profiles, 2 direct runtime manifests, and 4 authoring models"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
