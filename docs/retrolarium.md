# Editing in Retrolarium

Solomon's Key is edited in Retrolarium Studio, not by tools in this repository.
Open `solomons_key.rlj` at the repository root in the studio. It asks which
revision to edit, takes that revision's ROM (copied next to `solomons_key.rlj`
and never committed) and keeps the edits in `hack/<revision>/`. Builds go to
`.retrolarium/`. Neither folder is tracked; delete `hack/<revision>/` to start
over from the original.

## Revisions

| Revision | ROM                         | Timing |
| -------- | --------------------------- | ------ |
| `usa`    | `Solomon's Key (U) [!].nes` | NTSC   |
| `europe` | `Solomon's Key (E) [!].nes` | PAL    |
| `japan`  | `Solomon no Kagi (J).nes`   | NTSC   |

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

## Studio and source

The studio builds a revision from its original ROM and the documents in
`hack/<revision>/`; it does not assemble `src/`. `make build` assembles `src/`
and never reads `hack/`. So an edit to the source shows in `make build` and
`make play`, not in the studio, and a studio edit stays in the studio's
documents until someone writes it into the source by hand. Use the studio for
content (rooms, graphics, text, music) and the source for code.

## The game's names and tables

Retrolarium keeps nothing taken from the game; this repository gives it what it
needs. `config/names.json` holds the game's own names (the player, items,
constellations, enemy families and special rooms) in English. The studio and the
kit read it when a project opens and show the names as they are, untranslated;
without it they show numbers instead. Its `guard` list names what Retrolarium's
own repositories must never contain.

`config/game_profile.json` is the game's Retrolarium profile: its revisions with
their hashes and, for each resource, where it lies in each revision's image and
which codec reads it. The kit reads it when it opens `solomons_key.rlj` or a
project made from it; Retrolarium keeps no copy.

`config/profile_tables.json` names, by label, the tables the kit reads from the
image built from this source. `rltool profile tables` prints their offsets in
each revision's build, the values of `config/game_profile.json`;
`make profile-check` (part of `make test`) compares the two, so a source change
that moves such a table fails until the profile is updated. The profile's other
offsets are not derived from labels yet.

## Checking the repository

`make studio-check` runs `rltool studio check solomons_key.rlj`. In a throwaway
copy of the repository it prepares every revision, decodes and validates each
document and rebuilds each revision with no edits, requiring the original ROM
byte for byte. It needs the revisions' ROMs and the Retrolarium kit (`rltool` on
`PATH`, or `RLTOOL=...`), and never reads or writes `hack/` or `.retrolarium/`.
