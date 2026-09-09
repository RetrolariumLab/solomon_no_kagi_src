# Room data pipeline

This guide follows encoded room blocks, items, enemies, tiles, and buffered map updates into the rendered room.


---

## Room block-plane decoding

`InitializeRoomBlockMap` at `$99F2-$9A6C` initializes the runtime map and
expands the current room's two fixed block planes.

### Runtime map

RoomMap is 224 bytes arranged as 16x14 cells. Initialization fills it with
tile `$10`, then overwrites the first and last 16-cell rows with sentinel
`$F8`. The 16x12 playable area therefore occupies indices `$10-$CF`. These
relationships are shared as `RoomMapWidth`, `RoomMapHeight`,
`RoomMapPlayableHeight`, and the playable-boundary constants in
`src/memory/ram.inc`; assembly assertions pin the resulting `$E0/$10/$CF`
layout.

The two block planes expand to `$90` and `$F8`. In the shared byte contract,
the former is `RoomMapSolidBit | $10`; the latter begins the immutable tile
range. See `docs/room_data_pipeline.md#roommap-tile-byte-contract` for the collision and rendering classes.

### ROM addressing

Each room has 48 consecutive bytes beginning at CPU `$E02C`:

```text
record = RoomBlockData + CurrentRoomIndex * 48
```

The first 24 bytes are the brown/breakable bitplane; the second 24 are the
white/solid bitplane.

`RoomBlockData` and all 53 records are source-owned in the 485-line
`src/data/rooms/blocks.asm`. Each room is shown as three eight-byte rows per
brown/breakable plane followed by three per white/solid plane; the file can be
reproduced with `scripts/authoring/room_data.py --source-blocks`.

### Expansion

`ExpandRoomMapBitplane` accepts the source pointer in `RoomBlockDataPointer`
and the output tile in `A`. It traverses source bytes 23 down to 0, rotates
each byte right eight times, and writes set bits to RoomMap indices `$CF` down
to `$10`.

The initializer expands brown tile `$90` first and white tile `$F8` second.
When both source planes contain a bit, the later white write wins. Two other
gameplay callers reuse the same helper with their own pointers and tile values.

---

## Room item and metadata decoding

`LoadRoomItemsAndMetadata` at `$97C8-$9952` is the runtime consumer of the
ten-byte room item header and compressed item stream documented in
`docs/data_formats.md`.

Its complete 53-entry split pointer table and source records are reconstructed
at `$EA1C-$EFC3` in `src/data/rooms/items.asm`; the decoder now resolves the
table through symbols instead of fixed addresses.

It performs four stages:

1. Resolves two Demon Mirror schedule pointers and two enemy-set pointers from
   the first four header bytes.
2. Initializes timer rate, door/key tiles, and both Demon Mirror positions.
3. Decodes normal `(type, position)` records and `$C0-$DF` repeated records
   directly into `RoomMap`.
4. Decodes the terminator's CHR bank and optional constellation state.

Room index `$32` has an additional table-driven randomized placement pass:
16 item types are written at positions selected from a wrapping 32-entry list
whose starting index comes from `AdvanceRandomState` at `$C1E3`.

That shared routine keeps a 15-bit state at `$0448-$0449`. A changed Demon
Mirror spawn state reseeds it from the low spawn-timer byte and the first
gameplay frame counter. Two eight-step shift/add rounds then advance the state;
the low byte shifted right is returned to callers. Room decoding masks that
result to select one of the special room's 32 starting positions.

### Supporting tables

| Range | Meaning |
| --- | --- |
| `$9953-$99B2` | four 24-byte constellation tile patterns |
| `$99B3-$99BE` | twelve two-bit constellation modifiers |
| `$99BF-$99C2` | four timer decrement speeds |
| `$99C2-$99E1` | 32 special-room item positions |
| `$99E2-$99F1` | 16 special-room item types |

The timer and position tables deliberately share byte `$99C2`. The ca65 data
module emits that byte once and asserts the overlapping layout.

The decoder's source labels describe only proven storage and control flow.
The semantic meaning of individual item type values remains governed by the
lossless room codec rather than guessed names.

---

## Room enemy loading

`LoadRoomEnemies` at `$961B-$9660` turns the current room's compressed enemy
record into live runtime slots. `CurrentRoomIndex` selects one of 53 split
pointers at `$DCEC/$DD21`; the resulting stream uses the format already
round-tripped by `scripts/authoring/room_data.py`.

