# Enemy slot deactivation

`src/game/enemies/deactivation.asm` owns CPU `$B492-$B4B5`. The routine accepts
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
