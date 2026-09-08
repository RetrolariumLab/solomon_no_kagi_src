#!/usr/bin/env python3
"""Exercise public editor actions against disposable workstation outputs."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
from pathlib import Path
import sys
import tempfile
from tkinter import messagebox
from unittest import mock

from scripts.authoring import graphics_studio
from scripts.authoring import level_studio
from scripts.authoring import presentation_studio
from scripts.authoring import sound_studio
from scripts.build.project import parse_ines
from scripts.build.revision_profiles import (
    ROOT,
    get_profile,
    load_profiles,
    resolve_reference,
)


REQUIRED_ACTIONS = {
    "level": {"save", "build", "play", "preview", "dirty-close"},
    "sound": {"save", "build", "play", "preview", "dirty-close"},
    "graphics": {"save", "build", "preview", "dirty-close"},
    "presentation": {"save", "build", "preview", "dirty-close"},
}


class EditorWorkstationSmokeError(RuntimeError):
    """A workstation editor action failed its observable contract."""


def _verify_output(path: Path, action: str) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise EditorWorkstationSmokeError(f"{action} did not create {path}")


def _exercise_dirty_close(application: object) -> None:
    model = application.model
    with mock.patch.object(
        type(model), "dirty", new_callable=mock.PropertyMock, return_value=True
    ), mock.patch.object(
        messagebox, "askyesno", side_effect=(False, True)
    ) as prompt, mock.patch.object(application, "destroy") as destroy:
        application.close()
        if destroy.called:
            raise EditorWorkstationSmokeError(
                "editor closed after rejecting dirty-state confirmation"
            )
        application.close()
        if destroy.call_count != 1 or prompt.call_count != 2:
            raise EditorWorkstationSmokeError(
                "editor did not honor both dirty-state close decisions"
            )


def exercise_level(
    profile: dict[str, object], reference: Path, directory: Path
) -> set[str]:
    workspace = directory / "levels.json"
    output = directory / "levels.nes"
    fake_fceux = directory / "fceux64.exe"
    fake_fceux.touch()
    document = level_studio.load_studio_document(profile, reference, workspace)
    model = level_studio.StudioDocument(document)
    parsed = parse_ines(reference.read_bytes())
    application = level_studio.LevelStudio(
        model,
        profile,
        reference,
        workspace,
        output,
        fake_fceux,
        parsed["chr"],
        parsed["prg"],
    )
    application.withdraw()
    try:
        application.redraw()
        application.update_idletasks()
        if application.preview_image is None:
            raise EditorWorkstationSmokeError("level preview produced no image")
        if not application.save():
            raise EditorWorkstationSmokeError("level Save action failed")
        if not application.build_rom():
            raise EditorWorkstationSmokeError("level Build action failed")
        with mock.patch.object(level_studio.subprocess, "Popen") as launch:
            application.play()
            if launch.call_count != 1:
                raise EditorWorkstationSmokeError(
                    "level Play action did not launch the emulator adapter"
                )
        application.playtest_process = None
        _verify_output(workspace, "level Save")
        _verify_output(output, "level Build")
        _exercise_dirty_close(application)
    finally:
        application.destroy()
    return REQUIRED_ACTIONS["level"]


def exercise_sound(
    profile: dict[str, object], reference: Path, directory: Path
) -> set[str]:
    workspace = directory / "audio.json"
    output = directory / "audio.nes"
    model = sound_studio.load_studio_document(profile, reference, workspace, output)
    application = sound_studio.SoundStudio(model)
    application.withdraw()
    try:
        application.save()
        application.build_rom()
        application.preview_seconds.set("0.25")
        playback = nullcontext()
        if sys.platform == "win32":
            playback = mock.patch("winsound.PlaySound")
        with playback:
            application.preview_effect()
        preview = output.with_name("effect01-preview.wav")
        _verify_output(workspace, "sound Save")
        _verify_output(output, "sound Build")
        _verify_output(preview, "sound Preview/Play")
        if preview.stat().st_size <= 44:
            raise EditorWorkstationSmokeError("sound preview contains no PCM frames")
        _exercise_dirty_close(application)
    finally:
        application.destroy()
    return REQUIRED_ACTIONS["sound"]


def exercise_graphics(
    profile: dict[str, object], reference: Path, directory: Path
) -> set[str]:
    workspace = directory / "graphics.json"
    output = directory / "graphics.nes"
    model = graphics_studio.load_studio_document(profile, reference, workspace, output)
    application = graphics_studio.GraphicsStudio(model)
    application.withdraw()
    try:
        application.save()
        application.build_rom()
        application.refresh_all()
        application.update_idletasks()
        if application.atlas_image is None or application.atlas_zoom is None:
            raise EditorWorkstationSmokeError("graphics preview produced no atlas")
        _verify_output(workspace, "graphics Save")
        _verify_output(output, "graphics Build")
        _exercise_dirty_close(application)
    finally:
        application.destroy()
    return REQUIRED_ACTIONS["graphics"]


def exercise_presentation(
    profile: dict[str, object], reference: Path, directory: Path
) -> set[str]:
    workspace = directory / "presentation.json"
    output = directory / "presentation.nes"
    model = presentation_studio.load_studio_document(
        profile, reference, workspace, output
    )
    application = presentation_studio.PresentationStudio(model)
    application.withdraw()
    try:
        application.save()
        application.build_rom()
        application.refresh_all()
        application.update_idletasks()
        if not application.title_canvas.find_all():
            raise EditorWorkstationSmokeError(
                "presentation preview produced no canvas items"
            )
        _verify_output(workspace, "presentation Save")
        _verify_output(output, "presentation Build")
        _exercise_dirty_close(application)
    finally:
        application.destroy()
    return REQUIRED_ACTIONS["presentation"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profiles", type=Path, default=ROOT / "config" / "revision_profiles.json"
    )
    parser.add_argument("--private-root", type=Path, default=ROOT)
    parser.add_argument("--profile", required=True)
    args = parser.parse_args()

    try:
        profiles = load_profiles(args.profiles)
        profile = get_profile(profiles, args.profile)
        reference = resolve_reference(profile, args.private_root)
        build = ROOT / "build"
        build.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=f"editor-smoke-{args.profile}-", dir=build
        ) as temporary:
            directory = Path(temporary)
            actions = {
                "level": exercise_level(profile, reference, directory),
                "sound": exercise_sound(profile, reference, directory),
                "graphics": exercise_graphics(profile, reference, directory),
                "presentation": exercise_presentation(profile, reference, directory),
            }
        if actions != REQUIRED_ACTIONS:
            raise EditorWorkstationSmokeError(
                f"editor action coverage mismatch: {actions!r}"
            )
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    summary = "; ".join(
        f"{name}={','.join(sorted(values))}" for name, values in actions.items()
    )
    print(f"[OK] {args.profile} editor workstation actions: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
