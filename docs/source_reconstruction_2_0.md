# Source Reconstruction 2.0

Source Reconstruction 2.0 is the additive, profile-aware authoring baseline for
this repository. It inherits the published USA preservation contract without
changing its entrypoint, hashes, or release manifest, and adds a complete
European source build, regional runtime evidence, and verified level, audio,
and CHR graphics authoring models.

The machine-readable contract is
`config/source_reconstruction_2_0.json`. Its current status is `development`:
the accepted technical scope has an executable audit, while the release tag is
not claimed until the remaining review work is finished and the manifest is
explicitly changed to `tag-ready` on the final release commit.

## Predecessor and immutable baseline

The predecessor is the annotated tag `source-reconstruction-1.0`, peeled to:

```text
4398f2a134cd631d0bb6377236c9a2a046a06ce8
```

`config/source_reconstruction_1_0.json`, `assets/manifest.json`, the default
USA entrypoint, and its expected ROM hashes remain the 1.0 authority. Source
2.0 does not reinterpret regional support as permission to replace this
baseline.

The original `make release-check` ends with a pre-publication assertion that
the 1.0 tag does not exist. That assertion is intentionally false after the tag
has been published. `make source-1-regression-check` therefore runs the same
technical contract—toolchain, lint, tests, formats, build identity, symbols,
runtime, and release-manifest audit—without repeating publication-state checks.
`make release-check` itself still appends the original `pre-tag-audit`, so its
historical behavior is unchanged.

## Accepted profiles

Two NES profiles belong to the 2.0 release boundary:

| Profile | Timing | Source | Identity | Runtime |
| --- | --- | --- | --- | --- |
| `usa` | NTSC | complete PRG | byte-identical full iNES image | ten direct FCEUX scenarios |
| `europe` | PAL | complete PRG | byte-identical full iNES image | four direct FCEUX scenarios |

`config/revision_profiles.json` is the single owner of profile IDs, private
reference filenames, hashes, assembly defines, room layouts, preview addresses,
runtime addresses, and extracted-asset policy. A profile is accepted only when
its complete source-built image matches that manifest; semantic similarity to
another profile is not treated as evidence.

The Japanese image is known and hash-identified, but remains `planned`. It has
a distinct PRG and CHR, no complete source build, and no direct runtime matrix.
It is therefore not part of the 2.0 identity or authoring claims.

### Private regional inputs

Reference ROMs and generated CHR are never tracked. The expected local files
are:

```text
Solomon's Key (U) [!].nes
Solomon's Key (E) [!].nes
```

Verify and split them with:

```console
make verify-revision-references
make split-all
```

The USA and European images share the same 32 KiB CHR. The split tool verifies
each complete input before writing the ignored shared CHR output. Binary PRG
differences are represented by conditional source and data declarations rather
than checked-in extracted fragments or post-link patches.

## Regional source and data contracts

Both supported profiles assemble through `src/main.asm` with a manifest-owned
revision define. The common entrypoint keeps shared architecture visible, while
regional source branches expose PAL bootstrap, memory-layout, timing, address,
stream, and padding differences at their owning modules.

The paired data audits independently decode and validate:

- all room geometry, enemies, items, metadata, mirror schedules, mirror enemy
  sets, RoomMap patterns, and special-room tables;
- cooperative scheduler static and reviewed dynamic entry codes;
- enemy AI dispatch and split runtime record-pointer tables;
- item-handler dispatch;
- static PPU update streams;
- object-animation pointers, action descriptors, sequences, and frames;
- object-motion pointers, selector groups, and velocity vectors;
- packed title and attract-demo data;
- timing, envelope, descriptor, and complete reachable audio stream data.

Run the complete paired inventory with:

```console
make source-2-profile-audits
```

Each audit loads the selected image and its own profile manifest. A shared byte
range is still checked twice; relocation or regional identity is never inferred
from the USA result.

## Level authoring contract

The level toolchain is the primary 2.0 authoring deliverable. Its canonical
workspace is an ignored, profile-bound JSON document with schema version 2.
The headless codec and visual model share the same validation and encoder:

```console
make export-levels PROFILE=usa
make validate-levels PROFILE=usa
make build-levels PROFILE=usa
make roundtrip-level-profiles
make check-level-studio
```

The document exposes all 53 rooms and the complete supported data family:

- paired destructible/indestructible block bitplanes;
- placed enemy spawn records and their profile-specific fields;
- direct and repeated item commands plus ten-byte room metadata;
- both Demon Mirror tables;
- all 58 shared RoomMap four-tile patterns;
- random bonus-room, Seal, Princess, and rooms 20/30 special data.

Encoders preserve stream representation, shared references, terminators, and
profile-specific allocation boundaries. The untouched export/import path must
return the same 65,552-byte container hash for both profiles. Modified builds
must fit the original allocations; 2.0 does not silently expand or relocate
the ROM.

Level Studio is a thin interface over this headless model. Undo, whole-room
copy/paste and safe content clearing, record inspection, room rendering, native
CHR/palette previews, shared-table dialogs, allocation pressure, and FCEUX room
playtests do not bypass codec validation. The runtime smoke gate enters one
selected room in each source-built regional image through the game's original
room loader.

