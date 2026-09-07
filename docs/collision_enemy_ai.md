# Collision-driven enemy AI

`src/game/enemies/collision_ai.asm` owns CPU `$AD37-$AF5B`. It contains the
shared target for type groups `$1C-$37` and the shared target for `$5C-$63`,
with both action tables expressed as inline `.addr` data.

`SampleCurrentEnemyRoomMapCollision` probes four cells around the current
enemy coordinates and packs each tile's high bit into a four-bit mask. The
`$1C-$37` actions use that mask to interact with a non-solid RoomMap cell,
choose a new action, or reserve a linked enemy slot. Their lifetime path also
retires linked slots through `ClearLinkedEnemySlots`.

The `$5C-$63` family switches between forward-map tests, collision-direction
tests, linked-slot creation, and phase thresholds. Its action state preserves
the low direction bit while moving among the `$12`, `$14`, and `$16` action
groups. Several shared helpers later in PRG still retain neutral addresses
until the final enemy-AI range is reconstructed.

The five-byte table at `$AE19` deliberately overlaps the Y and X probe-offset
views by one byte. Keeping it as one table documents that storage property and
reproduces all four indexed reads. The complete segment is 549 bytes and is
byte-identical to the original PRG.
