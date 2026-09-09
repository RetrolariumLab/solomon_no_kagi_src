# Items, timer, and score

This guide covers item collision effects, inventory state, timer adjustments, scoring, and fireball services.


---

## Item interactions

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

### Handler appendix

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
`config/validation/item_handlers.json`.

The European item block moves `$80` bytes earlier, including all 20 unique
handler targets. `config/validation/item_handlers_europe.json` records those native PAL
addresses and its independently hashed 58-byte table while preserving the
same selector, map-tile, and semantic-name sequence. Run
`make item-handler-profile-audits` to validate both source-built layouts.

Tile `$21` is shared by the Page of Time and Page of Space rooms. Before
gameplay starts, the loader restores `CurrentRoomIndex` to the source-room
index saved in `SpecialRoomSourceIndex`; the item handler consequently sets
ending bit `$40` for the page reached after room 20 and bit `$80` for the page
reached after room 44. Tile `$22` sets gameplay bit `$40`, which
`EnterRoomDoor` consumes as the Golden Wings five-room skip.

### Bonus and red-bottle paths

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

### Item presentation context

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

### Key, door, and pool reset

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

---

## Inventory and item effects

`src/game/items/progression.asm` owns CPU `$C698-$C70F`. Bisqwit's map
identifies the public entries as Scroll Extender, two fireball bottles, Fairy
Bell, blue/red Tzo, Blue Crystal, and the shared type-04/type-06 score effect.

The fireball inventory uses eight two-bit slots packed into
`InventorySlotsHigh` and `InventorySlotsLow`. `AddItemToScroll` scans from mask
`$C0` downward in two-bit steps. It stops at the first zero slot within the
`InventorySlotCount` usable entries, then merges the selected bits from
`InventoryItemSlotPattern`. The small-bottle pattern `$55` supplies `01` in
every slot; the large-bottle pattern `$AA` supplies `10`. If every usable slot
is occupied, the routine returns without changing the inventory. The Scroll
Extender increments the usable count up to eight.

The Fairy Bell handler increments `FairiesQueued`, which the main gameplay
thread later consumes. The Tzo handlers reach `ExtendFireballLifetime` with
`A=$04` or `A=$10`; the helper skips the addition when
`FireballLifetimeHi >= 2`, otherwise adds through the low byte and propagates
carry to the high byte. The exact incoming-carry contract is still tied to the
item dispatcher and remains a runtime-trace item.

The complete selector mapping is now reconstructed in
`src/data/static_layout.asm`; see `docs/item_system.md#item-interactions`. The three
score-producing paths call `AddScoreByAAtDigitX` at `$C73B`.
Bisqwit's map confirms that entry and all six direct control-flow references
use its symbol. Its decimal arithmetic and game-state gate are reconstructed
in `src/game/scoring.asm`; see `docs/item_system.md#score-addition`.

---

## Item score lookup tables

`src/data/static_layout.asm` owns CPU `$C710-$C717` as two adjacent tables used
by the collectible-item score path at `$C480-$C497`:

| Address | Label | Values | Role |
| --- | --- | --- | --- |
| `$C710-$C714` | `ItemBonusScoreDigitIndices` | `5,4,3,2,1` | starting index passed in X |
| `$C715-$C717` | `ItemBonusScoreAmounts` | `1,2,5` | amount passed in A |

The caller divides its normalized item selector into a five-entry group index
and a three-entry remainder, then calls `AddScoreByAAtDigitX`. Assembly asserts
both table lengths so code and data cannot silently drift across their shared
boundary.

---

## Countdown timer

`src/game/timer/runtime.asm` owns CPU `$A15F-$A225`. The upstream Bisqwit map names
the public entries at `$A15F` and `$A183` as `DecrementTimer` and
`DecrementTimerByOne`; the instruction flow and RAM accesses independently
confirm countdown arithmetic over the four decimal timer digits.

`GameplayUpdateCount` is an eight-bit accumulator incremented by
`UpdateNmiGameplayFrame`. `MainGameplayThread` calls `DecrementTimer` before
`UpdateEnemiesMovement`: the timer snapshots the count without clearing it,
then the enemy prepass consumes the same value and clears the accumulator.
Repeated main-thread passes in one video frame therefore see zero after the
first pass, while a delayed pass sees all gameplay NMI ticks accumulated since
the previous prepass.

For each pending tick, the timer adds `TimerDecrementSpeed` to `TimerFraction`.
A carry subtracts `TimerDecrementStep` from `TimerDigit10` and propagates
decimal borrow through the higher digits. Bit 7 of `TimerDecrementStep` records
that the internal digits changed.

