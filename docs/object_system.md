# Object system

This guide defines gameplay object records, frame updates, movement, collision response, pointer access, and pool maintenance.


---

## Gameplay object record layout

The gameplay pool contains 21 contiguous `$14`-byte records at
`$057F-$0722`: Dana, the magic spark, the fireball, one auxiliary object, and
17 enemy objects. `ObjectRecordPointerLowTable` and
`ObjectRecordPointerHighTable` address every record and are checked by
`make enemy-pointer-audit`.

| Offset | Name | Role |
| ---: | --- | --- |
| 0 | `ObjectStateOffset` | active/lifecycle flags; values `$C0+` enter the update pipeline |
| 1 | `ObjectTypeOffset` | type-group selector plus low-two-bit variant |
| 2 | `ObjectCachedTypeOffset` | cached type used to detect definition changes |
| 3 | `ObjectActionOffset` | action selector into motion and animation definitions |
| 4 | `ObjectCachedActionOffset` | cached action used to detect definition changes |
| 5 | `ObjectYMotionOffset` | signed Y motion |
| 6 | `ObjectYFractionOffset` | fractional Y coordinate |
| 7 | `ObjectYPositionOffset` | integer Y coordinate |
| 8 | `ObjectXMotionOffset` | signed X motion |
| 9 | `ObjectXFractionOffset` | fractional X coordinate |
| 10 | `ObjectXPositionOffset` | integer X coordinate |
| 11 | `ObjectCollisionMaskOffset` | six RoomMap solidity samples |
| 12 | `ObjectAnimationCounterOffset` | current animation countdown |
| 13 | `ObjectAnimationDelayOffset` | animation countdown reload value |
| 14 | `ObjectAnimationPhaseOffset` | packed animation frame phase |
| 15 | `ObjectAnimationPointerLowOffset` | animation stream pointer low byte |
| 16 | `ObjectAnimationPointerHighOffset` | animation stream pointer high byte |
| 17 | `ObjectSpriteTile1Offset` | first 8x16 sprite tile |
| 18 | `ObjectSpriteTile2Offset` | second 8x16 sprite tile |
| 19 | `ObjectSpriteFlagsOffset` | packed attributes for both sprite halves |

The per-frame traversal independently establishes the cached type/action
contract. A change reloads motion and animation definitions; otherwise the
record proceeds directly through fixed-point integration, collision response,
and animation sequencing. Rendering copies the final Y, X, tile, and flags
fields into two OAM entries.

### Collision mask geometry

`SampleObjectRoomMapCollision` samples a two-column footprint at three nearby
Y coordinates. Duplicate cells are retained when the footprint does not cross
a 16-pixel tile boundary. The six sign tests are packed in this exact order:

| Bit | Mask | Sample coordinate |
| ---: | ---: | --- |
| 0 | `$01` | upper left: `(X-4, Y-13)` |
| 1 | `$02` | upper right: `(X+3, Y-13)` |
| 2 | `$04` | lower right: `(X+3, Y-1)` |
| 3 | `$08` | lower left: `(X-4, Y-1)` |
| 4 | `$10` | below left: `(X-4, Y)` |
| 5 | `$20` | below right: `(X+3, Y)` |

Bits 0-3 form `ObjectCollisionResponseMask` and select the 16-entry collision
handler table. For example, mask `$03` means both upper probes are solid and
uses the ceiling response; mask `$0C` means both lower probes are solid and
uses the floor response. Bits 4-5 are the immediately lower support probes;
enemy forward-path logic selects left or right according to facing, and the
mask-0/F response tests them together through `ObjectCollisionBelowMask`.

The mask records RoomMap sign-bit solidity, not tile identity. Its geometry is
therefore independent of the low-six-bit tile catalog still being researched.

---

## Per-frame object update pipeline

The NMI gameplay path calls `UpdateActiveObjects` at `$863C` once per serviced
frame. Four adjacent source modules own the complete `$863C-$87DF` pipeline.

