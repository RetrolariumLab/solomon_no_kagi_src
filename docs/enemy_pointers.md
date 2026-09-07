# Enemy record pointer helpers

`src/game/enemies/pointers.asm` owns CPU `$B28A-$B2A1`. Its two entry points
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
`src/data/enemies/record_pointers.asm`; see `docs/enemy_record_pointers.md`.
