# CNROM CHR-bank policy

The USA ROM has four switchable 8 KiB CHR banks. Static source inspection
finds exactly two cartridge-space write sites: the reset handshake at
`StartupChrBankSelectValue` and the per-frame `UpdateNmiChrBank` service.
Normal game code never writes the mapper directly; it publishes a one-byte
request through `ChrBankRequest` at `$007D`.

## Mapper transaction

`UpdateNmiChrBank` ignores a request whose sign bit is already set. Otherwise
it masks the request to two bits, indexes `ChrBankSelectValues`
(`$10,$11,$12,$13`), and writes the selected byte back to its own address in
fixed PRG-ROM. It then stores `$80` in `ChrBankRequest`, marking the request as
consumed. The selected table byte and its ROM address carry compatible low
bits, which is the source-level bus-conflict-safe form of a CNROM write.

During reset, `StartupChrBankSelectValue` (`$96`) is likewise written to its
own ROM address. Its low two bits select bank 2 while reset probes CHR through
`PPU_DATA`. The reason for the repeated `$DF` comparison remains a hardware
timing question, but the selected bank and both mapper write sites are fully
accounted for.

## Screen and transition requests

All non-room presentation paths select bank 3:

- `RunPostGameAttractThread` and `PrepareTitleScreen` select it for the
  post-game and title screens;
- `RoomClearThread` selects it before the room-clear messages;
- `RunTimeOverTransition` and the post-game result setup select it during
  gameplay-exit presentations;
- the ending sequence selects it before its final presentation.

`PrepareRoomIntro` selects a temporary bank for the intro marker and spark.
Normal rooms 1-16, 17-32, and 33-48 select banks 0, 1, and 2 respectively.
The special-room name transform selects bank 0 for rooms 49-50 and bank 1 for
rooms 51-53. After the intro, `LoadRoomItemsAndMetadata` replaces this request
with the gameplay bank encoded in the room item-stream terminator.

## Gameplay-room profile

The item terminator contains the two-bit gameplay CHR bank in bits 2-3.
Decoding all 53 source-owned streams gives:

| Bank | Rooms |
| ---: | --- |
| 0 | 1, 2, 4, 6, 8, 9, 12, 14, 16, 19, 21, 30, 34, 41, 47, 50, 51 |
| 1 | 3, 7, 10, 11, 13, 15, 20, 22, 24, 27, 28, 29, 31, 32, 37, 38, 42, 43, 45, 46, 52 |
| 2 | 5, 17, 18, 23, 25, 26, 33, 35, 36, 39, 40, 44, 48, 49, 53 |
| 3 | none |

The distribution is 17/21/15/0 rooms. `make verify` and the room-stream
round trip of `make studio-check` protect the exact per-room assignments.
