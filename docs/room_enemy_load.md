# Room enemy loading

`LoadRoomEnemies` at `$961B-$9660` turns the current room's compressed enemy
record into live runtime slots. `CurrentRoomIndex` selects one of 53 split
pointers at `$DCEC/$DD21`; the resulting stream uses the format already
round-tripped by `scripts/authoring/room_data.py`.

Both pointer halves and all 53 streams are source-owned in the 552-line
`src/data/rooms/enemies.asm`. Each record is expressed with macros for the
encoded lifetime, `(enemy_type, map_position)` pair, and terminator; the source
can be reproduced with `scripts/authoring/room_data.py --source-enemies`.

The first byte is split into `EnemySpawnLifetimeThresholdLo` (`bits 7..5`) and
`EnemySpawnLifetimeThresholdHi` (`bits 4..0`). `ApplyEnemyLifetimeThreshold`
subtracts these from AI-record bytes 2-3 as a low/high threshold pair. Each
following record contains an enemy type and packed 16-column map position;
type zero terminates the stream.

For every record, the loader:

1. asks `FindFreeEnemySlotIndex` for an inactive AI record;
2. marks that AI record active with bit 7;
3. converts the packed map position to pixel Y/X;
4. calls `InitializeEnemy` for the parallel records;
5. calls `ConfigureEnemyType` with the decoded type.

The loader assumes room data never exceeds the 17-slot enemy pool. That
invariant is independently exercised by the all-room decoder and pointer
audits in `make check`.
