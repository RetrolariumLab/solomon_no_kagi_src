# Revision Profiles

The source treats each regional ROM as an independently verified build
profile. A filename is only a convenient local default: the size and SHA-1
in `assets/manifest.json` (`retrolarium.assets`) are the authoritative
identities, and `rltool assets` (Retrolarium Kit) refuses a ROM that does not
match them.

USA and Europe are complete source revisions whose iNES images reproduce
their references byte for byte. Japan is recorded as a verified research
input: `make split` cuts its CHR, but the source does not build it yet.

## Contents

- [Known private images](#known-private-images)
- [Commands](#commands)
- [Source and binary boundaries](#source-and-binary-boundaries)
- [Editing](#editing)

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

`make split` checks every ROM that is here against `assets/manifest.json` and
cuts the assets the builds read into the ignored `assets/generated/`, replacing
a file only when its bytes changed. Neither a ROM nor a generated asset is
tracked by Git. `rltool assets images` lists the manifest's ROMs (`--present`:
those that are here).

Each revision's entry file, `src/revisions/usa.asm` or `europe.asm`, sets
`SolomonRevision` and includes `src/main.asm`. Build one revision and compare
it with its original (`rltool assets verify`), or check every revision whose
ROM is here:

```console
make verify REVISION=europe
make verify-revisions
```

Each 65,552-byte build equals its original image byte for byte; no European
code, data, padding, or graphics comes from an opaque PRG asset.

## Source and binary boundaries

Profile-specific data is not automatically an opaque binary asset. Data with
a known format and useful editing semantics belongs in reviewed source or an
authoring document. For example, European Demon Mirror timing and enemy spawn
lifetimes are decoded fields, so they should become conditional source data,
not anonymous `.incbin` blobs.

An unresolved byte range may be extracted from its private ROM while the
regional reconstruction is in progress, provided all of these conditions are
met:

- the range and owning image are declared in `assets/manifest.json`;
- the output is ignored under `assets/generated/`;
- size and hash are checked before assembly;
- documentation states why the format remains opaque.

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
