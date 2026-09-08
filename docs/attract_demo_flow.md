# Attract and demo flow

`src/game/flow/runtime.asm` owns CPU `$CA6E-$CB6E`. It connects the
gameplay-exit pipeline to the post-game summary, title wait, and automated
gameplay demonstration through three scheduler entries.

| Code | Context | Entry | Role |
| ---: | ---: | --- | --- |
| `$17` | 1 | `RunPostGameAttractThread` | post-game and title presentation |
| `$18` | 1 | `StartDemoPlayback` | demo-specific thread and room setup |
| `$22` | 2 | `RunDemoInputPlayback` | recorded controller producer |

These entry points are nested. The title-input path starts code `$10` before
falling into `StartDemoPlayback`; a direct scheduler `$18` entry deliberately
skips that first call. Likewise, code `$22` enters before clearing
`NmiFrameCounter` and `DemoInputIndex`, then falls into the polling loop at
`PollDemoInputPlayback`.

## Post-game and title stages

Code `$17` first stops competing secondary contexts, sets the fixed scroll and
CHR bank, and examines the sign of `RoomStateFlags`. A negative value marks an
interrupted demo: bit seven is cleared and the post-game summary is skipped.
The ordinary path clears both nametables and queues static PPU streams
`$0D-$11`, then waits for either the reused 16-bit counter to reach `$0100` or
a real Start/Select press.

`PrepareTitleScreen` repeats the context and display reset, calls
`DrawTitleLogoLayer` and `DrawTitleRecordLayer`, and resets the wait counter.
At `$0200` ticks it starts scheduler code `$18`; Start/Select can move to the
same demo setup earlier. Both button waits require release before the next
stage, preventing a held input from leaking across screens.

## Demo setup

The demo path starts context-two code `$22`, selects room index two, installs a
fixed packed inventory value `$54`, three slots, three lives, and then starts
room loading through code `$15`. It also sets a mode byte at `$0080`; that byte
is intentionally kept local because other transitions reuse the address for
unrelated orbit state.

## Recorded controller stream

Context two indexes source-owned parallel tables at `$CEF1` and `$CF13`. The first supplies
inclusive frame durations and the second supplies cached controller values.
For each entry, `NmiFrameCounter` must grow strictly larger than the duration;
the routine then installs the next value in `Joypad1Cached`, advances the
index, and resets the frame counter. The checked count is `$22` entries.

Real Start/Select bits remain observable because the controller cache merges
them separately while `GameStateFlags` bit zero is clear. Pressing either sets
`RoomStateFlags` bit seven and waits for release. Input exhaustion or manual
interruption starts gameplay-exit code `$35` and stops context two, returning
the attract loop through the shared exit machinery.

`DemoInputDurations` and `DemoInputValues` each contain exactly `$22` bytes.
Assembly assertions bind that count to the playback limit and require the
tables to remain adjacent.

The playback loop reads `DemoInputDurations,X` before comparing X with `$22`.
At exhaustion it therefore reads the first byte of the adjacent input table as
one final duration. That byte is zero, so the deliberate boundary alias adds a
single final wait before exit without indexing another controller value.

`make title-data-audit` decodes all 34 entries into inclusive durations and
named button sets, checks that boundary alias, and re-encodes both parallel
tables byte-for-byte. Their independent and aggregate SHA-1 fingerprints live
in `config/authoring/title_data.json`.
