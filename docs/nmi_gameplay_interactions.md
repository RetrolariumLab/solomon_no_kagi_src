# NMI gameplay interactions

`src/game/nmi/gameplay_interactions.asm` owns `$80FF-$837C`, immediately after
the core NMI handler. The range contains three related services invoked by the
active-gameplay NMI path: enemy overlap scans, fireball-to-map collision, and
Dana action request setup.

## Enemy overlap scans

`CheckGameplayObjectInteractions` toggles `GameplayFlags` bit 7 and performs
the scans only on the negative half of that cadence. It exits when bit 4 is
already set, when Dana is inactive, or before the fireball scan when the
fireball object is inactive.

Both scans walk the 17 enemy-object pointer pairs from index 16 down to zero.
`CheckEnemyOverlapAtCoordinates` accepts the selected enemy pointer in
`TempPointer08` and an extent selector in X. It rejects inactive records and
selector-specific state bits, then compares integer Y/X coordinates against
the target rectangle. Carry clear reports an overlap.

The fireball path sets bit 0 in every overlapping enemy state. For fireball
types below `$10`, it also copies the type to `FireballLifeCounter1Hi`. At
least one contact queues scheduler code `$50`, whose context-five entry is
`ProcessDefeatedEnemyDrops`. A Dana contact sets `GameplayFlags` bit 4 and
queues code `$31`, the context-three death transition.

## Fireball map collision

`UpdateActiveFireballCollision` integrates the fireball's fractional and
integer position with one of four direction deltas. It samples the old and
new bounding positions through `BuildFireballRoomCollisionMask`. That helper
converts a rectangle crossing at most two rows and two columns into four
RoomMap sign-bit tests and returns their packed low-nibble collision mask.

Before dispatch, the routine temporarily makes `EnemyAiPointer` address
`FireballActive` and `EnemyObjectPointer` address `FireballObject`. The
16-entry split handler table targets the path-mask handlers reconstructed in
`src/game/enemies/pathfinding_ai.asm`. The pointer setup, mask construction, and
all table destinations are statically confirmed and assemble byte-for-byte.
This synthetic AI-record view also proves `$0430-$0431` as the current and
alternate four-way path directions at AI offsets 6 and 7.

## Dana action requests

The A-button and B-button NMI paths enter `TryStartBlockMagicAction` and
`TryStartFireballAction`. Both pass a context-one scheduler code to
`TryStartDanaAction`: `$11` selects `CastOrRemoveBlock`, while `$13` selects
`CastFireballFromInventory`.

The shared setup rejects incompatible gameplay flags and Dana actions outside
`$10-$1B`. An accepted request snapshots Dana's action and Y-motion as
`DanaSavedAction` and `DanaSavedYMotion`, selects the casting action, shifts
Dana's X coordinate, marks the action active, and submits the code through
`QueuePendingThreadStart`.

That queue has four slots at `$041F-$0422`. It searches slots 3 through 1 for
zero and uses slot 0 as the fallback. Startup drains the same array and calls
`StartThread` for each nonzero request.