Both pointer halves and all 53 streams are source-owned in the 552-line
`src/data/rooms/enemies.asm`. Each record is expressed with macros for the
encoded lifetime, `(enemy_type, map_position)` pair, and terminator; the source
can be reproduced with `scripts/authoring/room_data.py --source-enemies`.

The first byte is split into `EnemySpawnLifetimeThresholdLo` (`bits 7..5`) and
`EnemySpawnLifetimeThresholdHi` (`bits 4..0`). `ApplyEnemyLifetimeThreshold`
subtracts these from AI-record bytes 2-3 as a low/high threshold pair. Each
following record contains an enemy type and packed 16-column map position;
type zero terminates the stream.

For every record, the loader:

1. asks `FindFreeEnemySlotIndex` for an inactive AI record;
2. marks that AI record active with bit 7;
3. converts the packed map position to pixel Y/X;
4. calls `InitializeEnemy` for the parallel records;
5. calls `ConfigureEnemyType` with the decoded type.

The loader assumes room data never exceeds the 17-slot enemy pool. That
invariant is independently exercised by the all-room decoder and pointer
audits in `make check`.

---

## RoomMap tile byte contract

Each of the 224 `RoomMap` cells stores one byte. The room decoder, collision
samplers, full renderer, item dispatcher, and block-magic paths establish a
shared structural encoding even where a creature or hazard name is not yet
known.

### Bit fields and ranges

`RoomMapTileIdentityMask` (`$3F`) preserves the low-six-bit identity.
`RoomMapDecorationBit` (`$40`) and `RoomMapSolidBit` (`$80`) are independent
class bits until the immutable range begins at `$F8`.

| Runtime value | Collision | Initial full-room pattern |
| ---: | --- | ---: |
| `$00-$3F` | passable | the value itself |
| `$40-$7F` | passable | `$10` |
| `$80-$F7` | solid | `$00` |
| `$F8-$FF` | solid and immutable to map interaction | `$03` |

`SampleObjectRoomMapCollision` and `BuildFireballRoomCollisionMask` test the
sign bit only, proving that `RoomMapSolidBit` is the collision bit. The
full-room renderer applies the four ranges above before indexing the 58-record
`RoomTilePatternTable`. Incremental redraws receive a logical pattern value
already selected by their caller.

### Interaction normalization

`ApplyMapTileInteractionToObject` leaves `$F8-$FF` unchanged. For every lower
value it stores `value & RoomMapTileIdentityMask` back into `RoomMap`. This
removes both class bits and exposes the underlying identity after a block or
concealment interaction. Its effect object retains the original byte long
enough to choose direction, coordinates, and action.

The fixed block planes make the encoding concrete:

- empty interior is `$10`;
- a brown/breakable block is `$90` (`RoomMapSolidBit | $10`);
- a white block and both boundary rows use immutable sentinel `$F8`.

The item decoder uses the same low-six-bit mask when deciding whether an
encoded item is ordinary or conditional. Key `$06`, open door `$07`, Demon
Mirror `$05`, hidden key `$46`, and embedded key `$86` all therefore share
this byte contract. The shared source constants build `$46/$86` from key
identity `$06` plus the decoration or solid bit.

### Identities written by room setup and scripts

These identities have both a producer and an independently described visual
in the bundled `skchain` reference:

| Identity | Source name | Producer or use |
| ---: | --- | --- |
| `$02` | `RoomMapClosedDoorIdentity` | initial closed door and ending-room door |
| `$04` | `RoomMapBatSymbolIdentity` | room 20 special bitplane |
| `$05` | `RoomMapDemonMirrorIdentity` | both room Demon Mirror positions |
| `$06` | `RoomMapKeyIdentity` | visible, hidden `$46`, or embedded `$86` key |
| `$07` | `RoomMapOpenDoorIdentity` | unlocked door |
| `$10` | `RoomMapEmptyIdentity` | empty interior and cleared item cell |
| `$20` | `RoomMapSolomonSealIdentity` | hidden Seal is encoded as `$60` |
| `$21` | `RoomMapSolomonPageIdentity` | Page of Time or Page of Space |
| `$22` | `RoomMapGoldenWingsIdentity` | five-room skip item |
| `$27` | `RoomMapBlueOpalIdentity` | room 30 special bitplane and score bonus |
| `$32` | `RoomMapTecmoBunnyRewardIdentity` | Bunny reward; score plus extra life |
| `$35` | `RoomMapDeferredDoorIdentity` | placeholder when header key position is zero |

