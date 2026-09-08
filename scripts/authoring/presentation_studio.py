#!/usr/bin/env python3
"""Visual editor for packed title tiles and attract-demo controller steps."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

from scripts.authoring import graphics_editor
from scripts.authoring.level_preview import NES_RGB
from scripts.authoring import presentation_editor
from scripts.build.project import ProjectError, parse_ines, write_if_changed
from scripts.build.revision_profiles import (
    ROOT,
    get_profile,
    load_profiles,
    resolve_reference,
    verify_reference,
)
from scripts.authoring.room_data import RoomDataError
from scripts.authoring import title_data


TITLE_COLUMNS = 32
TITLE_ROWS = 30
TITLE_SCALE = 2
TITLE_CHR_BANK = 3
TITLE_PATTERN_TABLE_TILE = 256
DISPLAY_PALETTE = (0x0F, 0x11, 0x21, 0x30)
BUTTONS = tuple(name for _, name in title_data.BUTTON_BITS)
COMMAND_KINDS = ("set_column", "set_row", "add_row", "terminate")


def rgb_hex(index: int) -> str:
    red, green, blue = NES_RGB[index & 0x3F]
    return f"#{red:02x}{green:02x}{blue:02x}"


def parse_integer(text: str, field: str, maximum: int = 0xFF) -> int:
    value = text.strip()
    base = 16 if value.startswith("$") else 0
    if value.startswith("$"):
        value = value[1:]
    try:
        result = int(value, base)
    except ValueError as exc:
        raise presentation_editor.PresentationEditorError(
            f"{field} is not an integer"
        ) from exc
    if not 0 <= result <= maximum:
        raise presentation_editor.PresentationEditorError(
            f"{field} must be between 0 and {maximum}"
        )
    return result


def literal_text(tiles: list[int]) -> str:
    return " ".join(f"{tile:02X}" for tile in tiles)


def parse_literal(text: str, expected: int) -> list[int]:
    words = text.replace(",", " ").split()
    try:
        tiles = [int(word[1:] if word.startswith("$") else word, 16) for word in words]
    except ValueError as exc:
        raise presentation_editor.PresentationEditorError(
            "literal tiles must be hexadecimal bytes"
        ) from exc
    if len(tiles) != expected:
        raise presentation_editor.PresentationEditorError(
            f"literal run must retain exactly {expected} tiles"
        )
    if any(not 0x80 <= tile <= 0xFF for tile in tiles):
        raise presentation_editor.PresentationEditorError(
            "literal title tiles must remain in $80-$FF"
        )
    return tiles


def encoded_stream(document: dict[str, Any], profile: dict[str, Any], index: int) -> bytes:
    manifest = presentation_editor.profile_manifest(profile)
    writes = presentation_editor.encode_streams(document, profile, manifest)
    return writes[index][1]


def stream_projection(
    document: dict[str, Any], profile: dict[str, Any], index: int
) -> list[list[int | None]]:
    """Decode a document stream into the physical $2800 nametable surface."""
    layout = document["layout"]["streams"][index]
    address = int(layout["address"])
    payload = encoded_stream(document, profile, index)
    prg = bytearray(0x8000)
    offset = title_data.prg_offset(address)
    prg[offset : offset + len(payload)] = payload
    decoded = title_data.decode_stream(bytes(prg), address)
    surface: list[list[int | None]] = [
        [None] * TITLE_COLUMNS for _ in range(TITLE_ROWS)
    ]
    for token in decoded.tokens:
        if not isinstance(token, title_data.TitleLiteralRun):
            continue
        for delta, tile in enumerate(token.tiles):
            ppu_address = token.ppu_address + delta
            if not 0x2800 <= ppu_address < 0x2BC0:
                raise presentation_editor.PresentationEditorError(
                    f"title literal targets unsupported PPU address ${ppu_address:04X}"
                )
            relative = ppu_address - 0x2800
            row, column = divmod(relative, TITLE_COLUMNS)
            surface[row][column] = tile
    return surface


def chr_title_tiles(image: bytes) -> list[list[str]]:
    parsed = parse_ines(image)
    chr_data = bytes(parsed["chr"])
    bank_start = TITLE_CHR_BANK * graphics_editor.CHR_BANK_SIZE
    table_start = bank_start + TITLE_PATTERN_TABLE_TILE * graphics_editor.TILE_SIZE
    result: list[list[str]] = []
    for tile in range(256):
        start = table_start + tile * graphics_editor.TILE_SIZE
        result.append(graphics_editor.decode_tile(chr_data[start : start + 16]))
    return result


def projected_literal_count(surface: list[list[int | None]]) -> int:
    return sum(tile is not None for row in surface for tile in row)


class PresentationStudioDocument:
    """Undoable presentation state backed by the deterministic ROM codec."""

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
        self.undo_stack: list[dict[str, Any]] = []
        self.saved = presentation_editor.canonical_document(self.document)
        self.title_tiles = chr_title_tiles(base_image)
        self.validate()

    @property
    def dirty(self) -> bool:
        return presentation_editor.canonical_document(self.document) != self.saved

    def _change(self, mutate: Callable[[dict[str, Any]], None]) -> bool:
        candidate = copy.deepcopy(self.document)
        mutate(candidate)
        if presentation_editor.canonical_document(candidate) == presentation_editor.canonical_document(
            self.document
        ):
            return False
        presentation_editor.build_presentation_image(candidate, self.base_image, self.profile)
        self.undo_stack.append(copy.deepcopy(self.document))
        del self.undo_stack[:-100]
        self.document = candidate
        return True

    def edit_literal(self, stream: int, token: int, tiles: list[int]) -> bool:
        current = self.document["streams"][stream]["tokens"][token]
        if current.get("kind") != "literal":
            raise presentation_editor.PresentationEditorError("selected token is not literal")
        if len(tiles) != len(current["tiles"]):
            raise presentation_editor.PresentationEditorError(
                "literal edit cannot change fixed stream capacity"
            )

        def mutate(document: dict[str, Any]) -> None:
            document["streams"][stream]["tokens"][token]["tiles"] = list(tiles)

        return self._change(mutate)

    def edit_command(self, stream: int, token: int, kind: str, value: int | None) -> bool:
        if kind not in COMMAND_KINDS:
            raise presentation_editor.PresentationEditorError("unknown title command")
        replacement: dict[str, object] = {"kind": kind}
        if kind != "terminate":
            replacement["value"] = value

        def mutate(document: dict[str, Any]) -> None:
            if document["streams"][stream]["tokens"][token].get("kind") == "literal":
                raise presentation_editor.PresentationEditorError(
                    "literal and command tokens have different encoded sizes"
                )
            document["streams"][stream]["tokens"][token] = replacement

        return self._change(mutate)

    def edit_demo_step(self, index: int, duration: int, buttons: list[str]) -> bool:
        if len(buttons) != len(set(buttons)):
            raise presentation_editor.PresentationEditorError("demo buttons are duplicated")

        def mutate(document: dict[str, Any]) -> None:
            step = document["demo_steps"][index]
            step["duration"] = duration
            step["buttons"] = [button for button in BUTTONS if button in buttons]

        return self._change(mutate)

    def projection(self, stream: int) -> list[list[int | None]]:
        return stream_projection(self.document, self.profile, stream)

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        self.document = self.undo_stack.pop()
        return True

    def rebuilt_image(self) -> bytes:
        image = presentation_editor.build_presentation_image(
            self.document, self.base_image, self.profile
        )
        presentation_editor.validate_rebuilt_document(
            self.document, image, self.profile
        )
        return image

    def validate(self) -> None:
        self.rebuilt_image()

    def save(self) -> str:
        self.validate()
        action = presentation_editor.save_document(self.path, self.document)
        self.saved = presentation_editor.canonical_document(self.document)
        return action

    def build(self) -> str:
        return write_if_changed(self.output, self.rebuilt_image())


def load_studio_document(
    profile: dict[str, Any], reference: Path, path: Path, output: Path
) -> PresentationStudioDocument:
    verify_reference(reference, profile)
    base_image = reference.read_bytes()
    if path.is_file():
        document = presentation_editor.load_document(path)
    else:
        document = presentation_editor.export_document(base_image, profile)
    return PresentationStudioDocument(document, profile, base_image, path, output)


class PresentationStudio(tk.Tk):
    def __init__(self, model: PresentationStudioDocument) -> None:
        super().__init__()
        self.model = model
        self.title("Solomon's Key Presentation Studio")
        self.geometry("1050x760")
        self.minsize(880, 640)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.stream_index = tk.IntVar(value=0)
        self.token_index = tk.IntVar(value=0)
        self.demo_index = tk.IntVar(value=0)
        self.command_kind = tk.StringVar()
        self.command_value = tk.StringVar()
        self.literal_value = tk.StringVar()
        self.duration_value = tk.StringVar()
        self.button_values = {button: tk.BooleanVar() for button in BUTTONS}
        self.status = tk.StringVar()
        self._build_menu()
        self._build_layout()
        self.refresh_all()

    def _build_menu(self) -> None:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Save document", accelerator="Ctrl+S", command=self.save)
        file_menu.add_command(label="Build ROM", accelerator="Ctrl+B", command=self.build_rom)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close)
        menu.add_cascade(label="File", menu=file_menu)
        edit_menu = tk.Menu(menu, tearoff=False)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        menu.add_cascade(label="Edit", menu=edit_menu)
        self.configure(menu=menu)
        self.bind_all("<Control-s>", lambda _event: self.save())
        self.bind_all("<Control-b>", lambda _event: self.build_rom())
        self.bind_all("<Control-z>", lambda _event: self.undo())

    def _build_layout(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)
        title_tab = ttk.Frame(notebook, padding=8)
        demo_tab = ttk.Frame(notebook, padding=8)
        notebook.add(title_tab, text="Title layers")
        notebook.add(demo_tab, text="Attract demo")
        self._build_title_tab(title_tab)
        self._build_demo_tab(demo_tab)
        ttk.Label(self, textvariable=self.status, anchor="w").pack(fill="x", padx=10, pady=(0, 8))

    def _build_title_tab(self, parent: ttk.Frame) -> None:
        controls = ttk.Frame(parent)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Label(controls, text="Layer:").pack(side="left")
        self.stream_box = ttk.Combobox(controls, state="readonly", width=18)
        self.stream_box.pack(side="left", padx=(5, 16))
        self.stream_box.bind("<<ComboboxSelected>>", self.select_stream)
        ttk.Label(controls, text="Token:").pack(side="left")
        self.token_box = ttk.Combobox(controls, state="readonly", width=38)
        self.token_box.pack(side="left", padx=5, fill="x", expand=True)
        self.token_box.bind("<<ComboboxSelected>>", self.select_token)

        body = ttk.Panedwindow(parent, orient="horizontal")
        body.pack(fill="both", expand=True)
        preview_frame = ttk.LabelFrame(body, text="32 x 30 nametable projection", padding=6)
        editor_frame = ttk.LabelFrame(body, text="Selected packed token", padding=10)
        body.add(preview_frame, weight=3)
        body.add(editor_frame, weight=2)
        width = TITLE_COLUMNS * 8 * TITLE_SCALE
        height = TITLE_ROWS * 8 * TITLE_SCALE
        self.title_canvas = tk.Canvas(
            preview_frame, width=width, height=height, bg="#101820", highlightthickness=0
        )
        self.title_canvas.pack(fill="both", expand=True)
        self.title_canvas.bind("<Button-1>", self.select_title_cell)

        self.token_description = ttk.Label(editor_frame, wraplength=300, justify="left")
        self.token_description.pack(fill="x", pady=(0, 12))
        ttk.Label(editor_frame, text="Command kind").pack(anchor="w")
        self.kind_box = ttk.Combobox(
            editor_frame, textvariable=self.command_kind, values=COMMAND_KINDS, state="readonly"
        )
        self.kind_box.pack(fill="x", pady=(2, 8))
        ttk.Label(editor_frame, text="Command value (decimal or $hex)").pack(anchor="w")
        self.value_entry = ttk.Entry(editor_frame, textvariable=self.command_value)
        self.value_entry.pack(fill="x", pady=(2, 8))
        ttk.Button(editor_frame, text="Apply command", command=self.apply_command).pack(fill="x")
        ttk.Separator(editor_frame).pack(fill="x", pady=14)
        ttk.Label(editor_frame, text="Literal tile bytes (fixed count)").pack(anchor="w")
        self.literal_entry = ttk.Entry(editor_frame, textvariable=self.literal_value)
        self.literal_entry.pack(fill="x", pady=(2, 8))
        ttk.Button(editor_frame, text="Apply literal tiles", command=self.apply_literal).pack(fill="x")
        ttk.Label(
            editor_frame,
            text="The preview uses CNROM bank 3 and background pattern table 1, matching PpuCtrlShadow $B0.",
            wraplength=300,
            justify="left",
        ).pack(fill="x", pady=(18, 0))

    def _build_demo_tab(self, parent: ttk.Frame) -> None:
        body = ttk.Panedwindow(parent, orient="horizontal")
        body.pack(fill="both", expand=True)
        list_frame = ttk.Frame(body)
        editor = ttk.LabelFrame(body, text="Selected controller step", padding=10)
        body.add(list_frame, weight=3)
        body.add(editor, weight=2)
        self.demo_tree = ttk.Treeview(
            list_frame, columns=("step", "duration", "buttons"), show="headings", selectmode="browse"
        )
        self.demo_tree.heading("step", text="Step")
        self.demo_tree.heading("duration", text="Duration")
        self.demo_tree.heading("buttons", text="Buttons")
        self.demo_tree.column("step", width=60, anchor="e")
        self.demo_tree.column("duration", width=90, anchor="e")
        self.demo_tree.column("buttons", width=260)
        self.demo_tree.pack(fill="both", expand=True)
        self.demo_tree.bind("<<TreeviewSelect>>", self.select_demo_step)
        ttk.Label(editor, text="Duration byte (0 means 256 playback frames)").pack(anchor="w")
        ttk.Entry(editor, textvariable=self.duration_value).pack(fill="x", pady=(2, 12))
        button_frame = ttk.LabelFrame(editor, text="Held buttons", padding=8)
        button_frame.pack(fill="x")
        for index, button in enumerate(BUTTONS):
            ttk.Checkbutton(
                button_frame, text=button, variable=self.button_values[button]
            ).grid(row=index // 2, column=index % 2, sticky="w", padx=5, pady=3)
        ttk.Button(editor, text="Apply demo step", command=self.apply_demo).pack(fill="x", pady=12)
        self.timeline = tk.Canvas(editor, height=120, bg="#101820", highlightthickness=0)
        self.timeline.pack(fill="x", pady=(8, 0))
        ttk.Label(
            editor,
            text="Each record is one duration byte plus one NES controller mask. Step order and count stay fixed.",
            wraplength=300,
            justify="left",
        ).pack(fill="x", pady=(12, 0))

    def selected_token(self) -> dict[str, Any]:
        return self.model.document["streams"][self.stream_index.get()]["tokens"][self.token_index.get()]

    def select_stream(self, _event: object = None) -> None:
        self.stream_index.set(self.stream_box.current())
        self.token_index.set(0)
        self.refresh_title()

    def select_token(self, _event: object = None) -> None:
        self.token_index.set(max(0, self.token_box.current()))
        self.refresh_token_editor()

    def select_title_cell(self, event: tk.Event[tk.Misc]) -> None:
        column = int(self.title_canvas.canvasx(event.x)) // (8 * TITLE_SCALE)
        row = int(self.title_canvas.canvasy(event.y)) // (8 * TITLE_SCALE)
        if not (0 <= column < TITLE_COLUMNS and 0 <= row < TITLE_ROWS):
            return
        target = row * TITLE_COLUMNS + column + 0x2800
        layout = self.model.document["layout"]["streams"][self.stream_index.get()]
        address = int(layout["address"])
        payload = encoded_stream(self.model.document, self.model.profile, self.stream_index.get())
        prg = bytearray(0x8000)
        prg[title_data.prg_offset(address) : title_data.prg_offset(address) + len(payload)] = payload
        decoded = title_data.decode_stream(bytes(prg), address)
        for token_index, token in enumerate(decoded.tokens):
            if isinstance(token, title_data.TitleLiteralRun) and token.ppu_address <= target < token.ppu_address + len(token.tiles):
                self.token_index.set(token_index)
                self.token_box.current(token_index)
                self.refresh_token_editor()
                break

    def select_demo_step(self, _event: object = None) -> None:
        selection = self.demo_tree.selection()
        if not selection:
            return
        self.demo_index.set(int(selection[0]))
        self.refresh_demo_editor()

    def apply_command(self) -> None:
        try:
            token = self.selected_token()
            if token.get("kind") == "literal":
                raise presentation_editor.PresentationEditorError("select a command token first")
            kind = self.command_kind.get()
            value = None if kind == "terminate" else parse_integer(self.command_value.get(), "command value")
            self.model.edit_command(self.stream_index.get(), self.token_index.get(), kind, value)
            self.refresh_all()
        except (presentation_editor.PresentationEditorError, RoomDataError) as exc:
            messagebox.showerror("Presentation Studio", str(exc), parent=self)

    def apply_literal(self) -> None:
        try:
            token = self.selected_token()
            if token.get("kind") != "literal":
                raise presentation_editor.PresentationEditorError("select a literal token first")
            tiles = parse_literal(self.literal_value.get(), len(token["tiles"]))
            self.model.edit_literal(self.stream_index.get(), self.token_index.get(), tiles)
            self.refresh_all()
        except presentation_editor.PresentationEditorError as exc:
            messagebox.showerror("Presentation Studio", str(exc), parent=self)

    def apply_demo(self) -> None:
        try:
            duration = parse_integer(self.duration_value.get(), "duration")
            buttons = [button for button in BUTTONS if self.button_values[button].get()]
            self.model.edit_demo_step(self.demo_index.get(), duration, buttons)
            self.refresh_all()
        except (presentation_editor.PresentationEditorError, RoomDataError) as exc:
            messagebox.showerror("Presentation Studio", str(exc), parent=self)

    def undo(self) -> None:
        if self.model.undo():
            self.refresh_all()

    def save(self) -> None:
        try:
            action = self.model.save()
            self.refresh_status(f"{action}: {self.model.path}")
        except (presentation_editor.PresentationEditorError, OSError) as exc:
            messagebox.showerror("Presentation Studio", str(exc), parent=self)

    def build_rom(self) -> None:
        try:
            action = self.model.build()
            self.refresh_status(f"{action}: {self.model.output}")
        except (presentation_editor.PresentationEditorError, OSError) as exc:
            messagebox.showerror("Presentation Studio", str(exc), parent=self)

    def refresh_title_canvas(self) -> None:
        self.title_canvas.delete("all")
        surface = self.model.projection(self.stream_index.get())
        scale = TITLE_SCALE
        colors = tuple(rgb_hex(value) for value in DISPLAY_PALETTE)
        for row, values in enumerate(surface):
            for column, tile in enumerate(values):
                if tile is None:
                    continue
                pixels = self.model.title_tiles[tile]
                left, top = column * 8 * scale, row * 8 * scale
                for y, pixels_row in enumerate(pixels):
                    for x, pixel in enumerate(pixels_row):
                        self.title_canvas.create_rectangle(
                            left + x * scale,
                            top + y * scale,
                            left + (x + 1) * scale,
                            top + (y + 1) * scale,
                            fill=colors[int(pixel)],
                            outline="",
                        )
        for column in range(TITLE_COLUMNS + 1):
            x = column * 8 * scale
            self.title_canvas.create_line(x, 0, x, TITLE_ROWS * 8 * scale, fill="#1d2932")
        for row in range(TITLE_ROWS + 1):
            y = row * 8 * scale
            self.title_canvas.create_line(0, y, TITLE_COLUMNS * 8 * scale, y, fill="#1d2932")

    def refresh_token_editor(self) -> None:
        tokens = self.model.document["streams"][self.stream_index.get()]["tokens"]
        self.token_index.set(min(self.token_index.get(), len(tokens) - 1))
        token = self.selected_token()
        kind = token["kind"]
        if kind == "literal":
            tiles = token["tiles"]
            self.token_description.configure(text=f"Literal run: {len(tiles)} consecutive title tiles")
            self.literal_value.set(literal_text(tiles))
            self.command_kind.set("")
            self.command_value.set("")
            self.literal_entry.configure(state="normal")
            self.kind_box.configure(state="disabled")
            self.value_entry.configure(state="disabled")
        else:
            self.token_description.configure(text=f"Cursor command: {kind.replace('_', ' ')}")
            self.command_kind.set(kind)
            self.command_value.set("" if "value" not in token else str(token["value"]))
            self.literal_value.set("")
            self.literal_entry.configure(state="disabled")
            self.kind_box.configure(state="readonly")
            self.value_entry.configure(state="normal")

    def refresh_title(self) -> None:
        streams = self.model.document["streams"]
        self.stream_box["values"] = [stream["name"] for stream in streams]
        self.stream_box.current(self.stream_index.get())
        tokens = streams[self.stream_index.get()]["tokens"]
        labels = []
        for index, token in enumerate(tokens):
            detail = f"{len(token['tiles'])} tiles" if token["kind"] == "literal" else str(token.get("value", ""))
            labels.append(f"{index:02d}  {token['kind']} {detail}".rstrip())
        self.token_box["values"] = labels
        self.token_box.current(self.token_index.get())
        self.refresh_title_canvas()
        self.refresh_token_editor()

    def refresh_demo_editor(self) -> None:
        step = self.model.document["demo_steps"][self.demo_index.get()]
        self.duration_value.set(str(step["duration"]))
        for button in BUTTONS:
            self.button_values[button].set(button in step["buttons"])

    def refresh_demo(self) -> None:
        selected = str(self.demo_index.get())
        self.demo_tree.delete(*self.demo_tree.get_children())
        for step in self.model.document["demo_steps"]:
            duration = 256 if step["duration"] == 0 else step["duration"]
            self.demo_tree.insert("", "end", iid=str(step["index"]), values=(step["index"], duration, "+".join(step["buttons"]) or "neutral"))
        self.demo_tree.selection_set(selected)
        self.demo_tree.see(selected)
        self.refresh_demo_editor()
        self.timeline.delete("all")
        steps = self.model.document["demo_steps"]
        total = sum(256 if step["duration"] == 0 else step["duration"] for step in steps)
        width = max(1, self.timeline.winfo_width())
        cursor = 0.0
        for index, step in enumerate(steps):
            frames = 256 if step["duration"] == 0 else step["duration"]
            next_cursor = cursor + width * frames / total
            color = "#e69f00" if step["buttons"] else "#54616c"
            self.timeline.create_rectangle(cursor, 20, next_cursor, 80, fill=color, outline="#101820")
            if index == self.demo_index.get():
                self.timeline.create_rectangle(cursor, 18, next_cursor, 82, outline="#ffcc33", width=2)
            cursor = next_cursor
        self.timeline.create_text(4, 100, anchor="w", fill="#d8e0e8", text=f"{total} effective frames across {len(steps)} steps")

    def refresh_status(self, message: str | None = None) -> None:
        marker = "modified" if self.model.dirty else "saved"
        self.status.set(message or f"{self.model.profile['id']} presentation — {marker}")

    def refresh_all(self) -> None:
        self.refresh_title()
        self.refresh_demo()
        self.refresh_status()

    def close(self) -> None:
        if self.model.dirty and not messagebox.askyesno(
            "Presentation Studio", "Discard unsaved presentation changes?", parent=self
        ):
            return
        self.destroy()


def check_profile(profile: dict[str, Any], reference: Path) -> str:
    verify_reference(reference, profile)
    image = reference.read_bytes()
    document = presentation_editor.export_document(image, profile)
    model = PresentationStudioDocument(
        document, profile, image, Path("presentation.json"), Path("presentation.nes")
    )
    projected = [model.projection(index) for index in range(len(document["streams"]))]
    source_literal_count = sum(
        len(token.get("tiles", []))
        for stream in document["streams"]
        for token in stream["tokens"]
        if token["kind"] == "literal"
    )
    projection_count = sum(projected_literal_count(surface) for surface in projected)
    if projection_count != source_literal_count:
        raise presentation_editor.PresentationEditorError(
            "title preview does not project every literal tile exactly once"
        )
    if len(model.title_tiles) != 256 or any(len(tile) != 8 for tile in model.title_tiles):
        raise presentation_editor.PresentationEditorError("title CHR projection is incomplete")
    effective_frames = sum(
        256 if step["duration"] == 0 else step["duration"]
        for step in document["demo_steps"]
    )
    if model.rebuilt_image() != image:
        raise presentation_editor.PresentationEditorError(
            "Presentation Studio changed the stock ROM"
        )
    return (
        f"{projection_count} projected title tiles, 256 CHR glyphs, "
        f"{len(document['demo_steps'])} demo steps, {effective_frames} effective frames"
    )


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
            print(f"[OK] {profile['id']} Presentation Studio: {check_profile(profile, reference)}")
            return 0
        document = args.document or ROOT / "content/workspace" / args.profile / "presentation.json"
        output = args.output or ROOT / "build/content" / args.profile / "solomons_key_presentation.nes"
        PresentationStudio(load_studio_document(profile, reference, document, output)).mainloop()
    except (
        presentation_editor.PresentationEditorError,
        RoomDataError,
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
