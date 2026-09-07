# Object X-coordinate left-surface clamp

`src/game/objects/clamp_x_left.asm` owns CPU `$8A7F-$8AA3`. Its three callers
operate on the object selected by `TempPointer08` during collision handling.

Calling convention:

```text
input:      TempPointer08 = object record
output:     object byte 10 has low nibble $4
            object bytes 9 and 8 are zero
preserved:  none of A, X, Y
clobbered:  A, X, Y, CoordinateClampDelta
```

The arithmetic computes the positive adjustment needed to place X at the
`...4` inset of a 16-pixel cell. Exhaustive evaluation of all 256 input bytes
shows that results always have low nibble `$4`; inputs already at `$4` remain
unchanged, while larger low nibbles advance into the following cell. Combined
with clearing the X fraction/motion fields, this is the response to a surface
on the object's left. The directional name is high-confidence; the byte-level
postcondition is confirmed directly by the instruction sequence.

The complementary right-surface routine at `$8AA4` shares
`ClearObjectXMotion`. Because ca65 cannot encode a relative branch relocation
between the two linker segments, that branch remains explicitly encoded as
`.byte $D0, $DD` with an explanatory source comment. Byte identity and the
target label address are both audited.
