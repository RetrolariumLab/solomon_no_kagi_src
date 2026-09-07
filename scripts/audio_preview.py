#!/usr/bin/env python3
"""Trace and render Solomon's Key audio effects from editable documents."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import math
from pathlib import Path
import struct
import sys
import wave
from typing import Any

import audio_editor
from project import ProjectError
from revision_profiles import ROOT, get_profile, load_profiles
from room_data import RoomDataError


SAMPLE_RATE = 44_100
FRAME_RATES = {"ntsc": 60.0988, "pal": 50.0070}
CPU_CLOCKS = {"ntsc": 1_789_773.0, "pal": 1_662_607.0}
NOISE_PERIODS = {
    "ntsc": (4, 8, 16, 32, 64, 96, 128, 160, 202, 254, 380, 508, 762, 1016, 2034, 4068),
    "pal": (4, 8, 14, 30, 60, 88, 118, 148, 188, 236, 354, 472, 708, 944, 1890, 3778),
}
PULSE_DUTIES = (0.125, 0.25, 0.5, 0.75)
MAX_COMMANDS_PER_NOTE = 10_000
MAX_STACK_DEPTH = 8
VOICE_NAMES = ("pulse1", "pulse2", "triangle", "noise")


class AudioPreviewError(ValueError):
    """An invalid or non-terminating preview program."""


@dataclass
class LoopFrame:
    start: int
    remaining: int


@dataclass
class VirtualChannel:
    number: int
    pc: int
    active: bool = True
    duration_counter: int = 1
    duration_reload: int = 0
    envelope: int = 0
    envelope_index: int = 0
    envelope_counter: int = 0
    envelope_volume: int = 0
    control: int = 0
    period: int = 0
    muted: bool = False
    sweep: int = 0
    call_stack: list[int] = field(default_factory=list)
    loop_stack: list[LoopFrame] = field(default_factory=list)


@dataclass(frozen=True)
class HardwareFrame:
    source: int | None
    period: int
    volume: int
    duty: int
    noise_mode: int


@dataclass(frozen=True)
class PreviewTrace:
    frames: tuple[tuple[HardwareFrame, ...], ...]
    note_events: int
    stopped: bool


@dataclass(frozen=True)
class TraceSegment:
    voice: int
    start: int
    end: int
    frame: HardwareFrame


def entry_indices(document: dict[str, Any]) -> dict[str, int]:
    return {
        command["entry"]: index
        for index, command in enumerate(document["commands"])
        if "entry" in command
    }


def byte_value(command: dict[str, Any], name: str) -> int:
    value = command.get("value")
    if not isinstance(value, int) or not 0 <= value <= 0xFF:
        raise AudioPreviewError(f"{name} is outside byte range")
    return value


class EffectSequencer:
    """Frame-step the reconstructed command VM and virtual-channel priority."""

    def __init__(self, document: dict[str, Any], effect_number: int) -> None:
        if not 1 <= effect_number <= len(document["effects"]):
            raise AudioPreviewError("effect number is outside 1..26")
        self.document = document
        self.commands = document["commands"]
        self.entries = entry_indices(document)
        self.channels: dict[int, VirtualChannel] = {}
        effect = document["effects"][effect_number - 1]
        for channel in effect["channels"]:
            number = int(channel["selector"]) & 7
            target = channel["stream"]
            if target not in self.entries:
                raise AudioPreviewError(f"effect targets unknown stream {target!r}")
            self.channels[number] = VirtualChannel(number, self.entries[target])
        self.note_events = 0

    def pointer(self, command: dict[str, Any]) -> int:
        target = command.get("target")
        if target not in self.entries:
            raise AudioPreviewError(f"command targets unknown stream {target!r}")
        return self.entries[target]

    def decode_note(self, channel: VirtualChannel, token: int) -> None:
        channel.pc += 1
        channel.muted = False
        if channel.number < 2:
            pitch = token & 0x0F
            if pitch == 0x0C:
                channel.muted = True
            elif pitch >= len(self.document["periods"]):
                raise AudioPreviewError(f"pitched note uses period index {pitch}")
            else:
                channel.period = int(self.document["periods"][pitch]) >> (token >> 4)
        elif token == 0x10:
            channel.muted = True
        else:
            channel.period = token
        channel.duration_counter = channel.duration_reload
        channel.envelope_counter = 1
        channel.envelope_index = 0
        self.note_events += 1

    def run_until_note(self, channel: VirtualChannel) -> None:
        for _ in range(MAX_COMMANDS_PER_NOTE):
            if not 0 <= channel.pc < len(self.commands):
                raise AudioPreviewError("audio program counter left command storage")
            command = self.commands[channel.pc]
            kind = command["kind"]
            if kind == "note":
                self.decode_note(channel, byte_value(command, "note"))
                return
            channel.pc += 1
            if kind == "duration":
                index = byte_value(command, "duration") & 0x3F
                if index >= len(self.document["durations"]):
                    raise AudioPreviewError(f"duration index {index} is outside table")
                duration = int(self.document["durations"][index])
                channel.duration_counter = duration
                channel.duration_reload = duration
            elif kind == "set_sequence":
                index = byte_value(command, "sequence")
                if index >= len(self.document["envelopes"]):
                    raise AudioPreviewError(f"envelope index {index} is outside table")
                channel.envelope = index
            elif kind == "set_control":
                channel.control = (channel.control & 0xF0) | byte_value(command, "control")
            elif kind == "jump":
                channel.pc = self.pointer(command)
            elif kind == "call":
                if len(channel.call_stack) >= MAX_STACK_DEPTH:
                    raise AudioPreviewError("audio call stack exceeds engine storage")
                channel.call_stack.append(channel.pc)
                channel.pc = self.pointer(command)
            elif kind == "return":
                if not channel.call_stack:
                    raise AudioPreviewError("audio return has no matching call")
                channel.pc = channel.call_stack.pop()
            elif kind == "begin_loop":
                if len(channel.loop_stack) >= MAX_STACK_DEPTH:
                    raise AudioPreviewError("audio loop stack exceeds engine storage")
                channel.loop_stack.append(
                    LoopFrame(channel.pc, byte_value(command, "loop count"))
                )
            elif kind == "end_loop":
                if not channel.loop_stack:
                    raise AudioPreviewError("audio loop end has no matching start")
                loop = channel.loop_stack[-1]
                loop.remaining = (loop.remaining - 1) & 0xFF
                if loop.remaining:
                    channel.pc = loop.start
                else:
                    channel.loop_stack.pop()
            elif kind == "set_sweep":
                channel.sweep = byte_value(command, "sweep")
            elif kind == "set_volume":
                channel.control = (channel.control & 0x3F) | byte_value(command, "volume")
            elif kind == "stop":
                channel.active = False
                return
            else:
                raise AudioPreviewError(f"unsupported command kind {kind!r}")
        raise AudioPreviewError("audio command loop produced no note or stop")

    def update_envelope(self, channel: VirtualChannel) -> None:
        channel.envelope_counter = (channel.envelope_counter - 1) & 0xFF
        if channel.envelope_counter:
            return
        envelope = self.document["envelopes"][channel.envelope]["steps"]
        if channel.envelope_index >= len(envelope):
            raise AudioPreviewError("envelope cursor left its encoded steps")
        step = envelope[channel.envelope_index]
        channel.envelope_counter = int(step["duration"])
        channel.envelope_volume = int(step["volume"])
        channel.envelope_index += 1

    def update_channel(self, channel: VirtualChannel) -> None:
        channel.duration_counter = (channel.duration_counter - 1) & 0xFF
        if channel.duration_counter == 0:
            self.run_until_note(channel)
        if channel.active:
            self.update_envelope(channel)

    def output(self, channel: VirtualChannel | None) -> HardwareFrame:
        if channel is None or not channel.active or channel.muted:
            return HardwareFrame(None, 0, 0, 0, 0)
        subtract = 15 if channel.control & 0x20 else channel.control & 0x0F
        volume = max(channel.envelope_volume - subtract, 0)
        return HardwareFrame(
            channel.number,
            channel.period,
            volume,
            (channel.control >> 6) & 3,
            (channel.period >> 7) & 1,
        )

    def step(self) -> tuple[HardwareFrame, ...]:
        for number in sorted(self.channels):
            channel = self.channels[number]
            if channel.active:
                self.update_channel(channel)
        outputs = []
        for primary in range(0, 8, 2):
            first = self.channels.get(primary)
            second = self.channels.get(primary + 1)
            selected = first if first is not None and first.active else second
            outputs.append(self.output(selected))
        return tuple(outputs)

    @property
    def stopped(self) -> bool:
        return not any(channel.active for channel in self.channels.values())


def trace_effect(
    document: dict[str, Any], effect_number: int, maximum_frames: int
) -> PreviewTrace:
    if maximum_frames <= 0:
        raise AudioPreviewError("preview frame limit must be positive")
    sequencer = EffectSequencer(document, effect_number)
    frames = []
    for _ in range(maximum_frames):
        frames.append(sequencer.step())
        if sequencer.stopped:
            break
    return PreviewTrace(tuple(frames), sequencer.note_events, sequencer.stopped)


def trace_segments(trace: PreviewTrace) -> list[TraceSegment]:
    """Collapse identical per-frame APU states for piano-roll presentation."""
    if not trace.frames:
        return []
    segments: list[TraceSegment] = []
    for voice in range(4):
        start = 0
        current = trace.frames[0][voice]
        for frame_number in range(1, len(trace.frames)):
            value = trace.frames[frame_number][voice]
            if value != current:
                segments.append(TraceSegment(voice, start, frame_number, current))
                start, current = frame_number, value
        segments.append(TraceSegment(voice, start, len(trace.frames), current))
    return segments


class OutputFilter:
    """Approximate the NES two-high-pass/one-low-pass output chain."""

    def __init__(self, sample_rate: int) -> None:
        self.hp90 = self.high_pass(90.0, sample_rate)
        self.hp440 = self.high_pass(440.0, sample_rate)
        self.lp14k = self.low_pass(14_000.0, sample_rate)
        self.hp90_input = self.hp90_output = 0.0
        self.hp440_input = self.hp440_output = 0.0
        self.low_output = 0.0

    @staticmethod
    def high_pass(cutoff: float, sample_rate: int) -> float:
        rc = 1.0 / (2.0 * math.pi * cutoff)
        return rc / (rc + 1.0 / sample_rate)

    @staticmethod
    def low_pass(cutoff: float, sample_rate: int) -> float:
        rc = 1.0 / (2.0 * math.pi * cutoff)
        return (1.0 / sample_rate) / (rc + 1.0 / sample_rate)

    def process(self, value: float) -> float:
        first = self.hp90 * (self.hp90_output + value - self.hp90_input)
        self.hp90_input, self.hp90_output = value, first
        second = self.hp440 * (
            self.hp440_output + first - self.hp440_input
        )
        self.hp440_input, self.hp440_output = first, second
        self.low_output += self.lp14k * (second - self.low_output)
        return self.low_output


def apu_mix(pulse1: float, pulse2: float, triangle: float, noise: float) -> float:
    pulse_sum = pulse1 + pulse2
    pulse = 0.0 if pulse_sum == 0 else 95.88 / ((8128.0 / pulse_sum) + 100.0)
    tnd_input = triangle / 8227.0 + noise / 12241.0
    tnd = 0.0 if tnd_input == 0 else 159.79 / ((1.0 / tnd_input) + 100.0)
    return pulse + tnd


class ApuRenderer:
    def __init__(self, timing: str, sample_rate: int) -> None:
        if timing not in FRAME_RATES:
            raise AudioPreviewError(f"unknown console timing {timing!r}")
        self.timing = timing
        self.sample_rate = sample_rate
        self.clock = CPU_CLOCKS[timing]
        self.phases = [0.0] * 4
        self.noise_clock = 0.0
        self.noise_shift = 1
        self.filter = OutputFilter(sample_rate)

    def pulse(self, index: int, frame: HardwareFrame) -> float:
        if frame.volume == 0 or frame.period < 8:
            return 0.0
        frequency = self.clock / (16.0 * (frame.period + 1))
        self.phases[index] = (self.phases[index] + frequency / self.sample_rate) % 1.0
        return float(frame.volume) if self.phases[index] < PULSE_DUTIES[frame.duty] else 0.0

    def triangle(self, frame: HardwareFrame) -> float:
        if frame.volume == 0:
            return 0.0
        frequency = self.clock / (32.0 * (frame.period + 1))
        self.phases[2] = (self.phases[2] + frequency / self.sample_rate) % 1.0
        phase = self.phases[2]
        return 15.0 * (phase * 2.0 if phase < 0.5 else 2.0 - phase * 2.0)

    def noise(self, frame: HardwareFrame) -> float:
        if frame.volume == 0:
            return 0.0
        period = NOISE_PERIODS[self.timing][frame.period & 0x0F]
        self.noise_clock += self.clock / (period * self.sample_rate)
        while self.noise_clock >= 1.0:
            tap = 6 if frame.noise_mode else 1
            feedback = (self.noise_shift & 1) ^ ((self.noise_shift >> tap) & 1)
            self.noise_shift = (self.noise_shift >> 1) | (feedback << 14)
            self.noise_clock -= 1.0
        return float(frame.volume) if not self.noise_shift & 1 else 0.0

    def sample(self, frame: tuple[HardwareFrame, ...]) -> int:
        mixed = apu_mix(
            self.pulse(0, frame[0]),
            self.pulse(1, frame[1]),
            self.triangle(frame[2]),
            self.noise(frame[3]),
        )
        return max(-32768, min(32767, round(self.filter.process(mixed) * 48_000)))


def render_trace(
    trace: PreviewTrace,
    timing: str,
    sample_rate: int = SAMPLE_RATE,
    enabled_voices: set[int] | None = None,
) -> bytes:
    if enabled_voices is None:
        enabled_voices = set(range(len(VOICE_NAMES)))
    invalid = enabled_voices - set(range(len(VOICE_NAMES)))
    if invalid:
        raise AudioPreviewError(f"unknown APU voice indices: {sorted(invalid)}")
    renderer = ApuRenderer(timing, sample_rate)
    samples = bytearray()
    frame_rate = FRAME_RATES[timing]
    boundary = 0.0
    emitted = 0
    for frame_number, frame in enumerate(trace.frames, 1):
        audible = tuple(
            value if voice in enabled_voices else HardwareFrame(None, 0, 0, 0, 0)
            for voice, value in enumerate(frame)
        )
        boundary = frame_number * sample_rate / frame_rate
        while emitted < round(boundary):
            samples.extend(struct.pack("<h", renderer.sample(audible)))
            emitted += 1
    return bytes(samples)


def parse_voices(value: str) -> set[int]:
    """Parse a comma-separated CLI mixer selection."""
    requested = [name.strip().lower() for name in value.split(",") if name.strip()]
    if requested == ["all"]:
        return set(range(len(VOICE_NAMES)))
    unknown = sorted(set(requested) - set(VOICE_NAMES))
    if unknown:
        raise AudioPreviewError(
            f"unknown APU voices: {', '.join(unknown)}; "
            f"choose from {', '.join(VOICE_NAMES)} or all"
        )
    return {VOICE_NAMES.index(name) for name in requested}


def write_preview(
    document: dict[str, Any],
    profile: dict[str, Any],
    effect_number: int,
    output: Path,
    seconds: float,
    sample_rate: int = SAMPLE_RATE,
    enabled_voices: set[int] | None = None,
) -> PreviewTrace:
    if not 0.05 <= seconds <= 120.0:
        raise AudioPreviewError("preview length must be between 0.05 and 120 seconds")
    timing = profile["timing"]
    maximum_frames = math.ceil(seconds * FRAME_RATES[timing])
    trace = trace_effect(document, effect_number, maximum_frames)
    payload = render_trace(trace, timing, sample_rate, enabled_voices)
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(sample_rate)
        target.writeframes(payload)
    return trace


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profiles", type=Path, default=ROOT / "config/revision_profiles.json"
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--profile")
    parser.add_argument("--effect", required=True, type=int)
    parser.add_argument("--seconds", type=float, default=12.0)
    parser.add_argument(
        "--channels",
        default="all",
        help="comma-separated pulse1,pulse2,triangle,noise selection, or all",
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        document = audio_editor.load_document(args.input)
        profile_id = args.profile or document.get("source_profile")
        profile = get_profile(load_profiles(args.profiles), profile_id)
        audio_editor.validate_header(document, profile)
        trace = write_preview(
            document,
            profile,
            args.effect,
            args.output,
            args.seconds,
            enabled_voices=parse_voices(args.channels),
        )
        print(
            f"[OK] effect {args.effect:02d}: {len(trace.frames)} frames, "
            f"{trace.note_events} notes, stopped={str(trace.stopped).lower()}, "
            f"preview={args.output}"
        )
    except (
        AudioPreviewError,
        audio_editor.AudioEditorError,
        RoomDataError,
        ProjectError,
        OSError,
        KeyError,
        IndexError,
        TypeError,
        wave.Error,
    ) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
