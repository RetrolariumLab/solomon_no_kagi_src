# Enemy system

This guide follows enemy records from allocation and configuration through movement, AI dispatch, and deactivation.


---

## Enemy AI record layout

The runtime enemy system has 17 eight-byte AI records at `$04F7-$057E`, in
parallel with 17 `$14`-byte object records at `$05CF-$0722`. The split pointer
tables and their arithmetic stride are machine-checked by
`make enemy-pointer-audit`.

Every byte now has a shared offset name. The last two bytes deliberately keep
multiple aliases because their role depends on the enemy family.

| Offset | Shared name | Established role |
| ---: | --- | --- |
| 0 | `EnemyAiFlagsOffset` | active bit 7 and family-specific state flags |
| 1 | `EnemyAiPhaseOffset` | independent eight-bit phase counter/state |
| 2 | `EnemyAiLifetimeLowOffset` | low byte of accumulated active lifetime |
| 3 | `EnemyAiLifetimeHighOffset` | high byte of accumulated active lifetime |
| 4 | `EnemyAiVerticalDeltaOffset` | signed half-distance component relative to Dana |
| 5 | `EnemyAiHorizontalDeltaOffset` | signed half-distance component relative to Dana |
| 6 | `EnemyAiFirstLinkedSlotOffset` / `EnemyAiPathDirectionOffset` | first child slot or current path direction |
| 7 | `EnemyAiSecondLinkedSlotOffset` / `EnemyAiAlternateDirectionOffset` | second child slot or alternate path direction |

`UpdateEnemiesMovement` processes only records whose flags byte is negative.
It consumes `GameplayUpdateCount`, adds it independently to byte 1, and adds
the same value as a 16-bit quantity to bytes 2-3. It then derives bytes 4-5
from the matching object's Y/X displacement from Dana. The phase field is
therefore not the low byte of the lifetime counter even though all three are
advanced in the same prepass.

`ApplyEnemyLifetimeThreshold` independently proves bytes 2-3 as a little-
endian pair by subtracting the room's 16-bit spawn-lifetime threshold. The
initializer clears bytes 1-3 for a newly allocated slot while preserving the
caller-supplied flags byte.

### Polymorphic tail fields

Linked-spawn families retain one or two allocated child indices in bytes 6-7.
Their cleanup and red-bottle paths read those indices through the linked-slot
aliases before deactivating the child records.

Path-following families instead store direction indices in the same bytes.
Values 0 through 3 mean right, left, up, and down. This contract is also used
by fireballs: NMI temporarily points `EnemyAiPointer` at `FireballActive`, so
`FireballDirectionIndex` and `FireballAlternateDirectionIndex` become offsets
6 and 7 of a synthetic AI record consumed by the shared path-mask handlers.

The overlapping names are intentional type-family views, not evidence that a
linked slot and a direction coexist in one record at the same time.

---

## Enemy slot initialization

`src/game/enemies/runtime.asm` owns CPU `$A3D7-$A3F7`. Bisqwit's map
identifies the entry as `InitializeEnemy`. Four call sites use the same
zero-page input contract:

- `SpawnSlotIndex` selects one of the 17 parallel enemy slots;
- `SpawnYPosition` and `SpawnXPosition` contain converted pixel coordinates;
- the caller invokes the adjacent type-specific initializer at `$A3F8` when a
  complete spawn is required.

`LoadEnemyAiPointer` resolves the selected eight-byte AI record. The routine
clears its phase byte and two-byte lifetime accumulator at offsets 1-3, then
`LoadEnemyObjectPointer` resolves the matching `$14`-byte object record and
receives Y/X at offsets 7 and 10. Both pointer helpers and all four split
tables are source-owned and machine-audited.

`InitializeDemonMirrorObject` at `$A144` uses only this position/state helper
while building a placeholder with state `$C6`, type `$04`, and action `$0C`;
the later activation pass applies `ConfigureEnemyType`. Room actors, fairies,
and the `$B930` spawn path continue directly into the type-specific `$A3F8`
service.

---

## Enemy type configuration

