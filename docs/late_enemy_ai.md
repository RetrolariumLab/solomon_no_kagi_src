# Late enemy AI families

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
