# Special-room scripts

Scheduler code `$60` enters `RunSpecialRoomScriptThread` at `$B800`. It calls a
room-indexed handler and stops context 6 after that handler returns. The room
loader starts this context for every room, so ordinary rooms deliberately map
to one-byte `RTS` handlers.

## Special-room selection

`EnterRoomDoor` combines the collected constellation flag with seal count and
the just-advanced source-room index. The high-nibble selectors have a complete
mapping:

| Selector | Internal room | Meaning |
| ---: | ---: | --- |
| `$10` | 51 | Page of Time after displayed room 20 with at least four seals |
| `$20` | 52 | Page of Space after displayed room 44 with at least six seals |
| `$30` | 50 | ordinary constellation bonus room |

The loader saves the source index in `SpecialRoomSourceIndex`, temporarily
loads one of these room records, then restores the source index before
gameplay. That value lets collectible tile `$21` set Page of Time ending bit
`$40` below room index `$1E` or Page of Space bit `$80` at and above it.
Internal room 48 is the Princess room reached after displayed room 48 only
with all eight seals; room 49 is Solomon's ending room. `SpecialRoomNameTiles`
independently names 48 as `PRINCESS`, 49 as ` SOLOMON`, and 50-52 as
` HIDDEN `.

## Dispatch format

`DispatchCurrentRoomScript` divides `CurrentRoomIndex` by eight and uses the
result to select one of seven group bases. A parallel 53-byte table supplies a
relative offset inside that group:

```text
group = room_index / 8
entry = group_base[group] + room_offset[room_index]
```

The seven bases occupy `$B824-$B831`; offsets occupy `$B832-$B866`. The final
four offsets are `$85,$00,$49,$4D`, selecting handlers `$BA34`, `$B9AF`,
`$B9F8`, and `$B9FC` for room indices 49-52. Those bytes form table data even
though `$85 $00 $49 $4D` can be decoded as `STA $00` and `EOR #$4D`. Treating
them as instructions both invents unreachable code and truncates the secret
room dispatch table.

Compile-time assertions hold the table at 53 entries and the reconstructed
module at exactly `$234` bytes.

## Trigger families

The reconstructed handlers fall into four mechanically verified families:

- no-op entries return immediately for rooms without a script;
- seal entries pass one of the bit values `$01,$02,$04,$08,$10,$20,$40,$80`
  to the shared reveal routine at `$BFAA`;
- enemy entries wait until Dana is active, set bit 6 in the first enemy AI
  record, or allocate a type-`$18` enemy at a scripted map cell;
- map entries cooperatively watch `RoomMap`, the block-cast target at `$007E`,
  the head-collision target at `$007F`, and Dana's action/state fields before
  publishing tile changes.

Displayed rooms 17 and 39 count eleven head hits at map positions `$7E` and
`$56`, then spawn the Mighty Bomb Jack object (type `$18`) at cells `$6E` and
`$36`. Displayed rooms 20 and 38 use the shared Tecmo Bunny trigger at cells
`$20` and `$9E`. It watches two cover/uncover cycles, waits for Dana's action,
then commits collectible tile `$32`; the generic item score path gives that
tile 500,000 points and an extra life. The room-20 path first expands the
special bitplane at `$BFE2`. Room index 29 expands the level-30 bitplane at
`$BFFA` and enables the first enemy AI phase.

The Princess room hides twelve fixed map cells, waits for casts at `$AD` and
`$57`, and checks the first enemy object's map position before changing cells
`$82` and `$65`. The Page of Time and Page of Space handlers place tile `$21`
at cells `$37` and `$A7`. Their shared trigger watches Dana's map position and
the last block-cast target, then changes either cell `$C7` or the three cells
`$46-$48`.

The table-backed part of this behavior is now the seventh canonical room-data
family. Its lossless codec owns 116 bytes: 32 random bonus-room positions, 16
corresponding item types, eight Seal positions, twelve Princess-room cells,
and the two 24-byte room 20/30 bitplanes. USA and Europe encode identical
semantics at different early-table addresses. Japan relocates the later tables
by `$430` and changes bonus position index 2 from `$B2` to `$D2`; this
single-byte content difference is fingerprinted rather than normalized away.

The room-index 49 offset selects `RunEndingRoomScript` at `$BA34`. That complete
ending handler is source-owned through `$BD93`. Its supporting waits, Solomon's
Seal reveal state, object-position table, text streams, and two special-room
bitplanes are source-owned in `src/game/ending_and_special_room_support.asm`.

The cameo and page names are cross-checked against the documented NES room
solutions and item effects in the
[GameFAQs guide](https://gamefaqs.gamespot.com/nes/570522-solomons-key/faqs/10324)
and the
[SDA mechanics reference](https://kb.speeddemosarchive.com/Solomon%27s_Key_%28NES%29/Game_Mechanics).
