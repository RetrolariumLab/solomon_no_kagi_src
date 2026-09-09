# Gameplay runtime

This guide follows the main gameplay thread, input, cooperative waits, pause handling, HUD work, and exit transitions.


---

## Main gameplay thread

`src/game/flow/runtime.asm` owns CPU `$A000-$A04B`. Scheduler code `$30`
selects context 3, selector 0. Its table slot contains `$9FFF`; because the
scheduler enters the context with `RTS`, this proves `$A000` is the entry point.

The loop invokes four groups of services and yields through `SwitchThreads`
after each group. It then checks `FairiesQueued`, attempts to allocate and
initialize the next fairy when one is pending, and returns to
`MainGameplayThread`. Both the no-fairy path and the failed-allocation path
converge at `ContinueMainGameplayThread`.

The first two services are now source-owned as
`UpdateDemonMirrorSpawnSchedule` and `ActivatePendingDemonMirrorEnemies`.
Together they sample both room schedules, allocate mirror placeholders, and
later configure their saved enemy slots from cyclic enemy sets. The former raw
service at `$C432` is now `CheckDanaMapTileInteraction`; it samples the map
cell under Dana and dispatches collectible effects. See
`docs/demon_mirror_runtime.md` and `docs/item_system.md#item-interactions`.

---

## Controller input

`src/system/boot_and_frame.asm` owns CPU `$837D-$83C1`. `ReadJoyPads` is
called once on the active NMI service path after the frame counter and
`RenderGameplayObjectsToOam` have run.

The routine strobes `JOYPAD1`, then calls `ReadJoyPad` with `X=0` and `X=1`.
Each call performs eight serial reads from `JOYPAD1,X` and stores the assembled
value in `Joypad1Raw,X`. The two rotates around `ORA ControllerPortSample`
fold port bits 0 and 1 together before shifting the result into the accumulator.
This accepts serial controller data exposed on either hardware bit.

After eight samples, the first button read occupies bit 7 and the final button
occupies bit 0. The resulting layout is:

```text
bit  7       6       5       4       3     2       1      0
     A       B       Select  Start   Up    Down    Left   Right
```

The cache update has two statically confirmed modes selected by bit 0 of
`GameStateFlags`:

- when set, both cached bytes are replaced by their complete raw values;
- when clear, only Select and Start are refreshed, while the cached A, B, and
  directional bits retain their prior values.

The larger game-state meaning of bit 0 and the reason for preserving gameplay
buttons in the second mode remain unresolved. The byte-level input and cache
contracts do not depend on assigning that policy a speculative name.

---

## Pause thread

`src/system/thread_runtime.asm` owns CPU `$8E47-$8E8C`. The scheduler's context
2 table begins at `$8E29`; selector 1 stores return address `$8E46`, proving
that packed thread code `$21` enters `PauseGameThread` at `$8E47` through the
scheduler's RTS-plus-one convention.

The thread performs this sequence:

1. queue sound command `$0C`, clear `NmiFrameCounter`, and initialize a
   nonzero Start-button latch in `X`;
2. wait at least `$28` NMI ticks while observing release of the original Start
   press;
3. set game-state flag `$04` and ensure the original press is released;
4. wait for a new Start press and then its release;
5. clear game-state flags `$06`, queue sound command `$0E`, and stop scheduler
   context 2.

`ClearStartLatchWhenReleased` is intentionally asymmetric: it leaves `X`
unchanged while `Joypad1Cached & JOY_BUTTON_START` is nonzero and clears `X`
after release. The surrounding loops therefore use `X` as a one-bit latch
without modifying it on every poll.

`NmiFrameCounter` is incremented on the active NMI service path. The `$28`
threshold supplies a minimum debounce/pause-transition delay.

The deterministic `room-1-pause-resume` runtime scenario presses Start on
frames 720-721 after natural Room 1 entry. `PauseGameThread` begins at frame
722 and the `$04` active bit appears at frame 762, exactly 40 frames later.
A distinct Start pulse on frames 800-801 is observed by the thread; release
clears the pause flags at frame 803, and `UpdateDanaControlState` resumes at
frame 804. The timer remains `04070900` throughout the active interval. The
trace validator also forbids any Dana-control update between activation and
clear, proving that normal gameplay work stays suspended during this window.

---

## Cooperative counter wait

`WaitForZeroPageCounterAboveThreshold` at `$9C52-$9C5F` provides a shared
delay primitive for the cooperative scheduler. The caller supplies an
unsigned threshold in `A` and a zero-page counter address in `X`. The routine
preserves both values across `SwitchThreads` and returns only after the
selected counter becomes strictly greater than the threshold.

All current call sites select bytes in `$20-$27`. The active gameplay path in
NMI increments every byte in that range once per serviced frame, so callers
can reset one counter and wait without blocking the other cooperative
contexts. The comparison is `CMP ZeroPageCounterBase,X` followed by `BCS`:
equality therefore continues waiting, and counter wraparound is not handled
inside this routine.

### Standard gameplay delay setup

`ResetAndSelectGameplayDelayCounter` at `$915E-$9164` prepares the most common
calling convention. It clears `GameplayDelayCounter` at `$21` and returns
`X = $21`, ready for `WaitForZeroPageCounterAboveThreshold`. Seven call sites
use this pair for delays with thresholds from `$08` through `$A0`.

