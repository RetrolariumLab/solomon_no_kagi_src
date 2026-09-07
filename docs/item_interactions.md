# Item interactions

The source-owned item subsystem now spans CPU `$C42E-$C627`. The main gameplay
thread calls `CheckDanaMapTileInteraction` once per service cycle. It rejects
Dana action states `$1C+`, samples the `RoomMap` cell at Dana's center
coordinate `(Y+8, X+8)`, and passes the tile value to
`ClassifyDanaMapTileInteraction`.

The classifier ignores values below `$06`, value `$10`, and values `$38+`.
Tiles `$06-$22` safely select one of 29 item handlers. The original comparison
also admits `$23-$24`, whose selectors read two-byte targets beyond the table;
neither identity occurs in the stock room streams. Tiles `$25-$31` use the
compact score digit/amount tables, while `$32-$37` award an extra life; tile
`$32` also adds five at score digit index 2. `ItemInteractionThreadCode` at
scratch byte `$02` is zero when no cooperative follow-up is needed, `$40` for
ordinary item presentation, `$41` for an extra life, `$34` for the key, or
another code selected by a specialized handler. The caller starts that code
through `StartThread` after classification returns.

Item tiles `$08-$24` are suppressed when `$0087` bit 0 is set. Otherwise the
classifier initializes `AuxiliaryObject` at the collected map cell before
dispatch. Key and door tiles `$06-$07` bypass that visual gate and use their
own state transitions. The exact meaning of `$0087` remains unassigned.

## Handler appendix

`ItemInteractionHandlerTable` at USA `$C4D3-$C50C` / Europe `$C453-$C48C` is
an inline appendix consumed by `JumpWithParams`. Carry is deliberately clear
before `SBC #$05`, so map
tiles `$06-$24` become selectors `$00-$1E`; the appendix itself ends at
selector `$1C`. If malformed map data exposes `$23/$24`, their words are read
from the first four bytes of the adjacent red-bottle routine and decode as
invalid CPU targets `$10A2/$208A`. This reconstruction intentionally preserves
that unchecked original behavior rather than inventing handlers.

| Selector | Map tile | Handler |
| ---: | ---: | --- |
| `$00` | `$06` | `CollectRoomKey` |
| `$01` | `$07` | `EnterRoomDoor` |
| `$02` | `$08` | `AwardBlueCrystalScore` |
| `$03` | `$09` | `ApplySmallFireballBottleItem` |
| `$04` | `$0A` | `AwardType04Or06Score` |
| `$05` | `$0B` | `ApplyRedTzoItem` |
| `$06` | `$0C` | `AwardType04Or06Score` |
| `$07` | `$0D` | `ApplyLargeFireballBottleItem` |
| `$08` | `$0E` | `IncreaseInventorySlotLimit` |
| `$09` | `$0F` | `QueueFairyItem` |
| `$0A` | `$10` | no effect |
| `$0B` | `$11` | `ApplyDoubleTimerItem` |
| `$0C` | `$12` | `ApplyQuintupleTimerItem` |
| `$0D` | `$13` | `SetTimerTo10000` |
| `$0E` | `$14` | `SetTimerTo05000` |
| `$0F` | `$15` | `ApplySmallFireballBottleItem` |
| `$10` | `$16` | `ApplyLargeFireballBottleItem` |
| `$11` | `$17` | `IncreaseInventorySlotLimit` |
| `$12` | `$18` | `QueueFairyItem` |
| `$13` | `$19` | `ApplyRedBottleKillAllEnemiesItem` |
| `$14` | `$1A` | no effect |
| `$15` | `$1B` | `ApplyBlueTzoItem` |
| `$16-$19` | `$1C-$1F` | `ApplyConstellationSymbolItem` |
| `$1A` | `$20` | `ApplySolomonSealItem` |
| `$1B` | `$21` | `ApplySolomonPageItem` |
| `$1C` | `$22` | `ApplyGoldenWingsItem` |

These selector names agree with Bisqwit's independently published item map.
The reconstruction preserves repeated pointers instead of inventing wrapper
routines for item types that intentionally share behavior.
`make item-handler-audit` independently decodes the built ROM and checks every
selector, semantic name, address, and the complete table SHA-1 against
`config/item_handlers.json`.

The European item block moves `$80` bytes earlier, including all 20 unique
handler targets. `config/item_handlers_europe.json` records those native PAL
addresses and its independently hashed 58-byte table while preserving the
same selector, map-tile, and semantic-name sequence. Run
`make item-handler-profile-audits` to validate both source-built layouts.

Tile `$21` is shared by the Page of Time and Page of Space rooms. Before
gameplay starts, the loader restores `CurrentRoomIndex` to the source-room
index saved in `SpecialRoomSourceIndex`; the item handler consequently sets
ending bit `$40` for the page reached after room 20 and bit `$80` for the page
reached after room 44. Tile `$22` sets gameplay bit `$40`, which
`EnterRoomDoor` consumes as the Golden Wings five-room skip.

## Bonus and red-bottle paths

Bonus tiles `$25-$31` are grouped in threes. Repeated subtraction selects one
of five score digit indices and the within-group remainder selects amount 1,
2, or 5. The two adjacent tables at `$C710-$C717` encode those choices.

The red-bottle handler scans all 17 enemy object records. Active records with
types in `$50-$67` receive state bit 0. If at least one record changed, it
starts scheduler code `$50`; the ordinary item presentation remains queued in
`ItemInteractionThreadCode`.

