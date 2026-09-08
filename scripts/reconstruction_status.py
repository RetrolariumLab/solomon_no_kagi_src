#!/usr/bin/env python3
"""Measure and audit semantic source-reconstruction progress."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LABEL_RE = re.compile(r"^([A-Za-z_@.?][A-Za-z0-9_@.?]*):\s*$")
GENERATED_LABEL_RE = re.compile(r"^_label_bank[0-9]+_[0-9a-f]+$")
RAW_FLOW_RE = re.compile(
    r"^\s*(?:BCC|BCS|BEQ|BMI|BNE|BPL|BVC|BVS|JMP|JSR)\s+\$[0-9A-Fa-f]{4}\b"
)
MAP_SEGMENT_RE = re.compile(
    r"^(\S+)\s+([0-9A-Fa-f]{6})\s+([0-9A-Fa-f]{6})\s+([0-9A-Fa-f]{6})\s+[0-9A-Fa-f]{5}\s*$"
)
LABEL_FILE_RE = re.compile(r"^al\s+([0-9A-Fa-f]{6})\s+\.?([^\s]+)\s*$")
MAKE_TARGET_RE = re.compile(r"^([A-Za-z0-9_.-]+)(?:\s+[^:]*)?:")
CONFIDENCE_LEVELS = {"confirmed", "high", "tentative", "unknown"}


@dataclass(frozen=True)
class SourceLabel:
    path: Path
    line: int


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def makefile_sources(path: Path) -> list[Path]:
    """Return the root Makefile followed by its responsibility fragments."""

    fragment_root = path.parent / "mk"
    fragments = sorted(fragment_root.glob("*.mk")) if fragment_root.is_dir() else []
    return [path, *fragments]


def parse_make_targets(path: Path) -> set[str]:
    targets: set[str] = set()
    for source in makefile_sources(path):
        for line in source.read_text(encoding="utf-8").splitlines():
            if line.startswith((" ", "\t", ".")):
                continue
            match = MAKE_TARGET_RE.match(line)
            if match:
                targets.add(match.group(1))
    return targets


def parse_number(value: object, field: str) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    raise ValueError(f"invalid integer for {field}: {value!r}")


def assembly_paths(project_root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in (project_root / "src").rglob("*")
            if path.is_file() and path.suffix.lower() in {".asm", ".inc"}
        ),
        key=lambda path: path.as_posix().lower(),
    )


def source_labels(project_root: Path) -> dict[str, SourceLabel]:
    labels: dict[str, SourceLabel] = {}
    for path in assembly_paths(project_root):
        relative = path.relative_to(project_root)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = LABEL_RE.match(line)
            if match:
                # The default-profile module owns names reused by later
                # mutually exclusive regional source alternatives.
                labels.setdefault(match.group(1), SourceLabel(relative, line_number))
    return labels


def parse_linker_map(path: Path) -> dict[str, tuple[int, int, int]]:
    segments: dict[str, tuple[int, int, int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = MAP_SEGMENT_RE.match(line)
        if match:
            segments[match.group(1)] = tuple(
                int(match.group(index), 16) for index in range(2, 5)
            )
    return segments


def parse_label_file(path: Path) -> dict[str, int]:
    labels: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = LABEL_FILE_RE.match(line)
        if match:
            labels[match.group(2)] = int(match.group(1), 16)
    return labels


def collect_metrics(project_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    paths = assembly_paths(project_root)
    labels = source_labels(project_root)
    generated = sum(GENERATED_LABEL_RE.fullmatch(name) is not None for name in labels)
    raw_flow = 0
    for path in paths:
        raw_flow += sum(
            RAW_FLOW_RE.match(line) is not None
            for line in path.read_text(encoding="utf-8").splitlines()
        )
    modules = manifest.get("modules", [])
    documented_bytes = sum(
        parse_number(module["end"], f"{module.get('id')}.end")
        - parse_number(module["start"], f"{module.get('id')}.start")
        + 1
        for module in modules
    )
    prg_size = parse_number(manifest.get("reference_prg_size"), "reference_prg_size")
    preservation = project_root / "src" / "preservation" / "prg.asm"
    preservation_lines = (
        len(preservation.read_text(encoding="utf-8").splitlines())
        if preservation.is_file()
        else 0
    )
    return {
        "assembly_files": len(paths),
        "semantic_modules": len(modules),
        "documented_prg_bytes": documented_bytes,
        "documented_prg_percent": round(documented_bytes * 100.0 / prg_size, 3),
        "preservation_lines": preservation_lines,
        "source_labels": len(labels),
        "semantic_labels": len(labels) - generated,
        "generated_labels": generated,
        "raw_control_flow_targets": raw_flow,
    }


def collect_provenance_metrics(ledger: dict[str, Any]) -> dict[str, int]:
    entries = ledger.get("entries")
    if not isinstance(entries, list):
        return {}
    counts = {
        confidence: sum(entry.get("confidence") == confidence for entry in entries)
        for confidence in CONFIDENCE_LEVELS
    }
    return {
        "provenance_entries": len(entries),
        "confirmed_provenance": counts["confirmed"],
        "high_provenance": counts["high"],
        "tentative_provenance": counts["tentative"],
        "unknown_provenance": counts["unknown"],
    }


def validate(
    project_root: Path,
    manifest: dict[str, Any],
    ledger: dict[str, Any],
    map_path: Path,
    labels_path: Path,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("unsupported reconstruction manifest schema")
    if ledger.get("schema_version") != 1:
        errors.append("unsupported label provenance schema")
    metrics = collect_metrics(project_root, manifest)
    metrics.update(collect_provenance_metrics(ledger))
    source = source_labels(project_root)
    segments = parse_linker_map(map_path)
    linked_labels = parse_label_file(labels_path)

    modules = manifest.get("modules")
    if not isinstance(modules, list):
        return metrics, errors + ["modules must be a list"]
    for module in modules:
        module_id = str(module.get("id", "<missing>"))
        relative = Path(str(module.get("path", "")))
        module_path = project_root / relative
        if not module_path.is_file():
            errors.append(f"module {module_id} is missing: {relative.as_posix()}")
            continue
        segment_name = str(module.get("segment", ""))
        expected_start = parse_number(module.get("start"), f"{module_id}.start")
        expected_end = parse_number(module.get("end"), f"{module_id}.end")
        expected_size = expected_end - expected_start + 1
        actual_segment = segments.get(segment_name)
        if actual_segment != (expected_start, expected_end, expected_size):
            errors.append(
                f"module {module_id} segment mismatch: expected "
                f"{expected_start:04X}-{expected_end:04X}/{expected_size:04X}, "
                f"got {actual_segment}"
            )
        for label in module.get("required_labels", []):
            location = source.get(str(label))
            if location is None or location.path != relative:
                errors.append(f"module {module_id} is missing required label {label}")

    entries = ledger.get("entries")
    if not isinstance(entries, list):
        return metrics, errors + ["provenance entries must be a list"]
    seen_addresses: set[int] = set()
    seen_names: set[str] = set()
    for entry in entries:
        current = str(entry.get("current", ""))
        address = parse_number(entry.get("address"), f"{current}.address")
        if address in seen_addresses:
            errors.append(f"duplicate provenance address: {address:04X}")
        if current in seen_names:
            errors.append(f"duplicate provenance name: {current}")
        seen_addresses.add(address)
        seen_names.add(current)
        if not entry.get("previous"):
            errors.append(f"provenance entry {current} has no previous identifier")
        if entry.get("confidence") not in CONFIDENCE_LEVELS:
            errors.append(f"provenance entry {current} has invalid confidence")
        evidence = entry.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"provenance entry {current} has no evidence")
        if current not in source:
            errors.append(f"provenance label is absent from source: {current}")
        if linked_labels.get(current) != address:
            errors.append(
                f"linked address mismatch for {current}: expected {address:04X}, "
                f"got {linked_labels.get(current)}"
            )

    original_labels = manifest.get("original_labels", [])
    if not isinstance(original_labels, list) or not all(
        isinstance(label, str) for label in original_labels
    ):
        errors.append("original_labels must be a list of strings")
        original_labels = []
    semantic_paths = {
        Path(str(module.get("path", "")))
        for module in modules
        if module.get("status") == "semantic"
    }
    for name, location in sorted(source.items()):
        if (
            location.path in semantic_paths
            and GENERATED_LABEL_RE.fullmatch(name) is None
            and name not in original_labels
            and name not in seen_names
        ):
            errors.append(f"semantic label has no provenance entry: {name}")
    for name in original_labels:
        location = source.get(name)
        if location is None or location.path not in semantic_paths:
            errors.append(f"declared original label is absent from semantic modules: {name}")

    thresholds = manifest.get("thresholds", {})
    minimums = {
        "minimum_semantic_modules": "semantic_modules",
        "minimum_documented_prg_bytes": "documented_prg_bytes",
        "minimum_provenance_entries": None,
    }
    for threshold_name, metric_name in minimums.items():
        expected = parse_number(thresholds.get(threshold_name), threshold_name)
        actual = len(entries) if metric_name is None else metrics[metric_name]
        if actual < expected:
            errors.append(f"{threshold_name} regression: got {actual}, require at least {expected}")
    maximums = {
        "maximum_preservation_lines": "preservation_lines",
        "maximum_generated_labels": "generated_labels",
        "maximum_raw_control_flow_targets": "raw_control_flow_targets",
    }
    for threshold_name, metric_name in maximums.items():
        expected = parse_number(thresholds.get(threshold_name), threshold_name)
        actual = metrics[metric_name]
        if actual > expected:
            errors.append(f"{threshold_name} regression: got {actual}, allow at most {expected}")
    return metrics, errors


def validate_release_paths(
    project_root: Path, release: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    documents = release.get("required_documents")
    if not isinstance(documents, list) or not all(
        isinstance(value, str) for value in documents
    ):
        errors.append("required_documents must be a list of paths")
    else:
        for relative in documents:
            if not (project_root / relative).is_file():
                errors.append(f"required release document is missing: {relative}")

    targets = release.get("required_make_targets")
    if not isinstance(targets, list) or not all(
        isinstance(value, str) for value in targets
    ):
        errors.append("required_make_targets must be a list of names")
    else:
        makefile_targets = parse_make_targets(project_root / "Makefile")
        for target in targets:
            if target not in makefile_targets:
                errors.append(f"required Make target is missing: {target}")

    deferred = release.get("deferred_to_2_0")
    if not isinstance(deferred, list) or not deferred:
        errors.append("deferred_to_2_0 must explicitly record later scope")
    return errors


def validate_release_v1(
    project_root: Path,
    release: dict[str, Any],
    metrics: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if release.get("schema_version") != 1:
        errors.append("unsupported Source Reconstruction 1.0 manifest schema")
    if release.get("status") != "tag-ready":
        errors.append("Source Reconstruction 1.0 status is not tag-ready")
    if release.get("tag") != "source-reconstruction-1.0":
        errors.append("Source Reconstruction 1.0 tag name differs")

    asset_path = project_root / str(release.get("asset_manifest", ""))
    runtime_path = project_root / str(release.get("runtime_manifest", ""))
    assets = load_json(asset_path)
    runtime = load_json(runtime_path)
    if assets.get("schema_version") != 1:
        errors.append("unsupported asset manifest schema")
    if runtime.get("schema_version") != 1:
        errors.append("unsupported runtime manifest schema")

    reference = release.get("reference")
    asset_reference = assets.get("reference_rom")
    if not isinstance(reference, dict) or not isinstance(asset_reference, dict):
        errors.append("release and asset reference contracts must be objects")
    else:
        for field in ("file_sha1", "prg_sha1", "chr_sha1"):
            if reference.get(field) != asset_reference.get(field):
                errors.append(f"release {field} differs from asset manifest")
        if runtime.get("rom_sha1") != reference.get("file_sha1"):
            errors.append("runtime ROM SHA-1 differs from release reference")

    expected_metrics = release.get("reconstruction_metrics")
    if not isinstance(expected_metrics, dict):
        errors.append("reconstruction_metrics must be an object")
    else:
        for name, expected in expected_metrics.items():
            if metrics.get(name) != expected:
                errors.append(
                    f"release metric {name} differs: "
                    f"expected {expected}, got {metrics.get(name)}"
                )

    expected_scenarios = release.get("runtime_scenarios")
    actual_scenarios = runtime.get("scenarios")
    if not isinstance(expected_scenarios, list) or not all(
        isinstance(value, str) for value in expected_scenarios
    ):
        errors.append("runtime_scenarios must be a list of names")
    elif not isinstance(actual_scenarios, list):
        errors.append("runtime scenario manifest has no scenario list")
    else:
        actual_names = [scenario.get("id") for scenario in actual_scenarios]
        if actual_names != expected_scenarios:
            errors.append("runtime scenario order differs from release manifest")

    errors.extend(validate_release_paths(project_root, release))
    return errors


REQUIRED_RELEASE_REQUIREMENTS = {
    "canonical_identity",
    "reproducible_build",
    "source_boundary",
    "provenance_and_unknowns",
    "baseline_documentation",
    "baseline_validation",
    "release_contract",
    "private_inputs",
    "generated_outputs",
    "claims_need_evidence",
    "toolchain_reproducibility",
    "runtime_coverage",
    "licensing_and_provenance",
    "tag_integrity",
    "commit_history",
}


def validate_release_evidence(
    project_root: Path,
    release: dict[str, Any],
    scenario_names: set[str],
    artifact_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    targets = parse_make_targets(project_root / "Makefile")
    requirements = release.get("requirements")
    if not isinstance(requirements, dict):
        return ["requirements must be an object"]
    if set(requirements) != REQUIRED_RELEASE_REQUIREMENTS:
        missing = sorted(REQUIRED_RELEASE_REQUIREMENTS - set(requirements))
        extra = sorted(set(requirements) - REQUIRED_RELEASE_REQUIREMENTS)
        errors.append(f"release requirement IDs differ: missing={missing}, extra={extra}")
    for identifier, requirement in requirements.items():
        if not isinstance(requirement, dict):
            errors.append(f"requirement {identifier} must be an object")
            continue
        if requirement.get("status") != "satisfied":
            errors.append(f"requirement {identifier} is not satisfied")
        evidence = requirement.get("evidence")
        if not isinstance(evidence, dict):
            errors.append(f"requirement {identifier} has no evidence object")
            continue
        evidence_count = 0
        for target in evidence.get("targets", []):
            evidence_count += 1
            if target not in targets:
                errors.append(f"requirement {identifier} names missing target: {target}")
        for relative in evidence.get("files", []):
            evidence_count += 1
            if not (project_root / str(relative)).exists():
                errors.append(f"requirement {identifier} names missing file: {relative}")
        for scenario in evidence.get("scenarios", []):
            evidence_count += 1
            if scenario not in scenario_names:
                errors.append(f"requirement {identifier} names unknown scenario: {scenario}")
        for artifact in evidence.get("artifacts", []):
            evidence_count += 1
            if artifact not in artifact_ids:
                errors.append(f"requirement {identifier} names unknown artifact: {artifact}")
        if not evidence_count:
            errors.append(f"requirement {identifier} has no concrete evidence")
    return errors


def validate_release_v3_paths(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("required_documents", "required_files"):
        paths = release.get(field)
        if not isinstance(paths, list) or not paths or not all(
            isinstance(value, str) for value in paths
        ):
            errors.append(f"{field} must be a non-empty list of paths")
            continue
        for relative in paths:
            if not (project_root / relative).exists():
                errors.append(f"required release path is missing: {relative}")
    required_targets = release.get("required_make_targets")
    if not isinstance(required_targets, list) or not required_targets or not all(
        isinstance(value, str) for value in required_targets
    ):
        errors.append("required_make_targets must be a non-empty list of names")
    else:
        targets = parse_make_targets(project_root / "Makefile")
        for target in required_targets:
            if target not in targets:
                errors.append(f"required Make target is missing: {target}")
    return errors


def validate_release(
    project_root: Path,
    release: dict[str, Any],
    metrics: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if release.get("schema_version") != 3:
        errors.append("unsupported Source Reconstruction 1.0 manifest schema")
    if release.get("release_line") != "1.0":
        errors.append("release_line must be 1.0")
    if "contract" in release:
        errors.append("release manifest must contain only project-owned metadata")
    if release.get("release") != {
        "name": "Source Reconstruction 1.0",
        "version": "1.0",
    }:
        errors.append("release name or version differs")
    if release.get("release_kind") != "preservation":
        errors.append("release_kind must be preservation")
    if release.get("status") != "tag-ready":
        errors.append("Source Reconstruction 1.0 status is not tag-ready")
    if release.get("tag") != "source-reconstruction-1.0":
        errors.append("Source Reconstruction 1.0 tag name differs")
    predecessor = release.get("predecessor")
    if not isinstance(predecessor, dict) or any(
        predecessor.get(field) is not None for field in ("manifest", "tag", "commit")
    ):
        errors.append("the first release predecessor must explicitly contain null refs")

    included_scope = release.get("included_scope")
    if not isinstance(included_scope, list) or "usa_preservation_profile" not in included_scope:
        errors.append("included_scope must accept the USA preservation profile")
    excluded_scope = release.get("excluded_scope")
    excluded_ids: set[str] = set()
    if not isinstance(excluded_scope, list) or not excluded_scope:
        errors.append("excluded_scope must explicitly record deferred work")
    else:
        for entry in excluded_scope:
            if not isinstance(entry, dict) or not entry.get("id"):
                errors.append("invalid excluded_scope entry")
                continue
            identifier = str(entry["id"])
            if identifier in excluded_ids:
                errors.append(f"duplicate excluded_scope id: {identifier}")
            excluded_ids.add(identifier)
            if entry.get("status") not in {"planned", "partial", "unsupported"}:
                errors.append(f"excluded_scope {identifier} has invalid status")
            if not entry.get("reason"):
                errors.append(f"excluded_scope {identifier} has no reason")
            for relative in entry.get("evidence", []):
                if not (project_root / str(relative)).is_file():
                    errors.append(f"excluded_scope {identifier} names missing evidence: {relative}")

    targets = parse_make_targets(project_root / "Makefile")
    artifacts = release.get("artifacts")
    artifact_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must be a non-empty list")
    else:
        for artifact in artifacts:
            if not isinstance(artifact, dict) or not artifact.get("id"):
                errors.append("invalid artifact entry")
                continue
            artifact_by_id[str(artifact["id"])] = artifact
            if artifact.get("build_target") not in targets:
                errors.append(f"artifact {artifact['id']} has no build target")

    asset_path = project_root / str(release.get("asset_manifest", ""))
    runtime_path = project_root / str(release.get("runtime_manifest", ""))
    toolchain_contract = release.get("toolchain")
    toolchain_path = project_root / str(
        toolchain_contract.get("manifest", "")
        if isinstance(toolchain_contract, dict)
        else ""
    )
    assets = load_json(asset_path)
    runtime = load_json(runtime_path)
    toolchain = load_json(toolchain_path)
    if assets.get("schema_version") != 1:
        errors.append("unsupported asset manifest schema")
    if runtime.get("schema_version") != 1:
        errors.append("unsupported runtime manifest schema")
    if toolchain.get("schema_version") != 1:
        errors.append("unsupported toolchain manifest schema")

    reference = release.get("reference")
    asset_reference = assets.get("reference_rom")
    if not isinstance(reference, dict) or not isinstance(asset_reference, dict):
        errors.append("release and asset reference contracts must be objects")
    else:
        for field in (
            "file_sha1",
            "file_sha256",
            "prg_sha1",
            "prg_sha256",
            "chr_sha1",
            "chr_sha256",
        ):
            if reference.get(field) != asset_reference.get(field):
                errors.append(f"release {field} differs from asset manifest")
        if runtime.get("rom_sha1") != reference.get("file_sha1"):
            errors.append("runtime ROM SHA-1 differs from release reference")

    artifact = artifact_by_id.get("usa_nes_rom")
    if artifact is None:
        errors.append("USA ROM artifact is missing")
    elif isinstance(asset_reference, dict):
        for artifact_field, asset_field in (
            ("size", "file_size"),
            ("sha1", "file_sha1"),
            ("sha256", "file_sha256"),
        ):
            if artifact.get(artifact_field) != asset_reference.get(asset_field):
                errors.append(f"USA ROM artifact {artifact_field} differs from asset manifest")
        regions = artifact.get("regions")
        if not isinstance(regions, dict):
            errors.append("USA ROM artifact has no significant regions")
        else:
            for region in ("header", "prg", "chr", "payload"):
                contract_region = regions.get(region)
                if not isinstance(contract_region, dict):
                    errors.append(f"USA ROM artifact region is missing: {region}")
                    continue
                for digest_name in ("sha1", "sha256"):
                    expected = asset_reference.get(f"{region}_{digest_name}")
                    if contract_region.get(digest_name) != expected:
                        errors.append(f"USA ROM {region} {digest_name} differs")

    expected_metrics = release.get("reconstruction_metrics")
    if not isinstance(expected_metrics, dict):
        errors.append("reconstruction_metrics must be an object")
    else:
        for name, expected in expected_metrics.items():
            if metrics.get(name) != expected:
                errors.append(
                    f"release metric {name} differs: expected {expected}, "
                    f"got {metrics.get(name)}"
                )

    actual_scenarios = runtime.get("scenarios")
    scenario_names = (
        [scenario.get("id") for scenario in actual_scenarios]
        if isinstance(actual_scenarios, list)
        else []
    )
    if release.get("runtime_scenarios") != scenario_names:
        errors.append("runtime scenario order differs from release manifest")
    coverage = release.get("runtime_coverage")
    if not isinstance(coverage, list) or len(coverage) != 1:
        errors.append("runtime_coverage must contain one direct USA record")
    else:
        record = coverage[0]
        if (
            not isinstance(record, dict)
            or record.get("profile_id") != "usa"
            or record.get("mode") != "direct"
            or record.get("scenarios") != scenario_names
        ):
            errors.append("USA direct runtime coverage differs from scenario manifest")

    profiles = release.get("profiles")
    profile_by_id = {
        str(profile.get("id")): profile
        for profile in profiles
        if isinstance(profile, dict) and profile.get("id")
    } if isinstance(profiles, list) else {}
    usa = profile_by_id.get("usa")
    if not isinstance(usa, dict) or (
        usa.get("status"), usa.get("identity"), usa.get("runtime"), usa.get("artifact")
    ) != ("supported", "byte-identical", "direct", "usa_nes_rom"):
        errors.append("USA profile does not bind byte identity, runtime, and artifact")
    for profile_id, excluded_id in (
        ("japan", "japanese_release_profile"),
        ("europe", "european_release_profile"),
    ):
        profile = profile_by_id.get(profile_id)
        if not isinstance(profile, dict) or profile.get("excluded_scope") != excluded_id:
            errors.append(f"{profile_id} profile is not tied to excluded scope")

    component_ids = {
        str(component.get("id"))
        for component in toolchain.get("components", [])
        if isinstance(component, dict)
    }
    private_ids = {
        str(entry.get("id"))
        for entry in toolchain.get("private_inputs", [])
        if isinstance(entry, dict)
    }
    host_ids = {
        str(host.get("id"))
        for host in toolchain.get("hosts", [])
        if isinstance(host, dict)
    }
    if not isinstance(toolchain_contract, dict) or (
        set(toolchain_contract.get("components", [])) != component_ids
        or set(toolchain_contract.get("private_inputs", [])) != private_ids
        or toolchain_contract.get("host") not in host_ids
    ):
        errors.append("release toolchain selection differs from toolchain manifest")
    for component in toolchain.get("components", []):
        if not isinstance(component, dict):
            continue
        for field in ("version", "source", "source_commit", "binary_sha256", "provenance", "verification_target"):
            if not component.get(field):
                errors.append(f"toolchain component {component.get('id')} lacks {field}")
        if len(str(component.get("binary_sha256", ""))) != 64:
            errors.append(f"toolchain component {component.get('id')} has invalid SHA-256")
        if component.get("verification_target") not in targets:
            errors.append(f"toolchain component {component.get('id')} has missing verification target")
    for private_input in toolchain.get("private_inputs", []):
        if not isinstance(private_input, dict):
            errors.append("invalid private toolchain input")
            continue
        if not all(
            private_input.get(field)
            for field in ("id", "role", "size", "sha256", "verification_target")
        ) or private_input.get("tracked") is not False:
            errors.append(f"private input {private_input.get('id')} is incomplete")
        if private_input.get("verification_target") not in targets:
            errors.append(f"private input {private_input.get('id')} has missing target")
    for host in toolchain.get("hosts", []):
        if not isinstance(host, dict) or not all(
            host.get(field)
            for field in (
                "id",
                "os",
                "architecture",
                "shell",
                "language_versions",
                "supported_status",
                "verification_target",
            )
        ):
            errors.append("supported toolchain host contract is incomplete")
        elif host.get("verification_target") not in targets:
            errors.append(f"host {host.get('id')} has missing verification target")

    aggregate = release.get("aggregate_gates")
    if aggregate != {
        "pre_tag": ["make release-check"],
        "post_tag": ["make source-1-post-tag-audit"],
    }:
        errors.append("aggregate_gates differ from the Source 1.0 interface")
    licensing = release.get("licensing")
    licensing_categories = {
        entry.get("category") for entry in licensing if isinstance(entry, dict)
    } if isinstance(licensing, list) else set()
    required_categories = {
        "project_authored",
        "reconstructed_game_source",
        "imported_material",
        "bundled_external_tools",
        "external_tool",
        "private_input",
    }
    if licensing_categories != required_categories:
        errors.append("licensing categories do not cover every release component")
    elif any(
        not all(
            entry.get(field)
            for field in (
                "component",
                "origin",
                "license_id_or_status",
                "redistribution",
                "notes",
            )
        )
        for entry in licensing
        if isinstance(entry, dict)
    ):
        errors.append("licensing entry lacks origin, status, or redistribution notes")

    provenance = release.get("provenance")
    if not isinstance(provenance, dict) or (
        provenance.get("private_inputs_tracked") is not False
        or provenance.get("generated_outputs_tracked") is not False
    ):
        errors.append("provenance must reject tracked private and generated data")
    else:
        for relative in provenance.get("references", []):
            if not (project_root / str(relative)).is_file():
                errors.append(f"provenance reference is missing: {relative}")

    delta = release.get("delta")
    if not isinstance(delta, list) or not delta:
        errors.append("delta must describe the complete initial release")
    else:
        delta_ids: set[str] = set()
        known_evidence = set(targets) | set(artifact_by_id)
        for entry in delta:
            if not isinstance(entry, dict) or not entry.get("id"):
                errors.append("invalid delta entry")
                continue
            identifier = str(entry["id"])
            if identifier in delta_ids:
                errors.append(f"duplicate delta id: {identifier}")
            delta_ids.add(identifier)
            if not entry.get("kind") or not entry.get("summary"):
                errors.append(f"delta {identifier} lacks kind or summary")
            evidence = entry.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"delta {identifier} has no evidence")
                continue
            for value in evidence:
                if value not in known_evidence and not (project_root / str(value)).exists():
                    errors.append(f"delta {identifier} names missing evidence: {value}")

    deviations = release.get("layout_deviations")
    if not isinstance(deviations, list):
        errors.append("layout_deviations must be a list")
    else:
        for entry in deviations:
            if not isinstance(entry, dict) or not all(
                entry.get(field)
                for field in ("rule_id", "actual_path", "reason", "equivalent_control")
            ):
                errors.append("layout deviation lacks rule, path, reason, or control")

    history = release.get("history")
    if not isinstance(history, dict) or not all(
        history.get(field)
        for field in ("base_commit", "release_subject", "expected_author", "codex_trailer")
    ):
        errors.append("history contract is incomplete")

    errors.extend(validate_release_v3_paths(project_root, release))
    errors.extend(
        validate_release_evidence(
            project_root,
            release,
            set(str(name) for name in scenario_names),
            set(artifact_by_id),
        )
    )
    return errors


def run_git(project_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def validate_commit_history(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    history = release.get("history", {})
    base = str(history.get("base_commit", ""))
    expected_author = str(history.get("expected_author", ""))
    trailer = str(history.get("codex_trailer", ""))
    ancestry = run_git(project_root, "merge-base", "--is-ancestor", base, "HEAD")
    if ancestry.returncode:
        return [f"history base is not an ancestor of HEAD: {base}"]
    result = run_git(
        project_root,
        "log",
        "--reverse",
        "--format=%H%x1f%an <%ae>%x1f%at%x1f%ct%x1f%s%x1f%b%x1e",
        f"{base}..HEAD",
    )
    if result.returncode:
        return [f"cannot inspect commit history: {result.stderr.strip()}"]
    records = [record.strip() for record in result.stdout.split(chr(30)) if record.strip()]
    previous_author_time = -1
    previous_commit_time = -1
    for record in records:
        commit, author, author_time, commit_time, subject, body = record.split(chr(31), 5)
        short = commit[:12]
        if author != expected_author:
            errors.append(f"commit {short} has unexpected author: {author}")
        if subject.endswith(".") or subject in {"Fix", "Update", "Changes", "WIP"}:
            errors.append(f"commit {short} has an invalid subject: {subject}")
        paragraphs = [paragraph.strip() for paragraph in body.strip().split("\n\n") if paragraph.strip()]
        if paragraphs.count(trailer) != 1 or not paragraphs or paragraphs[-1] != trailer:
            errors.append(f"commit {short} has invalid Codex attribution")
        content = paragraphs[:-1] if paragraphs and paragraphs[-1] == trailer else paragraphs
        if len(content) not in (2, 3):
            errors.append(f"commit {short} must have two or three body paragraphs")
        author_value = int(author_time)
        commit_value = int(commit_time)
        if author_value <= previous_author_time:
            errors.append(f"commit {short} AuthorDate is not strictly increasing")
        if commit_value <= previous_commit_time:
            errors.append(f"commit {short} CommitDate is not strictly increasing")
        previous_author_time = author_value
        previous_commit_time = commit_value
    if not records:
        errors.append("history range contains no release commits")
    return errors


def remote_tag_lines(project_root: Path, remote: str, tag: str) -> tuple[list[str], str | None]:
    try:
        result = run_git(
            project_root,
            "ls-remote",
            "--tags",
            remote,
            f"refs/tags/{tag}",
            f"refs/tags/{tag}^{{}}",
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], str(exc)
    if result.returncode:
        return [], result.stderr.strip() or "git ls-remote failed"
    return [line for line in result.stdout.splitlines() if line.strip()], None


def validate_pre_tag(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    status = run_git(project_root, "status", "--porcelain", "--untracked-files=all")
    if status.returncode or status.stdout.strip():
        errors.append("pre-tag audit requires a clean worktree")
    tag = str(release.get("tag", ""))
    local = run_git(project_root, "rev-parse", "-q", "--verify", f"refs/tags/{tag}")
    if local.returncode == 0:
        errors.append(f"future release tag already exists locally: {tag}")
    remote = str(release.get("publish_remote", ""))
    lines, remote_error = remote_tag_lines(project_root, remote, tag)
    if remote_error:
        errors.append(f"cannot verify publish remote tag state: {remote_error}")
    elif lines:
        errors.append(f"future release tag already exists on {remote}: {tag}")
    errors.extend(validate_commit_history(project_root, release))
    head_subject = run_git(project_root, "show", "-s", "--format=%s", "HEAD")
    expected = release.get("history", {}).get("release_subject")
    if head_subject.stdout.strip() != expected:
        errors.append(f"release commit subject differs: expected {expected!r}")
    return errors


def validate_post_tag(project_root: Path, release: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    tag = str(release.get("tag", ""))
    tag_type = run_git(project_root, "cat-file", "-t", f"refs/tags/{tag}")
    if tag_type.returncode or tag_type.stdout.strip() != "tag":
        return [f"release tag is missing or is not annotated: {tag}"]
    tag_commit = run_git(project_root, "rev-parse", f"refs/tags/{tag}^{{}}")
    head_commit = run_git(project_root, "rev-parse", "HEAD")
    if tag_commit.stdout.strip() != head_commit.stdout.strip():
        errors.append("release tag peeled target differs from HEAD")
    remote = str(release.get("publish_remote", ""))
    lines, remote_error = remote_tag_lines(project_root, remote, tag)
    if remote_error:
        errors.append(f"cannot verify published tag: {remote_error}")
    else:
        peeled = [line.split()[0] for line in lines if line.endswith(f"refs/tags/{tag}^{{}}")]
        if peeled != [head_commit.stdout.strip()]:
            errors.append(f"published tag on {remote} does not peel to HEAD")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("report", "audit", "release-audit", "pre-tag-audit", "post-tag-audit"),
    )
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--map", dest="map_path", type=Path)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--release", type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    manifest_path = args.manifest or root / "config" / "reconstruction.json"
    ledger_path = args.ledger or root / "docs" / "provenance" / "label_renames.json"
    map_path = args.map_path or root / "build" / "native" / "solomons_key.map"
    labels_path = args.labels or root / "build" / "native" / "solomons_key.lbl"
    release_path = args.release or root / "config" / "source_reconstruction_1_0.json"
    try:
        manifest = load_json(manifest_path)
        ledger = load_json(ledger_path)
        if args.command == "report":
            metrics = collect_metrics(root, manifest)
            metrics.update(collect_provenance_metrics(ledger))
            print(json.dumps(metrics, indent=2, sort_keys=True))
            return 0
        metrics, errors = validate(root, manifest, ledger, map_path, labels_path)
        if args.command in {"release-audit", "pre-tag-audit", "post-tag-audit"}:
            release = load_json(release_path)
            errors.extend(validate_release(root, release, metrics))
            if args.command == "pre-tag-audit":
                errors.extend(validate_pre_tag(root, release))
            elif args.command == "post-tag-audit":
                errors.extend(validate_post_tag(root, release))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        print(f"[FAIL] Reconstruction audit found {len(errors)} error(s)", file=sys.stderr)
        return 1
    if args.command in {"release-audit", "pre-tag-audit", "post-tag-audit"}:
        phase = {
            "release-audit": "release contract",
            "pre-tag-audit": "pre-tag contract",
            "post-tag-audit": "post-tag contract",
        }[args.command]
        print(
            f"[OK] Source Reconstruction 1.0 {phase}: "
            f"{metrics['semantic_modules']} modules, "
            f"{metrics['documented_prg_bytes']} PRG bytes, "
            f"{metrics['semantic_labels']} semantic labels, "
            f"{metrics['provenance_entries']} provenance entries"
        )
    else:
        print(
            "[OK] Reconstruction inventory: "
            f"{metrics['semantic_modules']} semantic module, "
            f"{metrics['documented_prg_bytes']}/{manifest['reference_prg_size']} "
            f"PRG bytes ({metrics['documented_prg_percent']:.3f}%), "
            f"{metrics['generated_labels']} generated labels, "
            f"{metrics['raw_control_flow_targets']} raw control-flow targets"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
