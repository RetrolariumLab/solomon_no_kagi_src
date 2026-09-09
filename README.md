# Solomon's Key NES source reconstruction

This repository contains byte-identical ca65 source reconstructions of the USA
and European NES releases of **Solomon's Key**. It combines preservation builds,
runtime evidence, decoded data formats, and profile-aware editing tools without
tracking original ROM images or extracted copyrighted assets.

## Release status

- Source Reconstruction 1.0 is published at the annotated
  `source-reconstruction-1.0` tag.
- Source Reconstruction 2.0 is published at the annotated
  `source-reconstruction-2.0` tag. It accepts the byte-identical USA and Europe
  profiles, direct runtime evidence, and four profile-aware authoring models.
- Source Reconstruction 2.1 is a tag-ready compatible-minor candidate. It adds
  improved editor previews and audio playback, semantic source organization,
  responsibility-based tooling, stronger public-command evidence, and a
  reviewed documentation corpus without changing the accepted ROM identities
  or fixed-layout authoring contracts.

The exact candidate boundary and exclusions are documented in
[Source Reconstruction 2.1](docs/source_reconstruction_2_1.md).

## Requirements and legal inputs

The repository includes pinned Windows x64 builds of ca65 and ld65. The full
runtime gate also uses the pinned FCEUX automation build described by the
[toolchain contract](docs/toolchain.md). Python, GNU Make, and the supported host
versions are recorded in `config/toolchain.json`.

Provide legally obtained copies of the accepted regional images using the
filenames declared by `config/revision_profiles.json`:

- `Solomon's Key (U) [!].nes`
- `Solomon's Key (E) [!].nes`

ROMs, extracted CHR data, editor workspaces, runtime traces, and build products
are private or reproducible local files and are ignored by Git. This project
does not grant rights to the original game code or data; see
[licensing](docs/licensing.md) and [provenance](docs/provenance.md).

## Setup and verification

From the repository root:

```console
make help
make split
make source-2-minor-check
```

`make split` validates the USA image and extracts the shared ignored CHR input.
`make source-2-minor-check` is the current complete aggregate verification
command: it runs the accepted Source 1.0 and 2.0 regression gates first, then
checks the Source 2.1 profiles, byte identity, runtime scenarios, authoring round
trips, editor actions, public command orchestration, documentation, and release
metadata.

For final local tag-readiness checks, use:

```console
make source-2-minor-pre-tag-check
```

That command additionally requires a clean tracked worktree and verifies the
future tag boundary. No Source 2.1 tag is created by either command.

See the [verification guide](docs/verification.md) for focused checks, failure
diagnostics, generated evidence, and profile selectors. Run `make help` for the
maintained command catalog instead of relying on a duplicated list here.

## Project map

- `src/main.asm` is the canonical profile-selected assembly entry point.
- `src/` groups assembly by runtime subsystem and data owner.
- `config/` contains release, profile, linker, authoring, debugger, validation,
  and reconstruction contracts.
- `assets/manifest.json` records the immutable USA reference identity;
  `assets/generated/` holds ignored extracted data.
- `scripts/` and `tests/` mirror the `authoring`, `build`, `runtime`, and
  `validation` responsibility boundaries.
- `scenarios/` declares runtime inputs and expected observations.
- `docs/` contains reader-facing architecture, workflow, subsystem, evidence,
  provenance, and release guides.
- `build/` contains only reproducible ignored output.

Start with the task-oriented [documentation index](docs/index.md). It provides
separate paths for building and verifying a release, understanding the source,
and evaluating evidence or project boundaries.

## Evidence boundary

The complete 65,552-byte USA and European iNES images assemble byte-for-byte
from the tracked PRG source and ignored extracted assets. The release gate checks
the pinned toolchain and private inputs, compares every image byte, validates
source-layout ownership, exercises direct runtime scenarios for both profiles,
and proves zero-edit round trips for level, audio, graphics, and presentation
documents.

Names and comments are classified by evidence strength. Readable terminology is
not treated as proof by itself; static control flow, tables, byte identity,
round trips, and repeatable runtime observations remain distinct evidence
layers. See [architecture](docs/architecture.md),
[naming](docs/naming.md), and [unknowns](docs/unknowns.md).

This is an unofficial preservation and research project. Solomon's Key and its
game data remain property of their respective rights holders.
