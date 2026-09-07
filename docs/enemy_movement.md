# Enemy movement prepass

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
records. `docs/enemy_ai_record.md` gives the complete AI layout;
`docs/enemy_ai_dispatch.md` describes the next consumer of the parallel pools.
