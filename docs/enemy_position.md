# Current enemy position helper

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
