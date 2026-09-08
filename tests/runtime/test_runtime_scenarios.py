from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]

from scripts.runtime import runtime_scenarios


def scenario_document() -> dict[str, object]:
    return {
        "schema_version": 1,
        "rom_sha1": "0" * 40,
        "scenarios": [
            {
                "id": "boot",
                "method": "test",
                "max_frames": 10,
                "inputs": [
                    {"start_frame": 2, "end_frame": 3, "buttons": ["start"]}
                ],
                "patches": [],
                "expected_events": {"first_nmi": 1},
                "expected_event_details": {"first_nmi": "NMI"},
                "expected_event_series": {"first_nmi": ["1:NMI"]},
                "expected_final": {"frame": "10", "thread": "01"},
            }
        ],
    }


def trace_rows() -> list[dict[str, str]]:
    return [
        {
            "frame": "0",
            "event": "trace_start",
            "detail": "boot",
            "thread": "00",
            "room": "00",
            "timer": "00000000",
            "dana_y": "00",
            "dana_x": "00",
            "active_enemies": "00",
            "remaining_lives": "00",
        },
        {
            "frame": "1",
            "event": "first_nmi",
            "detail": "NMI",
            "thread": "00",
            "room": "00",
            "timer": "00000000",
            "dana_y": "00",
            "dana_x": "00",
            "active_enemies": "00",
            "remaining_lives": "00",
        },
        {
            "frame": "10",
            "event": "trace_end",
            "detail": "boot",
            "thread": "01",
            "room": "00",
            "timer": "00000000",
            "dana_y": "00",
            "dana_x": "00",
            "active_enemies": "00",
            "remaining_lives": "00",
        },
    ]


class ScenarioTests(unittest.TestCase):
    def test_binds_legacy_and_explicit_regional_manifests(self) -> None:
        document = scenario_document()
        runtime_scenarios.validate_manifest_profile(document, "usa")
        with self.assertRaisesRegex(runtime_scenarios.RuntimeError, "profile mismatch"):
            runtime_scenarios.validate_manifest_profile(document, "europe")
        document["profile"] = "europe"
        runtime_scenarios.validate_manifest_profile(document, "europe")

    def test_committed_pal_manifest_has_complete_expectations(self) -> None:
        document = runtime_scenarios.load_scenarios(
            ROOT / "scenarios" / "runtime_scenarios_europe.json"
        )
        self.assertEqual(document["profile"], "europe")
        self.assertEqual(len(document["scenarios"]), 4)
        for scenario in document["scenarios"]:
            self.assertTrue(scenario["expected_events"])
            self.assertTrue(scenario["expected_final"])

    def test_loads_and_encodes_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scenarios.json"
            path.write_text(json.dumps(scenario_document()))
            document = runtime_scenarios.load_scenarios(path)
            scenario = document["scenarios"][0]
            self.assertEqual(runtime_scenarios.encode_inputs(scenario), "2-3:start")

    def test_rejects_overlapping_inputs(self) -> None:
        scenario = scenario_document()["scenarios"][0]
        scenario["inputs"].append(
            {"start_frame": 3, "end_frame": 4, "buttons": ["a"]}
        )
        with self.assertRaisesRegex(runtime_scenarios.RuntimeError, "overlapping"):
            runtime_scenarios.validate_inputs(scenario)

    def test_rejects_unknown_button(self) -> None:
        scenario = scenario_document()["scenarios"][0]
        scenario["inputs"][0]["buttons"] = ["turbo"]
        with self.assertRaisesRegex(runtime_scenarios.RuntimeError, "buttons"):
            runtime_scenarios.validate_inputs(scenario)

    def test_encodes_reviewed_patch(self) -> None:
        scenario = scenario_document()["scenarios"][0]
        scenario["patches"] = [
            {
                "frame": 5,
                "symbol": "GameplayFlags",
                "operation": "or",
                "value": "0x20",
                "reason": "mark_key_collected",
                "expected_detail": "0028:00>20:mark_key_collected",
            }
        ]
        runtime_scenarios.validate_patches(scenario)
        self.assertEqual(
            runtime_scenarios.encode_patches(scenario),
            "5,GameplayFlags,0,or,32,mark_key_collected",
        )


class TraceTests(unittest.TestCase):
    def test_validates_expected_event_and_final_state(self) -> None:
        scenario = scenario_document()["scenarios"][0]
        runtime_scenarios.validate_trace(scenario, trace_rows())

    def test_detects_changed_event_frame(self) -> None:
        scenario = scenario_document()["scenarios"][0]
        rows = trace_rows()
        rows[1]["frame"] = "2"
        with self.assertRaisesRegex(runtime_scenarios.RuntimeError, "first_nmi"):
            runtime_scenarios.validate_trace(scenario, rows)

    def test_detects_changed_event_detail(self) -> None:
        scenario = scenario_document()["scenarios"][0]
        rows = trace_rows()
        rows[1]["detail"] = "wrong"
        with self.assertRaisesRegex(runtime_scenarios.RuntimeError, "detail"):
            runtime_scenarios.validate_trace(scenario, rows)

    def test_detects_changed_event_series(self) -> None:
        scenario = scenario_document()["scenarios"][0]
        scenario["expected_event_series"]["first_nmi"] = ["2:NMI"]
        with self.assertRaisesRegex(runtime_scenarios.RuntimeError, "series"):
            runtime_scenarios.validate_trace(scenario, trace_rows())

    def test_detects_forbidden_event(self) -> None:
        scenario = scenario_document()["scenarios"][0]
        scenario["forbidden_events"] = ["first_nmi"]
        with self.assertRaisesRegex(runtime_scenarios.RuntimeError, "forbidden"):
            runtime_scenarios.validate_trace(scenario, trace_rows())

    def test_detects_undeclared_controlled_patch(self) -> None:
        scenario = scenario_document()["scenarios"][0]
        rows = trace_rows()
        rows.insert(1, dict(rows[0], frame="1", event="controlled_patch", detail="bad"))
        with self.assertRaisesRegex(runtime_scenarios.RuntimeError, "patch scope"):
            runtime_scenarios.validate_trace(scenario, rows)

    def test_load_trace_checks_schema_and_monotonic_frames(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.csv"
            rows = trace_rows()
            rows[1]["frame"] = "11"
            with path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(runtime_scenarios.RuntimeError, "monotonic"):
                runtime_scenarios.load_trace(path)


if __name__ == "__main__":
    unittest.main()
