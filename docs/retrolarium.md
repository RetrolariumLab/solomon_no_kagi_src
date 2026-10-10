# Editing in Retrolarium

Solomon's Key is edited in Retrolarium Studio, not by tools in this repository.
Open `solomons_key.rlj` at the repository root in the studio. It asks which
revision to edit, takes that revision's ROM (copied next to `solomons_key.rlj`
and never committed) and keeps the edits in `hack/<revision>/`. Builds go to
`.retrolarium/`. Neither folder is tracked; delete `hack/<revision>/` to start
over from the original.

## Revisions

| Revision | ROM                          | Timing |
| -------- | ---------------------------- | ------ |
| `usa`    | `Solomon's Key (U) [!].nes`  | NTSC   |
| `europe` | `Solomon's Key (E) [!].nes`  | PAL    |
| `japan`  | `Solomon no Kagi (J).nes`    | NTSC   |

The USA and European revisions are the ones this repository rebuilds from
source; the Japanese revision is edited from its ROM.

## What is edited

The kit's Solomon's Key profile defines every view; this repository only names
the revisions and the asset split. The studio offers:

- rooms and their objects, the Demon Mirrors and the special rooms (Solomon's
  Seals, the princess room's prizes, the random bonus room);
- room art, animations and sprite mappings, graphics and palettes;
- music and sound effects, with a piano roll and preview;
- the screens, the title and attract presentation, and the game text.

Capacities stay those of the original layout: each table keeps its place and
size, and the studio refuses an edit that would not fit.

## Checking the repository

`make studio-check` runs `rltool studio check solomons_key.rlj`. In a throwaway
copy of the repository it prepares every revision, decodes and validates each
document and rebuilds each revision with no edits, requiring the original ROM
byte for byte. It needs the revisions' ROMs and the Retrolarium kit (`rltool` on
`PATH`, or `RLTOOL=...`), and never reads or writes `hack/` or `.retrolarium/`.

## Source Reconstruction 3.0

`config/source_reconstruction_3_0.json` is the 3.0 release manifest. It names
the descriptor, the profile and the revisions, the kit and studio versions the
release is checked with, and every removed editor with the view that replaced
it. `make source-3-audit` runs studio-check with `--release`, which also checks
that section against the descriptor and the running kit; `make source-3-check`
runs the Source 2.1 gate first. The manifest stays in `development` with the kit unpinned
until Retrolarium publishes its first tags.
