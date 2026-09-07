# Runtime evidence

The static reconstruction is supplemented by deterministic FCEUX scenarios.
They execute the byte-identical built ROM, import symbols generated from the
same ld65 build, apply only declared controller input, and record focused CSV
events under `build/native/runtime/`.

## Reproduction

Run:

```bash
make trace-runtime
```

`FCEUX` defaults to the shared sibling-project automation build at
`../fceux_automation/vc/x64/Release/fceux64.exe` and can be overridden on the
command line. The runner verifies the complete ROM SHA-1 before starting the
emulator. `make validate-runtime` can revalidate already captured traces
without rerunning FCEUX.

The traces are generated evidence and are not committed. The committed
contract is `scenarios/runtime_scenarios.json`: it records the method, exact
input frames, expected first execution of semantic routines, forbidden events,
selected final RAM state, and every controlled patch. Undeclared, reordered,
or value-mismatched patches fail validation.

## Initial scenarios

`cold-boot-idle` performs a natural 180-frame power-on with no input. It proves
the first NMI, controller read, and cooperative scheduler switch while ensuring
that room loading and gameplay do not begin spontaneously.

`start-room-1` supplies Start only on frames 300-301 and otherwise leaves the
controller untouched. It observes the room loader, intro preparation, main
gameplay thread, timer path, Dana control, object motion and collision, and the
enemy-AI dispatcher. At frame 1000 it checks the internal room index, timer
digits, Dana position, and active-enemy count.

`room-1-walk-right` extends the same natural entry with Right held on frames
720-780. The trace proves that the raw controller state reaches RAM and that
Dana's horizontal coordinate subsequently changes, then fixes a final gameplay
state at frame 900.

`room-1-pause-resume` supplies independent Start pulses on frames 720-721 and
800-801. The pause thread starts at frame 722, sets `GameStateFlags` to `$07`
after its 40-frame debounce, and clears the pause bits to `$01` on frame 803.
The timer remains unchanged while pause is active, Dana control is forbidden
inside that interval, and its first post-resume execution is required on frame
804. No RAM or control-flow patch is used.

`room-1-life-loss-reload` makes one declared write to the scheduler request
mailbox at frame 720, selecting the documented context-three death entry `$31`.
Original code begins Dana's fall on frame 721, reaches its `$D1` boundary on
804, runs shared exit cleanup on 853, decrements `RemainingLives` from three to
two, and re-enters `RoomLoadThread` on 854. Its final state requires the same
room to be running again at frame 1800. It does not patch life, object, or timer
data, any ROM byte, or the scheduler stack.

`room-1-cast-block` presses A on frames 720-780. It observes the block-magic
request, execution of `CreateBlockInRoomMap`, and the resulting write of `$90`
to RAM address `$0387`, map index `$83`. The expected event detail protects
both the selected cell and encoded tile value.

`room-1-cast-fireball` uses three declared writes at frame 720 to supply one
small-fireball inventory slot and shorten its configured lifetime to `$0010`,
then presses B on frames 720-780. Original code casts and activates the object
at frame 722, reaches NMI collision processing at 723, clears
`FireballActive` and enters inactive cleanup at 739, and retires the object at
747. The trace validates every setup write and the exact RAM addresses changed
by deactivation and retirement.

`audio-channel-priority` starts Room 1 normally and injects three reviewed
mailbox requests without changing ROM code. Its event series records command
consumption, descriptor stream installation, the virtual channel selected for
each APU voice, and the complete active mask. It proves descending mailbox
precedence and temporary even-over-odd channel stealing on triangle and noise;
the exact frames and streams are part of the committed scenario contract.

`attract-demo-scheduler` supplies no input and waits for the built-in demo. It
compares a populated object pool with the first-room baseline. Both traces
preserve the context cycle `3,4,5,6,7,0,1,2`, while their 60-frame switch and
timer-service totals demonstrate the scheduler's workload-dependent cadence.

`room-1-door-transition` uses four declared writes at frame 720 to represent
the state immediately after obtaining the key and reaching the open door: set
the key flag, replace the Room 1 door cell with tile `$07`, and move Dana's Y/X
coordinates onto that cell. No control-flow or timer state is patched. Original
code then executes `EnterRoomDoor` and `RoomClearThread`, starts timer-to-score
conversion through `SubtractTimerBy8`, and reaches the next `RoomLoadThread` at
frame 1136. The final state proves gameplay in internal room `$01`.

These ten scenarios establish the runtime harness and a reproducible
boot-to-play, movement, pause/resume, block/fireball casting, progression, and
life-loss/reload, and scheduler-timing baseline.
Later subsystem traces should add focused, explicitly declared state setup
where reaching rare mechanics through input alone would make the evidence
prohibitively slow.

## European PAL baseline

Source Reconstruction 2.0 keeps a separate committed contract in
`scenarios/runtime_scenarios_europe.json`. It is bound to the complete European
ROM SHA-1 and to profile-selected linker symbols rather than copied USA
addresses. Capture or revalidate it with:

```console
make trace-revision-runtime PROFILE=europe
make validate-revision-runtime PROFILE=europe
```

The four-scenario baseline covers cold boot, natural Room 1 entry, pause and
resume, and overlapping audio-channel priority. It resolves execute hooks in
relocated PAL code and reads the shifted timer, audio-state, enemy, Dana, and
fireball RAM symbols live. The first gameplay frame remains 610 for this input,
but the first 60-frame window records 834 switches per scheduler context and
204 timer calls, versus 829 and 203 in the USA contract. The final Room 1 timer
at frame 1000 is `06020900` rather than `09030900`.

The audio scenario also proves that commands 7, 10, and 8 route through the
same virtual channels and APU priority order while resolving their PAL stream
starts at `$FB03`, `$FB57`, and `$FB15`. Its three controlled mailbox writes
are declared in the manifest and no code, channel state, or stream pointer is
patched. Generated CSV files remain under `build/revisions/europe/runtime/`.

`make trace-revision-runtimes` freshly captures the frozen ten-scenario USA
matrix and this focused PAL matrix together. The regional runner checks the
manifest profile in addition to ROM identity, so a USA contract cannot be
silently validated as European evidence.