`src/game/enemies/runtime.asm` owns CPU `$A3F8-$A44D`. Five call
sites supply `SpawnSlotIndex` and `SpawnType`; three complete spawn paths call
it immediately after `InitializeEnemy`, while two gameplay paths reconfigure
already allocated slots from encoded type streams.

The routine resolves the object record through `$B28A`. The low two type bits
select a variant, while `(SpawnType - $18) / 4` indexes the 27-byte
`EnemyTypeConfigurationTable` at `$A44E-$A468`. Types `$80/$81` present in the
original room streams require the final index 26 and therefore prove that
`$A468` belongs to this table.
Decoded table bits determine a `$C0`/`$E0` base, a derived value passed through
scratch byte `$04`, whether object offset 5 receives `$80`, and which X value
is passed to the helper at `$9D99`.

One decoded flag causes the matching AI record to be selected through
`LoadEnemyAiPointer`. The low two type bits seed `EnemyAiPathDirectionOffset`;
an XOR/mask transform chooses horizontal or vertical opposition for
`EnemyAiAlternateDirectionOffset`. The shared path-mask handlers establish
both fields as direction indices. The behavior of `$9D99` and the remaining
individual table bits stays unnamed until their consumers provide equivalent
evidence.

---

## Enemy slot allocation

`src/game/enemies/runtime.asm` owns CPU `$B42A-$B445` and provides
`FindFreeEnemySlotIndex`. Bisqwit's map independently assigns the same name to
the entry point.

The routine scans the seventeen-entry AI state pool from index zero. For every
candidate it leaves that record's address in `TempPointer04` (`$04/$05`) and
tests byte 0. A non-negative byte denotes an available record.

Return contract:

- carry set: `X` is the available slot index and `TempPointer04` addresses its
  AI record;
- carry clear: all seventeen slots were active and `X` equals 17;
- `Y` is zero on either path.

All thirteen static callers now use the semantic symbol. Allocation paths
immediately mark the returned record active and retain `X` for the matching
object-record initialization, confirming that this is a pool allocator rather
than a generic state search.

---

## Enemy record pointer helpers

`src/game/enemies/runtime.asm` owns CPU `$B28A-$B2A1`. Its two entry points
accept a slot index in `A`, copy it to `X`, and construct a 16-bit address in
`TempPointer00` (`$00/$01`) from split low/high pointer tables.

- `LoadEnemyObjectPointer` uses tables at `$B46C` and `$B481`.
- `LoadEnemyAiPointer` uses tables at `$B446` and `$B457`.

The source currently has 28 calls to these helpers. The callers show that the
object and AI records form parallel pools, while the pointer tables make their
different strides and base addresses opaque to most gameplay code. Bisqwit's
map independently names the two routines `LoadEnemyObjectPointer` and
`LoadEnemyAIvarsPointer`.

The table data and its four leading non-enemy object slots are reconstructed in
`src/data/enemies/tables.asm`; see `docs/enemy_system.md#enemy-and-object-record-pointer-tables`.

---

## Enemy and object record pointer tables

`src/data/enemies/tables.asm` owns CPU `$B446-$B491`. The 76-byte
region contains four split pointer tables:

| Table | Entries | Address sequence |
| --- | ---: | --- |
| enemy AI low/high | 17 | USA `$04F7`, PAL `$04F8` + `index * 8` |
| all object low/high | 21 | USA `$057F`, PAL `$0580` + `index * $14` |

The first four object entries address Dana (`$057F`), the magic spark
(`$0593`), the fireball (`$05A7`), and an auxiliary record (`$05BB`). The
remaining seventeen begin at `EnemyObjects` (`$05CF`). Consequently,
`EnemyObjectPointerLowTable` and `EnemyObjectPointerHighTable` are labels four
entries into the complete object tables, not separate duplicated data.
`NonDanaObjectPointerLowTable` and `NonDanaObjectPointerHighTable` are the
plus-one aliases at `$B469/$B47E`; they begin with the magic spark and feed
`LoadObjectPointer` plus eight direct consumers.

The source expresses both sequences from their RAM bases and strides with
assembly-time count and offset assertions. This keeps the byte-identical
layout while making the pool relationship reviewable.

