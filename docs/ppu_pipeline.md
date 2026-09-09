# PPU update pipeline

This guide describes direct PPU access, buffered update streams, repeated writers, static requests, and nametable clearing.


---

## Direct PPU address writes

`SetPpuAddressAX` at `$CD53-$CD5E` is the shared address setup helper for ten
direct PPU writers.

### Contract

- input `A`: high byte of the PPU address;
- input `X`: low byte of the PPU address;
- output: `PPU_ADDR` receives `A`, then `X`;
- clobbers processor flags; preserves the supplied values in `A` and `X`.

The helper temporarily pushes `A`, reads `PPU_STATUS` to reset the shared
`PPU_SCROLL`/`PPU_ADDR` write toggle, restores `A`, and performs the two address
writes. Callers restore `PpuCtrlShadow` separately when their transfer requires
it; this helper owns only latch reset and address selection. Longer transfers
use the separate begin/end contract documented in `docs/ppu_pipeline.md#direct-ppu-transfer-guard`.

---

## Direct PPU transfer guard

The game brackets bulk CPU-to-PPU writes with two adjacent helpers:

| Entry | Range | Static uses |
| --- | --- | ---: |
| `EndDirectPpuTransfer` | `$96DC-$96EF` | 7 |
| `BeginDirectPpuTransfer` | `$96F0-$970A` | 6 |

### Begin contract

`BeginDirectPpuTransfer` waits cooperatively until the high byte of
`PpuUpdateStreamPointer` is zero. It then:

- clears `PPU_CTRL` bit 7 to disable NMI;
- clears `PPU_CTRL` bit 2 to select one-byte address increments;
- stores that control value in both `PpuCtrlShadow` and hardware;
- clears the background/sprite enable bits in the value written to `PPU_MASK`.

The last operation intentionally does not overwrite `PpuMaskShadow`. The
disabled rendering state is temporary hardware state for the transfer.

### End contract

`EndDirectPpuTransfer` sets background/sprite enable bits 3 and 4 in
`PpuMaskShadow`, sets NMI-enable bit 7 in `PpuCtrlShadow`, writes the latter to
`PPU_CTRL`, and returns. It does not write `PPU_MASK` directly; the NMI path
later commits the restored shadow value.

Callers may use `JSR` or tail-call the end helper with `JMP`. The descriptor
nametable clear, full two-nametable clear, and several still-preserved screen
renderers all share this contract. The adjacent room-frame renderer uses the
repeated writers documented in `docs/ppu_pipeline.md#repeated-ppu-data-writers`.

---

## Repeated PPU data writers

Two small helpers at `$97A3-$97B7` support a direct screen renderer.

### Four-byte pattern writer

`WriteRepeatedFourBytePpuPattern` accepts:

- `TempPointer00`: address of a four-byte source pattern;
- `X`: number of pattern repetitions.

Each repetition resets `Y` to 3 and writes source offsets 3, 2, 1, and 0 to
`PPU_DATA`. The pointer is not advanced. The four current callers request 6,
6, 8, and 8 repetitions from the four records at `$97B8-$97C7`.

### Single-byte writer

`WriteRepeatedPpuByte` accepts the byte in `Y` and count in `X`, writing that
value to `PPU_DATA` until `X` reaches zero. Its current caller writes 64 zero
bytes.

### Pattern data

The four records are named `RepeatedPpuPattern0` through
`RepeatedPpuPattern3`. The first two form the outer and inner right frame
columns; the latter two fill the two bottom tile rows. The data module asserts
the complete 16-byte extent at assembly time. See
`docs/room_lifecycle.md#room-nametable-frame` for the PPU layout.

---

## PPU update-buffer publication

`src/system/thread_runtime.asm` owns CPU `$8EA0-$8EA8`. Its single entry,
`PublishPpuUpdateBuffer`, publishes the shared RAM update-program buffer at
`$03E6` through `PpuUpdateStreamPointer` at `$001A-$001B`.

Calling convention:

```text
input:      PpuUpdateBuffer contains a complete update program
output:     PpuUpdateStreamPointer = PpuUpdateBuffer
preserved:  X, Y
clobbered:  A
```

Sixteen static sites call or tail-call the helper. They include the timer
display builder and several still-unreconstructed producers, which is why the
base alias is `PpuUpdateBuffer`; `TimerDisplayUpdateBuffer` remains an equal-
address alias for the decoded timer-specific layout.

During NMI, the high byte of `PpuUpdateStreamPointer` gates
`ExecutePpuUpdateStream`. The consumer executes the compact command stream,
marks the pointer idle by clearing its high byte, and restores scroll and
`PPU_CTRL` state. See `docs/ppu_pipeline.md#ppu-update-stream-interpreter` for the bytecode format.

---

## PPU update stream interpreter

`ExecutePpuUpdateStream` at `$8B7F-$8BE1` is the NMI-side consumer for both
ROM-resident update streams and programs assembled in `PpuUpdateBuffer`.
The NMI enters with `Y = 1`; the routine decrements it to zero and reads the
first command through `PpuUpdateStreamPointer`.

Each command has this layout:

```text
byte 0    PPU address high byte; zero terminates the entire stream
byte 1    PPU address low byte
byte 2    control
bytes...  one repeated value or N literal values
```

The control byte is packed as follows:

```text
bit 7       PPU address step: 0 = +1, 1 = +32
bit 6       payload mode: 0 = repeat one byte, 1 = literal bytes
bits 5..0   write count minus one (1-64 writes)
```

