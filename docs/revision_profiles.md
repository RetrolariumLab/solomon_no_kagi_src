# Revision Profiles

Source Reconstruction 2.0 treats each regional ROM as an independently
verified build profile. A filename is only a convenient local default. The
complete-image and region SHA-256 values in `config/revision_profiles.json`
are the authoritative identities.

The profile layer has three responsibilities:

1. refuse a private ROM whose complete identity does not match the selected
   profile;
2. extract only manifest-owned binary assets under the ignored
   `assets/generated/` tree;
3. distinguish a verified reference from a source-complete profile.

This last distinction was important while the PAL reconstruction was partial.
USA and Europe are now both complete source profiles whose PRG and complete
iNES images reproduce their references byte for byte. Japan is recorded as a
verified research input and is not required by the minimum 2.0 scope.

## Known private images

| Profile | Timing | Complete SHA-256 | PRG SHA-256 | CHR relationship | Source status |
| --- | --- | --- | --- | --- | --- |
| `usa` | NTSC | `3d9f3bee199a3fbc04bab38e1d9d5cdeae1c6691dcca463a13c25e42f77bb03d` | `d86d94cd13a7199b9a58cfa0e372ea05ffeabee8ce301639e5d9f52ca860d6b7` | Shared with Europe | Complete |
| `europe` | PAL | `e8dc7ad587133869eaf6101018be676e9c14c3b97b988d2e96f7e398b5c33acb` | `3652cf993e369165774e2329062a90ee0167372d77c4dd3d81dc2bc874b5a051` | Byte-identical to USA | Complete |
| `japan` | NTSC | `b90bb344eff516863bc5278d9efba7ffd2a83a1e6cf27a6b2a9ab57ec094ae83` | `876d40256ba20bc0aa49cee99a91b4636d4fe2ca2d6b4152381bdb0367a3ba55` | Japan-specific | Planned |

All three inputs are 65,552-byte iNES mapper-3 images with a 32 KiB PRG and a
32 KiB CHR. Their 16-byte headers are byte-identical. USA and Europe also have
the same complete CHR, so both profiles deliberately select the existing
`assets/generated/chr/solomons_key.chr` output. Splitting either reference
must reproduce exactly the same ignored file.

Japan has different graphics. Its CHR is extracted to
`assets/generated/revisions/japan/chr/solomon_no_kagi.chr`. It cannot
accidentally overwrite the shared USA/Europe graphics because the manifest
gives it a separate destination and identity.

## Commands

List all recorded profiles and their source status:

```console
make list-revisions
```

Verify one private reference:

```console
make verify-revision-reference PROFILE=europe
```

Verify the required Source 2.0 references, currently USA and Europe:

```console
make verify-revision-references
```

Extract the assets owned by one profile:

```console
make split-revision-assets PROFILE=europe
```

Extract assets for all required 2.0 profiles:

```console
make split-all
```

The split operation validates the complete ROM before reading any slice. It
then validates every extracted slice independently by size, SHA-1, and
SHA-256, constrains its destination to the requested output tree, and replaces
the destination only when its bytes changed. Neither a ROM nor a generated
asset is tracked by Git.

An image with an uncertain filename can be identified by complete hash:

```console
make identify-revision REVISION_ROM="path/to/image.nes"
```

The command fails if the image matches zero or more than one manifest entry.
It does not guess from the filename, region byte, title text, or partial hash.

## Room-data comparison

The existing room codec now serves as the first cross-profile semantic probe.
It decodes every selected reference using its own known PRG layout, re-encodes
all six format families, and hashes canonical values after removing only
layout-dependent PRG offsets.

Run the required profile audit with:

```console
make revision-room-audit
```

Inspect one profile's family fingerprints with:

```console
make revision-room-report PROFILE=europe
```

Compare two profiles field by field with:

```console
make compare-revision-rooms LEFT_PROFILE=usa RIGHT_PROFILE=europe
```

The first USA/Europe comparison establishes the following boundaries:

| Room family | USA versus Europe | Interpretation |
| --- | --- | --- |
| Tile patterns | Identical | Shared source data |
| Demon Mirror enemy sets | Identical | Shared source data |
| Brown/white block planes | Identical | Shared level geometry |
| Item streams and room metadata | Identical | Shared items, doors, keys, starts, and mirrors |
| Demon Mirror schedules | Different | PAL-specific timing values |
| Enemy streams | Different | Enemy placements match, but spawn lifetimes include PAL-specific timing changes |

