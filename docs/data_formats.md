# Room data formats

All offsets below are within the 32 KiB PRG. Add 16 for offsets in a headered
iNES file. Runtime pointers address the same bytes at CPU `$8000-$FFFF`.

## Section map

| Section | PRG offset | Size / count |
| --- | ---: | ---: |
| RoomMap tile patterns | `$5000` | 58 x 4 bytes |
| Demon Mirror schedule pointers | `$5C00` | 16 split pointers |
| Demon Mirror enemy-set pointers | `$5C20` | 17 split pointers |
| Enemy stream pointers | `$5CEC` | 53 split pointers |
| Block planes | `$602C` | 53 x 48 bytes |
| Item stream pointers | `$6A1C` | 53 split pointers |

Pointer tables store all low bytes first and all high bytes second. A runtime
pointer is converted to a PRG offset by subtracting `$8000`.

## RoomMap tile patterns

The 58 records at CPU `$D000-$D0E7` map logical RoomMap values to one palette
and four pattern-table tiles. Each record occupies only four bytes because the
palette and top-left tile overlap:

```text
byte 0 bits 0-1 = attribute palette
byte 0 bits 2-7 = top-left tile bits 2-7
byte 1          = top-right tile
byte 2          = bottom-left tile
byte 3          = bottom-right tile
```

The consumer masks byte 0 with `$03` for the attribute quadrant and with
`$FC` for the top-left tile. The room-data codec splits those values into
independent semantic fields and recombines them, rejecting a top-left value
whose low bits would overlap the palette.

## Demon Mirror schedules and enemy sets

Each spawn schedule is eight bytes. Bytes 0-3 provide 32 initial MSB-first
trigger bits; bytes 4-7 provide the 32-bit looping half. The runtime derives
one phase every 64 NMI ticks and latches the looping half after the initial
phases have completed.

Enemy sets are variable-length byte streams. Values below `$90` are enemy
types. A control byte `$90+n` replaces that mirror's stream cursor with `n`,
allowing a suffix or the complete set to loop without a separate terminator.
The two mirrors keep independent cursors.

The exact consumer is reconstructed at `$A04C-$A15E`; see
`docs/demon_mirror_runtime.md`.

## Coordinates

One byte stores a grid coordinate:

```text
high nibble = y + 1
low nibble  = x
```

Thus `$B5` is `(5, 10)`. A zero high nibble represents `y = -1`, used to hide
metadata objects outside the visible room.

## Blocks

Each room has two 24-byte, 16x12 bitplanes: brown/breakable followed by
white/solid. Rows are stored top-to-bottom, two bytes per row, most-significant
bit first. If both planes contain a block at one position, the white block wins.

The runtime decoder at `$99F2-$9A6C` traverses source bytes and destination
cells in reverse order, rotating each byte right. This produces the same
top-to-bottom, MSB-first logical ordering while filling RoomMap indices
`$10-$CF`; indices `$00-$0F` and `$D0-$DF` are sentinel rows.

All 2,544 encoded bytes are source-owned in `src/data/rooms/blocks.asm` and can
be regenerated from a reviewed ROM with `scripts/room_data.py --source-blocks`.
The existing `make room-data-audit` check independently decodes and re-encodes
every bitplane.

## Enemy stream

The first byte is the Demonhead/Saramandor lifetime rotated right by three bits.
Rotate it left by three to decode. Remaining records are `(type, position)`
pairs terminated by type `$00`.

`LoadRoomEnemies` resolves the current room through the split tables at CPU
`$DCEC/$DD21`. It stores the packed lifetime threshold across `$0426-$0427`,
then allocates one runtime enemy slot per pair. The position byte is converted
to pixel coordinates before `InitializeEnemy` and `ConfigureEnemyType` fill
the parallel object and AI records.

The complete pointer tables and all streams through `$E02B` are symbolic ca65
source in `src/data/rooms/enemies.asm`. Its 53 stream labels replace raw ROM
addresses, while the existing round-trip codec remains the independent binary
contract.

## Item metadata and stream

Every item stream begins with ten bytes:

| Byte | Meaning |
| ---: | --- |
| 0 | mirror 2 spawn schedule |
| 1 | mirror 1 spawn schedule |
| 2 | mirror 2 enemy set |
| 3 | mirror 1 enemy set |
| 4 | key status plus time-decrease rate |
| 5 | door position |
| 6 | key position |
| 7 | player start position |
| 8 | mirror 1 position |
| 9 | mirror 2 position |

The schedule indices address 16 eight-byte records at `$DC42-$DCC1`. The enemy
set indices address 17 streams at `$DCC2-$DCEB`; bytes below `$90` are object
types and `$90+n` resets the reader offset to `n`. Both split pointer families
and their complete payloads are expressed symbolically in source.

Normal items are `(type, position)` pairs. `$C0-$DF` encode one repeated type:
`count = code - $C0 + 1`, followed by the type and `count` position bytes.
`$00` and `$E0-$EF` terminate the stream and encode the CHR bank. `$F0-$FB`
encode a constellation plus one position and also terminate the stream.
Terminator bits 2-3 select one of four 8 KiB CHR banks. For an ordinary
`$E0-$EF` terminator the low two bits survive the lossless codec but are not
consumed by the loader. For `$F0-$FB`, the complete low nibble selects one of
twelve constellation modifiers, so the zodiac and its CHR bank are coupled by
the original byte rather than stored as independent properties.

The runtime decoder is reconstructed at `$97C8-$9952`. Its supporting tables
at `$9953-$99F1` include four 24-byte constellation patterns, twelve low-bit
modifiers, four timer speeds, 32 special-room positions, and 16 special-room
item types. The fourth timer-speed byte intentionally overlaps the first
special-room position at `$99C2`.

The tested codec is `scripts/room_data.py`. Its JSON keeps raw type values and
the original item command grouping so that naming uncertainty or RLE expansion
does not corrupt the lossless structural result.

The 53-entry split pointer table at `$EA1C-$EA85` and every metadata/command
stream at `$EA86-$EFC3` are source-owned in `src/data/rooms/items.asm`. Named
macros preserve header, individual-item, repeated-item, constellation, and
terminator boundaries. The reviewed source can be regenerated with
`scripts/room_data.py --source-items`.

`make room-data-audit` decodes and re-encodes all 53 block-plane records,
enemy streams, item metadata/command streams, and both 53-entry split-pointer
tables. It also round-trips all 16 Demon Mirror schedules, 17 enemy-set
streams, and both of their split-pointer tables. The gate compares all 5,060
encoded bytes directly with the built PRG. Its RoomMap pattern codec adds 232
bytes, bringing the room-domain total to 5,292 checked bytes.

`make roundtrip-formats` is the aggregate byte-level codec gate. It includes
the room-data contract above, all 18 static PPU update streams, and every
reachable audio command stream. It also independently decodes and re-encodes
all object-animation pointers, descriptors, variant selectors, and frame
records plus all object-motion pointers, action selectors, and Y/X vectors.
The packed title codec contributes both command/literal streams, including an
independent reconstruction of the cursor opcodes and all 402 encoded bytes.
It also reconstructs the adjacent 34 duration/controller pairs from named NES
buttons, covering another 68 bytes of attract-demo data.
It is part of `make release-check`.

`make format-coverage-audit` binds these codecs to linker segment names. It
requires every segment classified as `stream` to have exactly one codec owner;
unknown, missing, duplicated, or non-stream ownership is rejected. The seven
owned segments total 8,113 bytes, exactly matching the stream byte count from
`make prg-layout-audit`.

## Nametable clear descriptors

The three records at CPU `$CA33-$CA3B` are independent of room streams. Each
record is `(width, start_index, row_count)`. The direct PPU clear routine maps
the start index to `$2000 + start_index * 4`; adding 8 to the index after each
row advances the PPU address by 32 bytes.

| Offset | Width | Start index | First PPU address | Rows |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 32 | `$00` | `$2000` | 26 |
| 3 | 32 | `$20` | `$2080` | 26 |
| 6 | 30 | `$20` | `$2080` | 24 |

The source keeps the records in `src/data/nametable_clear.asm` and asserts the
three-record extent at assembly time.