The only stock rooms with a zero key position are internal room 48 (Princess)
and room 49 (Solomon ending). Their scripts replace the placeholder map state;
`$35` is therefore named for its loader role rather than the generic extra-life
classification that would apply if Dana collected it as an ordinary exposed
cell.

Special-room scripts also write the encoded structural values
`RoomMapBrownBlock` (`$90`), `RoomMapWhiteBlock` (`$F8`), and
`RoomMapHiddenSolomonSeal` (`$60`). These are combinations of the shared
identity and class constants, not additional low-six-bit identities.

### Exposed item identities

`ClassifyDanaMapTileInteraction` gives a complete range-level contract for
exposed values:

- below `$06`, `$10`, and `$38+` do not enter item dispatch;
- `$06-$22` safely select the 29-entry item handler table, with `$10`
  explicitly ignored;
- `$23-$24` pass the original range check but index beyond that table into the
  following code bytes; neither identity occurs in the stock room streams;
- `$25-$31` select score bonuses in five three-value groups;
- `$32-$37` award an extra life, with `$32` also awarding score.

The safe handler-backed identities are:

| Identity | Visual name | Gameplay effect |
| ---: | --- | --- |
| `$08` | blue diamond | 500 points |
| `$09` | blue fire jar | small fireball inventory |
| `$0A` | gold double coin | 2,000 points |
| `$0B` | orange jewels / red Tzo | extend fireball lifetime |
| `$0C` | orange diamond | 2,000 points |
| `$0D` | orange fire jar | large fireball inventory |
| `$0E` | scroll | increase inventory capacity |
| `$0F` | bell | queue a fairy |
| `$11` | half time bottle | double timer rate and remaining time |
| `$12` | full time bottle | quintuple timer rate and remaining time |
| `$13` | blue hourglass | set timer to 10,000 |
| `$14` | orange hourglass | set timer to 5,000 |
| `$15` | blue fire jar | small fireball inventory |
| `$16` | orange fire jar | large fireball inventory |
| `$17` | scroll | increase inventory capacity |
| `$18` | bell | queue a fairy |
| `$19` | explosion jar | retire all eligible enemies |
| `$1A` | blue key | intentionally no effect |
| `$1B` | blue jewels / blue Tzo | 200 points and fireball lifetime |
| `$1C-$1F` | four constellation shrines | set the constellation flag |
| `$20` | Solomon's Seal | record the room's Seal |
| `$21` | Egyptian head | record the room-selected Solomon page |
| `$22` | warp item | grant the Golden Wings room skip |

The visual names come from the checked-in `skchain` item catalog. The gameplay
column comes from this reconstruction's handler table and handler bodies;
where the two vocabularies differ, source symbols use the proven gameplay
effect.

### Block-magic and head-hit thresholds

`TryCreateBlockAtMapCell` treats `$08-$0F` as two modifiable four-item groups.
Repeated casts advance the low two identity bits and wrap within `$08-$0B` or
`$0C-$0F`. Values below `$08` reject the cast, `$10-$37` other than empty
`$10` remain unchanged, and `$38+` may be replaced by a new block after the
object-overlap checks.

An item embedded in a brown block starts with the solid bit set. Dana's first
head hit adds the decoration bit; handler threshold
`RoomMapRevealedEmbeddedItemMinimum` (`$C8`) therefore means both class bits
plus the first modifiable item identity `$08`. A later interaction removes the
two class bits and exposes the underlying item. `$C8` is a class threshold,
not another identity.

### Presentation-only pattern values

`RoomMapUpdateTile` is a logical pattern input to incremental rendering; it is
not always copied into `RoomMap`. The Tecmo Bunny script first publishes
pattern `$38`, later stores reward identity `$32` in `RoomMap`, and publishes
the final orange Bunny pattern `$39`. Likewise, head collision publishes
covered-block pattern `$01`, and key flight publishes door-transition pattern
`$34` without changing the stored identity at those points. These values must
not be interpreted as additional runtime map identities merely because they
index `RoomTilePatternTable`.

---

## Room map rendering

`DrawRoomMapToNametable` at `$9661-$96DB` renders the 16x12 playable interior
of `RoomMap` during room initialization. It first waits for the NMI-consumed
PPU update pointer to become idle, then enters the rendering-disabled direct
transfer guard.

The traversal counts packed map positions from `$D0` down through `$11`.
Positions whose low nibble is zero are sentinel-column boundaries; all other
positions map to RoomMap indices `$CF-$10`, exactly 192 cells. For each cell
the renderer reads its current nametable attribute byte, classifies the map
tile, and calls `BuildRoomCellUpdateBuffer` at `$9E21`.