The canonical fingerprints are manifest data rather than a prose-only claim.
A decoder regression, unnoticed local ROM replacement, incorrect regional
offset, or semantic profile change therefore fails `revision-room-audit`.

USA and Japan currently match across all six canonical room families. That is
useful evidence for later Japanese support, but it does not imply that their
program code, presentation, audio, or graphics are shared.

## Source and binary boundaries

Profile-specific data is not automatically an opaque binary asset. Data with
a known format and useful editing semantics belongs in reviewed source or an
authoring document. For example, European Demon Mirror timing and enemy spawn
lifetimes are decoded fields, so they should become conditional source data,
not anonymous `.incbin` blobs.

An unresolved byte range may be extracted from its private ROM while the
regional reconstruction is in progress, provided all of these conditions are
met:

- the range and owning profile are declared in the revision manifest;
- the output is ignored under `assets/generated/`;
- size and cryptographic hashes are checked before assembly;
- documentation states why the format remains opaque;
- the Source 2.0 release manifest does not claim semantic ownership until the
  range is either decoded or explicitly accepted as a bounded binary asset.

The complete European PRG must not be used as a shortcut asset. Doing so would
prove container identity but not source reconstruction. Regional executable
changes will instead be expressed as profile-selected ca65 source, and known
data formats will remain editable.

## Planned build structure

The regional build will follow the same separation used by `smb1_src`:

- a small entrypoint per supported revision defines its profile constants;
- the shared semantic engine remains under `src/`;
- conditional source is limited to proven regional differences;
- outputs and linker evidence live under `build/revisions/PROFILE/`;
- `verify-revision` compares one complete build with its private reference;
- `verify-revisions` and the Source 2.0 aggregate gate cover every required
  profile;
- PAL runtime evidence runs the Europe image with PAL timing enabled.

The USA default targets and the tagged Source 1.0 contract remain unchanged.
The 2.0 profile targets are additive and do not alter the frozen USA 1.0
contract.

The regional assembly milestone is complete. `src/main.asm` accepts a
numeric `SolomonRevision` define, defaulting to USA so every 1.0 command keeps
its original behavior. The Europe research build uses:

```console
make build-revision PROFILE=europe
make verify-revision-source PROFILE=europe
make verify-revision PROFILE=europe
```

The PAL source selects its bootstrap and new-game state restore,
the one-byte-shifted gameplay RAM layout, localized system PPU streams, the
shorter pre-room layout, all sixteen European Demon Mirror schedules, the
decoded PAL mapping for every room's enemy spawn lifetime, all 35
profile-selected fixed-point object-motion vectors, PAL timer rates, the
relocated ending calls, and the PAL post-game restart flow. Regional filler is
expressed as layout data rather than imported as an opaque blob.

Run the combined source ownership gate with:

```console
make verify-revision-sources
```

It proves all 32,768 PRG bytes for each required profile. The PAL audio engine
preserves the same code shape while moving six channel-state fields one RAM
byte higher. Its period table and envelopes remain shared; the duration table
and 40-byte timing extension are profile-selected source. All 26 sound-effect
descriptors and 114 streams are source-owned, with the 44 changed streams kept
in one PAL module rather than split from the private ROM.

The stronger complete-image gate assembles each profile, verifies the header,
PRG, CHR, and full-ROM identities recorded in the manifest, and then compares
the result directly with its private reference:

```console
make verify-revision PROFILE=europe
make verify-revisions
```

Both required 65,552-byte images are byte-identical. No European executable,
structured data, padding, or graphics difference is supplied through an
opaque PRG asset.

## Level editor boundary

The level editor is the first authoring deliverable. Its canonical document
will expose the 16 by 12 block grid, enemy placements and profile-specific
spawn lifetime, item placements and compressed commands, player/key/door and
mirror positions, Demon Mirror schedules and enemy sets, room CHR-bank choice,
and tile-pattern metadata.

Import must decode a selected private or source-built profile. Export must be
deterministic and lossless for an untouched document. Modified documents must
be validated for grid bounds, encodable positions, legal object types,
terminators, pointer capacity, and the fixed PRG budget before they can produce
a ROM.

Shared geometry and item data will be authored once. Timing fields may select
NTSC or PAL defaults without silently copying one region into the other. This
lets the editor preserve both official profiles while also supporting an
explicit modified-content build later in the 2.0 line.

The visual studio will be added after the document model and command-line
round trip are stable. Like the SMB studio, it should support room selection,
direct grid editing, structured property controls, deterministic save, build,
and focused emulator playtest. The UI is not allowed to become the only route
to validate or reproduce edited content; all core operations remain callable
from Make and unit tests.

