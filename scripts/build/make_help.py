#!/usr/bin/env python3
"""Render the curated public Make interface."""

from __future__ import annotations


TARGET_GROUPS = (
    (
        "Getting started",
        (
            ("help", "show this command guide"),
            ("split", "extract ignored private CHR data"),
            ("build", "assemble the default USA reconstruction"),
            ("verify", "prove complete USA byte identity"),
            ("clean", "remove generated build output"),
        ),
    ),
    (
        "Quality",
        (
            ("format", "normalize authored assembly source"),
            ("format-check", "check formatting without changing files"),
            ("lint", "check source, metadata, links, and policy"),
            ("validate-public-text", "check English text in the tree and history"),
            ("scaffold-check", "run the ROM-less public gate"),
            ("quality-check", "run lint and the complete unit-test suite"),
            ("check", "run the complete static Source 1 gate"),
        ),
    ),
    (
        "Revision profiles",
        (
            ("list-revisions", "list supported ROM revision profiles"),
            ("identify-revision", "identify a private ROM by its hashes"),
            ("split-all", "extract assets for every revision profile"),
            ("build-revision", "assemble the selected revision profile"),
            ("verify-revision", "prove the selected profile byte-identical"),
            ("verify-revisions", "prove every supported profile"),
            ("compare-revision-rooms", "compare USA and European room data"),
        ),
    ),
    (
        "Content authoring",
        (
            ("level-studio", "open the visual room editor"),
            ("sound-studio", "open the music and sound-effect studio"),
            ("graphics-studio", "open the CHR graphics editor"),
            ("presentation-studio", "open the title and presentation editor"),
            ("roundtrip-level-profiles", "round-trip levels for both profiles"),
            ("roundtrip-audio-profiles", "round-trip audio for both profiles"),
            ("roundtrip-graphics-profiles", "round-trip graphics for both profiles"),
            ("roundtrip-presentation-profiles", "round-trip presentation data"),
            ("editor-ui-smoke-profiles", "exercise public actions in all editors"),
        ),
    ),
    (
        "Runtime evidence",
        (
            ("symbols", "export debugger symbols for the USA build"),
            ("validate-symbols", "validate USA symbols in FCEUX"),
            ("trace-runtime", "capture the USA runtime scenarios"),
            ("validate-runtime", "validate captured USA runtime evidence"),
            ("trace-revision-runtimes", "capture both profile scenario sets"),
            ("smoke-level-playtests", "launch both headless level playtests"),
        ),
    ),
    (
        "Published reconstruction releases",
        (
            ("source-1-regression-check", "re-run the published Source 1 gate"),
            ("source-2-release-audit", "reconcile the Source 2 manifest"),
            ("source-2-static-check", "run static two-profile validation"),
            ("source-2-regression-check", "re-run the published Source 2 gate"),
            ("source-2-pre-tag-audit", "check Source 2 tag readiness"),
            ("source-2-post-tag-audit", "validate the checked-out Source 2 tag"),
        ),
    ),
    (
        "Source Reconstruction 2.1 candidate",
        (
            ("source-2-minor-audit", "reconcile the compatible 2.1 delta"),
            ("public-command-smoke", "run lint in a disposable tracked-only clone"),
            ("source-2-minor-check", "run the accepted 2.0 gate and 2.1 audit"),
            ("source-2-minor-pre-tag-check", "validate a clean 2.1 candidate"),
            ("source-2-minor-tag-check", "validate the checked-out 2.1 tag"),
        ),
    ),
)


def documented_targets() -> set[str]:
    return {target for _heading, entries in TARGET_GROUPS for target, _help in entries}


def render_help() -> str:
    lines = ["Solomon's Key source reconstruction", ""]
    for heading, entries in TARGET_GROUPS:
        lines.append(f"{heading}:")
        lines.extend(f"  {target:<32} {description}" for target, description in entries)
        lines.append("")
    lines.extend(
        (
            "Common selectors:",
            "  PROFILE=usa|europe",
            "  LEFT_PROFILE=usa|europe RIGHT_PROFILE=usa|europe",
        )
    )
    return "\n".join(lines)


def main() -> int:
    print(render_help())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
