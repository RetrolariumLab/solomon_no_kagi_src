# Source organization

The source tree groups code by subsystem rather than by the order in which the
original bytes appeared in the ROM. The linker configuration remains the
authority for physical PRG order: each consolidated source can contain several
named segments, while `config/reconstruction/reconstruction.json` continues to bind every
segment to its original address range and required labels.

The main directories have distinct responsibilities:

- `src/audio` owns the audio engine, shared bank, and PAL stream alternative;
- `src/system` owns reset/NMI/input and the cooperative thread runtime;
- `src/game` contains gameplay code, divided into enemies, objects, rooms,
  items, flow, timer, transitions, ending, and NMI services;
- `src/graphics` owns PPU operations, room rendering, HUD rendering, title
  presentation, and the private generated CHR boundary;
- `src/data` owns large room/object streams and compact non-executable tables;
- `src/memory` defines hardware registers and RAM aliases.

## File-size policy

The preferred size for an ASM file is 300–700 lines. This is large enough to
keep a behavior family together and small enough for focused review. It is a
design target, not an excuse to mix unrelated code: a complete subsystem may
remain shorter, and a tightly coupled data bank may remain slightly longer.

`config/reconstruction/source_organization.json` records every exception with its reason.
`make lint` checks that:

- every ASM file outside the preferred range has a reviewed exception;
- exceptions cannot outlive the file or remain after it enters the range;
- no directory contains more than six ASM files;
- two files in the same directory cannot begin with the same underscore-
  delimited filename prefix.

The final rule is intentionally local. Names such as `runtime.asm` are useful
in several different subsystem directories, while names such as
`enemy_movement.asm`, `enemy_dispatch.asm`, and `enemy_setup.asm` in one flat
directory indicate that an `enemies` subsystem directory is missing.

## Reviewed compact boundaries

Small sources remain only where merging would obscure a real boundary:

- `src/main.asm` is the composition root and contains no gameplay logic;
- `src/graphics/chr.asm` is the generated CHR `incbin` boundary;
- enemy and room metadata files contain compact fixed tables separated from
  executable behavior;
- scoring, timer, transition-orbit, and HUD files each contain their complete
  subsystem and have no adjacent responsibility worth absorbing.

The shared audio data and object animation sources are slightly above the
upper target because splitting them would fragment pointer-local data banks.
Their exceptions prevent accidental growth from being mistaken for an
unlimited allowance: reviewers should revisit the boundary when either file
changes materially.

## Relationship to semantic modules

An ASM file is a navigation and maintenance unit. A semantic module in the
reconstruction audit is an address-owned linker segment. Consolidating files
does not combine those ownership records, weaken provenance, or change ROM
layout. The 160 semantic segments, stream codec owners, and byte-identity gates
remain independent of the smaller physical file inventory.
