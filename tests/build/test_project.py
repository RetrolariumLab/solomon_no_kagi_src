from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]

from scripts.build import project


def sample_ines() -> bytes:
    header = b"NES\x1a" + bytes((1, 1, 0x30, 0)) + bytes(8)
    return header + bytes(16_384) + bytes([0xFF]) * 8_192


def sample_manifest(image: bytes) -> dict[str, object]:
    parsed = project.parse_ines(image)
    return {
        "schema_version": 1,
        "reference_rom": {
            "file_size": len(image),
            "file_sha1": project.digest(image),
            "file_sha256": project.digest(image, "sha256"),
            "file_md5": project.digest(image, "md5"),
            "file_crc32": project.crc32(image),
            "payload_sha1": project.digest(parsed["payload"]),
            "payload_sha256": project.digest(parsed["payload"], "sha256"),
            "payload_crc32": project.crc32(parsed["payload"]),
            "header_sha1": project.digest(parsed["header"]),
            "header_sha256": project.digest(parsed["header"], "sha256"),
            "prg_sha1": project.digest(parsed["prg"]),
            "prg_sha256": project.digest(parsed["prg"], "sha256"),
            "prg_crc32": project.crc32(parsed["prg"]),
            "chr_sha1": project.digest(parsed["chr"]),
            "chr_sha256": project.digest(parsed["chr"], "sha256"),
            "chr_crc32": project.crc32(parsed["chr"]),
            "trainer_size": 0,
            "prg_size": 16_384,
            "chr_size": 8_192,
            "mapper": 3,
            "mirroring": "horizontal",
        },
    }


class InesTests(unittest.TestCase):
    def test_parse_ines(self) -> None:
        parsed = project.parse_ines(sample_ines())
        self.assertEqual(parsed["mapper"], 3)
        self.assertEqual(len(parsed["prg"]), 16_384)
        self.assertEqual(len(parsed["chr"]), 8_192)

    def test_rejects_trailing_data(self) -> None:
        with self.assertRaisesRegex(project.ProjectError, "expected exactly"):
            project.parse_ines(sample_ines() + b"trailing")

    def test_manifest_verifies_every_region(self) -> None:
        image = sample_ines()
        project.validate_image(image, sample_manifest(image))

    def test_region_change_is_detected(self) -> None:
        image = sample_ines()
        changed = image[:-1] + b"\x00"
        with self.assertRaisesRegex(project.ProjectError, "file_sha1 mismatch"):
            project.validate_image(changed, sample_manifest(image))


class PathTests(unittest.TestCase):
    def test_safe_asset_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(
                project.safe_asset_path(root, "chr/game.chr"),
                root / "chr" / "game.chr",
            )

    def test_rejects_parent_asset_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(project.ProjectError, "unsafe"):
                project.safe_asset_path(Path(directory), "../game.chr")

    def test_load_manifest_rejects_unknown_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps({"schema_version": 2}), encoding="utf-8")
            with self.assertRaisesRegex(project.ProjectError, "schema"):
                project.load_manifest(path)

    def test_require_rejects_missing_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            args = type(
                "Args",
                (),
                {"path": str(Path(directory) / "missing.chr"), "hint": "run split"},
            )()
            with self.assertRaisesRegex(project.ProjectError, "run split"):
                project.command_require(args)

    def test_split_writes_only_manifest_assets(self) -> None:
        image = sample_ines()
        manifest = sample_manifest(image)
        parsed = project.parse_ines(image)
        manifest["extracted_assets"] = [
            {
                "path": "chr/game.chr",
                "region": "chr",
                "size": len(parsed["chr"]),
                "sha1": project.digest(parsed["chr"]),
                "sha256": project.digest(parsed["chr"], "sha256"),
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image_path = root / "game.nes"
            manifest_path = root / "manifest.json"
            output = root / "generated"
            image_path.write_bytes(image)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "image": str(image_path),
                    "manifest": str(manifest_path),
                    "output_dir": str(output),
                },
            )()
            project.command_split(args)
            self.assertEqual((output / "chr" / "game.chr").read_bytes(), parsed["chr"])
            self.assertFalse((output / "header").exists())
            self.assertFalse((output / "prg").exists())