`make enemy-pointer-report` decodes the four byte planes from the built PRG.
`make enemy-pointer-audit` compares the reconstructed 16-bit pointers with
`config/validation/enemy_record_pointers.json`; the audit is part of `make release-check`.
Bisqwit's map independently classifies the same ranges as the enemy AI and
object pointer tables.

PAL keeps all four byte planes at the same PRG addresses but moves both RAM
pools one byte higher. `config/validation/enemy_record_pointers_europe.json` therefore
records native bases `$04F8` and `$0580`; the strides and counts remain shared.
`make enemy-pointer-profile-audits` validates all 38 reconstructed pointers
against both regional source builds.

---

## Current enemy position helper

`src/game/enemies/runtime.asm` owns CPU `$A4A6-$A4B2`. The helper reads the
current enemy object through `EnemyObjectPointer`, copies byte offsets 7 and 10
into `SpawnYPosition` and `SpawnXPosition`, and returns.

The two call sites are inside the handler families beginning at `$A4B3` and
`$A840`. Both select an enemy record before the call and consume the shared
spawn scratch afterward. This establishes the helper's data-flow contract;
the kind of related object being constructed remains deliberately unnamed
until those handlers are reconstructed.

The offsets differ from Dana's documented integer coordinate offsets because
enemy movement records store their working position in different fields. The
neutral `LoadCurrentEnemyPosition` name records the confirmed copy operation
without assigning unsupported field semantics.

---

## Enemy movement prepass

`src/game/enemies/runtime.asm` owns CPU `$A274-$A2DB`. Bisqwit's map identifies
the entry as `UpdateEnemiesMovement`; the routine is called once near the
start of `MainGameplayThread`.

The routine snapshots Dana's integer Y and X positions, consumes and clears
the shared `GameplayUpdateCount`, and visits all 17 enemy slots. Four split
pointer tables at `$B446`, `$B457`, `$B46C`, and `$B481` select the eight-byte
enemy AI record and the corresponding `$14`-byte object record.

Only AI records whose `EnemyAiFlagsOffset` byte has bit 7 set are processed and
counted in `ActiveEnemyCount`. The shared update count advances the independent
`EnemyAiPhaseOffset` byte and the little-endian lifetime pair at offsets 2-3.
Object Y/X are compared with Dana's coordinates, divided by two through `ROR`,
and cached as vertical/horizontal deltas at offsets 4-5.

The pointer tables are formula-generated and audited as 17 AI plus 21 object
records. `docs/enemy_system.md#enemy-ai-record-layout` gives the complete AI layout;
`docs/enemy_system.md#enemy-ai-dispatcher` describes the next consumer of the parallel pools.

---

## Enemy lifetime transition

`ApplyEnemyLifetimeThreshold` at `$B4C4-$B4F0` is shared by two enemy behavior
dispatch paths. Both are reached only after `RunEnemyAiDispatcher` accepts the
object type with a successful subtraction, so carry is set on entry. The
helper deliberately relies on that carry for its 16-bit low/high subtraction.

AI records whose low two flag bits are nonzero bypass the lifetime check.
Otherwise, `EnemyAiLifetimeLowOffset/HighOffset` are compared with the room-
configured threshold at `$0426-$0427`. Once the threshold has been reached and
object action byte 3 is nonzero, the helper:

1. clears object action byte 3;
2. clears `EnemyAiPhaseOffset`;
3. sets bit 1 in object state byte 0.

The complete shared record layout is documented in
`docs/enemy_system.md#enemy-ai-record-layout`; individual flag bits remain family-specific until
their writers and readers provide stronger evidence.

The adjacent `$B4F1-$B7FF` range is not executable. Bisqwit's map identifies
all 783 bytes as `FillerBeforeB800`; they remain explicit in the existing
enemy-deactivation source file to preserve the matching ROM without creating
a tiny standalone assembly file.

---

## Enemy AI dispatcher

`src/game/enemies/runtime.asm` owns CPU `$A2DC-$A30B`. Bisqwit's map calls
the entry `MaybeRunAllEnemyAI`; this reconstruction uses
`RunEnemyAiDispatcher` because the routine's proven responsibility is slot
selection, while the behavior-specific work remains in `$A469`.

