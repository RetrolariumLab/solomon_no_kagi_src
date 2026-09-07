# NMI Dana control and sprite composition

`src/game/nmi/dana_and_sprites.asm` owns `$83C2-$863B`. The NMI gameplay path
uses its first half to update Dana's action from cached input and its second
half to compose every two-sprite object into OAM.

## Dana control-state dispatch

`UpdateDanaControlState` requires an active Dana record, divides action byte 3
by four, and uses the resulting group index in a seven-entry split pointer
table. Groups 0 through 6 cover action values `$00-$1B`; group 3 is a direct
no-op entry. The dispatcher supplies `GameplayFrameCounters` byte 0 in A,
Dana's current action in X, and `Joypad1Cached` in Y.

The handlers choose new action encodings from the low action bits, directional
input, and elapsed-frame thresholds of 5, 7, 8, or 9. One group submits
scheduler code `$12`, the context-one `HandleDanaHeadCollision` entry. Bit 0
consistently selects right/left facing, and the controllable action pairs are
now defined as shared assembly constants. See `docs/dana_action_states.md` for
the complete `$00-$23` state map and the three pairs with no direct producer.

## Y sorting and overlap groups

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

## OAM records

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