Tile classification passed in `RoomRenderTileClass` is:

| RoomMap value | Class |
| --- | ---: |
| `$F8-$FF` | `$03` |
| `$80-$F7` | `$00` |
| `$40-$7F` | `$10` |
| `$00-$3F` | original value |

The builder emits address/data chunks into `PpuUpdateBuffer`. The renderer
immediately writes each two-byte address and each two-byte data pair to the
PPU, stopping on a zero data marker. After all cells it tail-calls
`EndDirectPpuTransfer`, restoring the normal rendering/NMI state.

The renderer shares `CalculateRoomMapAttributeAddressLow` with the cooperative
cell-update producer. Both helpers are now source-owned and their complete
contracts are documented in `docs/room_data_pipeline.md#buffered-roommap-cell-updates`.

---

## Buffered RoomMap cell updates

`BuildAndPublishRoomMapCellUpdate` at `$9DD0-$9EDF` converts one logical
`RoomMap` change into a compact RAM-resident PPU update program. The producer
runs in a cooperative thread and coordinates with NMI because an attribute
byte must be read before one two-bit quadrant can be replaced.

### Input and synchronization

The public cooperative entry accepts:

```text
RoomMapUpdateIndex ($02) = packed 16-column map cell
RoomMapUpdateTile  ($03) = logical tile/class to render
```

It waits for `GameplayFlags` bit 2 and `PpuAttributeReadState` to become idle,
calculates the target attribute-table address low byte, stores it in
`PpuAttributeAddressOrValue`, and sets the request bit. NMI reads `$23xx`
through the buffered PPU port and replaces that byte with the value read from
VRAM. The producer yields until completion, captures the byte, clears the
request, and then waits for `PpuUpdateStreamPointer` to become idle.

`ServiceRoomMapAttributeReadRequest` at `$8B51` is the NMI half of the
protocol. A nonnegative state triggers one dummy and one effective read from
`PPU_DATA`, after which `$001C` contains the attribute byte and state `$0029`
becomes `$80`. While the request remains unacknowledged, later NMIs increment
the state; once the pre-increment value reaches `$A8`, NMI clears the request
bit. With no request active, the main NMI path resets the state to `$00`.

`BuildRoomCellUpdateBuffer` at `$9E21` is a second public entry used by the
initial direct room renderer. That caller has already read the attribute byte
and prepared the saved index/tile fields, so it bypasses the cooperative
handshake and enters directly at buffer construction.

### Tile and attribute selection

Ordinary tile graphics are the 58 source-owned four-byte records in
`RoomTilePatternTable` at `$D000 + tile*4`. A size assertion binds the table to
that record count. Tile `$10` can select one of six expanded constellation
records at `$0407` when the map index falls in either of the two three-cell
rows rooted at `ConstellationPosition`.

The initial full-room renderer first maps decorated, solid, and immutable
runtime byte classes to pattern indices `$10`, `$00`, and `$03`; values below
`$40` remain direct pattern indices. Incremental callers provide the already
selected logical pattern value. The complete byte-class contract is in
`docs/room_data_pipeline.md#roommap-tile-byte-contract`.

The first record byte carries two independent values: palette in bits 0-1 and
the top-left tile in bits 2-7. The next three bytes are the top-right,
bottom-left, and bottom-right tiles. `make room-data-audit` decodes those five
fields and re-encodes all 232 table bytes without retaining a raw first byte.

`CalculateRoomMapAttributeAddressLow` also returns a quadrant selector in
`RoomMapUpdatePpuAddressHigh` (`$05`). The builder rotates the existing
attribute byte by two bits per quadrant, replaces only the selected low two
bits from the tile pattern, and rotates the byte back.

### Emitted update program

The 15-byte program at `PpuUpdateBuffer` contains:

| Offset | Meaning |
| ---: | --- |
| 0-4 | literal two-byte write for the top tile row |
| 5-9 | literal two-byte write 32 PPU bytes later for the bottom tile row |
| 10-13 | literal one-byte write to `$23xx` for the updated attribute byte |
| 14 | zero stream terminator |

Both tile commands use control `$41`; the attribute command uses `$40`.
`PublishPpuUpdateBuffer` publishes the finished program to the existing NMI
stream interpreter.

The adjacent `$9EE0-$9F22` module contains the packed-cell to nametable-address
and attribute-address conversions. `$9F23-$9FFF` is 221 bytes of non-code
filler, independently classified by Bisqwit's map and now held in a dedicated
data module.
