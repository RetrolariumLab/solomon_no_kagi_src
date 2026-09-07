#!/usr/bin/env python3
"""Visual editor for Solomon's Key effects, envelopes, timing, and streams."""

from __future__ import annotations

import argparse
import copy
import math
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

import audio_editor
import audio_preview
from project import ProjectError, write_if_changed
from revision_profiles import (
    ROOT,
    get_profile,
    load_profiles,
    resolve_reference,
    verify_reference,
)
from room_data import RoomDataError


COMMAND_GROUPS = (
    ("note", "duration", "return", "end_loop", "stop"),
    ("set_sequence", "set_control", "begin_loop", "set_sweep", "set_volume"),
    ("jump", "call"),
)
CHANNEL_NAMES = (
    "virtual 0",
    "virtual 1",
    "virtual 2",
    "virtual 3",
    "virtual 4",
    "virtual 5",
    "virtual 6",
    "virtual 7",
)
EFFECT_CONTEXTS = (
    "Room audio A / warning return A",
    "Room audio B / warning return B",
    "Room transition reset",
    "Timer warning",
    "Post-game result",
    "Extra life",
    "Create breakable block",
    "Remove breakable block",
    "Enemy drop",
    "Fireball cast",
    "Paired-enemy attack",
    "Pause / PAL resume",
    "Item pickup / enemy reward",
    "NTSC resume",
    "Fairy collected",
    "Ending input prompt",
    "Dana head collision",
    "Remove solid block",
    "Room-clear countdown / ending phase",
    "Room entry / ending convergence",
    "Enter door",
    "Collect key",
    "Linked-enemy spawn",
    "Title / new game / room-clear transition",
    "Ending object fall",
    "Ending fade",
)
VOICE_NAMES = ("Pulse 1", "Pulse 2", "Triangle", "Noise")
VOICE_COLORS = ("#56b4e9", "#e69f00", "#009e73", "#cc79a7")
PROGRAM_GROUPS = (
    ("Music loops", (1, 2, 4, 16, 19)),
    ("Musical cues", (5, 6, 15, 20, 22)),
    ("Sound effects", (7, 8, 9, 10, 11, 13, 17, 18, 21, 23, 25, 26)),
    ("Engine controls", (3, 12, 14, 24)),
    ("All programs", tuple(range(1, 27))),
)


def program_numbers(group: str) -> tuple[int, ...]:
    for name, numbers in PROGRAM_GROUPS:
        if name == group:
            return numbers
    raise audio_editor.AudioEditorError(f"unknown audio program group: {group}")


def program_label(effect_number: int) -> str:
    if not 1 <= effect_number <= len(EFFECT_CONTEXTS):
        raise audio_editor.AudioEditorError("audio program number must be 1..26")
    return f"{effect_number:02d} - {EFFECT_CONTEXTS[effect_number - 1]}"


def parse_integer(text: str, field: str, maximum: int = 0xFF) -> int:
    value = text.strip()
    base = 16 if value.startswith("$") else 0
    if value.startswith("$"):
        value = value[1:]
    try:
        result = int(value, base)
    except ValueError as exc:
        raise audio_editor.AudioEditorError(f"{field} is not an integer") from exc
    if not 0 <= result <= maximum:
        raise audio_editor.AudioEditorError(
            f"{field} must be between 0 and {maximum}"
        )
    return result


def command_group(kind: str) -> tuple[str, ...]:
    for group in COMMAND_GROUPS:
        if kind in group:
            return group
    raise audio_editor.AudioEditorError(f"unknown command kind: {kind}")


def command_operand(command: dict[str, Any]) -> str:
    if "target" in command:
        return str(command["target"])
    if "value" in command:
        return f"${int(command['value']):02X}"
    return ""


def command_meaning(command: dict[str, Any]) -> str:
    kind = command["kind"]
    if kind == "note":
        value = int(command["value"])
        pitch = value & 0x0F
        return "rest" if pitch == 0x0C else f"octave {value >> 4}, pitch {pitch}"
    if kind == "duration":
        return f"duration index {int(command['value']) & 0x3F}"
    if kind == "set_sequence":
        return f"envelope {int(command['value'])}"
    if kind in {"jump", "call"}:
        return f"{kind} {command['target']}"
    if kind == "begin_loop":
        return f"repeat {int(command['value'])} times"
    if "value" in command:
        return f"value ${int(command['value']):02X}"
    return kind.replace("_", " ")