### Record traversal and definition changes

`UpdateActiveObjects` walks all 21 `$14`-byte object records from index 20 down
to zero through `ObjectRecordPointerLowTable` and
`ObjectRecordPointerHighTable`. Records whose state byte 0 is below `$C0` are
skipped.

For active records, byte 1 is compared with cached byte 2 and action byte 3 is
compared with cached byte 4. A change calls
`LoadObjectMotionAndAnimationDefinition`; otherwise the existing definition
remains active. Each record then passes through:

```text
UpdateObjectMotionAndCollision
  -> fixed-point motion integration
  -> six-cell RoomMap collision sampling
DispatchObjectCollisionResponse
AdvanceObjectAnimation
```

After the sweep, a nonzero low nibble in Dana's collision mask clears gameplay
frame counter `$20`. The response-mask geometry is fully mapped in
`docs/object_system.md#gameplay-object-record-layout`; the response dispatcher is documented in
`docs/object_system.md#object-collision-response-dispatcher`.

### Fixed-point motion

`UpdateObjectMotionAndCollision` starts at `$8689`. Object bytes 5-7 form
signed Y motion, fractional Y, and integer Y; bytes 8-10 are the corresponding
X fields. The routine applies the original signed Y adjustment, sign-extends
both axis deltas, and adds them through the fractional byte into the integer
coordinate.

The code falls directly from segment `PRG_OBJECT_MOTION` into
`SampleObjectRoomMapCollision` at `$86D4`; the callable operation returns only
after collision sampling at `$8788`.

### RoomMap collision sampling

The sampler derives vertical probes from integer Y offsets `-13`, `-1`, and
the following row, and horizontal probes around integer X offsets `-4` and
`+3`. Nibble-boundary tests choose which neighboring packed RoomMap indices
are used. Six selected cells are tested by sign: a negative RoomMap byte sets
the current collision bit.

Those six results are shifted into object byte 11. This proves byte 11 is the
per-frame RoomMap collision mask. Bits 0-5 are upper-left, upper-right, lower-
right, lower-left, below-left, and below-right respectively. Assembly
constants lock the four response bits and the two below-support bits.

### Animation sequencing

`AdvanceObjectAnimation` at `$8789` decrements byte 12. On underflow it reloads
the counter from byte 13, steps packed phase byte 14 by `$F0`, and normalizes a
wrapped low nibble into both halves. The phase calculation produces
`frame_index * 3`, which indexes the animation pointer in bytes 15-16.

The selected three-byte frame is copied into bytes 17-19: two sprite tile
values and their flags. This is the per-frame consumer of the definition
loaded by `LoadObjectMotionAndAnimationDefinition`.

---

## Object motion and animation definitions

`LoadObjectMotionAndAnimationDefinition` owns CPU `$8AC0-$8B50`. The active
object loop calls it when either the object type/variant byte or action byte
changes.

Calling convention:

```text
TempPointer08 = current $14-byte object record
X             = object byte 1, type plus low-two-bit variant
A             = object byte 3, current action
Y             = $04, cached-action record offset
```

The entry caches the action in byte 4, selects new signed motion values for
bytes 5 and 8, resets animation counter byte 12, and fills animation delay,
phase, and pointer bytes 13-16. A motion-table value of `$40` means that the
corresponding component is preserved rather than overwritten.

### Motion selection

`ObjectMotionSelectorPointers` at USA `$D9D3` / Europe `$D953` contains 33
little-endian pointers.
The loader groups byte-1 values in sets of four by calculating
`(type >> 2) * 2`, then indexes the selected table by the action byte. A
nonnegative selector directly indexes paired Y/X values at `$DB99`.

A negative selector is a room-state mask. The loader intersects it with
`RoomStateFlags`, combines the result with the type's low-two-bit variant, and
uses that value for a second lookup in the same selector table. This accounts
for room-dependent motion without changing the object action.

