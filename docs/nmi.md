# Vertical-blank subsystem

## Owned range

`src/system/nmi.asm` owns CPU `$8000-$80FE` (255 bytes). The adjacent gameplay
services at `$80FF-$837C` are reconstructed separately in
`src/game/nmi/gameplay_interactions.asm`. The linker places both segments
before the remaining fixed PRG, and
`make reconstruction-audit` checks its start, end, size, and required labels.

## Entry and exit contract

The vector at `$FFFA` enters `NMI`. The handler saves X, Y, and A, performs its
PPU and frame services, restores those registers at `NmiRestoreRegisters`, and
returns with `RTI`. It deliberately does not save processor status because the
6502 interrupt sequence already pushes it.

At entry, `PpuCtrlShadow` and `PpuMaskShadow` provide the software-owned PPU
state. The handler temporarily clears control/mask bits while it prepares the
frame, then sets bit 7 in `PpuCtrlShadow` before restoring `PPU_CTRL` on exit.

## PPU and mapper transactions

- OAM DMA always uses page `>OamBuffer`, which is `$02` for the shadow OAM
  allocation beginning at `$0210`.
- `WritePpuScroll` reads `PPU_STATUS` to reset the shared PPU address latch,
  writes `PpuScrollX`, then writes the Y value passed in X to `PPU_SCROLL`.
- `ChrBankSelectValues` contains `$10,$11,$12,$13`. The NMI masks the selector
  to two bits, reads the corresponding value, and writes it to an address in
  the CNROM cartridge range. The low two data bits therefore select one of the
  four 8 KiB CHR banks; the high nibble is retained from the original bus value.
  `ChrBankRequest` is then set to the consumed value `$80`. See
  `docs/chr_bank_policy.md` for every producer and the per-room profile.

## Gameplay services

After the PPU work, the handler masks SP with `$1F` to obtain the offset in the
current context's 32-byte stack window. Offsets below `$08` branch through
`SkipNmiGameplayServicesForStack` directly to register restoration, protecting
the remaining stack space by omitting gameplay and post-gameplay calls for that
video frame. The runtime timer windows now count this branch explicitly.

The active path now uses symbolic calls for the alternating enemy-overlap
scan, fireball RoomMap collision, Dana A/B action requests, the four-slot
pending-thread queue, Dana's control-state dispatcher, and the complete
object-to-OAM composer. See `docs/nmi_gameplay_interactions.md` and
`docs/nmi_dana_and_sprites.md`.

## Evidence boundary

The register save/restore, PPU writes, OAM page, and four-way CNROM selection
are statically confirmed. The NMI now has no raw absolute control-flow target;
neutral names remain where the precise game-facing meaning of Dana's action
encodings still needs runtime evidence.