When the PPU update stream is free, the routine calls
`BuildTimerDisplayUpdate` at `$A238`. A busy stream defers only the HUD write:
the arithmetic has already consumed every pending tick, bit 7 remains set,
and a later pass publishes the current digits. Intermediate visual values can
therefore be skipped, but the internal countdown catches up. If the builder
reports an all-zero timer, scheduler code `$33` is started. The final part
compares the two high timer digits with a four-entry BCD threshold table at
`$A229`, queues one of two PPU update streams, and toggles bit 4 of
`TimerWarningState` as the threshold is crossed. The thresholds are `$02`,
`$04`, `$10`, and `$23`.

`src/data/static_layout.asm` owns `$A226-$A237`. The fourth threshold byte at
`$A22C` is deliberately shared with `EnterTimerWarningPpuUpdate`: the two
six-byte streams write two literal bytes at PPU `$23C2`, using `$F0,$30` on
entry and `$A0,$20` on exit. The three bytes at `$A226-$A228` duplicate the
`$20,$69,$44` timer HUD command header, but their consumer has not yet been
proved, so the source keeps the conservative `PreTimerWarningTableBytes` name.

### Display update builder

`src/game/timer/runtime.asm` owns `$A238-$A273`. It constructs a small update
program in RAM at `$03E6`: a copied three-byte `JSR $4469` prefix, the four
timer digits in most-significant-first order, and two zero terminators. Leading
zero digits are replaced with blank tile `$24`. The OR of all four digits is
left in `TimerDisplayNonzeroAccumulator`, which lets `DecrementTimer` detect
an all-zero countdown after the builder returns.

The builder tail-calls `PublishPpuUpdateBuffer`, which publishes `$03E6`
through the shared PPU update pointer. The `$20,$69,$44` bytes decode as a
literal five-tile command targeting PPU `$2069`; their instruction-like
appearance as `JSR $4469` is incidental.

### Runtime cadence

The deterministic runtime harness counts `DecrementTimer` calls and pending
ticks over the first 60 frames after `MainGameplayThread` starts. The first
call also exposes a room-intro backlog: 87 ticks in Room 1 and 64 in the
attract demo. After that initial batch, the lightly populated room executes
203 timer calls across all 60 frames and consumes all 59 new counter
increments one at a time. The populated attract room executes only 52 calls
across 52 frames, consumes 58 of 59 new increments, and leaves the final tick
queued at the cutoff. Delayed calls process at most two ticks.

This proves that cooperative main-thread load does not lose countdown ticks:
consumed steady-state ticks plus the queued remainder equal the observed
nonzero writes to `GameplayUpdateCount` in both scenarios. Neither trace takes
the NMI skip path. This does not make the timer an unconditional wall-clock:
the NMI handler deliberately skips gameplay services when the interrupted
context's local stack offset is below `$08`, and such a video frame cannot be
recovered because it never increments the accumulator. The eight-bit counter
would also wrap after 256 unconsumed gameplay updates, although the measured
maximum backlog after room entry is two.

`make trace-runtime` reproduces both measurements and validates their exact
summary strings against `scenarios/runtime_scenarios.json`.

---

## Timer item effects

`src/game/timer/runtime.asm` owns CPU `$C628-$C697`. The four public item
handlers are entries in the still-unreconstructed item dispatch data; Bisqwit's
map identifies them as the double-time, fivefold-time, `10000`, and `05000`
effects.

The remaining time is stored as four unpacked decimal digits from
`TimerDigit10` through `TimerDigit10000`. `DoubleRemainingTime` walks from the
least-significant digit upward, propagating decimal carry. The double-item
handler uses it once. The fivefold handler saves the original digits, doubles
twice to obtain four times the value, then adds the saved value. Carry beyond
the ten-thousands digit is discarded, so both operations are modulo 10000.

The item handlers also update `TimerDecrementStep`:

- the double handler preserves bit 7 and replaces the low rate with 2;
- the fivefold handler performs the original `ASL`, `ASL`, `ADC` sequence. For
  the observed small low-rate values, this preserves bit 7 and multiplies the
  rate by 5.

`SetTimerTenThousandsDigit` stores its input in `TimerDigit10000` and clears
all lower digits. `SetTimerTo10000` branches directly into that helper with
`A=1`; `SetTimerTo05000` first clears all four digits and then writes 5 to
`TimerDigit1000`.

---

## Score addition

`src/game/scoring.asm` owns CPU `$C73B-$C755`. `AddScoreByAAtDigitX` has six
direct callers and uses the following contract:

```text
input:      A = amount for the selected decimal digit
            X = index into ScoreDigits, 0..7
output:     decimal carry propagated toward lower indices
preserved:  Y and GameStateFlags
clobbered:  A, X, processor flags
```

