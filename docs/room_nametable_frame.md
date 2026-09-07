# Room nametable frame

`DrawRoomNametableFrame` at `$970B-$97A2` draws the fixed frame around the
30x24 room tile interior. Its sole caller is in the room initialization path.

## PPU layout

| Start | Increment | Output |
| ---: | ---: | --- |
| `$209F` | 32 | 24 bytes of pattern 0, then tiles `$A4,$A3` |
| `$209E` | 32 | 24 bytes of pattern 1 |
| `$2380` | 1 | 32 bytes of pattern 2, then 32 bytes of pattern 3 |
| `$23C0` | 1 | 64 zero attribute bytes |

The `$209E/$209F` transfers form the inner and outer right columns beginning
at nametable row 4. The `$2380` transfer fills rows 28 and 29, completing the
two-row bottom edge beneath the 24-row interior. Together these writes border
the 30-column area cleared by `Clear30x24NametableRegion`.

## Transfer behavior

The renderer waits for the buffered PPU update pointer to become idle, enters
the direct-transfer guard, switches `PPU_CTRL` between 32-byte and one-byte
increments as needed, and tail-calls `EndDirectPpuTransfer`.

Its four source records and repeated writers are separately owned by
`src/data/repeated_ppu_patterns.asm` and
`src/graphics/ppu/data_writers.asm`.
