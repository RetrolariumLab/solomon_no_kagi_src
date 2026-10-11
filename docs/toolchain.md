# Toolchain contract

The preservation build and runtime evidence use the pinned inputs declared in
`config/toolchain.json`. A matching filename is not sufficient: every executable
is checked by size and SHA-256 before it can participate in the corresponding
workflow.

## Build tools

The build uses `ca65` and `ld65` from cc65 2.19, upstream revision `0fca835`,
as Retrolarium Kit builds and ships them: `CA65` and `LD65` default to
`$(RLTOOL) build-tools path nes ca65` (and `ld65`), with `RLTOOL` naming the kit
command (default `rltool`). Their version output, sizes, kit release, and
executable hashes are fixed in the toolchain manifest. `make verify-build-toolchain` checks the actual paths selected by `CA65` and `LD65`;
both assembler prerequisites use that check as an order-only gate so a changed
executable cannot silently rebuild the ROM.

The kit carries cc65's license with the binaries; this repository holds no
executables.

## Runtime tool

Runtime evidence uses the external `oranguthang/fceux_automation` checkout at
commit `ec507d86c57acd8979547bc35e9627fb199fac9a`. The expected Windows x64
executable is source-built from that commit and has SHA-256
`97aadff4970e98a413377810a296c045fab717661dd8270f84d58190f43a232e`.

`make verify-runtime-toolchain` checks the executable selected by `FCEUX`, then
checks the HEAD of its source checkout. `make trace-runtime` depends on this
gate. A different emulator build is intentionally rejected even if it accepts
the same Lua API, because it has not produced the reviewed traces.

## Private reference input

The ignored USA ROM is identified by size 65,552 and SHA-256
`3d9f3bee199a3fbc04bab38e1d9d5cdeae1c6691dcca463a13c25e42f77bb03d`.
`make verify-private-input` checks the file selected by `REFERENCE_ROM` before
either verification or CHR extraction. `assets/manifest.json` independently
checks SHA-1, SHA-256, CRC32, container layout, and hashes of the significant
regions.

## Supported host

The release gate is supported on Windows x64 with Windows PowerShell 5.1,
Python 3.14.6, and GNU Make 4.4.1. The Python validation and build wrappers are
tracked source; the host versions document the environment in which the release
gate is accepted rather than claiming that other environments cannot work.

Run all three input checks directly with:

```text
make verify-toolchain
```
