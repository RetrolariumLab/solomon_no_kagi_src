# Enemy AI handler dispatch

`src/game/enemies/early_ai.asm` owns CPU `$A469-$A4A5`. Bisqwit's map names
the entry at `$A469` `MaybeRunOneEnemyAI`; this reconstruction uses
`DispatchEnemyAiHandler` because the routine performs two shifts and delegates
through the generic appendix dispatcher at `$8EA9`.

The 28 words immediately following that `JSR` are not executable fallthrough
bytes. `JumpWithParams` consumes them as an inline little-endian handler table
and transfers control to the selected target. Repeated targets are meaningful:
the table contains 28 entries but only 14 unique handler addresses.

`make enemy-ai-report` prints the decoded table from the built PRG.
`make enemy-ai-audit` compares every pointer with
`config/enemy_ai_handlers.json`; the audit is part of `make release-check`.
An assembly assertion independently fixes the source table at 28 entries.
The table and all 14 unique target addresses are physically identical in USA
and PAL. `make enemy-ai-profile-audits` verifies that shared contract against
both source-built ROMs rather than inferring it from the source conditionals.

The first two targets are source-owned as `RunType00To03EnemyAi` and
`RunType04To07EnemyAi` in `src/game/enemies/early_ai.asm`. Their shared contact
path awards score, an extra life, or an inventory effect. Four more handler
targets are source-owned in `src/game/enemies/mid_ai.asm`: the `$08-$0B`,
`$10-$13`, `$54-$5B`, and `$6C-$6F` type families. The `$14-$17` and `$18-$1B`
targets and their shared path selector are reconstructed in
`src/game/enemies/pathfinding_ai.asm`. `src/game/enemies/collision_ai.asm` owns the
repeated `$1C-$37` target and the `$5C-$63` target. The remaining `$0C-$0F`,
`$48-$53`, and `$64-$6B` targets are source-owned in
`src/game/enemies/late_ai.asm`; all 28 table entries are now symbolic.
