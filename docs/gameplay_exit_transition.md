# Gameplay-exit transition

`src/game/flow/exit_transition.asm` owns CPU `$C78A-$C980`. Four scheduler
entries enter different stages of the same cooperative exit pipeline:

| Code | Entry | Role |
| ---: | --- | --- |
| `$33` | `RunTimeOverTransition` | cycle PPUMASK and publish `TIME OVER.` |
| `$31` | `RunDanaDeathTransition` | configure and wait for Dana's death fall |
| `$35` | `FinalizeGameplayExit` | clear gameplay pools and select the outcome |
| `$16` | `PreparePostGameResult` | calculate and display `YOUR GDV` |

The scheduler stores each entry address minus one because `StartThread`
constructs an RTS frame. `src/system/scheduler.asm` now expresses all four
entries with symbols while preserving the original words.

## TIME OVER and Dana death

The `$33` path calls `ResetRoomTransitionState`, converts active non-Dana
records to state zero, and advances a counter once every four gameplay update
ticks. Its low two bits select `LifeLossPpuMaskCycle`; the chosen value is
merged into `PpuMaskShadow`. After 24 steps, the path restores PPUMASK, clears
the gameplay nametable region, and publishes `TimeOverPpuUpdateStream`.

The independent `$31` path also begins with the shared reset. It selects
facing-preserving death action `$20/$21`, converts other active objects to
state `$80`, then activates Dana in state `$C0` with Y motion `$C3` and yields
until `DanaYPosition` reaches `$D1`. At that boundary it advances the action
to `$22/$23`. Both paths converge at `FinalizeGameplayExit`.

## Result calculation and persistence

When the exit consumes the last remaining life, entry `$16` computes a compact
post-game value from three zero-page factors, state bits, collected Solomon
Seals, and the leading score digits. The three factors are named
`GdvFactor0..2`: their participation in the formula is established, but their
individual gameplay meanings remain intentionally undecided.

The ROM's PPU template decodes literally to `YOUR GDV`. The calculated value
is compared with the batteryless warm-RAM value at `$07F4`, formatted through
`FormatTwoDigitNumberTiles`, and inserted into the template. The same path
compares all eight unpacked score digits against `$07F6-$07FD` and replaces
that persistent best-score record when the current score is not lower.

The `$07F4` and `$07F6` storage aliases coexist with their startup-oriented
names: reset initializes this warm-RAM region only when its four-byte signature
does not match. This explains how the best GDV and score survive soft resets
without claiming any nonvolatile storage.

## Exit decisions

After publishing the result update, the thread waits for either controller
code `$C8` or the high byte of the reused presentation counter to reach two.
The first route clears score and selected state bits and prepares three lives;
the second starts post-game scheduler code `$17`. Ordinary life loss decrements
`RemainingLives` and starts room-load code `$15`.

Every route clears the gameplay nametable, starts the selected context, resets
fireball and Dana state, and stops context 3. Exact gameplay meanings for
unresolved flag bits remain expressed as local masks instead of stronger RAM
aliases.

## Runtime evidence

The deterministic `room-1-life-loss-reload` scenario enters Room 1 naturally,
then places scheduler code `$31` in `PendingThreadStarts` at frame 720. This is
the scenario's only controlled write. It does not patch object, life, or timer
data, any ROM byte, or the scheduler stack. Context 0 consumes the request and
enters
`RunDanaDeathTransition` at frame 721. Dana reaches the `$D1` fall boundary at
804, and `FinalizeGameplayExit` selects `ReloadRoomAfterLifeLoss` at 853. The
original routine stores two remaining lives and starts `RoomLoadThread` on
frame 854. By frame 1800 the same room is back in main gameplay with Dana at
the normal Room 1 start position.
