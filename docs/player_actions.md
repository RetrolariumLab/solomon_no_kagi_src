# Player actions

This guide connects Dana action threads and state encoding to coordinate helpers and inline parameter dispatch.


---

## Dana action threads

`src/game/dana_actions.asm` owns `$9A6D-$9C51`, three cooperative action
entries selected from context 1's scheduler table and their shared cleanup
path.

| Scheduler selector | Entry | Behavior |
| ---: | --- | --- |
| 1 | `CastOrRemoveBlock` (`$9B7A`) | target the cell in front of Dana and create or remove a block |
| 2 | `HandleDanaHeadCollision` (`$9A6D`) | inspect the two cells above Dana after a head collision |
| 3 | `CastFireballFromInventory` (`$9B05`) | consume the next two-bit fireball slot and activate the projectile |

The pointer table stores return addresses because `StartThread` installs each
value as a synthetic RTS frame. The source therefore emits each pointer as
`.addr <entry> - 1`; `make scheduler-audit` verifies the resulting addresses
and selector mapping.

### Head collision

The head-collision entry samples Dana's Y minus 8 and both map cells crossed by
the sprite width. It derives their packed `RoomMap` indices through
`ConvertPixelCoordinatesToMapIndex`, uses the sign bits of both tile values to
choose the contacted cell, and rejects the `$F8-$FF` boundary class.

For values below `$C8`, the routine sets tile bit 6 and requests a cell redraw.
The `$C8-$F7` class instead initializes the magic-spark record through
`ApplyMapTileInteractionToObject`. Both paths wait eight ticks on the standard
gameplay-delay counter before common action cleanup.

### Fireball cast

Fireball inventory is eight two-bit values packed into `$042E-$042F`. The cast
entry shifts that pair twice, moving the consumed value into the accumulator:
zero cancels the spawn, while the two nonzero encodings select the fireball
configuration written to the record at `$05A7`. Position and facing are
derived from Dana's saved action pose. After activation, the action calls
`BuildFireballInventoryDisplayUpdate` to redraw both packed-inventory HUD
rows. See `docs/item_system.md#fireball-inventory-display`.

### Block magic

The block entry computes a target cell from Dana's saved pose, direction, and
integer coordinates. A negative map value takes the removal path at `$9C02`;
a nonnegative value calls `TryCreateBlockAtMapCell`. Both operations use the
magic-spark object at `$0593`, wait on `GameplayDelayCounter`, and request
map-cell updates through `BuildAndPublishRoomMapCellUpdate`.

The NMI request path snapshots `ObjectActionOffset` and `ObjectYMotionOffset`
as `DanaSavedAction` and `DanaSavedYMotion` at `$002A-$002B`. The cast entry
stores the source action's facing bit as `FireballDirectionIndex` at `$0430`.
It also stores 2 for source actions `$10-$17` or 3 for airborne actions
`$18-$1B` in `FireballAlternateDirectionIndex` at `$0431`. These are the up
and down alternatives used by the shared path-selection collision handlers.

The shared `$9C12` continuation restores Dana's action state, horizontal
position, and byte-5 Y motion. The final `$9C3A` path filters the cached
controller bits, deactivates the magic spark, and stops scheduler context 1.
The action pairs and casting transformations are documented in
`docs/player_actions.md#dana-action-state-encoding`.

---

## Dana action-state encoding

Dana's object record uses the shared `ObjectActionOffset` byte at `$0582` as
an action-state selector. The NMI controller dispatcher divides values
`$00-$1B` by four and selects one of seven handlers; the motion and animation
loaders use the original byte as a direct table index.

Bit 0 is the facing direction throughout the controllable states. Even values
face right and odd values face left. This follows from two independent paths:
room loading chooses `$14/$15` from the high bit of Dana's initial X position,
while right/left controller input selects `$14/$15` directly. Collision and
transition paths preserve the same bit when changing action pairs.

The statically established action pairs are:

| Values | Source or transition | Motion/control role |
| ---: | --- | --- |
| `$00/$01` | Up input from a grounded state | five-tick jump startup |
| `$02/$03` | no direct producer found | reserved members of startup group 0 |
| `$04/$05` | upper-surface collision | ceiling-contact delay; queues head-collision code `$12` |
| `$06/$07` | lower-surface collision | landing recovery before returning to `$16/$17` |
| `$08/$09` | horizontal-surface collision | wall-contact recovery |
| `$0A/$0B` | no direct producer found | reserved members of collision group 2 |
| `$0C/$0D` | startup `$00/$01` after five ticks | jump ascent with Y motion `$C3` |
| `$0E/$0F` | no direct producer found | reserved members of no-control group 3 |
| `$10/$11` | Down plus horizontal input | crouched horizontal movement |
| `$12/$13` | Down without horizontal input | crouched idle |
| `$14/$15` | horizontal input | normal horizontal movement |
| `$16/$17` | no directional input | standing idle |
| `$18/$19` | airborne horizontal input | preserve Y motion and apply horizontal motion |
| `$1A/$1B` | airborne without horizontal input | preserve Y motion without horizontal motion |
| `$1C/$1D` | A/B request from `$14-$1B` | regular casting pose while context 1 owns the action |
| `$1E/$1F` | A/B request from `$10-$13` | crouched casting pose while context 1 owns the action |
| `$20/$21` | Dana-death transition | facing-preserving death fall |
| `$22/$23` | death fall reaches Y `$D1` | final death presentation |

