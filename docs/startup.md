# Reset and startup

## Owned range

`src/system/boot_and_frame.asm` owns CPU `$8C00-$8D5E` (351 bytes). Its
`PRG_STARTUP` linker segment sits between the unresolved pre-startup range and
the cooperative scheduler. `make reconstruction-audit` verifies that exact
layout and every accepted ROM-label address.

## Reset sequence

`Reset` disables interrupts and decimal mode, initializes SP, and waits for two
PPU vblank intervals before touching shared state. It then clears internal RAM,
disables DMC/frame audio state, enables the four ordinary APU channels, hides
all 64 sprites by writing `$F8` to each OAM Y byte, and initializes the two
nametables used by the game.

`InitializeNametable` receives the high PPU address byte in A. Startup invokes
it for `$2000` and `$2800`. Each call writes blank tile `$24` through the tile
area and zero through the 64-byte attribute area, then resets scroll and the
PPU latch.

## CHR and warm-boot state

After enabling NMI and waiting for two services, reset writes
`StartupChrBankSelectValue` to its own CNROM cartridge address and probes CHR
through `PPU_DATA`. This is a static high-confidence bank-switch handshake;
the exact hardware reason for the repeated `$DF` test still needs a mapper/bus
trace.

Internal RAM `$07F0-$07FD` survives the selective startup clear. Four bytes at
`WarmBootSignature` are compared with `StartupWarmBootSignature` (`FUKU`). On
a mismatch, reset copies that signature, eight default-state bytes, and marker
`$2F`. The retained state is therefore a warm-reset convention, not cartridge
battery-backed save RAM.

## Scheduler bootstrap

Reset partitions page-one stack storage at `$20`-byte intervals and installs
`IdleThreadLoop - 1` as an RTS continuation in unused contexts. It starts the
encoded initial context `$17`, scans four `PendingThreadStarts` bytes, calls
`StartThread` for nonzero requests, and yields through `SwitchThreads`.

Bytes `$1A-$1B` are the shared `PpuUpdateStreamPointer`. The warmup byte at
`$21` is `GameplayDelayCounter`; the active NMI path increments it together
with the other `$20-$27` counters. The semantic meaning of every pending start
code remains open until traces bind those selectors to behavior.
