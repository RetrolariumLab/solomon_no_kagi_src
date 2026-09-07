# Scaled coordinate deltas

`src/game/objects/update_pipeline.asm` owns CPU `$C364-$C385`. Five callers use the
same scratch-register contract when seeding room-entry, room-clear, enemy, and
other transition motion.

```text
input:
  $02 = origin Y
  $03 = origin X
  $04 = target Y
  $05 = target X

output:
  $02-$03 = signed 16-bit (target Y - origin Y) * 4, low/high
  $04-$05 = signed 16-bit (target X - origin X) * 4, low/high
```

`BuildScaledCoordinateDeltas` processes X then Y. For each eight-bit
difference, Y becomes `$00` or `$FF` according to subtraction borrow and is
used as the sign-extension byte. Two `ASL`/`ROL` pairs multiply the signed
16-bit value by four. The final two-register swap changes the temporary
interleaved layout into the conventional Y-low/Y-high/X-low/X-high order.

The arithmetic contract is fully determined by instruction flow and all five
call sites. The later consumer's physical unit (velocity, animation step, or
fixed-point increment) remains context-specific and is not baked into the
symbol name.