The three unused pairs are still valid table entries, but no reconstructed
writer selects them. They remain described structurally rather than assigned
gameplay names.

### Y motion and casting scratch

Object byte 5 at `$0584` is Dana's signed Y-motion field. The shared fixed-
point integrator updates it and carries its scaled delta through byte 6 into
integer Y byte 7. Surface collision paths reduce it to a sign-only `$00` or
`$80`. Cooperative A/B actions save and restore it through `DanaSavedYMotion`;
the death path explicitly writes `$C3`. This also corrects the former local
death constants, which had the state `$C0` and Y-motion `$C3` names reversed.

`FireballDirectionIndex` at `$0430` is an exact four-way index: 0 right, 1
left, 2 up, and 3 down. NMI uses it to select the matching signed coordinate
delta and copies it into the fireball action field before collision dispatch.
The normal cast producer currently writes only 0 or 1 because Dana's source
action contributes its facing bit.

`FireballAlternateDirectionIndex` at `$0431` receives 2 (up) for source
actions `$10-$17` and 3 (down) for airborne source actions `$18-$1B`. During
fireball collision handling, `EnemyAiPointer` is temporarily aimed at
`FireballActive`, making `$0430/$0431` offsets 6/7 of a synthetic AI record.
The shared path handlers read and update them as current and alternate
directions when selecting a route around solid RoomMap cells.

---

## Room-map coordinate conversion

`src/game/objects/update_pipeline.asm` owns CPU `$918A-$91B8`. Bisqwit's map
independently names both entry points. Together they define the bridge between
pixel coordinates and the packed byte used to index the 16-column `RoomMap`.

The shared zero-page contract is:

| Value | Address |
| --- | --- |
| pixel Y / packed map index | `$04` |
| pixel X | `$05` |

`ConvertPixelCoordinatesToMapIndex` applies:

```text
index = ((Y - $10) & $F0) | ((X - $08) >> 4)
```

It returns the index in `A`, `X`, and `$04`. The inverse
`ConvertMapIndexToPixelCoordinates` expands the high and low nibbles:

```text
Y = (index & $F0) + $10
X = (index & $0F) * 16 + $08
```

For example, index `$B5` maps to pixel Y=`$C0`, X=`$58`; the upper and lower
nibbles therefore represent logical row 11 and column 5. The `$10/$08` origin
places gameplay points within each 16-pixel logical cell rather than at the
PPU nametable origin.

All 31 static calls now use the semantic symbols. This module describes only
coordinate packing; tile meaning and collision state remain owned by the room
pipeline.

---

## Scaled coordinate deltas

`src/game/objects/update_pipeline.asm` owns CPU `$C364-$C385`. Five callers use the
same scratch-register contract when seeding room-entry, room-clear, enemy, and
other transition motion.

```text
input:
  $02 = origin Y
  $03 = origin X
  $04 = target Y
  $05 = target X

output:
  $02-$03 = signed 16-bit (target Y - origin Y) * 4, low/high
  $04-$05 = signed 16-bit (target X - origin X) * 4, low/high
```

`BuildScaledCoordinateDeltas` processes X then Y. For each eight-bit
difference, Y becomes `$00` or `$FF` according to subtraction borrow and is
used as the sign-extension byte. Two `ASL`/`ROL` pairs multiply the signed
16-bit value by four. The final two-register swap changes the temporary
interleaved layout into the conventional Y-low/Y-high/X-low/X-high order.

The arithmetic contract is fully determined by instruction flow and all five
call sites. The later consumer's physical unit (velocity, animation step, or
fixed-point increment) remains context-specific and is not baked into the
symbol name.

---

## Inline appendix dispatcher

`src/system/thread_runtime.asm` owns CPU `$8EA9-$8EBF`. Bisqwit's map names
the entry `JumpWithParams` and classifies it as a jump-table routine whose
parameters are appended to the caller.

Callers use this layout:

```asm
    ; A = zero-based selector
    JSR JumpWithParams
    .addr Handler0, Handler1, Handler2
```

The 6502 `JSR` leaves the address of its final operand byte on the hardware
stack. `JumpWithParams` doubles `A`, removes that return address, and reads the
selected little-endian word at `return + 1 + 2*A`. It then jumps indirectly to
the selected handler through `TempPointer00`.

The removed return address is deliberately not restored. A handler ending in
`RTS` therefore consumes the caller's next older stack frame and returns from
the dispatching routine as a whole. Bytes after the `JSR` are data, never
fallthrough instructions. The routine clobbers `A`, `Y`, and
`TempPointer00`; `X` is unchanged.

Eleven static call sites use this ABI. The 28-entry enemy AI appendix is
separately decoded and checked by `make enemy-ai-audit`; other appendices will
enter equivalent manifests as their surrounding subsystems are reconstructed.
