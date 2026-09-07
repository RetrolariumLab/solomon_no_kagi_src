# Room-map coordinate conversion

`src/game/objects/update_pipeline.asm` owns CPU `$918A-$91B8`. Bisqwit's map
independently names both entry points. Together they define the bridge between
pixel coordinates and the packed byte used to index the 16-column `RoomMap`.

The shared zero-page contract is:

| Value | Address |
| --- | --- |
| pixel Y / packed map index | `$04` |
| pixel X | `$05` |

`ConvertPixelCoordinatesToMapIndex` applies:

```text
index = ((Y - $10) & $F0) | ((X - $08) >> 4)
```

It returns the index in `A`, `X`, and `$04`. The inverse
`ConvertMapIndexToPixelCoordinates` expands the high and low nibbles:

```text
Y = (index & $F0) + $10
X = (index & $0F) * 16 + $08
```

For example, index `$B5` maps to pixel Y=`$C0`, X=`$58`; the upper and lower
nibbles therefore represent logical row 11 and column 5. The `$10/$08` origin
places gameplay points within each 16-pixel logical cell rather than at the
PPU nametable origin.

All 31 static calls now use the semantic symbols. This module describes only
coordinate packing; tile meaning and collision state remain owned by the room
pipeline.