def stream_spans(commands: list[dict[str, Any]]) -> dict[str, tuple[int, int]]:
    starts = [
        (index, command["entry"])
        for index, command in enumerate(commands)
        if "entry" in command
    ]
    spans: dict[str, tuple[int, int]] = {}
    for position, (start, entry) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(commands)
        spans[str(entry)] = (start, end)
    return spans


class SoundStudioDocument:
    """Undoable editor state which delegates every binary check to the codec."""

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
        self.saved = audio_editor.canonical_document(self.document)
        self.validate()

    @property
    def dirty(self) -> bool:
        return audio_editor.canonical_document(self.document) != self.saved

    def _change(self, mutate: Callable[[dict[str, Any]], None]) -> bool:
        candidate = copy.deepcopy(self.document)
        mutate(candidate)
        if audio_editor.canonical_document(candidate) == audio_editor.canonical_document(
            self.document
        ):
            return False
        audio_editor.encode_document(candidate, self.profile)
        self.undo_stack.append(copy.deepcopy(self.document))
        del self.undo_stack[:-100]
        self.document = candidate
        return True

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        self.document = self.undo_stack.pop()
        return True

    def edit_command(self, index: int, kind: str, operand: str) -> bool:
        command = self.document["commands"][index]
        if kind not in command_group(command["kind"]):
            raise audio_editor.AudioEditorError(
                "replacement command must keep the encoded byte size"
            )
        replacement: dict[str, Any] = {"kind": kind}
        if "entry" in command:
            replacement["entry"] = command["entry"]
        if kind in {"jump", "call"}:
            replacement["target"] = operand.strip()
        elif kind not in audio_editor.SIMPLE_COMMANDS:
            replacement["value"] = parse_integer(operand, "command value")
        return self._change(
            lambda document: document["commands"].__setitem__(index, replacement)
        )

    def edit_effect_channel(
        self, effect_index: int, channel_index: int, virtual: int, stream: str
    ) -> bool:
        if not 0 <= virtual <= 7:
            raise audio_editor.AudioEditorError("virtual channel must be 0..7")

        def mutate(document: dict[str, Any]) -> None:
            channel = document["effects"][effect_index]["channels"][channel_index]
            channel["selector"] = virtual | (0x80 if channel_index == 0 else 0)
            channel["stream"] = stream

        return self._change(mutate)

    def edit_envelope_step(
        self, envelope_index: int, step_index: int, duration: int, volume: int
    ) -> bool:
        if not 0 <= duration <= 0xFF or not 0 <= volume <= 0xFF:
            raise audio_editor.AudioEditorError("envelope bytes must be 0..255")

        def mutate(document: dict[str, Any]) -> None:
            step = document["envelopes"][envelope_index]["steps"][step_index]
            step.update(duration=duration, volume=volume)

        return self._change(mutate)

    def edit_timing(self, table: str, index: int, value: int) -> bool:
        maximum = 0xFFFF if table == "periods" else 0xFF
        if table not in {"periods", "durations"} or not 0 <= value <= maximum:
            raise audio_editor.AudioEditorError("invalid audio timing edit")
        return self._change(
            lambda document: document[table].__setitem__(index, value)
        )

    def rebuilt_image(self) -> bytes:
        image = audio_editor.build_audio_image(
            self.document, self.base_image, self.profile
        )
        audio_editor.validate_rebuilt_document(self.document, image, self.profile)
        return image

    def validate(self) -> None:
        self.rebuilt_image()

    def save(self) -> str:
        self.validate()
        action = audio_editor.save_document(self.path, self.document)
        self.saved = audio_editor.canonical_document(self.document)
        return action

    def build(self) -> str:
        return write_if_changed(self.output, self.rebuilt_image())

    def preview(
        self,
        effect_number: int,
        seconds: float,
        enabled_voices: set[int] | None = None,
    ) -> tuple[Path, audio_preview.PreviewTrace]:
        path = self.output.with_name(f"effect{effect_number:02d}-preview.wav")
        trace = audio_preview.write_preview(
            self.document,
            self.profile,
            effect_number,
            path,
            seconds,
            enabled_voices=enabled_voices,
        )
        return path, trace