The ignored `references/skchain` checkout is useful as an independent format
and editor-design reference. Likewise, `references/levelBlocks.csv` provides a
third-party rendering comparison. Neither file is a release input: the CSV
checker already proves all 10,176 USA logical cells against our decoder, and
the release claims rest on ROM identity and our own round trips.

## Audio authoring contract

The audio workspace uses schema version 2 and is also profile-bound. It exposes
regional period/duration tables, envelopes, overlapping effect descriptors,
and every reachable physical stream command. Stable symbolic entries let the
encoder reflow absolute jumps, calls, and effect pointers while fixed
allocations protect adjacent code and vectors.

```console
make export-audio PROFILE=europe
make validate-audio PROFILE=europe
make build-audio PROFILE=europe
make roundtrip-audio-profiles
make check-sound-studio
```

Sound Studio is backed by that same codec and supplies effect routing, stream
graph editing, envelope and pitch editors, a four-voice piano-roll view, and a
deterministic command-VM/APU-like preview for NTSC and PAL. Zero-edit documents
must reproduce both complete ROM images byte for byte.

The synthesized preview is an authoring aid, not a cycle-exact replacement for
the source-built game. Final subjective sound decisions should still be
auditioned in FCEUX; this limitation is recorded as partial excluded scope and
does not weaken the claimed codec round trip.

## Graphics authoring contract

The graphics workspace uses schema version 2 and covers all 32 KiB of fixed
CHR: four CNROM banks, 512 indexed tiles per bank, and both NES bitplanes of
every 8x8 tile. It also owns the eight room/sprite subpalettes, fourteen
room-group color selectors, and three ending-fade colors at profile-specific
PRG addresses. Pixel and palette values remain typed data without committing
either the original CHR or exported workspaces. Existing schema-1 CHR
workspaces are upgraded with palette values from their verified base image.

```console
make export-graphics PROFILE=usa
make validate-graphics PROFILE=usa
make build-graphics PROFILE=usa
make roundtrip-graphics-profiles
make check-graphics-studio
```

Graphics Studio presents a complete per-bank atlas and an enlarged tile editor
with drag painting, fill, horizontal and vertical reflection, rotation, copy,
paste, and bounded undo. A semantic palette panel selects any background or
sprite subpalette, edits its four slots against the complete 64-color NES
palette, and exposes the room-group and ending-fade tables; the room loader's
`$80` marker is available only for a group selector. The selected subpalette
colors the complete atlas and enlarged tile immediately. Save and build actions
call the same headless codec; the UI has no private serializer. The headless
check projects all 131,072 pixels and all 49 stored palette values for each
profile, and untouched documents reproduce both complete ROM images byte for
byte.

USA and Europe currently share their CHR bytes, but documents remain bound to
the complete selected ROM identity as well as the CHR hash. This prevents a
workspace exported from one regional base from being silently applied to the
other while preserving the verified fact that the graphics payload is shared.

## Runtime and debugger evidence

Both accepted profiles generate labels, maps, debug records, breakpoint files,
and watch files from their own source build. Validation resolves all configured
symbols before a trace begins, while execute hooks confirm live symbol-bound
events during the scenarios.

The USA profile retains all ten 1.0 scenarios. Europe directly covers cold
boot, Room 1 entry and PAL cadence, pause/resume, and relocated audio priority.
This is a bounded critical-path matrix, not a claim that every one of 53 rooms
or every ending frame has been replayed.

```console
make validate-revision-symbol-profiles
make trace-revision-runtimes
```

Further rare-mechanic traces are welcome when they support a new semantic or
editor claim. They are not added merely to inflate scenario count.

## Development and release gates

Fast additive validation is available as:

```console
make source-2-static-check
```

It verifies both references and source builds, runs all paired format audits,
proves all three editor round trips, checks all three headless studios, validates regional
symbols, and audits the 2.0 manifest. It does not capture emulator traces.

The reusable full technical gate is:

```console
make source-2-regression-check
```

It first runs the complete published 1.0 technical contract, then the additive
2.0 static checks, fresh direct runtime traces for both profiles, and both level
playtest smoke scenarios.

The final pre-tag interface is:

```console
make source-2-check
```

That command runs `source-2-regression-check` and then enforces `tag-ready`, a
clean worktree, the exact release commit subject and authorship/trailer policy,
and absence of the future 2.0 tag locally and on the publish remote. It is
expected to fail while this manifest says `development`.

After an annotated tag has been published and the manifest status is `tagged`,
the publication assertion is:

```console
make source-2-post-tag-audit
```

It requires the annotated local tag and its remote peeled target to equal the
reviewed `HEAD`.

## Remaining release work

Before changing the status to `tag-ready`:

1. finish the planned authoring review, especially final source-built emulator
   audition for edited audio and graphics and the explicit decision about any
   additional structured-data studios;
2. review the USA/PAL profile inventory and bounded runtime matrix against the
   final advertised capability list;
3. update roadmap wording that still describes already completed editor or
   regional tasks;
4. run `make source-2-regression-check` from a clean checkout with both private
   references and the pinned FCEUX build;
5. make the final release commit with subject
   `Complete Source Reconstruction 2.0`, set status to `tag-ready`, and run
   `make source-2-check` on that exact clean commit.

Expanded ROMs, mapper changes, Japanese reconstruction, and unclaimed content
studios remain outside this tag. They require their own explicit manifests and
gates rather than being implied by the 2.0 name.
