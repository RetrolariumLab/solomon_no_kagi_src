# Revision Profiles

The source treats each regional ROM as an independently verified build
profile. A filename is only a convenient local default. The
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

## Contents

- [Known private images](#known-private-images)
- [Commands](#commands)
- [Room-data comparison](#room-data-comparison)
- [Source and binary boundaries](#source-and-binary-boundaries)
- [Planned build structure](#planned-build-structure)
- [Editing](#editing)
- [Source 2.0 release boundary](#source-20-release-boundary)

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

Verify the required references, USA and Europe:

```console
make verify-revision-references
```

Extract the assets owned by one profile:

```console
make split-revision-assets PROFILE=europe
```

Extract assets for all required profiles:

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

`src/main.asm` takes a numeric `SolomonRevision` define and defaults to USA.
Build one revision and compare it with its reference, or check both:

```console
make verify-revision PROFILE=europe
make verify-revisions
```

`make verify-revision-sources` additionally checks the source-owned byte
ranges each profile declares. Both 65,552-byte images are byte-identical; no
European code, data, padding, or graphics comes from an opaque PRG asset.

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

## Editing

Releases 2.0 and 2.1 had four profile-aware editors (levels, audio, graphics
and presentation); 3.0 retired them: Retrolarium Studio edits every revision from
`solomons_key.rlj` through the kit's Solomon's Key profile, which owns the
codecs, the capacity limits and the views. See
[editing in Retrolarium](retrolarium.md). The editors and their documents
remain in the `source-reconstruction-2.0` and `-2.1` tags.