`make object-motion-audit` locks the frozen USA layout before source
extraction: 33 object-type pointers, 20 unique selector groups containing 388
action bytes, and 35 paired Y/X motion vectors. It also rejects any nonnegative
selector outside the vector table and checks independent SHA-1 values for all
three regions. Its encoder additionally reconstructs all 524 bytes from the
decoded pointer, selector, and vector records and compares them byte-for-byte.
`make object-motion-report` emits the decoded JSON view from the built ROM
using `config/validation/object_motion.json`.

Source Reconstruction 2.0 adds the independent
`config/validation/object_motion_europe.json` contract. The 66-byte pointer table and
388-byte selector region move `$80` bytes earlier; selectors are semantically
and byte-identical after relocation, while all 35 paired PAL vectors are
profile-selected values with their own hash. Run
`make object-motion-profile-audits` to decode, validate exact coverage, and
round-trip all 524 bytes from both source-built ROMs.

The complete `$D9D3-$DBDE` range is now source-owned in the 523-line
`src/data/objects/motion.asm`. Its macros distinguish direct vector indices
from negative room-state selectors, and its pointer table uses the same
type-group symbols as the selector payload.

### Animation selection

`ObjectAnimationDescriptorPointers` at USA `$D0E8-$D129` / Europe
`$D068-$D0A9` is a source-owned, parallel 33-pointer table. Its first target at
USA `$D12A` / Europe `$D0AA` also proves the table's end boundary independently
of its consumer's 33-type indexing contract.
Each action selects a four-byte descriptor:

```text
byte 0    initial packed animation phase
byte 1    delay * 2 plus variant-pointer flag in bit 0
bytes 2-3 animation data pointer, or a pointer to variant pointers
```

When byte 1 bit 0 is set, the low two type bits choose one of four
little-endian animation pointers. Otherwise bytes 2-3 are used directly.
The named per-frame stage `AdvanceObjectAnimation` at `$8789` consumes record
bytes 12-16 as a counter, reload delay, packed phase, and animation-data
pointer, confirming the output contract independently of the table layout.
See `docs/object_system.md#per-frame-object-update-pipeline`.

The complete animation descriptor and frame payload is source-owned in
`src/data/objects/animations.asm`; the adjacent motion pointer, selector, and
vector families are source-owned in `src/data/objects/motion.asm`.

`make object-animation-audit` independently locks the reviewed data layout:

- 33 object-type pointers selecting 18 unique descriptor groups;
- 340 four-byte action descriptors, 44 of which select a variant table;
- four overlapping four-pointer variant selectors in two eight-pointer tables;
- 126 referenced animation sequences covering 275 three-byte frame records;
- exact hashes for the pointer, definition, and frame-data regions;
- byte-for-byte reconstruction of all 2,283 bytes from decoded records.

The corresponding JSON report is available through
`make object-animation-report`. The manifest lives at
`config/validation/object_animations.json`; it records structural facts, not speculative
enemy names.

Source Reconstruction 2.0 gives the relocated PAL layout its own reviewed
`config/validation/object_animations_europe.json` contract. The entire descriptor and
frame region moves `$80` bytes earlier. Relocated type, descriptor, variant,
and frame pointers therefore give the pointer and definition regions distinct
hashes, while the 825 raw frame bytes remain identical. Run
`make object-animation-profile-audits` to decode and reconstruct all 2,283
bytes independently from both source-built ROMs.

---

## Object collision response dispatcher

The complete `$87E0-$8A61` range turns the collision mask produced by
`SampleObjectRoomMapCollision` into coordinate, motion, and action changes.

`DispatchObjectCollisionResponse` first requires object state byte 0 to be at
least `$E0`. It caches action byte 3 and collision byte 11, doubles the low
nibble, and tail-dispatches through the 16-entry
`ObjectCollisionHandlerTable` at `$8806`.