---

## Cooperative masked-RAM waits

`src/system/thread_runtime.asm` owns CPU `$9165-$9189`. Its two entries use
the same zero-page calling convention:

```text
input:      A = bit mask
            X = zero-page address
output:     wait condition satisfied
preserved:  A, X
changed:    Y = input mask
```

`WaitForMaskedBitsClear` returns when `(A & RAM[X]) == 0`;
`WaitForMaskedBitsSet` returns when `(A & RAM[X]) != 0`. While the condition is
not satisfied, each routine saves its arguments on the current context's
hardware-stack partition, calls `SwitchThreads`, restores the arguments, and
checks again. Ten direct callers now use these names.

The second routine ends with a conditional branch rather than a trailing
`RTS`. `SwitchThreads` is statically proven to return with carry set, so the
branch always returns to the wait head after a yield. The only normal exit is
the earlier `BNE FinishMaskedRamWait`, which removes the two saved values and
returns. This unusual fall-through edge is part of the scheduler ABI and is
preserved byte-for-byte.

---

## Secondary-thread transition reset

`src/system/thread_runtime.asm` owns CPU `$C756-$C789` and has six
direct callers. `ResetOtherSecondaryThreads` accepts in `X` the secondary
context that must remain active during a scene transition.

The routine first waits cooperatively for `GameStateFlags & $02` to clear. It
then advances a context index seven times modulo eight. Index 0 is skipped;
the input index is excluded because seven advances return to it only after the
loop is complete. Every other index from 1 through 7 is passed to `StopThread`.

After stopping those six contexts, it clears all four bytes at
`PendingThreadStarts`, clears bit 2 of `GameplayFlags`, and clears bit 0 of the
still-unidentified RAM byte `$87`. This establishes a common transition reset
boundary without assigning meanings to those two cleared flags beyond their
observed behavior.

Calling convention:

```text
input:      X = secondary context to keep active, 1..7
output:     contexts 1..7 except X stopped; pending starts cleared
clobbered:  A, X, ThreadStopIndex, RemainingThreadStops
preserved:  Y
```

---

## Gameplay HUD refresh

`src/graphics/hud/runtime.asm` owns CPU `$C3D4-$C3FD`, the five-byte fairy
template owns `$C3FE-$C402`, and `src/graphics/hud/runtime.asm` owns
`$C403-$C42D`. Together they construct and serialize the score, packed
fireball-inventory, and collected-fairy updates that form the gameplay HUD.

`RefreshGameplayHud` builds the score update, publishes it, calls
`BuildFireballInventoryDisplayUpdate`, and tail-calls the fairy-count builder.
Both later builders begin by waiting for `PpuUpdateStreamPointer + 1` to clear,
so none overwrites `PpuUpdateBuffer` before NMI has consumed the preceding
program.

### Collected fairies

`BuildAndPublishFairyCountDisplay` copies a five-byte template to the shared
buffer, replaces its payload byte with `FairiesCollected`, and publishes it.
The template is one literal byte at PPU `$2071`, followed by the stream
terminator.

### Score

`BuildScoreDisplayUpdate` waits for the update slot but deliberately does not
publish it; callers may extend the buffer before publication. It copies the
three-byte header `$20,$60,$47`, which describes eight literal bytes at PPU
`$2060`. Seven bytes come from `ScoreDigits[0..6]`; leading zero digits become
blank tile `$24`, and the eighth displayed byte is fixed to zero. A second zero
terminates the update program.

The score builder ends at `$C42D` and falls through to the shared `RTS` at
`$C42E`. The following bytes `$20,$60,$47` are solely the PPU header described
above; a linear disassembler renders them as the unreachable instruction
`JSR $4760`, but the actual item-interaction entry is `$C432`. The source keeps
the return, header data, and entry distinct in `src/game/items/collection.asm`.

---

## Gameplay-exit transition

`src/game/flow/runtime.asm` owns CPU `$C78A-$C980`. Four scheduler
entries enter different stages of the same cooperative exit pipeline:

| Code | Entry | Role |
| ---: | --- | --- |
| `$33` | `RunTimeOverTransition` | cycle PPUMASK and publish `TIME OVER.` |
| `$31` | `RunDanaDeathTransition` | configure and wait for Dana's death fall |
| `$35` | `FinalizeGameplayExit` | clear gameplay pools and select the outcome |
| `$16` | `PreparePostGameResult` | calculate and display `YOUR GDV` |

The scheduler stores each entry address minus one because `StartThread`
constructs an RTS frame. `src/system/thread_runtime.asm` now expresses all four
entries with symbols while preserving the original words.

### TIME OVER and Dana death

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

### Result calculation and persistence

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

### Exit decisions

After publishing the result update, the thread waits for either controller
code `$C8` or the high byte of the reused presentation counter to reach two.
The first route clears score and selected state bits and prepares three lives;
the second starts post-game scheduler code `$17`. Ordinary life loss decrements
`RemainingLives` and starts room-load code `$15`.

Every route clears the gameplay nametable, starts the selected context, resets
fireball and Dana state, and stops context 3. Exact gameplay meanings for
unresolved flag bits remain expressed as local masks instead of stronger RAM
aliases.

### Runtime evidence

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
