# Demon Mirror runtime

The complete `$A04C-$A15E` range is the runtime consumer for the two Demon
Mirror schedules, enemy sets, coordinates, and allocated enemy slots.
`MainGameplayThread` first calls `UpdateDemonMirrorSpawnSchedule`, then
`ActivatePendingDemonMirrorEnemies` on every service pass.

## Runtime state

Room metadata decoding resolves two eight-byte schedule pointers at
`$0036/$0038`, two variable-length enemy-set pointers at `$003A/$003C`, and
two mirror Y/X positions at `$0441-$0444`.

The ROM definitions are source-owned at `$DC00-$DCEB` in
`src/game/demon_mirror/schedule.asm`: split pointers select 16 fixed-size
schedules and 17 variable-length enemy-set streams. Count, adjacency, and total
payload assertions guard all four data segments.

The NMI increments the shared 16-bit counter at `$043C-$043D`. The mirror
runtime uses the following adjacent bytes:

| Address | Meaning |
| ---: | --- |
| `$043C-$043D` | NMI-incremented spawn timer |
| `$043E` | phase/loop state in bits 0-5; pending mirrors in bits 6-7 |
| `$043F-$0440` | independent enemy-set stream offsets |
| `$0441-$0442` | two mirror Y positions |
| `$0443-$0444` | two mirror X positions |
| `$0445-$0446` | allocated enemy slot for each mirror |

## Schedule sampling

The sampler derives a six-bit phase equivalent to `(timer >> 6) & $3F`.
The low three bits select one bit within a schedule byte; phase divided by
eight selects one of eight bytes. Bits are consumed most-significant first:
phase 0 tests bit 7, while phase 7 tests bit 0.

Each schedule therefore has two halves:

```text
bytes 0-3  phases 0-31, played once after room start
bytes 4-7  phases 32-63, retained as the looping half
```

State bit 5 latches after the initial half so later timer wraparound repeats
bytes 4-7 instead of returning to bytes 0-3. State bits 6 and 7 block new
sampling while one or both placeholder objects await activation.

A set schedule bit is accepted only when `ActiveEnemyCount <= 14`. The two
accepted carries are packed into bits 6-7 and passed to
`SpawnScheduledDemonMirrorObjects`.

## Placeholder allocation

For each accepted mirror trigger, the spawn routine calls
`FindFreeEnemySlotIndex`. A successful allocation:

1. stores the enemy slot at `$0445 + mirror_index`;
2. writes active marker `$80` into AI record byte 0;
3. copies the selected mirror's decoded Y/X coordinates;
4. initializes the object header with state `$C6`, type `$04`, cached byte
   `$FF`, and action `$0C`.

Only successful allocations remain packed into state bits 6-7. This prevents
the activation pass from configuring a slot that was not actually reserved.

## Delayed enemy activation

Pending placeholders are activated once `timer_low & $3F` reaches `$18`.
Each mirror owns an independent enemy-set pointer and stream offset. A value
below `$90` is an enemy type and is passed to `ConfigureEnemyType` for the
saved slot. A byte `$90+n` does not spawn an enemy; it replaces that mirror's
stream offset with `n` and decoding continues. This provides a compact cyclic
enemy sequence without a separate length field.

After the pending bits are consumed, `$043E` retains only its low six phase
bits and schedule sampling may resume.

All 17 streams end with `$90`, which is the compact loop command `$90+0` and
therefore restarts each stream at byte zero after its last enemy type.

The older Bisqwit map called `$A04C/$A0A7` possible fireball AI. The resolved
schedule/enemy-set pointers, mirror coordinates, two-slot state, and skchain
format specification provide stronger evidence for the Demon Mirror names now
used by the source.
