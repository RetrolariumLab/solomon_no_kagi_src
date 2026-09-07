# Enemy slot allocation

`src/game/enemies/slot_allocation.asm` owns CPU `$B42A-$B445` and provides
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
