# Object Y-coordinate surface clamp

`src/game/objects/clamp_y.asm` owns CPU `$8A62-$8A7E`. Bisqwit's map names its
single entry `ObjectClampYCoordinateToSurface`; all three static callers now
use that symbol.

Calling convention:

```text
input:      TempPointer08 = object record
output:     object byte 7 aligned down to a multiple of 16
            object byte 5 reduced to its previous sign bit ($00 or $80)
preserved:  none of A, X, Y
clobbered:  A, X, Y, TempPointer0A
```

Byte 7 is the integer Y coordinate shared by the `$14`-byte object layout. The
routine saves its low nibble in scratch byte `$0A` and subtracts it, snapping
the coordinate to the top of the containing 16-pixel row. It then rotates the
old high bit of signed Y-motion byte 5 through carry into a fresh zero
accumulator, retaining only `$00` or `$80`. The adjacent byte 6 is the Y
fraction consumed by the shared movement integrator.

The three callers combine the clamp with the now-reconstructed left/right
horizontal surface helpers documented in `docs/object_x_left_clamp.md` and
`docs/object_x_right_clamp.md`.
Collision responses also use `ObjectClampYCoordinateToThirteenInset`, which
aligns the same integer Y field to low nibble `$D` while clearing byte 6 and
preserving only the sign of motion byte 5.
