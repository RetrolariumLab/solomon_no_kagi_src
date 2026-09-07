# Room-map object interactions

`src/game/rooms/map_interactions.asm` owns `$9C60-$9DB0`. It connects runtime
`RoomMap` cells, object-record initialization, and Dana's block magic. The
adjacent coordinate/object overlap predicate at `$9DB1-$9DCF` is separated
because it has a stable general-purpose calling contract.

## Applying a map tile to an object

`ApplyMapTileInteractionToObject` accepts:

- `A`: the current map tile;
- `Y` and `MapInteractionY` on entry: the packed map-cell index;
- `MapInteractionObjectPointer`: destination object record;
- `MapInteractionDirection`: direction bits used for negative tile classes.

Tiles below `$F8` have their upper two bits cleared in `RoomMap`. The packed
cell is converted to pixel coordinates, optionally offset according to the
tile sign and direction, and stored in object bytes 7 and 10. The common
header initializer writes state `$C6`, variant `$04`, sentinel `$FF` in byte
2, and a tile-dependent action byte. Nonnegative source tiles are then queued
for redraw through `BuildAndPublishRoomMapCellUpdate`.

The entry has six external callers. `HandleDanaHeadCollision` and
`RemoveBlockAtTarget` supply the magic-spark record. The four enemy paths are
`UpdateType1CTo37MapInteraction`, `AllocateSingleLinkedEnemy`,
`UpdateType0CTo0FMapInteraction`, and `ApplyForwardEnemyMapInteraction`.
Every call uses the semantic symbol and the shared zero-page aliases.

## Creating a block

`TryCreateBlockAtMapCell` receives the target cell in `MapInteractionY` and a
destination effect object through `MapInteractionObjectPointer`. For ordinary
empty/blockable tile classes it checks whether the target coordinate overlaps
the active fireball and then each of the seventeen enemy records.

The enemy scan advances by `$14` bytes. Its compact pointer update adds `$13`
with the carry returned by the no-overlap predicate, producing the full object
stride without a separate increment.

Depending on occupancy, the routine either:

- marks an overlapping enemy record;
- positions and initializes the effect record from the fireball or enemy;
- writes a new negative block value to `RoomMap`;
- advances the low two-bit variant of an existing `$08-$0F` tile.

## Shared object header initializer

`InitializeObjectStateHeader` at `$9D99` initializes object bytes 0 through 3
through `MapInteractionObjectPointer`:

```text
ObjectStateOffset      = MapInteractionY
ObjectTypeOffset       = MapInteractionX
ObjectCachedTypeOffset = $FF
ObjectActionOffset     = A, unless A is negative
```

Eleven static calls use this symbol: eight external call sites and three paths
inside this module. The scratch names reflect this calling convention; the
gameplay meaning of every possible byte value remains open until the individual
object behaviors are reconstructed.

## Coordinate/object overlap

`CheckCoordinateOverlapWithObject` starts with carry set. A nonnegative object
state returns immediately as no overlap. Active records are tested against
`MapInteractionX/MapInteractionY` using the integer X/Y fields at offsets 10
and 7. Carry clear denotes overlap inside the routine's asymmetric `$15` by
`$1D` comparison window; carry set denotes no overlap.
