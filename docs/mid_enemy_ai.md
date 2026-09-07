# Mid-table enemy AI families

`src/game/enemies/ai_mid.asm` owns CPU `$A68C-$A997`. It reconstructs four
unique targets used by the 28-word enemy AI handler table while keeping enemy
names neutral until type-to-creature identities are verified in play.

Each family begins with `LoadEnemyActionSelector`, which divides object action
byte 3 by four, followed by `JumpWithParams` and an inline little-endian action
table. The source expresses all four tables as `.addr`; bytes that looked like
overlapping instructions in the preservation listing are therefore recognized
as dispatcher data.

The `$10-$13` family has two actions. One resets phase and action state after a
threshold; the other allocates a free linked enemy slot and stores its index in
AI byte 6. The `$6C-$6F` family has seven action entries. Three paths use
different proximity thresholds before scheduling thread `$31`, while the
shared overlap helper compares Dana and enemy X coordinates over a ten-pixel
window.

The `$54-$5B` pair of dispatch entries share one seven-action table. Its main
update probes motion thresholds and the forward RoomMap cell, changes facing,
and can reserve two free enemy slots. Allocation is transactional: if the
second slot is unavailable, the first temporary record is disabled again.

The `$08-$0B` family handles fairy collection and a two-axis correction step.
Collection increments `FairiesCollected`, queues the normal item presentation,
and on every tenth fairy takes the extra-life presentation path. Its motion
routine uses four small signed-adjustment/limit tables at `$A988-$A997` to
update object Y and X motion while retaining a direction value in AI byte 6.

Action targets beyond this range now resolve to symbols in the later enemy-AI
modules. This module assembles to exactly 780 bytes, and `make verify-prg`
proves it is identical to the original PRG image.