The dispatcher walks all 17 slots in descending order and resolves parallel AI
and object pointers through the same four split tables used by the movement
prepass. It calls `DispatchEnemyAiHandler` only when `ObjectStateOffset` is at
least `ActiveObjectStateMinimum` (`$C0`) and `ObjectTypeOffset` is at least
`EnemyAiDispatchTypeMinimum` (`$14`). X is preserved around each potential
call so the outer slot scan remains stable.

The state threshold is shared with `UpdateActiveObjects`. The type subtraction
normalizes `$14-$6F` to `$00-$5B`; the handler then divides that selector by
four and indexes the 28-entry table documented in `docs/enemy_system.md#enemy-ai-handler-dispatch`.
The subtraction deliberately consumes the carry left set by the successful
state comparison, so no separate `SEC` is required.

---

## Enemy AI handler dispatch

`src/game/enemies/early_ai.asm` owns CPU `$A469-$A4A5`. Bisqwit's map names
the entry at `$A469` `MaybeRunOneEnemyAI`; this reconstruction uses
`DispatchEnemyAiHandler` because the routine performs two shifts and delegates
through the generic appendix dispatcher at `$8EA9`.

The 28 words immediately following that `JSR` are not executable fallthrough
bytes. `JumpWithParams` consumes them as an inline little-endian handler table
and transfers control to the selected target. Repeated targets are meaningful:
the table contains 28 entries but only 14 unique handler addresses.

`make enemy-ai-report` prints the decoded table from the built PRG.
`make enemy-ai-audit` compares every pointer with
`config/validation/enemy_ai_handlers.json`; the audit is part of `make release-check`.
An assembly assertion independently fixes the source table at 28 entries.
The table and all 14 unique target addresses are physically identical in USA
and PAL. `make enemy-ai-profile-audits` verifies that shared contract against
both source-built ROMs rather than inferring it from the source conditionals.

The first two targets are source-owned as `RunType00To03EnemyAi` and
`RunType04To07EnemyAi` in `src/game/enemies/early_ai.asm`. Their shared contact
path awards score, an extra life, or an inventory effect. Four more handler
targets are source-owned in `src/game/enemies/mid_ai.asm`: the `$08-$0B`,
`$10-$13`, `$54-$5B`, and `$6C-$6F` type families. The `$14-$17` and `$18-$1B`
targets and their shared path selector are reconstructed in
`src/game/enemies/pathfinding_ai.asm`. `src/game/enemies/collision_ai.asm` owns the
repeated `$1C-$37` target and the `$5C-$63` target. The remaining `$0C-$0F`,
`$48-$53`, and `$64-$6B` targets are source-owned in
`src/game/enemies/late_ai.asm`; all 28 table entries are now symbolic.

---

## Early enemy AI families

`src/game/enemies/early_ai.asm` owns `$A4B3-$A68B`, the first two targets of the
28-entry enemy AI dispatcher.

`RunType00To03EnemyAi` combines lifetime/action gating, map collision, motion
selection, and contact rewards. Rewards include grouped score amounts 1/2/5,
an extra life, or one of four inventory effects selected through an inline
`JumpWithParams` table.

`UpgradeSmallFireballInventory` scans the configured packed two-bit inventory
slots backwards and changes the first small-fireball entry into a large one.

`RunType04To07EnemyAi` chooses randomized motion on open paths and adjusts it
after collision. Its contact path replaces all active enemy object headers
with `$E2,$1C,$FF,$00`, clears their AI phase bytes, and deactivates the
triggering enemy. Shared helpers beyond this range retain neutral addresses
until their own reconstruction.

---

## Mid-table enemy AI families

`src/game/enemies/mid_ai.asm` owns CPU `$A68C-$A997`. It reconstructs four
unique targets used by the 28-word enemy AI handler table while keeping enemy
names neutral until type-to-creature identities are verified in play.

Each family begins with `LoadEnemyActionSelector`, which divides object action
byte 3 by four, followed by `JumpWithParams` and an inline little-endian action
table. The source expresses all four tables as `.addr`; bytes that looked like
overlapping instructions in the preservation listing are therefore recognized
as dispatcher data.

