# NMI runtime

This guide describes the vertical-blank dispatcher, gameplay interactions, Dana control, and sprite composition.


---

## Vertical-blank subsystem

### Owned range

`src/system/boot_and_frame.asm` owns CPU `$8000-$80FE` (255 bytes). The adjacent gameplay
services at `$80FF-$837C` are reconstructed separately in
`src/game/nmi/gameplay_interactions.asm`. The linker places both segments
before the remaining fixed PRG, and
`make reconstruction-audit` checks its start, end, size, and required labels.

### Entry and exit contract

The vector at `$FFFA` enters `NMI`. The handler saves X, Y, and A, performs its
PPU and frame services, restores those registers at `NmiRestoreRegisters`, and
returns with `RTI`. It deliberately does not save processor status because the
6502 interrupt sequence already pushes it.

At entry, `PpuCtrlShadow` and `PpuMaskShadow` provide the software-owned PPU
state. The handler temporarily clears control/mask bits while it prepares the
frame, then sets bit 7 in `PpuCtrlShadow` before restoring `PPU_CTRL` on exit.

### PPU and mapper transactions

- OAM DMA always uses page `>OamBuffer`, which is `$02` for the shadow OAM
  allocation beginning at `$0210`.
- `WritePpuScroll` reads `PPU_STATUS` to reset the shared PPU address latch,
  writes `PpuScrollX`, then writes the Y value passed in X to `PPU_SCROLL`.
- `ChrBankSelectValues` contains `$10,$11,$12,$13`. The NMI masks the selector
  to two bits, reads the corresponding value, and writes it to an address in
  the CNROM cartridge range. The low two data bits therefore select one of the
  four 8 KiB CHR banks; the high nibble is retained from the original bus value.
  `ChrBankRequest` is then set to the consumed value `$80`. See
  `docs/chr_bank_policy.md` for every producer and the per-room profile.

### Gameplay services

After the PPU work, the handler masks SP with `$1F` to obtain the offset in the
current context's 32-byte stack window. Offsets below `$08` branch through
`SkipNmiGameplayServicesForStack` directly to register restoration, protecting
the remaining stack space by omitting gameplay and post-gameplay calls for that
video frame. The runtime timer windows now count this branch explicitly.

The active path now uses symbolic calls for the alternating enemy-overlap
scan, fireball RoomMap collision, Dana A/B action requests, the four-slot
pending-thread queue, Dana's control-state dispatcher, and the complete
object-to-OAM composer. See `docs/nmi_runtime.md#nmi-gameplay-interactions` and
`docs/nmi_runtime.md#nmi-dana-control-and-sprite-composition`.

### Evidence boundary

The register save/restore, PPU writes, OAM page, and four-way CNROM selection
are statically confirmed. The NMI now has no raw absolute control-flow target;
neutral names remain where the precise game-facing meaning of Dana's action
encodings still needs runtime evidence.

---

## NMI gameplay interactions

`src/game/nmi/gameplay_interactions.asm` owns `$80FF-$837C`, immediately after
the core NMI handler. The range contains three related services invoked by the
active-gameplay NMI path: enemy overlap scans, fireball-to-map collision, and
Dana action request setup.

### Enemy overlap scans

`CheckGameplayObjectInteractions` toggles `GameplayFlags` bit 7 and performs
the scans only on the negative half of that cadence. It exits when bit 4 is
already set, when Dana is inactive, or before the fireball scan when the
fireball object is inactive.

Both scans walk the 17 enemy-object pointer pairs from index 16 down to zero.
`CheckEnemyOverlapAtCoordinates` accepts the selected enemy pointer in
`TempPointer08` and an extent selector in X. It rejects inactive records and
selector-specific state bits, then compares integer Y/X coordinates against
the target rectangle. Carry clear reports an overlap.

The fireball path sets bit 0 in every overlapping enemy state. For fireball
types below `$10`, it also copies the type to `FireballLifeCounter1Hi`. At
least one contact queues scheduler code `$50`, whose context-five entry is
`ProcessDefeatedEnemyDrops`. A Dana contact sets `GameplayFlags` bit 4 and
queues code `$31`, the context-three death transition.

