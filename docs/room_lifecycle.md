# Room lifecycle

This guide covers the state transitions that leave one room, prepare the next room, and present its introductory frame.


---

## Room-clear and room-load pipeline

The complete `$8EC0-$915D` range is source-owned as the context-one room
transition pipeline. The scheduler tables prove three distinct entry contracts:

| Scheduler code | Entry | Role |
| ---: | ---: | --- |
| `$10` | `$901E` | reset new-game state, then load room zero |
| `$14` | `$8EE4` | finish a cleared room and convert time to score |
| `$15` | `$9021` | load the selected room without a new-game reset |

`RoomClearThread` first shuts down the other secondary contexts and waits for
the transition flags to settle. It builds the timer display, initializes two
temporary AI/object records, queues static PPU messages 2 through 4, and runs
the room-clear presentation. After a delay it calls `SubtractTimerBy8`, clears
the two temporary object states, clears the nametable area, plays the final
sound request, and replaces context 1 with scheduler selector `$15`.

The room-clear data has a deliberate overlap. `RoomClearAiStateTemplate` is
nine bytes beginning at `$8FA2`, while `RoomClearObjectHeaderPredecessors`
begins at `$8FAA`; byte `$8FAA` is therefore both the AI template's last byte
and the object-header table's first byte. The ca65 source preserves that shared
entry rather than duplicating data. The two initialized gameplay objects use
X positions `$28` and `$C8`, Y position `$50`, state `$C0`, type `$1C`, and
actions `$18/$19`.

`SubtractTimerBy8` is independently named in Bisqwit's map. It performs
decimal borrow propagation across the four unpacked timer digits at
`$0438-$043B`. Each successful subtraction adds eight at score digit index 6;
the final remainder is credited separately, all timer digits are cleared, and
the combined score/timer PPU update is published. The display loop uses carry
as a leading-zero latch, replacing only leading zeroes with tile `$24`.

`NewGameRoomLoadThread` calls `ResetNewGameState` and falls through to the
common `RoomLoadThread`; selector `$15` enters the common path directly. The
loader:

1. selects the normal or special room index;
2. initializes the block map and starts context 6;
3. queues the initial static PPU streams and waits for the presentation delay;
4. decodes room items, metadata, and enemies;
5. renders the 16x12 RoomMap interior;
6. copies and patches the room palette update in shared RAM;
7. initializes Dana's object header;
8. starts scheduler code `$30` (`MainGameplayThread`) and stops context 1.

`RoomLoadPaletteTemplate` begins with a `$3F00` literal command. The loader
copies its command header and first 16 colors, changes the control byte to a
16-byte literal command, selects one color from the 14-entry
`RoomPaletteColorByRoomGroup` table using `room_index / 4`, writes that color
at payload offsets `$01/$05/$09/$0D`, terminates the RAM program, and publishes
it for NMI consumption. The 14 groups cover every zero-based room index from
0 through 52.

`ResetNewGameState` selects room zero, grants three remaining lives and three
inventory slots, clears the eight decimal score digits and adjacent state
flags, then seeds `GameStateFlags`, `$0080`, and the high fireball-lifetime
byte with one.

The former raw dependencies at `$91EB`, `$91B9`, `$92BC`, `$9340`, `$C2A6`,
`$C3D4`, and `$C403` are now source-owned as `PrepareRoomIntro`,
`PublishRoomDoorAndKeyUpdates`, `RunRoomEntryAnimation`,
`RunTransitionObjectOrbit`, `AnimateDoorUnlockFromDanaPosition`,
`RefreshGameplayHud`, and `BuildScoreDisplayUpdate`. The shared coordinate
dependency at `$C364` is `BuildScaledCoordinateDeltas`. The room-load pipeline
therefore has no remaining raw call targets.

### Runtime transition evidence

The `room-1-door-transition` scenario creates only the four prerequisite RAM
conditions for an already collected key and an open-door overlap. From there,
the original ROM executes `EnterRoomDoor` at frame 721, enters
`RoomClearThread` in context 1 on the same frame, reaches the first
`SubtractTimerBy8` score conversion at frame 854, and invokes `RoomLoadThread`
for internal room `$01` at frame 1136. Every setup write and previous value is
declared in `scenarios/runtime_scenarios.json` and checked by
`make validate-runtime`.

---

## Room-transition state reset

`src/game/rooms/lifecycle.asm` owns CPU `$C981-$C9BC`: the presentation
data immediately before the reset helper and the helper itself. Both reset
callers are named in the source-owned gameplay-exit flow beginning at `$C78A`.

The data block contains the four-value PPU-mask cycle used by the life-loss
animation, the direct PPU program that displays `TIME OVER.`, and a 15-byte
post-game result template. The result flow copies that final template into the
shared buffer and patches two value bytes before publication.

`ResetRoomTransitionState` performs four operations:

1. keeps scheduler context 3 active while resetting the other secondary
   contexts through `ResetOtherSecondaryThreads`;
2. clears bits 6 and 2 of `GameplayFlags` with mask `$BB`;
3. clears `FireballActive`;
4. queues sound-effect command 3.

The helper exposes a repeated room-transition boundary while the preceding
animation, life handling, score comparison, and PPU control flow remains the
next reconstruction range.

