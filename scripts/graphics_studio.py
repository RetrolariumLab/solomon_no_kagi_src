#!/usr/bin/env python3
"""Visual four-bank CHR tile editor backed by the byte-exact graphics codec."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

import graphics_editor
from project import ProjectError, write_if_changed
from revision_profiles import (
    ROOT,
    get_profile,
    load_profiles,
    resolve_reference,
    verify_reference,
)


ATLAS_COLUMNS = 16
ATLAS_ROWS = graphics_editor.TILES_PER_BANK // ATLAS_COLUMNS
ATLAS_SCALE = 2
EDITOR_SCALE = 32
DISPLAY_COLORS = ("#101820", "#54616c", "#a7b0b7", "#f2f4f5")


def tile_position(index: int) -> tuple[int, int]:
    if not 0 <= index < graphics_editor.TILES_PER_BANK:
        raise graphics_editor.GraphicsEditorError("tile index must be 0..511")
    return index % ATLAS_COLUMNS, index // ATLAS_COLUMNS


def tile_index(column: int, row: int) -> int:
    if not 0 <= column < ATLAS_COLUMNS or not 0 <= row < ATLAS_ROWS:
        raise graphics_editor.GraphicsEditorError("atlas position is outside the bank")
    return row * ATLAS_COLUMNS + column


def atlas_pixels(document: dict[str, Any], bank: int) -> list[str]:
    """Project one complete bank into a compact 128x256 color-index raster."""
    if not 0 <= bank < graphics_editor.CHR_BANK_COUNT:
        raise graphics_editor.GraphicsEditorError("bank index must be 0..3")
    width = ATLAS_COLUMNS * graphics_editor.TILE_WIDTH
    rows = [["0"] * width for _ in range(ATLAS_ROWS * graphics_editor.TILE_HEIGHT)]
    tiles = document["banks"][bank]["tiles"]
    if len(tiles) != graphics_editor.TILES_PER_BANK:
        raise graphics_editor.GraphicsEditorError("atlas bank has an incomplete tile set")
    for index, tile in enumerate(tiles):
        tile_column, tile_row = tile_position(index)
        checked = graphics_editor.validate_rows(
            tile.get("rows"), f"banks[{bank}].tiles[{index}].rows"
        )
        left = tile_column * graphics_editor.TILE_WIDTH
        top = tile_row * graphics_editor.TILE_HEIGHT
        for y, source in enumerate(checked):
            rows[top + y][left : left + graphics_editor.TILE_WIDTH] = source
    return ["".join(row) for row in rows]


class GraphicsStudioDocument:
    """Undoable tile state which delegates binary checks to graphics_editor."""

    def __init__(
        self,
        document: dict[str, Any],
        profile: dict[str, Any],
        base_image: bytes,
        path: Path,
        output: Path,
    ) -> None:
        self.document = copy.deepcopy(document)
        self.profile = profile
        self.base_image = base_image
        self.path = path
        self.output = output
        self.undo_stack: list[tuple[int, int, list[str]]] = []
        self.saved = graphics_editor.canonical_document(self.document)
        self.validate()

    @property
    def dirty(self) -> bool:
        return graphics_editor.canonical_document(self.document) != self.saved

    def rows(self, bank: int, tile: int) -> list[str]:
        tile_position(tile)
        if not 0 <= bank < graphics_editor.CHR_BANK_COUNT:
            raise graphics_editor.GraphicsEditorError("bank index must be 0..3")
        return list(self.document["banks"][bank]["tiles"][tile]["rows"])

    def replace_rows(self, bank: int, tile: int, rows: list[str]) -> bool:
        checked = graphics_editor.validate_rows(rows, "replacement tile")
        current = self.rows(bank, tile)
        if current == checked:
            return False
        graphics_editor.encode_tile(checked)
        self.undo_stack.append((bank, tile, current))
        del self.undo_stack[:-100]
        self.document["banks"][bank]["tiles"][tile]["rows"] = list(checked)
        return True

    def edit_pixel(self, bank: int, tile: int, x: int, y: int, pixel: int) -> bool:
        if not 0 <= x < 8 or not 0 <= y < 8 or not 0 <= pixel <= 3:
            raise graphics_editor.GraphicsEditorError("pixel edit is outside 8x8/2-bit bounds")
        rows = self.rows(bank, tile)
        rows[y] = rows[y][:x] + str(pixel) + rows[y][x + 1 :]
        return self.replace_rows(bank, tile, rows)

    def transform(self, bank: int, tile: int, operation: str, pixel: int = 0) -> bool:
        rows = self.rows(bank, tile)
        if operation == "fill":
            changed = [str(pixel) * 8 for _ in range(8)]
        elif operation == "flip_horizontal":
            changed = [row[::-1] for row in rows]
        elif operation == "flip_vertical":
            changed = list(reversed(rows))
        elif operation == "rotate_clockwise":
            changed = ["".join(rows[7 - x][y] for x in range(8)) for y in range(8)]
        else:
            raise graphics_editor.GraphicsEditorError(f"unknown tile operation: {operation}")
        return self.replace_rows(bank, tile, changed)

    def undo(self) -> tuple[int, int] | None:
        if not self.undo_stack:
            return None
        bank, tile, rows = self.undo_stack.pop()
        self.document["banks"][bank]["tiles"][tile]["rows"] = rows
        return bank, tile

    def rebuilt_image(self) -> bytes:
        image = graphics_editor.build_graphics_image(
            self.document, self.base_image, self.profile
        )
        graphics_editor.validate_rebuilt_document(self.document, image, self.profile)
        return image

    def validate(self) -> None:
        self.rebuilt_image()

    def save(self) -> str:
        self.validate()
        action = graphics_editor.save_document(self.path, self.document)
        self.saved = graphics_editor.canonical_document(self.document)
        return action

    def build(self) -> str:
        return write_if_changed(self.output, self.rebuilt_image())


def load_studio_document(
    profile: dict[str, Any], reference: Path, path: Path, output: Path
) -> GraphicsStudioDocument:
    verify_reference(reference, profile)
    document = (
        graphics_editor.load_document(path)
        if path.is_file()
        else graphics_editor.export_document(reference.read_bytes(), profile)
    )
    document = graphics_editor.upgrade_document(
        document, reference.read_bytes(), profile
    )
    return GraphicsStudioDocument(
        document, profile, reference.read_bytes(), path, output
    )


class GraphicsStudio(tk.Tk):
    def __init__(self, model: GraphicsStudioDocument) -> None:
        super().__init__()
        self.model = model
        self.bank = tk.IntVar(value=0)
        self.tile = tk.IntVar(value=0)
        self.pixel = tk.IntVar(value=1)
        self.status = tk.StringVar()
        self.clipboard_tile: list[str] | None = None
        self.atlas_image: tk.PhotoImage | None = None
        self.atlas_zoom: tk.PhotoImage | None = None
        self.title(f"Solomon's Key Graphics Studio [{model.profile['id']}]")
        self.geometry("920x690")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.build_ui()
        self.bind_shortcuts()
        self.refresh_all()

    def build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=7)
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text=f"Profile: {self.model.profile['name']}").pack(
            side="left"
        )
        ttk.Label(toolbar, text="Bank:").pack(side="left", padx=(14, 3))
        bank = ttk.Combobox(
            toolbar,
            textvariable=self.bank,
            values=tuple(range(graphics_editor.CHR_BANK_COUNT)),
            width=3,
            state="readonly",
        )
        bank.pack(side="left")
        bank.bind("<<ComboboxSelected>>", lambda _event: self.select_bank())
        for label, command in (
            ("Undo", self.undo),
            ("Save", self.save),
            ("Build ROM", self.build_rom),
        ):
            ttk.Button(toolbar, text=label, command=command).pack(side="left", padx=4)

        body = ttk.Frame(self, padding=(7, 0, 7, 7))
        body.pack(fill="both", expand=True)
        atlas_frame = ttk.LabelFrame(body, text="512-tile bank atlas", padding=5)
        atlas_frame.pack(side="left", fill="y")
        atlas_width = ATLAS_COLUMNS * 8 * ATLAS_SCALE
        atlas_height = ATLAS_ROWS * 8 * ATLAS_SCALE
        self.atlas = tk.Canvas(
            atlas_frame,
            width=atlas_width,
            height=atlas_height,
            highlightthickness=0,
            bg=DISPLAY_COLORS[0],
        )
        self.atlas.pack()
        self.atlas.bind("<Button-1>", self.click_atlas)

        editor_frame = ttk.LabelFrame(body, text="Selected 8x8 tile", padding=10)
        editor_frame.pack(side="left", fill="both", expand=True, padx=(9, 0))
        heading = ttk.Frame(editor_frame)
        heading.pack(fill="x")
        ttk.Label(heading, text="Tile:").pack(side="left")
        tile = ttk.Spinbox(
            heading,
            from_=0,
            to=graphics_editor.TILES_PER_BANK - 1,
            textvariable=self.tile,
            width=6,
            command=self.select_tile,
        )
        tile.pack(side="left", padx=4)
        tile.bind("<Return>", lambda _event: self.select_tile())
        self.address = ttk.Label(heading)
        self.address.pack(side="left", padx=8)

        self.editor = tk.Canvas(
            editor_frame,
            width=8 * EDITOR_SCALE,
            height=8 * EDITOR_SCALE,
            highlightthickness=1,
            highlightbackground="#39434c",
        )
        self.editor.pack(pady=12)
        self.editor.bind("<Button-1>", self.paint_pixel)
        self.editor.bind("<B1-Motion>", self.paint_pixel)

        palette = ttk.Frame(editor_frame)
        palette.pack()
        ttk.Label(palette, text="Pixel:").pack(side="left", padx=(0, 6))
        for value, color in enumerate(DISPLAY_COLORS):
            button = tk.Radiobutton(
                palette,
                variable=self.pixel,
                value=value,
                bg=color,
                activebackground=color,
                selectcolor=color,
                width=3,
                indicatoron=False,
                text=str(value),
                fg="white" if value < 2 else "black",
                command=self.refresh_status,
            )
            button.pack(side="left", padx=2)

        actions = ttk.Frame(editor_frame)
        actions.pack(pady=12)
        for label, command in (
            ("Fill", self.fill_tile),
            ("Flip H", lambda: self.transform("flip_horizontal")),
            ("Flip V", lambda: self.transform("flip_vertical")),
            ("Rotate", lambda: self.transform("rotate_clockwise")),
            ("Copy", self.copy_tile),
            ("Paste", self.paste_tile),
        ):
            ttk.Button(actions, text=label, command=command).pack(
                side="left", padx=3
            )

        ttk.Label(
            editor_frame,
            text=(
                "Click or drag to paint. Arrow keys select tiles; "
                "Page Up/Down switches banks."
            ),
            wraplength=420,
        ).pack(pady=(4, 0))
        ttk.Label(self, textvariable=self.status, anchor="w", padding=7).pack(fill="x")

    def bind_shortcuts(self) -> None:
        self.bind("<Control-s>", lambda _event: self.save())
        self.bind("<Control-z>", lambda _event: self.undo())
        self.bind("<Control-c>", lambda _event: self.copy_tile())
        self.bind("<Control-v>", lambda _event: self.paste_tile())
        self.bind("<Left>", lambda _event: self.move_tile(-1, 0))
        self.bind("<Right>", lambda _event: self.move_tile(1, 0))
        self.bind("<Up>", lambda _event: self.move_tile(0, -1))
        self.bind("<Down>", lambda _event: self.move_tile(0, 1))
        self.bind("<Prior>", lambda _event: self.move_bank(-1))
        self.bind("<Next>", lambda _event: self.move_bank(1))

    def guarded(self, action: Callable[[], Any]) -> Any | None:
        try:
            return action()
        except (graphics_editor.GraphicsEditorError, OSError, KeyError, IndexError) as exc:
            messagebox.showerror("Graphics Studio", str(exc), parent=self)
            return None

    def select_bank(self) -> None:
        self.bank.set(max(0, min(3, self.bank.get())))
        self.refresh_all()

    def select_tile(self) -> None:
        self.tile.set(max(0, min(511, self.tile.get())))
        self.refresh_selection()

    def move_bank(self, amount: int) -> None:
        self.bank.set((self.bank.get() + amount) % graphics_editor.CHR_BANK_COUNT)
        self.refresh_all()

    def move_tile(self, dx: int, dy: int) -> None:
        column, row = tile_position(self.tile.get())
        column = (column + dx) % ATLAS_COLUMNS
        row = (row + dy) % ATLAS_ROWS
        self.tile.set(tile_index(column, row))
        self.refresh_selection()

    def click_atlas(self, event: tk.Event[tk.Misc]) -> None:
        size = 8 * ATLAS_SCALE
        column = max(0, min(ATLAS_COLUMNS - 1, event.x // size))
        row = max(0, min(ATLAS_ROWS - 1, event.y // size))
        self.tile.set(tile_index(column, row))
        self.refresh_selection()

    def paint_pixel(self, event: tk.Event[tk.Misc]) -> None:
        x = max(0, min(7, event.x // EDITOR_SCALE))
        y = max(0, min(7, event.y // EDITOR_SCALE))
        changed = self.guarded(
            lambda: self.model.edit_pixel(
                self.bank.get(), self.tile.get(), x, y, self.pixel.get()
            )
        )
        if changed:
            self.refresh_all()

    def fill_tile(self) -> None:
        self.transform("fill")

    def transform(self, operation: str) -> None:
        changed = self.guarded(
            lambda: self.model.transform(
                self.bank.get(), self.tile.get(), operation, self.pixel.get()
            )
        )
        if changed:
            self.refresh_all()

    def copy_tile(self) -> None:
        self.clipboard_tile = self.model.rows(self.bank.get(), self.tile.get())
        self.status.set(f"Copied bank {self.bank.get()} tile ${self.tile.get():03X}")

    def paste_tile(self) -> None:
        if self.clipboard_tile is None:
            self.status.set("Copy a tile before pasting")
            return
        changed = self.guarded(
            lambda: self.model.replace_rows(
                self.bank.get(), self.tile.get(), self.clipboard_tile or []
            )
        )
        if changed:
            self.refresh_all()

    def undo(self) -> None:
        restored = self.model.undo()
        if restored is not None:
            bank, tile = restored
            self.bank.set(bank)
            self.tile.set(tile)
            self.refresh_all()

    def save(self) -> None:
        action = self.guarded(self.model.save)
        if action is not None:
            self.status.set(f"[{action}] graphics document: {self.model.path}")

    def build_rom(self) -> None:
        action = self.guarded(self.model.build)
        if action is not None:
            self.status.set(f"[{action}] graphics ROM: {self.model.output}")

    def refresh_atlas(self) -> None:
        pixels = atlas_pixels(self.model.document, self.bank.get())
        image = tk.PhotoImage(
            width=ATLAS_COLUMNS * 8,
            height=ATLAS_ROWS * 8,
        )
        for y, row in enumerate(pixels):
            colors = " ".join(DISPLAY_COLORS[int(pixel)] for pixel in row)
            image.put("{" + colors + "}", to=(0, y))
        self.atlas_image = image
        self.atlas_zoom = image.zoom(ATLAS_SCALE, ATLAS_SCALE)
        self.atlas.delete("all")
        self.atlas.create_image(0, 0, image=self.atlas_zoom, anchor="nw")
        size = 8 * ATLAS_SCALE
        for row in range(ATLAS_ROWS):
            for column in range(ATLAS_COLUMNS):
                self.atlas.create_rectangle(
                    column * size,
                    row * size,
                    (column + 1) * size,
                    (row + 1) * size,
                    outline="#29343c",
                )

    def refresh_selection(self) -> None:
        self.editor.delete("all")
        rows = self.model.rows(self.bank.get(), self.tile.get())
        for y, row in enumerate(rows):
            for x, pixel in enumerate(row):
                self.editor.create_rectangle(
                    x * EDITOR_SCALE,
                    y * EDITOR_SCALE,
                    (x + 1) * EDITOR_SCALE,
                    (y + 1) * EDITOR_SCALE,
                    fill=DISPLAY_COLORS[int(pixel)],
                    outline="#39434c",
                )
        column, row = tile_position(self.tile.get())
        size = 8 * ATLAS_SCALE
        self.atlas.delete("selection")
        self.atlas.create_rectangle(
            column * size + 1,
            row * size + 1,
            (column + 1) * size - 1,
            (row + 1) * size - 1,
            outline="#ffcc33",
            width=2,
            tags="selection",
        )
        absolute = self.bank.get() * 512 + self.tile.get()
        self.address.configure(text=f"bank ${self.bank.get():X}  tile ${self.tile.get():03X}  absolute ${absolute:03X}")
        self.refresh_status()

    def refresh_status(self) -> None:
        marker = "modified" if self.model.dirty else "saved"
        self.status.set(
            f"Bank {self.bank.get()} / tile {self.tile.get()} / pixel {self.pixel.get()} — {marker}"
        )

    def refresh_all(self) -> None:
        self.refresh_atlas()
        self.refresh_selection()

    def close(self) -> None:
        if self.model.dirty and not messagebox.askyesno(
            "Graphics Studio", "Discard unsaved graphics changes?", parent=self
        ):
            return
        self.destroy()


def check_profile(profile: dict[str, Any], reference: Path) -> str:
    verify_reference(reference, profile)
    document = graphics_editor.export_document(reference.read_bytes(), profile)
    model = GraphicsStudioDocument(
        document,
        profile,
        reference.read_bytes(),
        Path("graphics.json"),
        Path("graphics.nes"),
    )
    pixel_total = 0
    for bank in range(graphics_editor.CHR_BANK_COUNT):
        projection = atlas_pixels(model.document, bank)
        if len(projection) != 256 or any(len(row) != 128 for row in projection):
            raise graphics_editor.GraphicsEditorError("invalid bank atlas projection")
        pixel_total += sum(len(row) for row in projection)
    if model.rebuilt_image() != reference.read_bytes():
        raise graphics_editor.GraphicsEditorError("Graphics Studio changed stock CHR")
    return f"4 bank atlases, 2,048 tiles, {pixel_total:,} projected pixels"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profiles", type=Path, default=ROOT / "config" / "revision_profiles.json"
    )
    parser.add_argument("--private-root", type=Path, default=ROOT)
    parser.add_argument("--profile", default="usa")
    parser.add_argument("--document", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        profiles = load_profiles(args.profiles)
        profile = get_profile(profiles, args.profile)
        reference = resolve_reference(profile, args.private_root)
        if args.check:
            print(f"[OK] {profile['id']} Graphics Studio: {check_profile(profile, reference)}")
            return 0
        document = args.document or ROOT / "content/workspace" / args.profile / "graphics.json"
        output = args.output or ROOT / "build/content" / args.profile / "solomons_key_graphics.nes"
        GraphicsStudio(load_studio_document(profile, reference, document, output)).mainloop()
    except (
        graphics_editor.GraphicsEditorError,
        ProjectError,
        OSError,
        KeyError,
        IndexError,
        tk.TclError,
    ) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
