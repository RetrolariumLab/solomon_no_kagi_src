# Enemy slot initialization

`src/game/enemies/initialization.asm` owns CPU `$A3D7-$A3F7`. Bisqwit's map
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
