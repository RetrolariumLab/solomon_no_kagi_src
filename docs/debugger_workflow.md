# Debugger workflow

Use the exact image and generated labels for the selected profile. The base
`make symbols` command remains the frozen USA Source 1.0 path. Source 2.0 binds
the same semantic breakpoint/watch inventory to profile-specific linker output:

```console
make validate-revision-symbols PROFILE=usa
make validate-revision-symbols PROFILE=europe
make validate-revision-symbol-profiles
```

Each entry retains its USA preservation address and records an explicit Europe
override where code relocation or the PAL gameplay-RAM insertion changes it.
The exporter rejects an override that disagrees with the selected `.dbg` and
VICE label files, then writes FCEUX `.nl` files beside that profile's ROM under
`build/revisions/PROFILE/`. A symbol file from another regional build is not
valid evidence.

## Mesen 2 setup

1. For USA 1.0, run `make verify` and `make symbols`, then open
   `build/native/solomons_key.nes`. For a 2.0 profile, run the matching
   `validate-revision-symbols` command and open
   `build/revisions/PROFILE/solomons_key.nes`.
2. Open the debugger and import the `.lbl` beside the selected ROM if Mesen
   does not discover it automatically (`build/native/solomons_key.lbl` for the
   1.0 path or `build/revisions/PROFILE/solomons_key.lbl` for Source 2.0).
   FCEUX automatically finds the generated `.nl` files next to the ROM in
   `build/native/`.
3. Add the starting watches from `config/debugger/watches.json`. Every entry
   names the RAM symbol anchoring the range; `make validate-symbols` rejects a
   stale address.
4. Add only the breakpoints needed for the current question from
   `config/debugger/breakpoints.json`; every breakpoint is checked against both
   the ld65 debug database and VICE label file. The scheduler breakpoint is
   extremely hot and should normally log conditionally rather than pause.
5. Record ROM SHA-1, room, input frame, PC, context index, SP, and affected RAM
   bytes with every observation.

## Scheduler trace

At `$8DB4`, log the current `$0302`, CPU SP, and bytes `$0012-$0019`. Compare a
quiet room against a room with many spawned enemies. The first goal is to prove
which index owns Dana input, enemy AI, movement integration, room services, and
audio—not merely to count calls.

## Object-field trace

Use write breakpoints on one `$14`-byte record at a time. Start with Dana at
`$057F-$0592`, then compare the same offsets in the first enemy at
`$05CF-$05E2`. A field should receive a semantic name only after its writers,
readers, and visible effect agree.

## Room-loader trace

Break on writes beginning at `$0304` during a room transition. Correlate each
write with the decoded JSON from `scripts/authoring/room_data.py --room N`. This separates
fixed room input from later runtime mutations such as revealed items, broken
blocks, key state, and door state.

## Room-transition trace

Break at `RoomClearThread` (`$8EE4`) and `SubtractTimerBy8` (`$8FB0`). Capture
timer digits `$0438-$043B`, score digits `$044A-$0451`, and the shared PPU
buffer after each credited chunk. The static reconstruction predicts repeated
chunks of eight followed by one final remainder.

Break at `RunTransitionObjectOrbit` (`$9340`), watch `$04F7-$050F`, and log
object Y/X writes for indices 0-14 until `GameplayDelayCounter` reaches `$40`.
The source predicts eight phase units between objects and one position update
per distinct delay-counter value.

Break at `PrepareRoomIntro` (`$91EB`) across normal and special rooms and save
`$03E6-$03FF` immediately before publication. This verifies room/life digits,
the literal `PRINSESS`/` SOLOMON`/` HIDDEN ` strings, and the marker grouping
against the source tables.

## Demon Mirror trace

Break at `UpdateDemonMirrorSpawnSchedule` (`$A0A7`) and record `$043C-$0447`
plus both schedule bytes selected through `$0036-$0039`. Verify that a new
phase appears once per `$40` NMI increments, phases 0-7 consume bits 7-0, and
state bit 5 remains set after the initial 32 phases.

Break at `SpawnScheduledDemonMirrorObjects` (`$A110`) and
`ActivatePendingDemonMirrorEnemies` (`$A04C`). Record allocation carry, saved
slots `$0445-$0446`, stream offsets `$043F-$0440`, and the byte read through
`$003A-$003D`. A `$90+n` control byte must replace the corresponding stream
offset without calling `ConfigureEnemyType`.

Runtime findings belong in a focused document or reproducible scenario, while
unresolved contradictions belong in `docs/unknowns.md`.