def load_studio_document(
    profile: dict[str, Any], reference: Path, path: Path, output: Path
) -> SoundStudioDocument:
    parsed = verify_reference(reference, profile)
    document = (
        audio_editor.load_document(path)
        if path.is_file()
        else audio_editor.export_document(parsed["prg"], profile)
    )
    return SoundStudioDocument(document, profile, reference.read_bytes(), path, output)


class SoundStudio(tk.Tk):
    def __init__(self, model: SoundStudioDocument) -> None:
        super().__init__()
        self.model = model
        self.status = tk.StringVar()
        self.stream = tk.StringVar(value="stream_000")
        self.command_kind = tk.StringVar()
        self.command_value = tk.StringVar()
        self.effect_number = tk.IntVar(value=1)
        self.program_group = tk.StringVar(value=PROGRAM_GROUPS[0][0])
        self.program_name = tk.StringVar(value=program_label(1))
        self.effect_context = tk.StringVar()
        self.effect_channel = tk.StringVar(value=CHANNEL_NAMES[0])
        self.effect_stream = tk.StringVar(value="stream_000")
        self.preview_seconds = tk.StringVar(value="12")
        self.loop_preview = tk.BooleanVar(value=False)
        self.voice_enabled = [tk.BooleanVar(value=True) for _name in VOICE_NAMES]
        self.envelope_number = tk.IntVar(value=0)
        self.envelope_duration = tk.StringVar()
        self.envelope_volume = tk.StringVar()
        self.timing_value = tk.StringVar()
        self.title(f"Solomon's Key Sound Studio [{model.profile['id']}]")
        self.geometry("1320x790")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.build_ui()
        self.refresh_all()

    def build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=7)
        toolbar.pack(fill="x")
        ttk.Label(
            toolbar,
            text=f"Profile: {self.model.profile['name']}",
        ).pack(side="left")
        for label, command in (
            ("Undo", self.undo),
            ("Save", self.save),
            ("Build ROM", self.build_rom),
        ):
            ttk.Button(toolbar, text=label, command=command).pack(side="left", padx=4)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=7)
        streams = ttk.Frame(self.notebook, padding=7)
        effects = ttk.Frame(self.notebook, padding=7)
        envelopes = ttk.Frame(self.notebook, padding=7)
        timing = ttk.Frame(self.notebook, padding=7)
        self.streams_tab = streams
        self.notebook.add(effects, text="Music player")
        self.notebook.add(streams, text="Streams")
        self.notebook.add(envelopes, text="Envelopes")
        self.notebook.add(timing, text="Timing")
        self.build_streams(streams)
        self.build_effects(effects)
        self.build_envelopes(envelopes)
        self.build_timing(timing)
        ttk.Label(self, textvariable=self.status, anchor="w", padding=7).pack(fill="x")

    def tree(
        self,
        parent: tk.Widget,
        columns: tuple[tuple[str, str, int], ...],
    ) -> ttk.Treeview:
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        names = tuple(name for name, _label, _width in columns)
        tree = ttk.Treeview(frame, columns=names, show="headings")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        for name, label, width in columns:
            tree.heading(name, text=label)
            tree.column(name, width=width, stretch=name == names[-1])
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def build_streams(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(0, 6))
        ttk.Label(row, text="Physical entry").pack(side="left")
        self.stream_box = ttk.Combobox(
            row,
            state="readonly",
            width=18,
            textvariable=self.stream,
            values=[audio_editor.stream_id(index) for index in range(114)],
        )
        self.stream_box.pack(side="left", padx=6)
        self.stream_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_stream())
        body = ttk.Panedwindow(parent, orient="horizontal")
        body.pack(fill="both", expand=True)
        listing = ttk.Frame(body)
        self.command_tree = self.tree(
            listing,
            (
                ("index", "#", 55),
                ("entry", "Entry", 105),
                ("kind", "Command", 120),
                ("operand", "Operand", 100),
                ("meaning", "Decoded meaning", 260),
            ),
        )
        self.command_tree.bind("<<TreeviewSelect>>", self.select_command)
        body.add(listing, weight=4)
        editor = ttk.LabelFrame(body, text="Selected physical command", padding=10)
        body.add(editor, weight=1)
        ttk.Label(editor, text="Kind").grid(row=0, column=0, sticky="w")
        self.command_kind_box = ttk.Combobox(
            editor, state="readonly", width=18, textvariable=self.command_kind
        )
        self.command_kind_box.grid(row=0, column=1, padx=5, pady=4)
        ttk.Label(editor, text="Value / target").grid(row=1, column=0, sticky="w")
        ttk.Entry(editor, width=20, textvariable=self.command_value).grid(
            row=1, column=1, padx=5, pady=4
        )
        ttk.Button(editor, text="Apply command", command=self.apply_command).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=6
        )
        ttk.Label(
            editor,
            text=(
                "Kinds are limited to the same encoded size. Symbolic targets are "
                "re-resolved when command positions move."
            ),
            wraplength=250,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=8)

    def build_effects(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(0, 6))
        ttk.Label(row, text="Library").pack(side="left")
        group_box = ttk.Combobox(
            row,
            state="readonly",
            width=17,
            textvariable=self.program_group,
            values=[name for name, _numbers in PROGRAM_GROUPS],
        )
        group_box.pack(side="left", padx=6)
        group_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_programs())
        ttk.Label(row, text="Selection").pack(side="left")
        self.program_box = ttk.Combobox(
            row,
            state="readonly",
            width=46,
            textvariable=self.program_name,
        )
        self.program_box.pack(side="left", padx=6)
        self.program_box.bind("<<ComboboxSelected>>", lambda _event: self.select_program())
        ttk.Label(row, text="Preview seconds").pack(side="left", padx=(16, 0))
        ttk.Entry(row, width=7, textvariable=self.preview_seconds).pack(
            side="left", padx=6
        )
        ttk.Button(row, text="Play selection", command=self.preview_effect).pack(
            side="left", padx=4
        )
        ttk.Button(row, text="Stop", command=self.stop_preview).pack(side="left", padx=4)

        mixer = ttk.LabelFrame(parent, text="Preview mixer", padding=5)
        mixer.pack(fill="x", pady=(0, 7))
        for voice, name in enumerate(VOICE_NAMES):
            ttk.Checkbutton(
                mixer,
                text=name,
                variable=self.voice_enabled[voice],
                command=lambda: self.draw_effect_roll(self.effect_number.get()),
            ).pack(side="left", padx=10)
        ttk.Checkbutton(
            mixer,
            text="Loop generated WAV until Stop",
            variable=self.loop_preview,
        ).pack(side="left", padx=(24, 10))
        ttk.Label(mixer, textvariable=self.effect_context).pack(side="left", padx=10)

        roll_frame = ttk.LabelFrame(
            parent, text="APU piano roll (first 10 seconds; editable descriptor below)"
        )
        roll_frame.pack(fill="x", pady=(0, 7))
        self.effect_roll = tk.Canvas(roll_frame, height=210, bg="#111824")
        self.effect_roll.pack(fill="x", expand=True)
        self.effect_roll.bind(
            "<Configure>",
            lambda _event: self.draw_effect_roll(self.effect_number.get()),
        )
        body = ttk.Panedwindow(parent, orient="horizontal")
        body.pack(fill="both", expand=True)
        listing = ttk.Frame(body)
        self.effect_tree = self.tree(
            listing,
            (
                ("index", "#", 55),
                ("selector", "Selector", 90),
                ("channel", "Virtual channel", 150),
                ("stream", "Starting stream", 180),
            ),
        )
        self.effect_tree.bind("<<TreeviewSelect>>", self.select_effect_channel)
        body.add(listing, weight=3)
        editor = ttk.LabelFrame(body, text="Selected channel", padding=10)
        body.add(editor, weight=1)
        ttk.Label(editor, text="Virtual channel").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            editor,
            state="readonly",
            values=CHANNEL_NAMES,
            textvariable=self.effect_channel,
            width=17,
        ).grid(row=0, column=1, padx=5, pady=4)
        ttk.Label(editor, text="Starting stream").grid(row=1, column=0, sticky="w")
        ttk.Combobox(
            editor,
            state="readonly",
            values=[audio_editor.stream_id(index) for index in range(114)],
            textvariable=self.effect_stream,
            width=17,
        ).grid(row=1, column=1, padx=5, pady=4)
        ttk.Button(editor, text="Apply channel", command=self.apply_effect).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=6
        )
        ttk.Button(
            editor, text="Open starting stream", command=self.open_effect_stream
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=6)

    def build_envelopes(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(0, 6))
        ttk.Label(row, text="Envelope").pack(side="left")
        box = ttk.Combobox(
            row,
            state="readonly",
            width=12,
            textvariable=self.envelope_number,
            values=list(range(8)),
        )
        box.pack(side="left", padx=6)
        box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_envelope())
        self.envelope_canvas = tk.Canvas(row, height=150, bg="#111824")
        self.envelope_canvas.pack(side="left", fill="x", expand=True, padx=12)
        body = ttk.Panedwindow(parent, orient="horizontal")
        body.pack(fill="both", expand=True)
        listing = ttk.Frame(body)
        self.envelope_tree = self.tree(
            listing,
            (
                ("index", "Step", 70),
                ("duration", "Duration", 110),
                ("volume", "Volume", 110),
            ),
        )
        self.envelope_tree.bind("<<TreeviewSelect>>", self.select_envelope_step)
        body.add(listing, weight=3)
        editor = ttk.LabelFrame(body, text="Selected envelope step", padding=10)
        body.add(editor, weight=1)
        ttk.Label(editor, text="Duration byte").grid(row=0, column=0, sticky="w")
        ttk.Entry(editor, textvariable=self.envelope_duration, width=12).grid(
            row=0, column=1, padx=5, pady=4
        )
        ttk.Label(editor, text="Volume byte").grid(row=1, column=0, sticky="w")
        ttk.Entry(editor, textvariable=self.envelope_volume, width=12).grid(
            row=1, column=1, padx=5, pady=4
        )
        ttk.Button(editor, text="Apply step", command=self.apply_envelope).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=6
        )

    def build_timing(self, parent: ttk.Frame) -> None:
        body = ttk.Panedwindow(parent, orient="horizontal")
        body.pack(fill="both", expand=True)
        listing = ttk.Frame(body)
        self.timing_tree = self.tree(
            listing,
            (
                ("table", "Table", 120),
                ("index", "Index", 70),
                ("value", "Value", 110),
                ("meaning", "Meaning", 260),
            ),
        )
        self.timing_tree.bind("<<TreeviewSelect>>", self.select_timing)
        body.add(listing, weight=3)
        editor = ttk.LabelFrame(body, text="Selected timing value", padding=10)
        body.add(editor, weight=1)
        ttk.Label(editor, text="Value").grid(row=0, column=0, sticky="w")
        ttk.Entry(editor, textvariable=self.timing_value, width=14).grid(
            row=0, column=1, padx=5, pady=4
        )
        ttk.Button(editor, text="Apply timing", command=self.apply_timing).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=6
        )

    def guarded(self, action: Callable[[], Any]) -> Any:
        try:
            return action()
        except (
            audio_editor.AudioEditorError,
            audio_preview.AudioPreviewError,
            OSError,
            KeyError,
            IndexError,
        ) as exc:
            messagebox.showerror("Sound Studio", str(exc), parent=self)
            return None

    def selected_index(self, tree: ttk.Treeview) -> int | None:
        selection = tree.selection()
        return int(selection[0]) if selection else None

    def refresh_all(self) -> None:
        self.refresh_stream()
        self.refresh_programs()
        self.refresh_envelope()
        self.refresh_timing()
        state = "modified" if self.model.dirty else "saved"
        self.status.set(
            f"{audio_editor.document_summary(self.model.document)}; workspace {state}"
        )

    def refresh_stream(self) -> None:
        self.command_tree.delete(*self.command_tree.get_children())
        commands = self.model.document["commands"]
        start, end = stream_spans(commands)[self.stream.get()]
        for index in range(start, end):
            command = commands[index]
            self.command_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    index,
                    command.get("entry", ""),
                    command["kind"],
                    command_operand(command),
                    command_meaning(command),
                ),
            )

    def select_command(self, _event: object = None) -> None:
        index = self.selected_index(self.command_tree)
        if index is None:
            return
        command = self.model.document["commands"][index]
        group = command_group(command["kind"])
        self.command_kind_box.configure(values=group)
        self.command_kind.set(command["kind"])
        self.command_value.set(command_operand(command))

    def apply_command(self) -> None:
        index = self.selected_index(self.command_tree)
        if index is None:
            return
        if self.guarded(
            lambda: self.model.edit_command(
                index, self.command_kind.get(), self.command_value.get()
            )
        ) is not None:
            self.refresh_all()
            self.command_tree.selection_set(str(index))

    def refresh_programs(self) -> None:
        numbers = program_numbers(self.program_group.get())
        self.program_box.configure(
            values=[program_label(number) for number in numbers]
        )
        effect_number = self.effect_number.get()
        if effect_number not in numbers:
            effect_number = numbers[0]
            self.effect_number.set(effect_number)
        self.program_name.set(program_label(effect_number))
        self.refresh_effect()

    def select_program(self) -> None:
        numbers = program_numbers(self.program_group.get())
        selected = self.program_box.current()
        if not 0 <= selected < len(numbers):
            return
        self.effect_number.set(numbers[selected])
        self.refresh_effect()

    def refresh_effect(self) -> None:
        self.effect_tree.delete(*self.effect_tree.get_children())
        effect_number = self.effect_number.get()
        self.effect_context.set(EFFECT_CONTEXTS[effect_number - 1])
        effect = self.model.document["effects"][effect_number - 1]
        for index, channel in enumerate(effect["channels"]):
            virtual = int(channel["selector"]) & 7
            self.effect_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    index,
                    f"${int(channel['selector']):02X}",
                    CHANNEL_NAMES[virtual],
                    channel["stream"],
                ),
            )
        self.draw_effect_roll(effect_number)

    def draw_effect_roll(self, effect_number: int) -> None:
        timing = self.model.profile["timing"]
        frame_limit = round(audio_preview.FRAME_RATES[timing] * 10)
        trace = audio_preview.trace_effect(
            self.model.document, effect_number, frame_limit
        )
        segments = audio_preview.trace_segments(trace)
        canvas = self.effect_roll
        canvas.delete("all")
        width = max(canvas.winfo_width(), 700)
        plot_left, plot_right = 75, width - 10
        for voice, name in enumerate(VOICE_NAMES):
            top = 8 + voice * 49
            enabled = self.voice_enabled[voice].get()
            label = name if enabled else f"{name} (muted)"
            color = "#d8e2f0" if enabled else "#697484"
            canvas.create_text(7, top + 20, text=label, fill=color, anchor="w")
            canvas.create_line(plot_left, top + 42, plot_right, top + 42, fill="#344052")
        for segment in segments:
            if (
                not self.voice_enabled[segment.voice].get()
                or segment.frame.volume == 0
                or segment.frame.source is None
            ):
                continue
            x1 = plot_left + segment.start * (plot_right - plot_left) / len(trace.frames)
            x2 = plot_left + segment.end * (plot_right - plot_left) / len(trace.frames)
            top = 8 + segment.voice * 49
            if segment.voice == 3:
                pitch = segment.frame.period & 0x0F
            else:
                period = max(segment.frame.period, 1)
                pitch = max(0, min(15, round(15 - math.log2(period) * 1.5 + 8)))
            y = top + 36 - pitch * 2
            outline = "#ffffff" if segment.frame.source % 2 == 0 else ""
            canvas.create_rectangle(
                x1,
                y,
                max(x1 + 1, x2),
                y + max(2, segment.frame.volume / 3),
                fill=VOICE_COLORS[segment.voice],
                outline=outline,
            )
        canvas.create_text(
            plot_right,
            202,
            text=f"{len(trace.frames)} frames / {trace.note_events} notes",
            fill="#9fb0c5",
            anchor="e",
        )

    def select_effect_channel(self, _event: object = None) -> None:
        index = self.selected_index(self.effect_tree)
        if index is None:
            return
        channel = self.model.document["effects"][self.effect_number.get() - 1][
            "channels"
        ][index]
        self.effect_channel.set(CHANNEL_NAMES[int(channel["selector"]) & 7])
        self.effect_stream.set(channel["stream"])

    def apply_effect(self) -> None:
        index = self.selected_index(self.effect_tree)
        if index is None:
            return
        if self.guarded(
            lambda: self.model.edit_effect_channel(
                self.effect_number.get() - 1,
                index,
                CHANNEL_NAMES.index(self.effect_channel.get()),
                self.effect_stream.get(),
            )
        ) is not None:
            self.refresh_all()
            self.effect_tree.selection_set(str(index))

    def open_effect_stream(self) -> None:
        index = self.selected_index(self.effect_tree)
        if index is None:
            return
        channel = self.model.document["effects"][self.effect_number.get() - 1][
            "channels"
        ][index]
        self.stream.set(channel["stream"])
        self.refresh_stream()
        self.notebook.select(self.streams_tab)

    def refresh_envelope(self) -> None:
        self.envelope_tree.delete(*self.envelope_tree.get_children())
        steps = self.model.document["envelopes"][self.envelope_number.get()]["steps"]
        for index, step in enumerate(steps):
            self.envelope_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(index, f"${step['duration']:02X}", f"${step['volume']:02X}"),
            )
        self.envelope_canvas.delete("all")
        width = max(self.envelope_canvas.winfo_width(), 400)
        baseline = 135
        step_width = max(8, (width - 20) / max(len(steps), 1))
        points = []
        for index, step in enumerate(steps):
            points.extend((10 + index * step_width, baseline - min(step["volume"], 15) * 8))
        if len(points) >= 4:
            self.envelope_canvas.create_line(*points, fill="#62d6ff", width=2)

    def select_envelope_step(self, _event: object = None) -> None:
        index = self.selected_index(self.envelope_tree)
        if index is None:
            return
        step = self.model.document["envelopes"][self.envelope_number.get()]["steps"][index]
        self.envelope_duration.set(f"${step['duration']:02X}")
        self.envelope_volume.set(f"${step['volume']:02X}")

    def apply_envelope(self) -> None:
        index = self.selected_index(self.envelope_tree)
        if index is None:
            return
        if self.guarded(
            lambda: self.model.edit_envelope_step(
                self.envelope_number.get(),
                index,
                parse_integer(self.envelope_duration.get(), "envelope duration"),
                parse_integer(self.envelope_volume.get(), "envelope volume"),
            )
        ) is not None:
            self.refresh_all()
            self.envelope_tree.selection_set(str(index))

    def refresh_timing(self) -> None:
        self.timing_tree.delete(*self.timing_tree.get_children())
        for table in ("periods", "durations"):
            for index, value in enumerate(self.model.document[table]):
                meaning = "APU period word" if table == "periods" else "frame count"
                shown = f"${value:04X}" if table == "periods" else f"${value:02X}"
                self.timing_tree.insert(
                    "",
                    "end",
                    iid=f"{table}:{index}",
                    values=(table, index, shown, meaning),
                )

    def selected_timing(self) -> tuple[str, int] | None:
        selection = self.timing_tree.selection()
        if not selection:
            return None
        table, index = selection[0].split(":")
        return table, int(index)

    def select_timing(self, _event: object = None) -> None:
        selected = self.selected_timing()
        if selected is None:
            return
        table, index = selected
        value = self.model.document[table][index]
        self.timing_value.set(f"${value:04X}" if table == "periods" else f"${value:02X}")

    def apply_timing(self) -> None:
        selected = self.selected_timing()
        if selected is None:
            return
        table, index = selected
        maximum = 0xFFFF if table == "periods" else 0xFF
        if self.guarded(
            lambda: self.model.edit_timing(
                table, index, parse_integer(self.timing_value.get(), table, maximum)
            )
        ) is not None:
            self.refresh_all()
            self.timing_tree.selection_set(f"{table}:{index}")

    def undo(self) -> None:
        if self.model.undo():
            self.refresh_all()

    def save(self) -> None:
        if self.guarded(self.model.save) is not None:
            self.refresh_all()

    def build_rom(self) -> None:
        action = self.guarded(self.model.build)
        if action is not None:
            self.status.set(f"[{action}] audio ROM: {self.model.output}")

    def preview_effect(self) -> None:
        try:
            seconds = float(self.preview_seconds.get())
        except ValueError:
            messagebox.showerror(
                "Sound Studio", "Preview seconds is not a number", parent=self
            )
            return
        enabled_voices = {
            voice
            for voice, enabled in enumerate(self.voice_enabled)
            if enabled.get()
        }
        result = self.guarded(
            lambda: self.model.preview(
                self.effect_number.get(), seconds, enabled_voices
            )
        )
        if result is None:
            return
        path, trace = result
        try:
            import winsound

            flags = winsound.SND_FILENAME | winsound.SND_ASYNC
            if self.loop_preview.get():
                flags |= winsound.SND_LOOP
            winsound.PlaySound(str(path), flags)
            action = "playing"
        except (ImportError, RuntimeError):
            action = "wrote"
        self.status.set(
            f"{action} {program_label(self.effect_number.get())}: "
            f"{len(trace.frames)} frames, {trace.note_events} notes - {path}"
        )

    def stop_preview(self) -> None:
        try:
            import winsound

            winsound.PlaySound(None, 0)
            self.status.set("Preview stopped")
        except (ImportError, RuntimeError):
            self.status.set(
                "Playback control is available on Windows; WAV output is preserved"
            )

    def close(self) -> None:
        if self.model.dirty and not messagebox.askyesno(
            "Sound Studio", "Discard unsaved audio changes?", parent=self
        ):
            return
        try:
            import winsound

            winsound.PlaySound(None, 0)
        except (ImportError, RuntimeError):
            pass
        self.destroy()