The interpreter writes each command directly through `PPU_ADDR` and
`PPU_DATA`. A repeat command advances past its single payload byte after all
writes; a literal command advances after every byte. The next address-high
byte starts another command, while zero finishes the program.

Completion clears `PpuUpdateStreamPointer + 1`, making the shared producer
slot available again. It then performs the game's `$3F00`/`$0000` PPU-address
sequence, resets the PPU latch through `PPU_STATUS`, and restores `PpuScrollX`,
`PpuScrollY`, and `PpuCtrlShadow`. `RestorePpuStateAfterUpdate` at `$8BCE` is
also a shared entry used by the adjacent status-read path.

---

## Static PPU update queue

`QueueStaticPpuUpdateStream` at USA `$9471-$9487` / Europe `$948B-$94A1` is
the producer for 18 ROM-resident PPU update programs. The caller supplies a
zero-based stream index in `A`.

If `PpuUpdateStreamPointer + 1` is nonzero, the producer preserves the index on
the current cooperative context's stack and yields through `SwitchThreads`.
Once the NMI consumer clears that high byte, the producer indexes parallel
low- and high-byte tables at USA `$9488`/`$949A` or Europe
`$94A2`/`$94B4` and publishes the selected address through
`PpuUpdateStreamPointer`.

The routine therefore serializes static updates with RAM-buffer producers; it
does not overwrite a stream still being consumed. Eleven call sites select
indices spanning the complete `$00-$11` table. The pointer tables and their
18 target programs occupy USA `$9488-$961A` or Europe `$94A2-$9622`. They are
source-owned by `src/data/static_layout.asm`: pointer order follows
the public indices, while stream labels remain in physical ROM order.

`make ppu-update-report` emits the decoded pointers, commands, PPU addresses,
increments, modes, counts, and payloads. `make ppu-update-audit` binds the
tables and complete payload range to `config/validation/ppu_update_streams.json`, checks
that the 18 programs cover every byte exactly once, and re-encodes each stream
byte-for-byte. The audit is part of `make release-check`.

Source Reconstruction 2.0 adds an independent PAL manifest at
`config/validation/ppu_update_streams_europe.json`. PAL decodes 25 commands in 349
encoded bytes, versus 26 commands in 367 bytes for USA: two text streams
select a regional tile value, and stream 17 uses the shorter European license
message. Run
`make ppu-update-profile-audits` to bind both physical pointer layouts and
localized payloads to their own hashes and round-trip every stream.

The source representation uses `PpuUpdateCommand` headers rather than opaque
control bytes. Each header names its PPU address, repeat/literal mode, and
write count; payload bytes remain exact tile or palette values. The split
pointer tables use `<` and `>` references to the 18 stream labels, so linker
movement cannot silently detach an index from its program.

---

## Direct nametable clearing

The transition code has two public entries into one descriptor-driven direct
PPU writer:

| Entry | Descriptor | Cleared tile area |
| --- | ---: | --- |
| `Clear30x24NametableRegion` | 6 | 30 columns from `$2080`, 24 rows |
| `Clear32x26NametableRegion` | 3 | 32 columns from `$2080`, 26 rows |

Six callers use the 30x24 entry and one uses the 32x26 entry. Descriptor zero,
which describes 32 columns from `$2000` for 26 rows, has no direct static
wrapper in the reconstructed call inventory.

### Descriptor and address calculation

Each three-byte record is `(width, start_index, row_count)`. The routine turns
`start_index` into a PPU address with:

```text
address = $2000 + start_index * 4
```

It writes `width` copies of blank tile `$24`, adds 8 to `start_index`, and
continues for `row_count` rows. Since the address calculation multiplies by
four, each increment advances 32 PPU bytes to the next nametable row.

After the tile rectangle, every path writes zero to 48 bytes beginning at
`$23C8`, clearing `$23C8-$23F7` in the attribute table.

### Boundaries and contract

The code owns `$C9BD-$CA32`; the descriptor table owns `$CA33-$CA3B`. Keeping
them separate prevents the preservation disassembly from interpreting the
nine data bytes as three false 6502 instructions.

The helper at `$96F0` and both wrapper continuations at `$96DC` remain outside
this semantic range and deliberately retain raw addresses pending their own
reconstruction. The code reads `PPU_STATUS` to reset the address latch, writes
`PPU_ADDR`, restores `PpuCtrlShadow`, and streams bytes through `PPU_DATA`.
`NametableClearWidth` is scratch byte `$0002`; the descriptor table has an
assembly-time size assertion. Direct writes are bracketed by
`BeginDirectPpuTransfer` and `EndDirectPpuTransfer`.

### Full two-nametable clear

`ClearBothNametables` at `$CB6F` drives a second direct PPU path. It calls
`ClearFullNametable` with high address bytes `$20` and `$28`, selecting the two
physical nametables used with horizontal mirroring.

For each nametable, the compact counter loop writes:

```text
192 + 3 * 256 = 960 bytes of blank tile $24
64 bytes of attribute value $FF
```

The result covers the complete 32x30 tile plane and its complete 64-byte
attribute table. All three static callers use the two-nametable wrapper at
screen-reset boundaries. Transfer state uses the reconstructed direct-PPU
begin/end helpers, while address writes use `SetPpuAddressAX`, with high byte
in `A` and low byte in `X`.
