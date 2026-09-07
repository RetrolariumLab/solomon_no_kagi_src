# Room item and metadata decoding

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

## Supporting tables

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
