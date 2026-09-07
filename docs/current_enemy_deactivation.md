# Current enemy deactivation

`src/game/enemies/current_deactivation.asm` owns CPU `$B4B6-$B4C3`. It clears
byte 0 in the records selected by `EnemyAiPointer` and `EnemyObjectPointer`,
then writes the hidden/offscreen `$F8` sentinel to object offset 7.

This is the current-record counterpart to `DeactivateEnemySlot` at `$B492`.
The earlier routine accepts a slot index and resolves both pointers itself;
`DeactivateCurrentEnemy` relies on the dispatcher-selected shared pointers and
therefore needs only fourteen bytes.

All eleven static uses are tail-calls from enemy behavior paths. Returning
from this helper consequently returns directly to the AI dispatcher caller
after the current slot has been retired.