Code `$50` enters `ProcessDefeatedEnemyDrops` in context 5. The routine scans
all 17 records again and accepts active objects carrying the retirement bit.
The enemy type selects one of ten eight-entry groups in
`EnemyDropTypeTable`; `AdvanceRandomState & 7` selects the entry inside that
group. Any linked enemy slots named by AI-state bytes 6 and 7 are retired when
the corresponding AI-state flag is set. The source enemy is then reinitialized
as object type `$14`, state `$C6`, with the selected drop code stored in AI
byte 6. After the sweep, sound effect `$09` is queued and context 5 stops.

The 27-byte type-to-group table and 80-byte drop table remain adjacent to the
consumer and have compile-time size checks. Zero entries are preserved as
real outcomes; the source does not invent item names for still-unclassified
drop codes.

## Item presentation context

Context 4 owns four entry variants for the shared `AuxiliaryObject` effect.
Map-originated effects (`$40/$41`) clear the collected tile before entering
the common lifecycle; enemy-originated effects (`$42/$43`) skip that initial
map write. Ordinary effects wait `$12` gameplay ticks, while extra-life
variants wait `$40` and set object Y-motion byte 5 to `$C0`. All four refresh
the score, inventory, and fairy HUD before waiting.

At completion, the lifecycle clears the auxiliary object's state and stops
context 4. `ClearAuxiliaryItemMapCell` converts the object's current integer
Y/X position back to a RoomMap index and replaces that cell with interior tile
`$10` through the normal buffered PPU update. It brackets the map mutation
with bit 0 of `$0087`; the item classifier tests the same bit to suppress a
second effect during the update. `ItemEffectFrameCounter` at `$0024` is one of
the eight NMI-incremented gameplay counters.

The source preserves a scheduler-specific control-flow detail at `$C3AD`:
`StopThread` replaces the current context's stack, so its `RTS` returns to the
idle loop instead of falling through into the physically adjacent map-clear
helper at `$C3B0`.

## Key, door, and pool reset

`CollectRoomKey` reads the door map index from room-item header offset 5,
replaces that cell with tile `$07`, conditionally sets `GameplayFlags` bit
`$20`, queues sound `$16`, stops context 4, and selects follow-up code `$34`.

Scheduler code `$34` enters the context-3 key animation at `$C23C`. The routine
removes the key tile, suspends active object states, and enters
`AnimateKeyToDoorFromHeaderPosition` with Y=6, the key-position header offset.
The room loader uses the other public entry when gameplay flag `$20` is
already set: `AnimateDoorUnlockFromDanaPosition` supplies header offset 7 as
the origin. Both paths target the door position at header offset 5.

`RunKeyCollectionPresentation` first waits for Dana's state bit 0 to clear.
It then clears state bit 6 on Dana, the fireball, and all 17 enemy objects;
because the object updater accepts states `$C0+`, this takes previously active
records below the motion, collision, and animation threshold. Fireball and
enemy states are saved in record byte 2. The routine changes the key's RoomMap
cell to interior tile `$10`, publishes that removal, and runs the flight.

After the door opens, all 17 enemy state bytes and the fireball state are
restored from byte 2, Dana receives state `$E0`, and scheduler code `$30`
replaces the current context with `MainGameplayThread`. As with context-4
shutdown, this same-context `StartThread` call replaces the stack and cannot
fall through into the adjacent `$C2A6` entry.

The animation installs a six-byte header in `AuxiliaryObject`, converts the
origin and door cells to pixels, and constructs two signed 16-bit deltas. It
subtracts `$0100` from the initial Y delta to create the rising half of the
arc. The first eight boundary bytes of `RoomMap` are temporary scratch during
the sequence: offsets 4-7 hold Y and X fixed-point motion words. Each changed
`GameplayUpdateCount` adds `$0008` to Y motion, then adds the two motion words
to the auxiliary object's Y/X fraction and integer fields. After `$40` ticks,
the scratch cells return to the `$F8` boundary sentinel and the object is
deactivated.

`PublishKeyDoorTile` first displays transition tile `$34`, waits six gameplay
ticks, and replaces it with open-door tile `$07`. `KeyFlightPointers` resolves
the generic motion helper's source and destination records. Its offset tables
deliberately overlap: source offsets are the four bytes `$04,$05,$06,$07`,
while destination offsets are `$06,$07,$09,$0A`. This maps two little-endian
motion words to the object's Y and X fraction/integer pairs without duplicating
the shared `$06,$07` bytes in ROM.

`EnterRoomDoor` deactivates Dana, resets the other secondary contexts, applies
the five-room skip flag when present, advances `CurrentRoomIndex`, and derives
special-room flag bits from the constellation flag, `SolomonSealCount`, and
room indices `$14/$2C`. Two counters at `$0084-$0085` participate in this
progression but remain unnamed pending stronger evidence. The routine clears
the key flag, resets fireball and room state, starts `RoomClearThread` through
code `$14`, and stops context 3.

`ClearGameplayObjectAndEnemyState` clears exactly 21 `$14`-byte object records
from `$057F-$0722` and all 17 eight-byte enemy AI records at `$04F7-$057E`.
The object clear is split into a 256-byte loop and a `$A4`-byte tail because a
single 8-bit Y index cannot cover the complete 420-byte pool.
