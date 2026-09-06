#!/usr/bin/env python3
"""Visual 16x12 room editor backed by the byte-exact level document codec."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

from level_editor import (
    KEY_STATUS_BITS,
    POSITION_FIELDS,
    ROOM_COUNT,
    ROOM_HEIGHT,
    ROOM_WIDTH,
    LevelEditorError,
    build_level_image,
    canonical_document,
    export_document,
    load_document,
    save_document,
    validate_rebuilt_document,
)
from project import ProjectError, write_if_changed
from revision_profiles import (
    ROOT,
    get_profile,
    load_profiles,
    resolve_reference,
    verify_reference,
)
from room_data import RoomDataError


CELL = 40
CANVAS_WIDTH = ROOM_WIDTH * CELL
CANVAS_HEIGHT = ROOM_HEIGHT * CELL
EDIT_MODES = (
    "select",
    "brown block",
    "white block",
    "erase cell",
    "player start",
    "key",
    "door",
    "mirror 1",
    "mirror 2",
    "enemy",
    "item",
)
ANCHOR_MODES = {
    "player start": "player_start",
    "key": "key",
    "door": "door",
    "mirror 1": "mirror_1",
    "mirror 2": "mirror_2",
}


@dataclass(frozen=True)
class ItemPlacement:
    command_index: int
    position_index: int | None
    item_type: int
    position: dict[str, int]


class StudioDocument:
    def __init__(self, document: dict[str, Any]) -> None:
        self.document = document
        self.original = canonical_document(document)
        self.undo_stack: list[dict[str, Any]] = []

    @property
    def dirty(self) -> bool:
        return canonical_document(self.document) != self.original

    def mark_saved(self) -> None:
        self.original = canonical_document(self.document)

    def room(self, room_index: int) -> dict[str, Any]:
        if not 0 <= room_index < ROOM_COUNT:
            raise LevelEditorError(f"room index outside 0..{ROOM_COUNT - 1}")
        return self.document["rooms"][room_index]

    def mutate(self, callback: Callable[[], bool]) -> bool:
        before = copy.deepcopy(self.document)
        changed = callback()
        if changed:
            self.undo_stack.append(before)
            if len(self.undo_stack) > 100:
                del self.undo_stack[0]
        return changed

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        self.document = self.undo_stack.pop()
        return True

    @staticmethod
    def same_position(value: dict[str, int], x: int, y: int) -> bool:
        return value.get("x") == x and value.get("y") == y

    def set_block(self, room_index: int, kind: str, x: int, y: int) -> bool:
        if kind not in {"brown", "white"}:
            raise LevelEditorError(f"unknown block kind: {kind}")

        def apply() -> bool:
            blocks = self.room(room_index)["blocks"]
            target = blocks[kind]
            other = blocks["white" if kind == "brown" else "brown"]
            existing = next(
                (value for value in target if self.same_position(value, x, y)),
                None,
            )
            changed = False
            if existing is None:
                target.append({"x": x, "y": y})
                target.sort(key=lambda value: (value["y"], value["x"]))
                changed = True
            removed = [value for value in other if self.same_position(value, x, y)]
            if removed:
                other[:] = [value for value in other if value not in removed]
                changed = True
            return changed

        return self.mutate(apply)

    def set_anchor(self, room_index: int, field: str, x: int, y: int) -> bool:
        if field not in POSITION_FIELDS:
            raise LevelEditorError(f"unknown room anchor: {field}")

        def apply() -> bool:
            metadata = self.room(room_index)["items"]["metadata"]
            value = {"x": x, "y": y}
            if metadata[field] == value:
                return False
            metadata[field] = value
            return True

        return self.mutate(apply)

    def set_room_properties(
        self,
        room_index: int,
        spawn_lifetime: int,
        key_status: str,
        time_rate: int,
        schedules: tuple[int, int],
        enemy_sets: tuple[int, int],
    ) -> bool:
        if not 0 <= spawn_lifetime <= 0xFF:
            raise LevelEditorError("spawn lifetime must be 0..255")
        if key_status not in KEY_STATUS_BITS:
            raise LevelEditorError(f"unknown key status: {key_status}")
        if not 0 <= time_rate <= 0x0F:
            raise LevelEditorError("time decrease rate must be 0..15")
        if any(not 0 <= value < 16 for value in schedules):
            raise LevelEditorError("mirror schedule index must be 0..15")
        if any(not 0 <= value < 17 for value in enemy_sets):
            raise LevelEditorError("mirror enemy-set index must be 0..16")

        def apply() -> bool:
            room = self.room(room_index)
            metadata = room["items"]["metadata"]
            new_values = {
                "spawn_lifetime": spawn_lifetime,
                "key_status": key_status,
                "time_decrease_rate": time_rate,
                "mirror_1_schedule": schedules[0],
                "mirror_2_schedule": schedules[1],
                "mirror_1_enemy_set": enemy_sets[0],
                "mirror_2_enemy_set": enemy_sets[1],
            }
            old_values = {
                "spawn_lifetime": room["enemies"]["spawn_lifetime"],
                **{key: metadata[key] for key in new_values if key != "spawn_lifetime"},
            }
            if old_values == new_values:
                return False
            room["enemies"]["spawn_lifetime"] = spawn_lifetime
            for key, value in new_values.items():
                if key != "spawn_lifetime":
                    metadata[key] = value
            return True

        return self.mutate(apply)

    def add_enemy(
        self,
        room_index: int,
        enemy_type: int,
        x: int,
        y: int,
    ) -> bool:
        if not 1 <= enemy_type <= 0xFF:
            raise LevelEditorError("enemy type must be $01..$FF")

        def apply() -> bool:
            self.room(room_index)["enemies"]["placements"].append(
                {"type": enemy_type, "position": {"x": x, "y": y}}
            )
            return True

        return self.mutate(apply)

    def add_item(
        self,
        room_index: int,
        item_type: int,
        x: int,
        y: int,
    ) -> bool:
        if not (1 <= item_type < 0xC0 or 0xFC <= item_type <= 0xFF):
            raise LevelEditorError("item type must be $01..$BF or $FC..$FF")

        def apply() -> bool:
            commands = self.room(room_index)["items"]["commands"]
            insertion = len(commands)
            if commands and commands[-1]["kind"] in {"end", "constellation"}:
                insertion -= 1
            commands.insert(
                insertion,
                {"kind": "item", "type": item_type, "position": {"x": x, "y": y}},
            )
            return True

        return self.mutate(apply)

    def item_placements(self, room_index: int) -> list[ItemPlacement]:
        result: list[ItemPlacement] = []
        commands = self.room(room_index)["items"]["commands"]
        for command_index, command in enumerate(commands):
            kind = command["kind"]
            if kind == "item":
                result.append(
                    ItemPlacement(
                        command_index,
                        None,
                        command["type"],
                        command["position"],
                    )
                )
            elif kind == "repeat":
                result.extend(
                    ItemPlacement(command_index, index, command["type"], position)
                    for index, position in enumerate(command["positions"])
                )
            elif kind == "constellation":
                result.append(
                    ItemPlacement(
                        command_index,
                        None,
                        command["opcode"],
                        command["position"],
                    )
                )
        return result

    def erase_cell(self, room_index: int, x: int, y: int) -> bool:
        def apply() -> bool:
            room = self.room(room_index)
            changed = False
            for kind in ("brown", "white"):
                values = room["blocks"][kind]
                kept = [value for value in values if not self.same_position(value, x, y)]
                if len(kept) != len(values):
                    values[:] = kept
                    changed = True
            placements = room["enemies"]["placements"]
            kept_enemies = [
                value
                for value in placements
                if not self.same_position(value["position"], x, y)
            ]
            if len(kept_enemies) != len(placements):
                placements[:] = kept_enemies
                changed = True
            commands = room["items"]["commands"]
            for command in list(commands):
                if command["kind"] in {"item", "constellation"}:
                    if self.same_position(command["position"], x, y):
                        commands.remove(command)
                        changed = True
                elif command["kind"] == "repeat":
                    values = command["positions"]
                    kept = [
                        value for value in values
                        if not self.same_position(value, x, y)
                    ]
                    if len(kept) != len(values):
                        changed = True
                        if kept:
                            command["positions"] = kept
                        else:
                            commands.remove(command)
            return changed

        return self.mutate(apply)


class LevelStudio(tk.Tk):
    def __init__(
        self,
        model: StudioDocument,
        profile: dict[str, Any],
        reference: Path,
        document_path: Path,
        output_path: Path,
        fceux: Path,
    ) -> None:
        super().__init__()
        self.model = model
        self.profile = profile
        self.reference = reference
        self.document_path = document_path
        self.output_path = output_path
        self.fceux = fceux
        self.room_index = tk.IntVar(value=0)
        self.room_choice = tk.StringVar(value="Room 01")
        self.mode = tk.StringVar(value="select")
        self.enemy_type = tk.StringVar(value="71")
        self.item_type = tk.StringVar(value="18")
        self.status = tk.StringVar()
        self.property_vars = {
            "spawn_lifetime": tk.IntVar(),
            "time_decrease_rate": tk.IntVar(),
            "key_status": tk.StringVar(),
            "mirror_1_schedule": tk.IntVar(),
            "mirror_2_schedule": tk.IntVar(),
            "mirror_1_enemy_set": tk.IntVar(),
            "mirror_2_enemy_set": tk.IntVar(),
        }
        self.title(f"Solomon's Key Level Studio [{profile['id']}]")
        self.geometry("1120x690")
        self.minsize(920, 620)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.build_ui()
        self.load_properties()
        self.redraw()

    def build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=7)
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="Room").pack(side="left")
        room_box = ttk.Combobox(
            toolbar,
            textvariable=self.room_choice,
            values=[f"Room {number:02d}" for number in range(1, ROOM_COUNT + 1)],
            state="readonly",
            width=10,
        )
        room_box.pack(side="left", padx=(4, 12))
        room_box.bind("<<ComboboxSelected>>", self.select_room)
        ttk.Label(toolbar, text="Tool").pack(side="left")
        mode_box = ttk.Combobox(
            toolbar,
            textvariable=self.mode,
            values=EDIT_MODES,
            state="readonly",
            width=15,
        )
        mode_box.pack(side="left", padx=4)
        for text, command in (
            ("Undo", self.undo),
            ("Save", self.save),
            ("Build ROM", self.build_rom),
            ("Play", self.play),
        ):
            ttk.Button(toolbar, text=text, command=command).pack(side="left", padx=3)
        ttk.Label(toolbar, textvariable=self.status).pack(side="right")

        body = ttk.Frame(self, padding=(7, 0, 7, 7))
        body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(
            body,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg="#101820",
            highlightthickness=0,
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.canvas.bind("<Button-3>", self.erase_click)

        side = ttk.Frame(body, padding=(10, 0))
        side.pack(side="right", fill="y")
        type_box = ttk.LabelFrame(side, text="Placed object", padding=7)
        type_box.pack(fill="x", pady=(0, 8))
        ttk.Label(type_box, text="Enemy type (hex)").grid(row=0, column=0, sticky="w")
        ttk.Entry(type_box, textvariable=self.enemy_type, width=8).grid(row=0, column=1)
        ttk.Label(type_box, text="Item type (hex)").grid(row=1, column=0, sticky="w")
        ttk.Entry(type_box, textvariable=self.item_type, width=8).grid(row=1, column=1)

        properties = ttk.LabelFrame(side, text="Room properties", padding=7)
        properties.pack(fill="x")
        rows = (
            ("spawn_lifetime", "Enemy lifetime", 0, 255),
            ("time_decrease_rate", "Time rate", 0, 15),
            ("mirror_1_schedule", "Mirror 1 schedule", 0, 15),
            ("mirror_2_schedule", "Mirror 2 schedule", 0, 15),
            ("mirror_1_enemy_set", "Mirror 1 set", 0, 16),
            ("mirror_2_enemy_set", "Mirror 2 set", 0, 16),
        )
        for row, (name, label, low, high) in enumerate(rows):
            ttk.Label(properties, text=label).grid(row=row, column=0, sticky="w")
            ttk.Spinbox(
                properties,
                from_=low,
                to=high,
                textvariable=self.property_vars[name],
                width=7,
            ).grid(row=row, column=1, padx=(8, 0), pady=2)
        ttk.Label(properties, text="Key status").grid(row=len(rows), column=0, sticky="w")
        ttk.Combobox(
            properties,
            textvariable=self.property_vars["key_status"],
            values=tuple(KEY_STATUS_BITS),
            state="readonly",
            width=10,
        ).grid(row=len(rows), column=1, padx=(8, 0), pady=2)
        ttk.Button(
            properties,
            text="Apply properties",
            command=self.apply_properties,
        ).grid(row=len(rows) + 1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        legend = ttk.LabelFrame(side, text="Legend", padding=7)
        legend.pack(fill="x", pady=(8, 0))
        ttk.Label(
            legend,
            justify="left",
            text=(
                "Brown / white: block planes\n"
                "P player, K key, D door\n"
                "M1/M2 Demon Mirrors\n"
                "Red circles: enemies\n"
                "Gold diamonds: items\n\n"
                "Left click applies selected tool.\n"
                "Right click erases the cell."
            ),
        ).pack(anchor="w")

    def current_room(self) -> dict[str, Any]:
        return self.model.room(self.room_index.get())

    def select_room(self, _event: object = None) -> None:
        self.room_index.set(int(self.room_choice.get().split()[-1]) - 1)
        self.load_properties()
        self.redraw()

    def load_properties(self) -> None:
        room = self.current_room()
        metadata = room["items"]["metadata"]
        self.property_vars["spawn_lifetime"].set(room["enemies"]["spawn_lifetime"])
        for name in self.property_vars:
            if name != "spawn_lifetime":
                self.property_vars[name].set(metadata[name])

    def apply_properties(self) -> None:
        try:
            changed = self.model.set_room_properties(
                self.room_index.get(),
                self.property_vars["spawn_lifetime"].get(),
                self.property_vars["key_status"].get(),
                self.property_vars["time_decrease_rate"].get(),
                (
                    self.property_vars["mirror_1_schedule"].get(),
                    self.property_vars["mirror_2_schedule"].get(),
                ),
                (
                    self.property_vars["mirror_1_enemy_set"].get(),
                    self.property_vars["mirror_2_enemy_set"].get(),
                ),
            )
            self.set_status("Room properties updated" if changed else "No change")
        except (tk.TclError, LevelEditorError) as exc:
            messagebox.showerror("Invalid room properties", str(exc))
        self.redraw()

    @staticmethod
    def parse_hex(value: str, description: str) -> int:
        try:
            return int(value.removeprefix("$").removeprefix("0x"), 16)
        except ValueError as exc:
            raise LevelEditorError(f"invalid {description}: {value!r}") from exc

    def canvas_cell(self, event: tk.Event) -> tuple[int, int]:
        x = min(max(int(self.canvas.canvasx(event.x)) // CELL, 0), ROOM_WIDTH - 1)
        y = min(max(int(self.canvas.canvasy(event.y)) // CELL, 0), ROOM_HEIGHT - 1)
        return x, y

    def canvas_click(self, event: tk.Event) -> None:
        x, y = self.canvas_cell(event)
        mode = self.mode.get()
        try:
            if mode == "brown block":
                changed = self.model.set_block(self.room_index.get(), "brown", x, y)
            elif mode == "white block":
                changed = self.model.set_block(self.room_index.get(), "white", x, y)
            elif mode == "erase cell":
                changed = self.model.erase_cell(self.room_index.get(), x, y)
            elif mode in ANCHOR_MODES:
                changed = self.model.set_anchor(
                    self.room_index.get(), ANCHOR_MODES[mode], x, y
                )
            elif mode == "enemy":
                changed = self.model.add_enemy(
                    self.room_index.get(),
                    self.parse_hex(self.enemy_type.get(), "enemy type"),
                    x,
                    y,
                )
            elif mode == "item":
                changed = self.model.add_item(
                    self.room_index.get(),
                    self.parse_hex(self.item_type.get(), "item type"),
                    x,
                    y,
                )
            else:
                self.set_status(f"Cell ({x}, {y})")
                return
            self.set_status(f"Updated ({x}, {y})" if changed else "No change")
            self.redraw()
        except LevelEditorError as exc:
            messagebox.showerror("Invalid edit", str(exc))

    def erase_click(self, event: tk.Event) -> None:
        x, y = self.canvas_cell(event)
        if self.model.erase_cell(self.room_index.get(), x, y):
            self.set_status(f"Erased ({x}, {y})")
            self.redraw()

    def undo(self) -> None:
        if self.model.undo():
            self.load_properties()
            self.redraw()
            self.set_status("Undid last edit")
        else:
            self.set_status("Nothing to undo")

    def set_status(self, text: str) -> None:
        suffix = " *" if self.model.dirty else ""
        self.status.set(text + suffix)

    def draw_cell(self, x: int, y: int, color: str) -> None:
        self.canvas.create_rectangle(
            x * CELL + 1,
            y * CELL + 1,
            (x + 1) * CELL - 1,
            (y + 1) * CELL - 1,
            fill=color,
            outline="",
        )

    def draw_label(self, position: dict[str, int], text: str, color: str) -> None:
        x, y = position["x"], position["y"]
        if y < 0 or y >= ROOM_HEIGHT:
            return
        self.canvas.create_text(
            x * CELL + CELL // 2,
            y * CELL + CELL // 2,
            text=text,
            fill=color,
            font=("Consolas", 10, "bold"),
        )

    def redraw(self) -> None:
        self.canvas.delete("all")
        room = self.current_room()
        for position in room["blocks"]["brown"]:
            self.draw_cell(position["x"], position["y"], "#8a4f2a")
        for position in room["blocks"]["white"]:
            self.draw_cell(position["x"], position["y"], "#d7d7cf")
        for x in range(ROOM_WIDTH + 1):
            self.canvas.create_line(x * CELL, 0, x * CELL, CANVAS_HEIGHT, fill="#405060")
        for y in range(ROOM_HEIGHT + 1):
            self.canvas.create_line(0, y * CELL, CANVAS_WIDTH, y * CELL, fill="#405060")
        metadata = room["items"]["metadata"]
        for field, text, color in (
            ("player_start", "P", "#66ddff"),
            ("key", "K", "#ffff55"),
            ("door", "D", "#66ff77"),
            ("mirror_1", "M1", "#dd88ff"),
            ("mirror_2", "M2", "#bb66ff"),
        ):
            self.draw_label(metadata[field], text, color)
        for enemy in room["enemies"]["placements"]:
            position = enemy["position"]
            x, y = position["x"], position["y"]
            self.canvas.create_oval(
                x * CELL + 5,
                y * CELL + 5,
                (x + 1) * CELL - 5,
                (y + 1) * CELL - 5,
                fill="#bb3344",
                outline="#ff99aa",
            )
            self.draw_label(position, f"{enemy['type']:02X}", "white")
        for item in self.model.item_placements(self.room_index.get()):
            x, y = item.position["x"], item.position["y"]
            if y < 0 or y >= ROOM_HEIGHT:
                continue
            self.canvas.create_polygon(
                x * CELL + CELL // 2,
                y * CELL + 4,
                (x + 1) * CELL - 4,
                y * CELL + CELL // 2,
                x * CELL + CELL // 2,
                (y + 1) * CELL - 4,
                x * CELL + 4,
                y * CELL + CELL // 2,
                fill="#d6a900",
                outline="#fff099",
            )
            self.draw_label(item.position, f"{item.item_type:02X}", "#201800")
        self.set_status(
            f"Room {self.room_index.get() + 1:02d}: "
            f"{len(room['enemies']['placements'])} enemies, "
            f"{len(self.model.item_placements(self.room_index.get()))} items"
        )

    def validate_and_build(self) -> bytes:
        base = self.reference.read_bytes()
        image, _ = build_level_image(self.model.document, base, self.profile)
        validate_rebuilt_document(self.model.document, image, self.profile)
        return image

    def save(self) -> bool:
        try:
            self.validate_and_build()
            save_document(self.document_path, self.model.document)
            self.model.mark_saved()
            self.set_status("Saved and validated")
            return True
        except (OSError, LevelEditorError, RoomDataError, ProjectError) as exc:
            messagebox.showerror("Cannot save level document", str(exc))
            return False

    def build_rom(self) -> bool:
        try:
            image = self.validate_and_build()
            save_document(self.document_path, self.model.document)
            write_if_changed(self.output_path, image)
            self.model.mark_saved()
            self.set_status(f"Built {self.output_path}")
            return True
        except (OSError, LevelEditorError, RoomDataError, ProjectError) as exc:
            messagebox.showerror("Cannot build level ROM", str(exc))
            return False

    def play(self) -> None:
        if not self.build_rom():
            return
        if not self.fceux.is_file():
            messagebox.showerror("FCEUX not found", str(self.fceux))
            return
        try:
            subprocess.Popen([str(self.fceux), str(self.output_path)])
        except OSError as exc:
            messagebox.showerror("Cannot start FCEUX", str(exc))

    def close(self) -> None:
        if self.model.dirty and not messagebox.askyesno(
            "Unsaved edits", "Discard unsaved level edits?"
        ):
            return
        self.destroy()


def load_studio_document(
    profile: dict[str, Any],
    reference: Path,
    document_path: Path,
) -> dict[str, Any]:
    parsed = verify_reference(reference, profile)
    if document_path.is_file():
        document = load_document(document_path)
        if document["source_profile"] != profile["id"]:
            raise LevelEditorError("workspace profile does not match selected profile")
        return document
    document = export_document(parsed, profile)
    save_document(document_path, document)
    return document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="usa")
    parser.add_argument(
        "--profiles",
        type=Path,
        default=ROOT / "config" / "revision_profiles.json",
    )
    parser.add_argument("--private-root", type=Path, default=ROOT)
    parser.add_argument("--base-rom", type=Path)
    parser.add_argument("--document", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--fceux",
        type=Path,
        default=ROOT.parent / "fceux_automation" / "vc" / "x64" / "Release" / "fceux64.exe",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the workspace and codec without opening a window",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        profiles = load_profiles(args.profiles)
        profile = get_profile(profiles, args.profile)
        reference = resolve_reference(profile, args.private_root, args.base_rom)
        document_path = args.document or (
            ROOT / "content" / "workspace" / profile["id"] / "levels.json"
        )
        output_path = args.output or (
            ROOT / "build" / "content" / profile["id"] / "solomons_key_levels.nes"
        )
        document = load_studio_document(profile, reference, document_path)
        model = StudioDocument(document)
        base_image = reference.read_bytes()
        rebuilt, usage = build_level_image(document, base_image, profile)
        validate_rebuilt_document(document, rebuilt, profile)
        if args.check:
            print(
                f"[OK] Level Studio {profile['id']}: {ROOM_COUNT} rooms, "
                f"{sum(used for used, _ in usage.values())} encoded bytes"
            )
            return 0
        studio = LevelStudio(
            model,
            profile,
            reference,
            document_path,
            output_path,
            args.fceux,
        )
        studio.mainloop()
    except (
        OSError,
        KeyError,
        TypeError,
        tk.TclError,
        ProjectError,
        RoomDataError,
        LevelEditorError,
    ) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
