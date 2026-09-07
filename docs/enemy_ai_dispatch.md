# Enemy AI dispatcher

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
four and indexes the 28-entry table documented in `docs/enemy_ai_handlers.md`.
The subtraction deliberately consumes the carry left set by the successful
state comparison, so no separate `SEC` is required.
