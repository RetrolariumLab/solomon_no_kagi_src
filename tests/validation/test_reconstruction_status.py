from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.validation.reconstruction_status import (
    collect_metrics,
    collect_provenance_metrics,
    parse_make_targets,
    source_labels,
    validate,
    validate_release,
)
from scripts.validation.source_2_release import (
    make_recipe,
    validate_lifecycle_status,
    validate_source_2_release,
)


class ReconstructionStatusTests(unittest.TestCase):
    def make_release_fixture(
        self,
    ) -> tuple[Path, dict[str, object], dict[str, object]]:
        root = Path(__file__).resolve().parents[2]
        release = json.loads(
            (root / "config" / "source_reconstruction_1_0.json").read_text(
                encoding="utf-8"
            )
        )
        metrics = deepcopy(release["reconstruction_metrics"])
        return root, deepcopy(release), metrics

    def make_source_2_release_fixture(self) -> tuple[Path, dict[str, object]]:
        root = Path(__file__).resolve().parents[2]
        release = json.loads(
            (root / "config" / "source_reconstruction_2_0.json").read_text(
                encoding="utf-8"
            )
        )
        return root, deepcopy(release)

    def make_fixture(self) -> tuple[Path, dict[str, object], dict[str, object], Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "src" / "system").mkdir(parents=True)
        (root / "src" / "preservation").mkdir(parents=True)
        (root / "src" / "system" / "boot_and_frame.asm").write_text(
            '.segment "PRG_NMI"\nNMI:\n    RTI\n',
            encoding="utf-8",
        )
        (root / "src" / "preservation" / "prg.asm").write_text(
            "_label_bank0_9000:\n    JSR $9003\n",
            encoding="utf-8",
        )
        manifest: dict[str, object] = {
            "schema_version": 1,
            "reference_prg_size": 32768,
            "original_labels": [],
            "modules": [
                {
                    "id": "nmi",
                    "path": "src/system/boot_and_frame.asm",
                    "segment": "PRG_NMI",
                    "start": "0x8000",
                    "end": "0x8000",
                    "status": "semantic",
                    "required_labels": ["NMI"],
                }
            ],
            "thresholds": {
                "minimum_semantic_modules": 1,
                "minimum_documented_prg_bytes": 1,
                "minimum_provenance_entries": 1,
                "maximum_preservation_lines": 2,
                "maximum_generated_labels": 1,
                "maximum_raw_control_flow_targets": 1,
            },
        }
        ledger: dict[str, object] = {
            "schema_version": 1,
            "entries": [
                {
                    "address": "0x8000",
                    "previous": "$8000",
                    "current": "NMI",
                    "confidence": "confirmed",
                    "evidence": ["Vector target"],
                }
            ],
        }
        map_path = root / "game.map"
        map_path.write_text(
            "PRG_NMI              008000  008000  000001  00001\n",
            encoding="utf-8",
        )
        labels_path = root / "game.lbl"
        labels_path.write_text("al 008000 .NMI\n", encoding="utf-8")
        return root, manifest, ledger, map_path, labels_path

    def test_collects_monotonic_progress_metrics(self) -> None:
        root, manifest, _ledger, _map, _labels = self.make_fixture()
        metrics = collect_metrics(root, manifest)
        self.assertEqual(metrics["semantic_modules"], 1)
        self.assertEqual(metrics["documented_prg_bytes"], 1)
        self.assertEqual(metrics["generated_labels"], 1)
        self.assertEqual(metrics["raw_control_flow_targets"], 1)

    def test_collects_exact_provenance_confidence_distribution(self) -> None:
        _root, _manifest, ledger, _map, _labels = self.make_fixture()
        ledger["entries"].append(
            {
                "address": "0x8001",
                "previous": "$8001",
                "current": "SecondLabel",
                "confidence": "high",
                "evidence": ["Static evidence"],
            }
        )
        self.assertEqual(
            collect_provenance_metrics(ledger),
            {
                "provenance_entries": 2,
                "confirmed_provenance": 1,
                "high_provenance": 1,
                "tentative_provenance": 0,
                "unknown_provenance": 0,
            },
        )

    def test_default_source_owns_duplicate_regional_label(self) -> None:
        root, _manifest, _ledger, _map, _labels = self.make_fixture()
        alternative = root / "src" / "system" / "nmi_europe.asm"
        alternative.write_text("NMI:\n    RTI\n", encoding="utf-8")
        labels = source_labels(root)
        self.assertEqual(labels["NMI"].path, Path("src/system/boot_and_frame.asm"))

    def test_accepts_consistent_module_and_provenance(self) -> None:
        root, manifest, ledger, map_path, labels_path = self.make_fixture()
        _metrics, errors = validate(root, manifest, ledger, map_path, labels_path)
        self.assertEqual(errors, [])

    def test_rejects_linked_label_address_mismatch(self) -> None:
        root, manifest, ledger, map_path, labels_path = self.make_fixture()
        labels_path.write_text("al 008001 .NMI\n", encoding="utf-8")
        _metrics, errors = validate(root, manifest, ledger, map_path, labels_path)
        self.assertTrue(any("linked address mismatch" in error for error in errors))

    def test_rejects_semantic_label_without_provenance(self) -> None:
        root, manifest, ledger, map_path, labels_path = self.make_fixture()
        module = root / "src" / "system" / "boot_and_frame.asm"
        module.write_text(
            module.read_text(encoding="utf-8") + "UndocumentedName:\n    RTS\n",
            encoding="utf-8",
        )
        _metrics, errors = validate(root, manifest, ledger, map_path, labels_path)
        self.assertIn(
            "semantic label has no provenance entry: UndocumentedName",
            errors,
        )

    def test_release_contract_accepts_consistent_manifests(self) -> None:
        root, release, metrics = self.make_release_fixture()
        self.assertEqual(validate_release(root, release, metrics), [])
        targets = parse_make_targets(root / "Makefile")
        self.assertIn("build", targets)
        self.assertIn("source-1-audit", targets)
        self.assertIn("source-2-check", targets)

    def test_make_surface_includes_responsibility_fragments(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "mk").mkdir()
        (root / "Makefile").write_text(
            "include mk/validation.mk\nroot-target:\n\t@true\n",
            encoding="utf-8",
        )
        (root / "mk" / "validation.mk").write_text(
            "fragment-target:\n\t$(MAKE) root-target\n",
            encoding="utf-8",
        )
        self.assertEqual(
            parse_make_targets(root / "Makefile"),
            {"root-target", "fragment-target"},
        )
        self.assertEqual(
            make_recipe(root / "Makefile", "fragment-target"),
            ["$(MAKE) root-target"],
        )

    def test_release_contract_detects_metric_and_scenario_drift(self) -> None:
        root, release, metrics = self.make_release_fixture()
        metrics["generated_labels"] = 1
        release["runtime_scenarios"] = ["gameplay", "boot"]
        errors = validate_release(root, release, metrics)
        self.assertTrue(any("generated_labels" in error for error in errors))
        self.assertIn("runtime scenario order differs from release manifest", errors)

    def test_release_contract_requires_declared_files_and_targets(self) -> None:
        root, release, metrics = self.make_release_fixture()
        release["required_documents"] = ["docs/missing.md"]
        release["required_make_targets"] = ["missing-target"]
        errors = validate_release(root, release, metrics)
        self.assertTrue(any("release path is missing" in error for error in errors))
        self.assertTrue(any("Make target is missing" in error for error in errors))

    def test_source_2_contract_accepts_current_development_scope(self) -> None:
        root, release = self.make_source_2_release_fixture()
        self.assertEqual(validate_source_2_release(root, release), [])

    def test_source_2_contract_pins_the_published_predecessor(self) -> None:
        root, release = self.make_source_2_release_fixture()
        release["predecessor"]["commit"] = "0" * 40
        errors = validate_source_2_release(root, release)
        self.assertIn(
            "predecessor commit differs from the peeled Source 1.0 tag",
            errors,
        )

    def test_source_2_contract_rejects_regional_identity_drift(self) -> None:
        root, release = self.make_source_2_release_fixture()
        europe = next(
            artifact
            for artifact in release["artifacts"]
            if artifact["id"] == "europe_nes_rom"
        )
        europe["sha256"] = "0" * 64
        errors = validate_source_2_release(root, release)
        self.assertIn(
            "artifact europe_nes_rom sha256 differs from revision profile",
            errors,
        )

    def test_source_2_contract_rejects_runtime_scenario_drift(self) -> None:
        root, release = self.make_source_2_release_fixture()
        europe = next(
            coverage
            for coverage in release["runtime_coverage"]
            if coverage["profile_id"] == "europe"
        )
        europe["scenarios"] = list(reversed(europe["scenarios"]))
        errors = validate_source_2_release(root, release)
        self.assertIn("runtime scenario order differs for europe", errors)

    def test_source_2_contract_binds_runtime_to_profile_image(self) -> None:
        root, release = self.make_source_2_release_fixture()
        usa = next(
            artifact
            for artifact in release["artifacts"]
            if artifact["id"] == "usa_nes_rom"
        )
        usa["sha1"] = "0" * 40
        errors = validate_source_2_release(root, release)
        self.assertIn("runtime ROM SHA-1 differs for usa", errors)

    def test_source_2_contract_requires_complete_authoring_roles(self) -> None:
        root, release = self.make_source_2_release_fixture()
        levels = next(
            authoring
            for authoring in release["authoring"]
            if authoring["id"] == "levels"
        )
        del levels["targets"]["roundtrip"]
        errors = validate_source_2_release(root, release)
        self.assertIn("authoring levels target roles differ", errors)

    def test_source_2_contract_requires_profile_owned_capacities(self) -> None:
        root, release = self.make_source_2_release_fixture()
        audio = next(
            authoring
            for authoring in release["authoring"]
            if authoring["id"] == "audio"
        )
        audio["capacity_contract"]["owner"] = "gui"
        errors = validate_source_2_release(root, release)
        self.assertIn("authoring audio capacities are not profile-owned", errors)

    def test_source_2_contract_requires_the_graphics_authoring_model(self) -> None:
        root, release = self.make_source_2_release_fixture()
        release["authoring"] = [
            entry for entry in release["authoring"] if entry["id"] != "graphics"
        ]
        errors = validate_source_2_release(root, release)
        self.assertIn(
            "authoring must declare exactly the accepted level, audio, graphics, and presentation tools",
            errors,
        )

    def test_source_2_contract_requires_the_presentation_authoring_model(self) -> None:
        root, release = self.make_source_2_release_fixture()
        release["authoring"] = [
            entry for entry in release["authoring"] if entry["id"] != "presentation"
        ]
        errors = validate_source_2_release(root, release)
        self.assertIn(
            "authoring must declare exactly the accepted level, audio, graphics, and presentation tools",
            errors,
        )

    def test_source_2_contract_requires_stable_aggregate_gates(self) -> None:
        root, release = self.make_source_2_release_fixture()
        release["aggregate_gates"]["pre_tag"] = ["make check"]
        errors = validate_source_2_release(root, release)
        self.assertIn(
            "aggregate_gates differ from the Source 2.0 interface",
            errors,
        )

    def test_source_2_gate_recipes_preserve_predecessor_order(self) -> None:
        root, _release = self.make_source_2_release_fixture()
        self.assertIn(
            "source-1-regression-check",
            make_recipe(root / "Makefile", "source-2-regression-check")[0],
        )
        self.assertIn(
            "source-2-regression-check",
            make_recipe(root / "Makefile", "source-2-check")[0],
        )

    def test_source_2_tag_audits_use_the_immutable_ready_status(self) -> None:
        _root, release = self.make_source_2_release_fixture()
        self.assertEqual(validate_lifecycle_status(release, "pre-tag-audit"), [])
        self.assertEqual(validate_lifecycle_status(release, "post-tag-audit"), [])
        release["status"] = "tagged"
        self.assertEqual(
            validate_lifecycle_status(release, "post-tag-audit"),
            ["post-tag-audit requires status tag-ready"],
        )


if __name__ == "__main__":
    unittest.main()