### Authoring document workflow

The command-line document model is implemented in `scripts/level_editor.py`.
Create a private, ignored workspace from either required profile:

```console
make export-levels PROFILE=usa
make export-levels PROFILE=europe
```

The defaults are `content/workspace/usa/levels.json` and
`content/workspace/europe/levels.json`. Each document records its source
profile and complete source-ROM SHA-256, so a USA document cannot be applied
silently to the PAL ROM or vice versa.

Validate a document and build its profile-derived image with:

```console
make validate-levels PROFILE=usa
make build-levels PROFILE=usa
```

Validation performs more than JSON syntax checking. It encodes all fixed and
variable room families, enforces contiguous room/schedule/set identities,
checks every packed coordinate and record, rejects stream growth past the
original PRG budgets, rebuilds an image, decodes that image again, and compares
the resulting canonical document with the input.

Variable records are packed deterministically and their split low/high pointer
planes are rebuilt. Unused bytes at the end of a format's fixed budget retain
their profile's base-ROM values. This keeps a modified build minimally
different while an untouched import remains exactly identical to all 65,552
bytes of its private reference.

The current per-profile budgets are:

| Family | Used bytes | Capacity | Pointer behavior |
| --- | ---: | ---: | --- |
| Demon Mirror schedules | 128 | 128 | 16 pointers rebuilt |
| Demon Mirror enemy sets | 42 | 42 | 17 pointers rebuilt |
| Room enemy streams | 726 | 726 | 53 pointers rebuilt |
| Room block planes | 2,544 | 2,544 | Fixed 48 bytes per room |
| Room item streams | 1,342 | 1,342 | 53 pointers rebuilt |

These figures describe both the original USA and Europe images. Editors may
redistribute bytes within the variable families, but cannot overwrite the next
owned PRG region. Later expansion support must use a separately declared
modified-build layout instead of weakening this preservation constraint.

Run the untouched identity proof for both required profiles with:

```console
make roundtrip-level-profiles
```

The proof imports every editable field, rebuilds all pointer tables and
payloads, and compares the entire generated image with its corresponding
private ROM. It currently passes byte-for-byte for both USA and Europe.

The JSON intentionally omits derived storage fields such as PRG offsets,
packed coordinates, encoded enemy lifetimes, item-repeat opcodes, and the raw
key-status/timer byte. Those values are deterministically regenerated from the
editable representation. This prevents a GUI edit from leaving a stale raw
field that disagrees with the visible room state.

### Visual Level Studio

Open the visual editor for either required profile with:

```console
make level-studio PROFILE=usa
make level-studio PROFILE=europe
```

The studio creates the ignored workspace on first launch, then presents each
room as its native 16 by 12 logical grid. Its toolbar can place brown or white
blocks, erase a complete cell, move the player start, key, door, and either
Demon Mirror, and add typed enemies or items. Existing direct, repeated, and
constellation item records are all visible; erasing one repeated placement
shrinks the command and removes it when its last position disappears.

The room-property panel exposes enemy spawn lifetime, key state, timer decrease
rate, both mirror schedule selectors, and both mirror enemy-set selectors.
These are the known profile-sensitive level fields: opening a European
workspace displays PAL values from the European ROM instead of silently
copying USA timing.

`Save` encodes and decodes the complete document before replacing its JSON.
`Build ROM` performs the same validation and writes the ignored profile image
under `build/content/PROFILE/`. `Play` first builds that exact image and then
starts the pinned FCEUX executable. A bounded in-memory undo history covers all
grid and property mutations, and closing a dirty workspace asks before
discarding changes.

The UI delegates every binary operation to `scripts/level_editor.py`; it has no
private serializer or ROM patch path. This keeps GUI edits subject to the same
pointer, capacity, coordinate, and decode-after-build checks used by Make and
the unit suite. Use the headless smoke target when a display is unavailable:

```console
make check-level-studio
```

## Remaining Source 2.0 work

The complete European source build closes the regional byte-reconstruction
milestone: semantic symbols align the profiles, every PRG difference is
classified and source-owned, and both images reproduce without post-link
patching. The remaining release work is now evidence and authoring depth:

1. add Europe-specific debugger symbols and deterministic PAL runtime traces;
2. make the remaining structured-data audits profile-aware where PAL differs;
3. deepen level authoring and add music and other content editors;
4. create the Source Reconstruction 2.0 manifest and aggregate release gate;
5. keep Japanese reconstruction as a later, explicitly scoped profile.

Regional work must not weaken the byte-identical USA build or mutate the
Source 1.0 manifest retroactively.