class ToolchainTests(unittest.TestCase):
    def test_verifies_component_hash_and_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "tool.exe"
            binary.write_bytes(b"pinned tool")
            entry = {
                "id": "tool",
                "size": binary.stat().st_size,
                "binary_sha256": project.digest(binary.read_bytes(), "sha256"),
                "version": "unused",
                "version_arguments": [],
            }
            project.verify_component(binary, entry)

    def test_rejects_changed_component_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "tool.exe"
            binary.write_bytes(b"changed tool")
            entry = {
                "id": "tool",
                "size": binary.stat().st_size,
                "binary_sha256": "0" * 64,
                "version": "unused",
                "version_arguments": [],
            }
            with self.assertRaisesRegex(project.ProjectError, "SHA-256 mismatch"):
                project.verify_component(binary, entry)

    def test_rejects_duplicate_component_override(self) -> None:
        with self.assertRaisesRegex(project.ProjectError, "duplicate"):
            project.parse_path_overrides(["assembler=first", "assembler=second"])


class RepositoryLintTests(unittest.TestCase):
    def test_accepts_local_and_external_markdown_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "target.md").write_text("# Target\n", encoding="utf-8")
            (root / "README.md").write_text(
                "[local](docs/target.md) [anchor](#section) "
                "[external](https://example.com)\n",
                encoding="utf-8",
            )
            project.lint_markdown_links(root)

    def test_rejects_broken_markdown_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "index.md").write_text(
                "[missing](missing.md)\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(project.ProjectError, "broken"):
                project.lint_markdown_links(root)

    def test_rejects_invalid_json_and_python(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (
                "assets",
                "config",
                "docs",
                "scenarios",
                "scripts",
                "tests",
            ):
                (root / name).mkdir()
            (root / "config" / "broken.json").write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(project.ProjectError, "invalid JSON"):
                project.lint_json_files(root)
            (root / "config" / "broken.json").write_text("{}", encoding="utf-8")
            (root / "scripts" / "broken.py").write_text("if:\n", encoding="utf-8")
            with self.assertRaisesRegex(project.ProjectError, "invalid Python"):
                project.lint_python_files(root)


class SourceOrganizationTests(unittest.TestCase):
    def policy(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "preferred_line_range": {"minimum": 3, "maximum": 5},
            "maximum_asm_files_per_directory": 2,
            "exceptions": {},
        }

    def test_accepts_preferred_size_and_reviewed_exception(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src" / "game"
            source.mkdir(parents=True)
            (source / "runtime.asm").write_text("a\nb\nc\n", encoding="utf-8")
            (source / "tables.asm").write_text("a\n", encoding="utf-8")
            policy = self.policy()
            policy["exceptions"] = {
                "src/game/tables.asm": "A deliberately compact fixed table owner."
            }
            project.validate_source_organization(root, policy)

    def test_rejects_unreviewed_size_and_repeated_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src" / "game"
            source.mkdir(parents=True)
            (source / "room_load.asm").write_text("a\n", encoding="utf-8")
            (source / "room_clear.asm").write_text("a\nb\nc\n", encoding="utf-8")
            with self.assertRaisesRegex(project.ProjectError, "without a reviewed exception"):
                project.validate_source_organization(root, self.policy())
            policy = self.policy()
            policy["exceptions"] = {
                "src/game/room_load.asm": "A deliberately compact layout boundary."
            }
            with self.assertRaisesRegex(project.ProjectError, "repeats filename prefix"):
                project.validate_source_organization(root, policy)


class ToolLayoutTests(unittest.TestCase):
    def make_layout(self, root: Path) -> None:
        for owner in ("authoring", "build", "runtime", "validation"):
            for base in (root / "scripts", root / "tests"):
                package = base / owner
                package.mkdir(parents=True, exist_ok=True)
                (package / "__init__.py").touch()
        (root / "scripts" / "run.py").touch()

    def test_accepts_mirrored_responsibility_packages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_layout(root)

            project.validate_tool_layout(root)

    def test_rejects_uncategorized_script(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_layout(root)
            (root / "scripts" / "orphan.py").touch()

            with self.assertRaisesRegex(project.ProjectError, "uncategorized scripts"):
                project.validate_tool_layout(root)


class ConfigLayoutTests(unittest.TestCase):
    def make_layout(self, root: Path) -> None:
        for owner in ("authoring", "debugger", "reconstruction", "validation"):
            (root / "config" / owner).mkdir(parents=True, exist_ok=True)
        (root / "config" / "revision_profiles.json").write_text("{}", encoding="utf-8")

    def test_accepts_owned_config_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_layout(root)

            project.validate_config_layout(root)

    def test_rejects_uncategorized_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_layout(root)
            (root / "config" / "orphan.json").write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(project.ProjectError, "uncategorized config"):
                project.validate_config_layout(root)


if __name__ == "__main__":
    unittest.main()
