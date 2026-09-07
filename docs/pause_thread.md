# Pause thread

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
