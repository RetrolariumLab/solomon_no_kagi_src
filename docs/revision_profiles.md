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

This last distinction is important during 2.0 development. USA remains the
only complete source build at the start of the line. Europe is a verified PAL
reference with a decoded room layout, but its executable and all remaining
regional data differences still need to be reconstructed. Japan is recorded
as a verified research input and is not required by the minimum 2.0 scope.

## Known private images

| Profile | Timing | Complete SHA-256 | PRG SHA-256 | CHR relationship | Source status |
| --- | --- | --- | --- | --- | --- |
| `usa` | NTSC | `3d9f3bee199a3fbc04bab38e1d9d5cdeae1c6691dcca463a13c25e42f77bb03d` | `d86d94cd13a7199b9a58cfa0e372ea05ffeabee8ce301639e5d9f52ca860d6b7` | Shared with Europe | Complete |
| `europe` | PAL | `e8dc7ad587133869eaf6101018be676e9c14c3b97b988d2e96f7e398b5c33acb` | `3652cf993e369165774e2329062a90ee0167372d77c4dd3d81dc2bc874b5a051` | Byte-identical to USA | In progress |
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
The 2.0 profile targets are additive until Europe reaches byte identity.

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

## Remaining regional work

The profile inventory is evidence, not completion of the Europe build. The
following items remain open:

1. align the USA and Europe PRGs by semantic source symbols rather than raw
   file offsets;
2. classify every differing range as code, structured data, padding, address
   relocation, or bounded opaque data;
3. introduce revision entrypoints and a linker layout that reproduce both
   images without post-link patching;
4. move decoded PAL room timings into profile-selected source;
5. identify and reconstruct PAL timing, physics, audio, text, and any other
   executable differences;
6. add Europe-specific debugger symbols and deterministic PAL runtime traces;
7. create the Source Reconstruction 2.0 manifest and aggregate release gate.

Each step should be committed when its own identity, round-trip, or runtime
evidence passes. Regional research must not weaken the byte-identical USA
build or mutate the Source 1.0 manifest retroactively.