### Fireball map collision

`UpdateActiveFireballCollision` integrates the fireball's fractional and
integer position with one of four direction deltas. It samples the old and
new bounding positions through `BuildFireballRoomCollisionMask`. That helper
converts a rectangle crossing at most two rows and two columns into four
RoomMap sign-bit tests and returns their packed low-nibble collision mask.

Before dispatch, the routine temporarily makes `EnemyAiPointer` address
`FireballActive` and `EnemyObjectPointer` address `FireballObject`. The
16-entry split handler table targets the path-mask handlers reconstructed in
`src/game/enemies/pathfinding_ai.asm`. The pointer setup, mask construction, and
all table destinations are statically confirmed and assemble byte-for-byte.
This synthetic AI-record view also proves `$0430-$0431` as the current and
alternate four-way path directions at AI offsets 6 and 7.

### Dana action requests

The A-button and B-button NMI paths enter `TryStartBlockMagicAction` and
`TryStartFireballAction`. Both pass a context-one scheduler code to
`TryStartDanaAction`: `$11` selects `CastOrRemoveBlock`, while `$13` selects
`CastFireballFromInventory`.

The shared setup rejects incompatible gameplay flags and Dana actions outside
`$10-$1B`. An accepted request snapshots Dana's action and Y-motion as
`DanaSavedAction` and `DanaSavedYMotion`, selects the casting action, shifts
Dana's X coordinate, marks the action active, and submits the code through
`QueuePendingThreadStart`.

That queue has four slots at `$041F-$0422`. It searches slots 3 through 1 for
zero and uses slot 0 as the fallback. Startup drains the same array and calls
`StartThread` for each nonzero request.

---

## NMI Dana control and sprite composition

`src/game/nmi/dana_and_sprites.asm` owns `$83C2-$863B`. The NMI gameplay path
uses its first half to update Dana's action from cached input and its second
half to compose every two-sprite object into OAM.

### Dana control-state dispatch

`UpdateDanaControlState` requires an active Dana record, divides action byte 3
by four, and uses the resulting group index in a seven-entry split pointer
table. Groups 0 through 6 cover action values `$00-$1B`; group 3 is a direct
no-op entry. The dispatcher supplies `GameplayFrameCounters` byte 0 in A,
Dana's current action in X, and `Joypad1Cached` in Y.

The handlers choose new action encodings from the low action bits, directional
input, and elapsed-frame thresholds of 5, 7, 8, or 9. One group submits
scheduler code `$12`, the context-one `HandleDanaHeadCollision` entry. Bit 0
consistently selects right/left facing, and the controllable action pairs are
now defined as shared assembly constants. See `docs/player_actions.md#dana-action-state-encoding` for
the complete `$00-$23` state map and the three pairs with no direct producer.

### Y sorting and overlap groups

`RenderGameplayObjectsToOam` loads integer Y for all 20 non-Dana object records
into `$0040-$0053` and seeds the parallel order array at `$0054-$0067`. A
diminishing-gap insertion sort runs gaps 10 down to 1, leaving both arrays in
Y order.

The following pass compares adjacent Y values. Separations below 16 pixels
remain in one overlap group; larger gaps close the current group through
`UpdateScanlineObjectAllowance`. The 16-byte array at `$0068-$0077` records
row-indexed allowances used while selecting the next object. This reorders
overlapping two-sprite objects before OAM emission and rotates which records
receive the limited scanline slots.

### OAM records

Dana always owns the first two OAM entries. The 20 non-Dana records use the
following 40 entries in the selected order. Each active object contributes:

| OAM byte | Source |
| --- | --- |
| Y | object byte 7, shared by both halves |
| tile | object bytes 17 and 18 |
| attributes | two projections of packed object byte 19 |
| X | object byte 10 and byte 10 plus 8 |

An inactive object writes `$F8` to both OAM Y bytes, hiding the pair. The
routine therefore owns the complete object-to-sprite composition step before
the next NMI performs OAM DMA.
