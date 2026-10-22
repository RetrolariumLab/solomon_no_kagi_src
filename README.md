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

You need Python 3.11 or later, GNU Make and Retrolarium Kit (`rltool` on
`PATH`, or `RLTOOL=...`); the kit supplies ca65 and ld65 and checks them. Copy
`Solomon's Key (U) [!].nes` and `Solomon's Key (E) [!].nes` into the repository
root (either is enough for its own revision), then:

```bash
make                    # the targets
make split              # cut the private CHR out of the ROMs (once)
make verify             # build the USA revision and compare byte for byte
make verify-revisions   # every revision whose ROM is here
```

`assets/manifest.json` names the ROMs and the assets cut out of them
(`rltool assets`, Retrolarium Kit). ROMs, extracted assets and build products
are ignored by Git. This project
does not grant rights to the original game code or data; see
[licensing](docs/licensing.md) and [provenance](docs/provenance.md).

## Targets

```bash
make build / verify [REVISION=europe]  # one revision (USA unless given), in build/revisions/<id>/
make verify-revisions                  # every revision whose ROM is here
make build-relocated [REVISION=...]    # fifty-one segments moved, in build/relocated/<id>/
make studio-check / profile-check      # the kit opens and rebuilds it; the profile's table places
make test / test-full / golden         # the checks
make play [MOVIE=attract]              # watch a movie in MAME
make lint / format / hooks / clean
```

Each revision builds from its entry file, `src/revisions/<id>.asm`, which sets
`SolomonRevision` and includes `src/main.asm`.

## Tests

`make test` (about twenty seconds) runs the unit tests, verifies every revision
whose ROM is here byte for byte, builds each relocated, checks the table places
of `config/game_profile.json` against the builds and runs the studio check.

`make test-full` adds the attract mode played in MAME on the relocated build:
with no input the game shows its title, plays its demo and ends it with a game
over, and at seven checkpoints the room, room state, score, lives, timer and
Dana's position must equal what the original ROM gives
(`movies/attract.check.json`). In the relocated build one byte follows each of
fifty-one segments before the audio code, and the filler before the audio code
shrinks by as many. Name MAME once with `rltool movie mame <path>`
(or `MAME=<path>`);
`make golden` records the reference values again.

Only the first demo is checked: the next one depends on a random seed taken
from frame counters, which a moved build may reach a frame later. For the same
reason the European relocated build has no movie yet: its first demo already
departs from the original's (`movies/attract-europe.check.json`,
[unknowns](docs/unknowns.md)).

`make play MOVIE=attract` shows a movie in a MAME window at the game's
speed, on the relocated build (or on `ROM=<image>`), and compares its cells
with the original's once the window is closed; in MAME, F10 lifts the speed
limit and Insert fast-forwards. `FRAMES=<frame>` closes MAME at that frame, `CLOSE=1`
when the movie ends. `make play` alone plays `attract`.

## Repository map

```text
src/              ca65 source (main.asm, grouped by subsystem)
src/revisions/    one entry file per revision the source builds
config/           linker layout, lint, names, profile and its table places
assets/           manifest.json (the extracted CHR is ignored)
scripts/build/    relocate.py, the relocated build's source rewrite
tests/            its unit tests
movies/           the attract-mode checks
docs/             architecture, subsystems, RAM, data formats
solomons_key.rlj  the Retrolarium project
```

Start with the task-oriented [documentation index](docs/index.md).

## Trademarks

This is an unofficial reconstruction, made for study and preservation. The game,
its title and its characters are trademarks of their owners, who have not made,
licensed or endorsed this project. It contains no part of the game: you need
your own copy of Solomon's Key to build anything.
