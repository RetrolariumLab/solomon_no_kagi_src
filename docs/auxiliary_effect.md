# Auxiliary effect object

`src/game/scoring.asm` owns CPU `$C718-$C73A`. It initializes the
shared object record at `AuxiliaryObject` (`$05BB`) through two entry points:

- `SpawnAuxiliaryEffectAtMapCell` converts `MapCellIndex` in `$04` to pixel
  coordinates, initializes the object, and preserves the caller's `A` value;
- `SpawnAuxiliaryEffectAtCoordinates` accepts Y/X in `$04/$05`, writes object
  offsets 7 and 10, and copies a four-byte template to offsets 0 through 3.

The fixed template is `$C6,$1C,$FF,$0C`. Its individual field meanings remain
unassigned; what is confirmed is that all three coordinate-based callers
create the same auxiliary record state. Two callers provide the current enemy
position and the wrapper is used by two item-acquisition paths. The neutral
`AuxiliaryEffect` name records this shared role without claiming a particular
sprite, score popup, or animation until runtime traces identify it.