`ScoreDigits` stores eight unpacked decimal digits from most significant at
index 0 to least significant at index 7. The routine adds at index `X`, wraps
values of ten or more, and propagates carry by decrementing `X`. Carry beyond
index 0 is discarded.

Before the addition, the routine rotates bit 0 of `GameStateFlags` into carry.
When that bit is clear it replaces the requested amount with zero; when set it
keeps the caller's amount. A matching rotate restores the flags byte exactly
before arithmetic begins. This proves that bit 0 gates score updates, matching
its already observed role in selecting complete controller-cache refreshes.

---

## Fireball inventory display

`src/graphics/hud/runtime.asm` owns CPU `$A30C-$A39A`; its
three tile/header tables occupy `$A39B-$A3A3`. Both known callers refresh the
HUD after packed fireball inventory can have changed: Dana's successful cast
at `$9B74` and `RefreshGameplayHud` at `$C3DA`.

The routine first waits until the shared PPU stream pointer is idle, then
builds two literal 11-tile commands in `PpuUpdateBuffer`. Their destination
addresses are `$2054` and `$2074`, so the rows are vertically adjacent in the
nametable. Each command header is stored in reverse ROM order because the
three-byte copy loops count X down from 2 while advancing the RAM destination.

### Packed-slot decoding

`InventorySlotsHigh` and `InventorySlotsLow` contain eight two-bit values.
The top-row loop copies them to scratch bytes `$04-$05`, shifts the pair twice
per cell, and rotates the outgoing value into A. Encodings 1 and 2 select top
tiles `$B0` and `$B1`. Zero ends occupied-slot decoding; the remaining usable
capacity from `InventorySlotCount` is drawn with `$B4`, and cells outside that
capacity are blanked with `$24`. Tile `$A5` is emitted as the row's left cap.

The bottom row is derived from the completed top row already resident at
`PpuUpdateBuffer + 3`. Negative top tiles are converted by adding 2. When the
first nonnegative blank is reached, the routine backs up one destination byte
and fills the tail with `$B7` until it encounters `$20`, the high address byte
of the following command header in the top-row buffer. A zero byte terminates
the complete update program before `PublishPpuUpdateBuffer` publishes it.

This reconstruction names only the observed tile roles. Their exact artwork
depends on the selected CHR bank and is not inferred from numeric tile values.

---

## Fireball lifetime service

`src/game/items/progression.asm` owns CPU `$A3A4-$A3D6`. Bisqwit's map labels
the entry `MaybeRunFireballAI_1`; the narrower reconstructed name
`UpdateFireballLifetime` reflects what this routine proves directly.

The entry returns immediately unless `FireballObject` is active (bit 7 set).
For an active fireball it compares the 16-bit configured lifetime at
`$0432-$0433` with the first 16-bit life counter at `$042C-$042D`. When the
counter has exceeded the configured lifetime, the routine clears
`FireballActive` and the low counter byte, then writes state `$04` to object
offset 3.

On later calls with `FireballActive` clear, a low counter value of at least
eight retires the object by clearing its first byte. This establishes a short
post-expiration cleanup interval without assigning semantics to the remaining
fireball record fields.

The deterministic `room-1-cast-fireball` scenario supplies one inventory slot
and lifetime `$0010` through three declared RAM writes, then uses ordinary B
input. It observes activation at frame 722, the first NMI collision service at
723, active-state clearing and the cleanup branch at 739, and object retirement
eight frames later at 747. This binds both phases of the service to runtime
behavior in the byte-identical build.

The adjacent services at `$A3D7` and `$A3F8` initialize and render object
records and remain the next evidence boundary.

---

## Auxiliary effect object

`src/game/scoring.asm` owns CPU `$C718-$C73A`. It initializes the
shared object record at `AuxiliaryObject` (`$05BB`) through two entry points:

- `SpawnAuxiliaryEffectAtMapCell` converts `MapCellIndex` in `$04` to pixel
  coordinates, initializes the object, and preserves the caller's `A` value;
- `SpawnAuxiliaryEffectAtCoordinates` accepts Y/X in `$04/$05`, writes object
  offsets 7 and 10, and copies a four-byte template to offsets 0 through 3.

The fixed template is `$C6,$1C,$FF,$0C`. Its individual field meanings remain
unassigned; what is confirmed is that all three coordinate-based callers
create the same auxiliary record state. Two callers provide the current enemy
position and the wrapper is used by two item-acquisition paths. The neutral
`AuxiliaryEffect` name records this shared role without claiming a particular
sprite, score popup, or animation until runtime traces identify it.