---

## Room intro and transition orbit

The complete `$91B9-$9470` range owns the visible room-entry setup after the
room data has been decoded. It publishes the initial door/key cells, builds the
room intro HUD, positions Dana, and drives a fifteen-object orbit presentation.

### Door and key cells

`PublishRoomDoorAndKeyUpdates` consumes the already-resolved `RoomItemPointer`.
Header byte 5 is the door's packed RoomMap position and byte 6 is the key
position. A nonzero door position receives tile `$02`, or tile `$35` when the
key position is zero. The key receives tile `$06` only when gameplay flag
`$20` and header flag mask `$C0` are both clear. Every visible change is sent
through `BuildAndPublishRoomMapCellUpdate`, so the RoomMap and nametable stay
synchronized.

### Intro PPU program

`PrepareRoomIntro` copies the 27-byte `RoomIntroPpuTemplate` to the shared RAM
buffer and patches room/life digits before publishing it. Decoded as the normal
PPU update bytecode, the template is:

| PPU address | Payload |
| ---: | --- |
| `$216B` | six tiles spelling `SHRINE` |
| `$21CB` | eight tiles: space, `ROOM`, space, two digits |
| `$226F` | glyph `$98` and two life-count digits |

`FormatTwoDigitNumberTiles` performs repeated subtraction by ten. It returns
the ones digit in A and the tens digit in X, replacing a zero tens digit with
blank tile `$24`.

Room indices `$30+` select one of three fixed eight-tile names. The source
preserves the literal ROM spelling `PRINSESS`, followed by ` SOLOMON` and
` HIDDEN `. Later special indices clamp to the third string. The intro also
derives a marker tile from four-room groups, publishes it at RoomMap index
`$49`, stores the group as `ChrBankRequest`, and initializes
`MagicSparkObject`.

### Entry animation

`RunRoomEntryAnimation` reads header byte 7, the packed Dana start position.
It converts that cell to pixels, seeds 13 bytes of transition AI state, and
calls `RunTransitionObjectOrbit`. After the orbit completes, Dana and the
spark object receive the decoded coordinates. Two cooperative 16-tick waits
then select spark action `$07/$08` from the X side and replace its type with
`$04`.

The four-byte `TransitionAiCoordinateSourceOffsets` table is shared by room
entry and room clear. Values `0, 2, 1, 3` reorder the four zero-page scratch
bytes into the transition AI record; this shared use is now symbolic at both
call sites.

### Fifteen-object orbit

`RunTransitionObjectOrbit` deactivates the non-Dana pool, initializes records
0 through 14 with state `$C0`, type `$1C`, cached byte `$FF`, and action zero,
then resets `GameplayDelayCounter`. For each new counter value below `$40`, it:

1. calls `PositionTransitionOrbitObjects`;
2. advances two little-endian center accumulators;
3. advances a little-endian radius accumulator;
4. adds `$0080` as a phase step and masks the phase to six bits.

On completion it clears 25 transition AI bytes and changes every active
non-Dana object state to zero.

The positioner visits object indices 14 through 0. Each successive object adds
eight to the six-bit phase. `LoadQuarterSineMagnitude` reflects phase bit 5
into the 32-byte `QuarterSineTable`; phase bit 6 supplies the sign. A second
lookup shifted by `$20` produces the perpendicular component. The fixed-point
shift/add helper at `$9429` scales both magnitudes by the current radius before
they are added to the center and stored as object Y/X.

The table rises monotonically from `$00` to `$7F`, providing one quadrant of a
seven-bit sine magnitude. Reflection and conditional complement reconstruct
the full orbit without a 256-byte trigonometric table.

The coordinate preparation dependency at `$C364` is now source-owned as
`BuildScaledCoordinateDeltas`. It converts origin and target Y/X bytes into
two signed 16-bit differences scaled by four before the transition state is
seeded. See `docs/player_actions.md#scaled-coordinate-deltas`.

---

## Room nametable frame

`DrawRoomNametableFrame` at `$970B-$97A2` draws the fixed frame around the
30x24 room tile interior. Its sole caller is in the room initialization path.

### PPU layout

| Start | Increment | Output |
| ---: | ---: | --- |
| `$209F` | 32 | 24 bytes of pattern 0, then tiles `$A4,$A3` |
| `$209E` | 32 | 24 bytes of pattern 1 |
| `$2380` | 1 | 32 bytes of pattern 2, then 32 bytes of pattern 3 |
| `$23C0` | 1 | 64 zero attribute bytes |

The `$209E/$209F` transfers form the inner and outer right columns beginning
at nametable row 4. The `$2380` transfer fills rows 28 and 29, completing the
two-row bottom edge beneath the 24-row interior. Together these writes border
the 30-column area cleared by `Clear30x24NametableRegion`.

### Transfer behavior

The renderer waits for the buffered PPU update pointer to become idle, enters
the direct-transfer guard, switches `PPU_CTRL` between 32-byte and one-byte
increments as needed, and tail-calls `EndDirectPpuTransfer`.

Its four source records and repeated writers are separately owned by
`src/data/static_layout.asm` and
`src/graphics/ppu/runtime.asm`.