def check_profile(profile: dict[str, Any], reference: Path) -> str:
    parsed = verify_reference(reference, profile)
    document = audio_editor.export_document(parsed["prg"], profile)
    model = SoundStudioDocument(
        document,
        profile,
        reference.read_bytes(),
        Path("audio.json"),
        Path("audio.nes"),
    )
    spans = stream_spans(model.document["commands"])
    if len(spans) != 114 or any(start >= end for start, end in spans.values()):
        raise audio_editor.AudioEditorError("invalid Sound Studio stream projection")
    traces = [
        audio_preview.trace_effect(model.document, effect, 180)
        for effect in range(1, 27)
    ]
    if any(not trace.frames or trace.note_events == 0 for trace in traces):
        raise audio_preview.AudioPreviewError("an effect produced no preview notes")
    if len(EFFECT_CONTEXTS) != 26 or any(
        not audio_preview.trace_segments(trace) for trace in traces
    ):
        raise audio_preview.AudioPreviewError("incomplete effect catalog projection")
    categorized = [
        effect
        for _name, effects in PROGRAM_GROUPS[:-1]
        for effect in effects
    ]
    if sorted(categorized) != list(range(1, 27)) or len(set(categorized)) != 26:
        raise audio_preview.AudioPreviewError("invalid audio program categories")
    if PROGRAM_GROUPS[-1][1] != tuple(range(1, 27)):
        raise audio_preview.AudioPreviewError("incomplete all-programs catalog")
    return f"{audio_editor.document_summary(model.document)}, 26 traced effects"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profiles", type=Path, default=ROOT / "config/revision_profiles.json"
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
            print(f"[OK] {profile['id']} Sound Studio: {check_profile(profile, reference)}")
            return 0
        document = args.document or ROOT / "content/workspace" / args.profile / "audio.json"
        output = args.output or ROOT / "build/content" / args.profile / "solomons_key_audio.nes"
        SoundStudio(load_studio_document(profile, reference, document, output)).mainloop()
    except (
        audio_editor.AudioEditorError,
        audio_preview.AudioPreviewError,
        RoomDataError,
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