| Mask | Handler address | Structure |
| ---: | ---: | --- |
| `$0/$F` | `$8826` | shared no/fully-surrounded response |
| `$1` | `$8843` | choose the smaller Y/X correction |
| `$2` | `$88A5` | mirrored X correction or shared Y path |
| `$3` | `$8982` | `$...D` Y clamp and action transition |
| `$4` | `$8949` | X correction or shared lower-Y path |
| `$5` | `$89F6` | Y-position test, then mask-7 response |
| `$6` | `$89D6` | right-surface X clamp |
| `$7` | `$89FE` | `$...D` Y plus right-surface X clamp |
| `$8` | `$88E1` | choose X correction or lower-Y response |
| `$9` | `$89B8` | left-surface X clamp |
| `$A` | `$8A0B` | Y-position test, then mask-B response |
| `$B` | `$8A13` | `$...D` Y plus left-surface X clamp |
| `$C` | `$8990` | `$...0` Y clamp and action/motion response |
| `$D` | `$8A20` | `$...0` Y plus left-surface X clamp |
| `$E` | `$8A2A` | `$...0` Y plus right-surface X clamp |

The mask-5/7 and mask-A/B pairs intentionally use shared entry tails rather
than duplicate code. The table is reconstructed with `.addr` expressions, so
these relationships are explicit and checked by byte-identical assembly.

The handlers clear the appropriate fractional/motion fields, preserve a
motion sign where required, and select new action values from `$04-$09` or
`$18-$1B`. Their exact coordinate postconditions are now source-visible. The
low-nibble bits mean upper-left, upper-right, lower-right, and lower-left;
`docs/object_system.md#gameplay-object-record-layout` derives the complete six-bit sample order. Handler
names retain mask values because several combinations intentionally choose
between axes according to sub-tile penetration.

`ObjectClampYCoordinateToThirteenInset` at `$8A41` is the shared lower-inset
helper. It maps every integer Y input to low nibble `$D`, clears Y fraction
byte 6, and reduces signed Y motion byte 5 to `$00` or `$80`.

---

## Non-Dana object pointer helper

`src/game/objects/update_pipeline.asm` owns CPU `$CA4F-$CA59`. Bisqwit's map identifies
the entry as `LoadObjectPointer`. It resolves a zero-based index in `X` through
the split pointer planes at `$B469` and `$B47E` and writes the selected address
to `TempPointer00`.

Calling convention:

```text
input:      X = non-Dana object index, 0..19
output:     TempPointer00 = address of object record X + 1
preserved:  X, Y
clobbered:  A, TempPointer00
```

The plus-one table bases are source-owned as `NonDanaObjectPointerLowTable`
and `NonDanaObjectPointerHighTable`. Index 0 therefore selects
`MagicSparkObject`, followed by the fireball, auxiliary object, and seventeen
enemy records; Dana at complete-table index 0 is deliberately excluded.

Both helper callers iterate `X` from `$13` down to zero, covering all twenty
non-Dana object records. Eight other code paths access the same plus-one table
bases directly and now use the same semantic aliases.

---

## Non-Dana object-pool maintenance

Two routines surrounding `LoadObjectPointer` sweep all twenty object records
after Dana. Both initialize `X` to `$13`, use the pointer helper, decrement to
zero, and therefore cover the magic spark, fireball, auxiliary object, and all
seventeen enemy records exactly once.

`SetActiveNonDanaObjectState` owns `$CA3C-$CA4E`. For each record it tests byte
0 and replaces that byte with scratch value `$02` only when the old value is
negative. Nonnegative/inactive records are left unchanged. Four callers use
replacement values `$00`, `$80`, or `$82`; the exact meanings of those active
state values remain tied to their surrounding transitions.

`DeactivateAllNonDanaObjects` owns `$CA5A-$CA6D`. It unconditionally clears
byte 0 and writes the offscreen sentinel `$F8` to byte 7 in every non-Dana
record. Its two callers use it during whole-room or scene teardown.

