# Solomon's Key NES source reconstruction

Byte-identical ca65 reconstructions of the USA and European NES releases of
**Solomon's Key**, edited in Retrolarium Studio. Both revisions build from
shared source; the ROM-derived assets stay private.

## Status

Source Reconstruction 3.1. Editing happens in Retrolarium Studio:
`solomons_key.rlj` opens every revision
([`docs/retrolarium.md`](docs/retrolarium.md)).

3.1 keeps only what builds and checks the source. The earlier releases'
validation codecs and audits, release manifests, FCEUX runtime scenarios and
debugger exports remain in the history (tags `source-reconstruction-1.0` to
`3.0`); the source is now edited directly.

## Quick start

You need Python 3, GNU Make and Retrolarium Kit (`rltool` on `PATH`, or
`RLTOOL=...`); the kit supplies the pinned ca65 and ld65 of
`config/toolchain.json`. Copy `Solomon's Key (U) [!].nes` and
`Solomon's Key (E) [!].nes` into the repository root, then:

```bash
make split              # unpack the private CHR (once)
make verify             # build the USA revision and compare byte for byte
make verify-revisions   # USA and Europe
```

ROMs, extracted assets and build products are ignored by Git. This project
does not grant rights to the original game code or data; see
[licensing](docs/licensing.md) and [provenance](docs/provenance.md).

## Targets

```bash
make build / verify                    # the USA revision
make verify-revisions                  # USA and Europe (PROFILE=usa|europe for one)
make build-relocated                   # fifty-one segments moved
make studio-check                      # open and rebuild every revision in the kit
make test / test-full / golden         # the checks
make lint / format / format-check / hooks / rom-info / list-revisions / clean / help
```

## Tests

`make test` (about half a minute) runs the unit tests, verifies both revisions
byte for byte, builds the relocated ROM and runs the studio check.

`make test-full` adds the attract mode played in MAME on the relocated build:
with no input the game shows its title, plays its demo and ends it with a game
over, and at seven checkpoints the room, room state, score, lives, timer and
Dana's position must equal what the original ROM gives
(`movies/attract.check.json`). In the relocated build one byte follows each of
fifty-one segments before the audio code, and the filler before the audio code
shrinks by as many. Name MAME with `MAME=<path>` or `RETROLARIUM_MAME`;
`make golden` records the reference values again.

Only the first demo is checked: the next one depends on a random seed taken
from frame counters, which a moved build may reach a frame later.

## Repository map

```text
src/              ca65 source (main.asm, grouped by subsystem)
config/           linker layout, revisions, toolchain, lint, names, profile
assets/           manifest.json (the extracted CHR is ignored)
scripts/build/    split, verification, revision and relocation scripts
tests/            their unit tests
movies/           the attract-mode check
docs/             architecture, subsystems, RAM, data formats
solomons_key.rlj  the Retrolarium project
```

Start with the task-oriented [documentation index](docs/index.md).

## Trademarks

This is an unofficial reconstruction, made for study and preservation. The game,
its title and its characters are trademarks of their owners, who have not made,
licensed or endorsed this project. It contains no part of the game: you need
your own copy of Solomon's Key to build anything.
