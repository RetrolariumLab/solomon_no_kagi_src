# Room block-plane decoding

`InitializeRoomBlockMap` at `$99F2-$9A6C` initializes the runtime map and
expands the current room's two fixed block planes.

## Runtime map

RoomMap is 224 bytes arranged as 16x14 cells. Initialization fills it with
tile `$10`, then overwrites the first and last 16-cell rows with sentinel
`$F8`. The 16x12 playable area therefore occupies indices `$10-$CF`. These
relationships are shared as `RoomMapWidth`, `RoomMapHeight`,
`RoomMapPlayableHeight`, and the playable-boundary constants in
`src/memory/ram.inc`; assembly assertions pin the resulting `$E0/$10/$CF`
layout.

The two block planes expand to `$90` and `$F8`. In the shared byte contract,
the former is `RoomMapSolidBit | $10`; the latter begins the immutable tile
range. See `docs/room_map_tiles.md` for the collision and rendering classes.

## ROM addressing

Each room has 48 consecutive bytes beginning at CPU `$E02C`:

```text
record = RoomBlockData + CurrentRoomIndex * 48
```

The first 24 bytes are the brown/breakable bitplane; the second 24 are the
white/solid bitplane.

`RoomBlockData` and all 53 records are source-owned in the 485-line
`src/data/rooms/blocks.asm`. Each room is shown as three eight-byte rows per
brown/breakable plane followed by three per white/solid plane; the file can be
reproduced with `scripts/room_data.py --source-blocks`.

## Expansion

`ExpandRoomMapBitplane` accepts the source pointer in `RoomBlockDataPointer`
and the output tile in `A`. It traverses source bytes 23 down to 0, rotates
each byte right eight times, and writes set bits to RoomMap indices `$CF` down
to `$10`.

The initializer expands brown tile `$90` first and white tile `$F8` second.
When both source planes contain a bit, the later white write wins. Two other
gameplay callers reuse the same helper with their own pointers and tile values.
