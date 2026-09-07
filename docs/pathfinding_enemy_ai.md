# Pathfinding enemy AI

`src/game/enemies/ai_pathfinding.asm` owns CPU `$A998-$AD36`. The first 209
bytes complete the three still-external actions of the `$08-$0B` handler
table: phase-to-action promotion, horizontal orientation, and vertical
orientation. `CheckEnemyAiDeltaRange` then checks both signed AI motion deltas
against the same compact threshold and preserves the original carry contract.

`RunType14To17EnemyAi` and `RunType18To1BEnemyAi` share the remaining path
selector. Their only difference is a four-entry offset into the initial
fractional-delta tables. The routine advances a candidate fixed-point
position, samples four RoomMap cells around each of two candidate coordinates,
and packs the solid/open results into two four-bit masks.

The primary mask selects one of 16 inline `.addr` entries. The handlers use
the secondary mask, current direction, coordinate low nibbles, and four small
direction maps to choose the next direction or snap a candidate coordinate to
a tile boundary. Every exit either stores direction bytes 6/7 or commits the
candidate Y/X bytes to object offsets 7/10.

The direction fields now have shared names because the fireball collision
path proves the same contract independently. It temporarily points
`EnemyAiPointer` at `FireballActive`, placing `FireballDirectionIndex` and
`FireballAlternateDirectionIndex` at AI offsets 6 and 7 before dispatching
these handlers. Direction values 0 through 3 mean right, left, up, and down.

Three handlers deliberately share the short trampoline at `$ABAD`, and some
mask paths contain branches whose fallthrough is unreachable from that entry.
Those shapes are retained because they are part of the original machine code,
not simplified pseudocode. The segment is exactly 927 bytes and remains
byte-identical under `make verify-prg`.