The `$10-$13` family has two actions. One resets phase and action state after a
threshold; the other allocates a free linked enemy slot and stores its index in
AI byte 6. The `$6C-$6F` family has seven action entries. Three paths use
different proximity thresholds before scheduling thread `$31`, while the
shared overlap helper compares Dana and enemy X coordinates over a ten-pixel
window.

The `$54-$5B` pair of dispatch entries share one seven-action table. Its main
update probes motion thresholds and the forward RoomMap cell, changes facing,
and can reserve two free enemy slots. Allocation is transactional: if the
second slot is unavailable, the first temporary record is disabled again.

The `$08-$0B` family handles fairy collection and a two-axis correction step.
Collection increments `FairiesCollected`, queues the normal item presentation,
and on every tenth fairy takes the extra-life presentation path. Its motion
routine uses four small signed-adjustment/limit tables at `$A988-$A997` to
update object Y and X motion while retaining a direction value in AI byte 6.

Action targets beyond this range now resolve to symbols in the later enemy-AI
modules. This module assembles to exactly 780 bytes, and `make verify-prg`
proves it is identical to the original PRG image.

---

## Late enemy AI families

`src/game/enemies/late_ai.asm` owns CPU `$AF5C-$B289`, the final range formerly
held in the address-ordered preservation source. It reconstructs handler
targets for type groups `$64-$6B`, `$0C-$0F`, and `$48-$53`, plus shared
collision, direction, linked-slot, and forward-map helpers.

The `$64-$6B` family dispatches seven actions. Its linked-spawn path positions
a related object through two overlapping signed-offset tables, initializes its
object header, and queues sound `$17`. A second action can replace the object
header with `$E2,$1C,$FF,$00`; the source keeps those four bytes as named data.

`CheckEnemyForwardCollisionBit` selects `ObjectCollisionBelowLeftBit` or
`ObjectCollisionBelowRightBit` from object direction. These are the Y-edge
support probes at collision-mask bits 4 and 5. `CheckEnemyDeltaDirectionThreshold`
compares an AI delta with a caller-provided threshold and reports whether its
direction agrees with the object's facing bit. These helpers are now used
symbolically by the earlier reconstructed families.

The `$0C-$0F` family samples the shared four-cell collision mask, converts the
first set bit into an overlapping Y/X offset pair, and either creates a map
interaction object or retires the enemy. The `$48-$53` family combines the
existing lifetime gate with a seven-action table and owns the concrete linked
slot cleanup and paired-enemy state transitions previously referenced by
address aliases.

The segment is exactly 814 bytes. With it, every PRG byte belongs to a named
semantic or classified-data module; no address-ordered preservation listing
remains. Full ROM verification still proves the generated 65,552-byte iNES
image identical to the reference.

---

## Linked enemy AI support

`src/game/enemies/early_ai.asm` now owns the contiguous `$B2A2-$B429`
support range in addition to the primary handler table. The source file is 300
lines, keeping the related code together without introducing another small
assembly module.

### Action dispatch

`RunEnemyAiDispatcher` subtracts `$14` from an eligible object's type and
`DispatchEnemyAiHandler` divides that selector by four. Handler-table entries
15-17 therefore route types `$50-$5B` to `RunType50To5BEnemyAi`.

That handler first applies the room lifetime threshold, then shifts object
action byte 3 right twice. The resulting selector enters a seven-address
`JumpWithParams` appendix at `$B351`. Its locally reconstructed paths can
retire the current slot after AI phase `$11`, begin horizontal movement, or
run the single-linked-slot state machine.

The adjacent `$B178` handler is reconstructed as `RunType48To53EnemyAi` in
`src/game/enemies/late_ai.asm`; its inline appendix calls
`SetEnemyHorizontalStepAndFacing` and `UpdateLinkedEnemyPairSpawn` in this
range.

### Linked slots

Both allocation paths use the carry contract of `FindFreeEnemySlotIndex` and
its returned `TempPointer04` AI-record pointer:

