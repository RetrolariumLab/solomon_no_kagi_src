# Fireball lifetime service

`src/game/items/fireball_lifetime.asm` owns CPU `$A3A4-$A3D6`. Bisqwit's map labels
the entry `MaybeRunFireballAI_1`; the narrower reconstructed name
`UpdateFireballLifetime` reflects what this routine proves directly.

The entry returns immediately unless `FireballObject` is active (bit 7 set).
For an active fireball it compares the 16-bit configured lifetime at
`$0432-$0433` with the first 16-bit life counter at `$042C-$042D`. When the
counter has exceeded the configured lifetime, the routine clears
`FireballActive` and the low counter byte, then writes state `$04` to object
offset 3.

On later calls with `FireballActive` clear, a low counter value of at least
eight retires the object by clearing its first byte. This establishes a short
post-expiration cleanup interval without assigning semantics to the remaining
fireball record fields.

The deterministic `room-1-cast-fireball` scenario supplies one inventory slot
and lifetime `$0010` through three declared RAM writes, then uses ordinary B
input. It observes activation at frame 722, the first NMI collision service at
723, active-state clearing and the cleanup branch at 739, and object retirement
eight frames later at 747. This binds both phases of the service to runtime
behavior in the byte-identical build.

The adjacent services at `$A3D7` and `$A3F8` initialize and render object
records and remain the next evidence boundary.