The nine bytes at `$CA33-$CA3B` immediately before the first routine have no
control-flow references and remain preservation data. They are deliberately
not absorbed into either code module until their format and owner are proven.

---

## Object X-coordinate left-surface clamp

`src/game/objects/collision_and_motion.asm` owns CPU `$8A7F-$8AA3`. Its three callers
operate on the object selected by `TempPointer08` during collision handling.

Calling convention:

```text
input:      TempPointer08 = object record
output:     object byte 10 has low nibble $4
            object bytes 9 and 8 are zero
preserved:  none of A, X, Y
clobbered:  A, X, Y, CoordinateClampDelta
```

The arithmetic computes the positive adjustment needed to place X at the
`...4` inset of a 16-pixel cell. Exhaustive evaluation of all 256 input bytes
shows that results always have low nibble `$4`; inputs already at `$4` remain
unchanged, while larger low nibbles advance into the following cell. Combined
with clearing the X fraction/motion fields, this is the response to a surface
on the object's left. The directional name is high-confidence; the byte-level
postcondition is confirmed directly by the instruction sequence.

The complementary right-surface routine at `$8AA4` shares
`ClearObjectXMotion`. Because ca65 cannot encode a relative branch relocation
between the two linker segments, that branch remains explicitly encoded as
`.byte $D0, $DD` with an explanatory source comment. Byte identity and the
target label address are both audited.

---

## Object X-coordinate right-surface clamp

`ObjectClampXCoordinateToRightSurface` owns CPU `$8AA4-$8ABF`. Its three
callers use the object record selected by `TempPointer08` during collision
response.

Calling convention:

```text
input:      TempPointer08 = object record
output:     object byte 10 has low nibble $C
            object bytes 9 and 8 are zero
preserved:  none of A, X, Y
clobbered:  A, X, Y, CoordinateClampDelta
```

The arithmetic subtracts `(X + 4) & $0F` from the original coordinate.
Exhaustive evaluation of all 256 input values therefore produces the `$...C`
inset of a 16-pixel cell. The final `DEY` leaves zero clear, so the original
`BNE` always reaches the shared `ClearObjectXMotion` tail at `$8A9D`; that tail
clears the motion and fractional fields and returns.

Together with the `$...4` result of `ObjectClampXCoordinateToLeftSurface`, the
two routines establish the object's horizontal collision insets on opposite
sides of a tile boundary.

---

## Object Y-coordinate surface clamp

`src/game/objects/collision_and_motion.asm` owns CPU `$8A62-$8A7E`. Bisqwit's map names its
single entry `ObjectClampYCoordinateToSurface`; all three static callers now
use that symbol.

Calling convention:

```text
input:      TempPointer08 = object record
output:     object byte 7 aligned down to a multiple of 16
            object byte 5 reduced to its previous sign bit ($00 or $80)
preserved:  none of A, X, Y
clobbered:  A, X, Y, TempPointer0A
```

Byte 7 is the integer Y coordinate shared by the `$14`-byte object layout. The
routine saves its low nibble in scratch byte `$0A` and subtracts it, snapping
the coordinate to the top of the containing 16-pixel row. It then rotates the
old high bit of signed Y-motion byte 5 through carry into a fresh zero
accumulator, retaining only `$00` or `$80`. The adjacent byte 6 is the Y
fraction consumed by the shared movement integrator.

The three callers combine the clamp with the now-reconstructed left/right
horizontal surface helpers documented in `docs/object_system.md#object-x-coordinate-left-surface-clamp` and
`docs/object_system.md#object-x-coordinate-right-surface-clamp`.
Collision responses also use `ObjectClampYCoordinateToThirteenInset`, which
aligns the same integer Y field to low nibble `$D` while clearing byte 6 and
preserving only the sign of motion byte 5.
