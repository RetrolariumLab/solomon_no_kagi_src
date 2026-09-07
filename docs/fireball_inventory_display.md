# Fireball inventory display

`src/graphics/hud/fireball_inventory.asm` owns CPU `$A30C-$A39A`; its
three tile/header tables occupy `$A39B-$A3A3`. Both known callers refresh the
HUD after packed fireball inventory can have changed: Dana's successful cast
at `$9B74` and `RefreshGameplayHud` at `$C3DA`.

The routine first waits until the shared PPU stream pointer is idle, then
builds two literal 11-tile commands in `PpuUpdateBuffer`. Their destination
addresses are `$2054` and `$2074`, so the rows are vertically adjacent in the
nametable. Each command header is stored in reverse ROM order because the
three-byte copy loops count X down from 2 while advancing the RAM destination.

## Packed-slot decoding

`InventorySlotsHigh` and `InventorySlotsLow` contain eight two-bit values.
The top-row loop copies them to scratch bytes `$04-$05`, shifts the pair twice
per cell, and rotates the outgoing value into A. Encodings 1 and 2 select top
tiles `$B0` and `$B1`. Zero ends occupied-slot decoding; the remaining usable
capacity from `InventorySlotCount` is drawn with `$B4`, and cells outside that
capacity are blanked with `$24`. Tile `$A5` is emitted as the row's left cap.

The bottom row is derived from the completed top row already resident at
`PpuUpdateBuffer + 3`. Negative top tiles are converted by adding 2. When the
first nonnegative blank is reached, the routine backs up one destination byte
and fills the tail with `$B7` until it encounters `$20`, the high address byte
of the following command header in the top-row buffer. A zero byte terminates
the complete update program before `PublishPpuUpdateBuffer` publishes it.

This reconstruction names only the observed tile roles. Their exact artwork
depends on the selected CHR bank and is not inferred from numeric tile values.
