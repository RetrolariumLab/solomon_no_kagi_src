# Countdown timer

`src/game/timer/runtime.asm` owns CPU `$A15F-$A225`. The upstream Bisqwit map names
the public entries at `$A15F` and `$A183` as `DecrementTimer` and
`DecrementTimerByOne`; the instruction flow and RAM accesses independently
confirm countdown arithmetic over the four decimal timer digits.

`GameplayUpdateCount` is an eight-bit accumulator incremented by
`UpdateNmiGameplayFrame`. `MainGameplayThread` calls `DecrementTimer` before
`UpdateEnemiesMovement`: the timer snapshots the count without clearing it,
then the enemy prepass consumes the same value and clears the accumulator.
Repeated main-thread passes in one video frame therefore see zero after the
first pass, while a delayed pass sees all gameplay NMI ticks accumulated since
the previous prepass.

For each pending tick, the timer adds `TimerDecrementSpeed` to `TimerFraction`.
A carry subtracts `TimerDecrementStep` from `TimerDigit10` and propagates
decimal borrow through the higher digits. Bit 7 of `TimerDecrementStep` records
that the internal digits changed.

When the PPU update stream is free, the routine calls
`BuildTimerDisplayUpdate` at `$A238`. A busy stream defers only the HUD write:
the arithmetic has already consumed every pending tick, bit 7 remains set,
and a later pass publishes the current digits. Intermediate visual values can
therefore be skipped, but the internal countdown catches up. If the builder
reports an all-zero timer, scheduler code `$33` is started. The final part
compares the two high timer digits with a four-entry BCD threshold table at
`$A229`, queues one of two PPU update streams, and toggles bit 4 of
`TimerWarningState` as the threshold is crossed. The thresholds are `$02`,
`$04`, `$10`, and `$23`.

`src/data/timer_warning.asm` owns `$A226-$A237`. The fourth threshold byte at
`$A22C` is deliberately shared with `EnterTimerWarningPpuUpdate`: the two
six-byte streams write two literal bytes at PPU `$23C2`, using `$F0,$30` on
entry and `$A0,$20` on exit. The three bytes at `$A226-$A228` duplicate the
`$20,$69,$44` timer HUD command header, but their consumer has not yet been
proved, so the source keeps the conservative `PreTimerWarningTableBytes` name.

## Display update builder

`src/game/timer/display.asm` owns `$A238-$A273`. It constructs a small update
program in RAM at `$03E6`: a copied three-byte `JSR $4469` prefix, the four
timer digits in most-significant-first order, and two zero terminators. Leading
zero digits are replaced with blank tile `$24`. The OR of all four digits is
left in `TimerDisplayNonzeroAccumulator`, which lets `DecrementTimer` detect
an all-zero countdown after the builder returns.

The builder tail-calls `PublishPpuUpdateBuffer`, which publishes `$03E6`
through the shared PPU update pointer. The `$20,$69,$44` bytes decode as a
literal five-tile command targeting PPU `$2069`; their instruction-like
appearance as `JSR $4469` is incidental.

## Runtime cadence

The deterministic runtime harness counts `DecrementTimer` calls and pending
ticks over the first 60 frames after `MainGameplayThread` starts. The first
call also exposes a room-intro backlog: 87 ticks in Room 1 and 64 in the
attract demo. After that initial batch, the lightly populated room executes
203 timer calls across all 60 frames and consumes all 59 new counter
increments one at a time. The populated attract room executes only 52 calls
across 52 frames, consumes 58 of 59 new increments, and leaves the final tick
queued at the cutoff. Delayed calls process at most two ticks.

This proves that cooperative main-thread load does not lose countdown ticks:
consumed steady-state ticks plus the queued remainder equal the observed
nonzero writes to `GameplayUpdateCount` in both scenarios. Neither trace takes
the NMI skip path. This does not make the timer an unconditional wall-clock:
the NMI handler deliberately skips gameplay services when the interrupted
context's local stack offset is below `$08`, and such a video frame cannot be
recovered because it never increments the accumulator. The eight-bit counter
would also wrap after 256 unconsumed gameplay updates, although the measured
maximum backlog after room entry is two.

`make trace-runtime` reproduces both measurements and validates their exact
summary strings against `scenarios/runtime_scenarios.json`.
