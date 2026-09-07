# Gameplay HUD refresh

`src/graphics/hud/runtime.asm` owns CPU `$C3D4-$C3FD`, the five-byte fairy
template owns `$C3FE-$C402`, and `src/graphics/hud/runtime.asm` owns
`$C403-$C42D`. Together they construct and serialize the score, packed
fireball-inventory, and collected-fairy updates that form the gameplay HUD.

`RefreshGameplayHud` builds the score update, publishes it, calls
`BuildFireballInventoryDisplayUpdate`, and tail-calls the fairy-count builder.
Both later builders begin by waiting for `PpuUpdateStreamPointer + 1` to clear,
so none overwrites `PpuUpdateBuffer` before NMI has consumed the preceding
program.

## Collected fairies

`BuildAndPublishFairyCountDisplay` copies a five-byte template to the shared
buffer, replaces its payload byte with `FairiesCollected`, and publishes it.
The template is one literal byte at PPU `$2071`, followed by the stream
terminator.

## Score

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