- the pair path stores allocated indices in parent AI bytes 6 and 7;
- if the second allocation fails, it clears the first allocated AI state;
- the single path stores one index in byte 6 and resolves its parallel object
  record through `EnemyObjectPointerLowTable` and its high table;
- parent state/action bits record whether the linked transition is active.

The drop-conversion code consumes the same byte-6/byte-7 links when retiring
multi-slot enemies, so these offsets now live in the shared RAM registry.

### Map probe

`CalculateEnemyForwardMapCoordinates` tests action bit 0 and selects a point
24 pixels to the right or 8 pixels to the left of the object, with an
eight-pixel vertical offset. The ordinary pixel-to-map converter then lets the
linked-slot paths distinguish occupied tiles, interactive tiles below `$F8`,
and the open/sentinel range beginning at `$F8`.

AI bytes 1, 4, and 5 are named only by their observed phase/delta roles here.
Enemy-specific creature names remain deferred until runtime traces bind each
numeric type group to an observed room entity.

---

## Pathfinding enemy AI

`src/game/enemies/pathfinding_ai.asm` owns CPU `$A998-$AD36`. The first 209
bytes complete the three still-external actions of the `$08-$0B` handler
table: phase-to-action promotion, horizontal orientation, and vertical
orientation. `CheckEnemyAiDeltaRange` then checks both signed AI motion deltas
against the same compact threshold and preserves the original carry contract.

`RunType14To17EnemyAi` and `RunType18To1BEnemyAi` share the remaining path
selector. Their only difference is a four-entry offset into the initial
fractional-delta tables. The routine advances a candidate fixed-point
position, samples four RoomMap cells around each of two candidate coordinates,
and packs the solid/open results into two four-bit masks.

The primary mask selects one of 16 inline `.addr` entries. The handlers use
the secondary mask, current direction, coordinate low nibbles, and four small
direction maps to choose the next direction or snap a candidate coordinate to
a tile boundary. Every exit either stores direction bytes 6/7 or commits the
candidate Y/X bytes to object offsets 7/10.

The direction fields now have shared names because the fireball collision
path proves the same contract independently. It temporarily points
`EnemyAiPointer` at `FireballActive`, placing `FireballDirectionIndex` and
`FireballAlternateDirectionIndex` at AI offsets 6 and 7 before dispatching
these handlers. Direction values 0 through 3 mean right, left, up, and down.

Three handlers deliberately share the short trampoline at `$ABAD`, and some
mask paths contain branches whose fallthrough is unreachable from that entry.
Those shapes are retained because they are part of the original machine code,
not simplified pseudocode. The segment is exactly 927 bytes and remains
byte-identical under `make verify-prg`.

---

## Collision-driven enemy AI

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

---

## Enemy slot deactivation

`src/game/enemies/runtime.asm` owns CPU `$B492-$B4B5`. The routine accepts
an enemy slot index in `A`, resolves both parallel record pointers, clears byte
0 in the AI and object records, and writes `$F8` to object offset 7.

Object byte 0 is the active/state byte tested throughout the enemy pipeline,
and `$F8` is the established hidden/offscreen Y sentinel. Together these
writes retire the slot from both AI processing and rendering, which supports
the confirmed name `DeactivateEnemySlot`.

There are three static callers. One follows an AI link-mask path near `$B1AB`;
two more consume linked slot indices during the object cleanup pass beginning
at `$C104`. The link-field meanings remain offset-based until those larger
callers are reconstructed.

---

## Current enemy deactivation

`src/game/enemies/runtime.asm` owns CPU `$B4B6-$B4C3`. It clears
byte 0 in the records selected by `EnemyAiPointer` and `EnemyObjectPointer`,
then writes the hidden/offscreen `$F8` sentinel to object offset 7.

This is the current-record counterpart to `DeactivateEnemySlot` at `$B492`.
The earlier routine accepts a slot index and resolves both pointers itself;
`DeactivateCurrentEnemy` relies on the dispatcher-selected shared pointers and
therefore needs only fourteen bytes.

All eleven static uses are tail-calls from enemy behavior paths. Returning
from this helper consequently returns directly to the AI dispatcher caller
after the current slot has been retired.
