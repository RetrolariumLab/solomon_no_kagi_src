# Controller input

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
