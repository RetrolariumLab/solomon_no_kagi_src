# Licensing and redistribution boundaries

This project separates the legal status of its tools and documentation from the
status of reconstructed game code and private reference data. Nothing in the
repository grants rights to Nintendo Entertainment System ROM images or to
Tecmo's original Solomon's Key code, graphics, audio, or other game data.

## Component classification

| Component | Origin | Status | Redistribution boundary |
| --- | --- | --- | --- |
| Project-authored tools and documentation | Contributors to this repository | No project-wide license grant is currently declared | Retain repository authorship; do not infer a license for game material |
| Reconstructed game source and encoded data | Derived from the Solomon's Key USA binary and the imported disassembly | License not granted | Treat as copyrighted game material; source availability is not a redistribution license |
| Imported preservation listing | `rbmichael/solomons_key_disassembly`, attributed there to `ninespaces` | No explicit upstream license observed at import time | Attribution and provenance are retained; no additional rights are asserted |
| Bundled `ca65.exe` and `ld65.exe` | cc65 revision `0fca835`, official Snapshot Build 795 | cc65 zlib license | Redistribution is permitted under the unchanged notice in `bin/cc65-LICENSE.txt` |
| FCEUX automation executable | External source-built `oranguthang/fceux_automation` checkout | External, unbundled dependency | The executable is not tracked here; its upstream license governs it |
| USA reference ROM and extracted CHR | Legally obtained and supplied privately by the user | Private user-supplied input | Never tracked or redistributed by this project |

## Repository policy

Original `.nes` images, extracted `.chr` data, objects, built images, emulator
states, screenshots containing private data, and local research checkouts are
ignored. `make lint` independently rejects tracked private extensions and files
under generated/build roots. `make split` validates the private USA image before
deriving the ignored CHR cache.

The source and evidence provenance ledger is in `docs/provenance.md`; individual
semantic names are recorded in `config/reconstruction/label_renames.json`. The
machine-readable release manifest repeats this classification so a release
cannot silently treat a tool license as a license for reconstructed game code.
