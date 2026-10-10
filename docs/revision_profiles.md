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
all seven format families, and hashes canonical values after removing only
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
| Special-room tables | Identical | Shared bonus-room positions/types, Seal positions, Princess cells, and room 20/30 bitplanes |

The canonical fingerprints are manifest data rather than a prose-only claim.
A decoder regression, unnoticed local ROM replacement, incorrect regional
offset, or semantic profile change therefore fails `revision-room-audit`.

USA and Japan match across the original six canonical room families. Their
new special-room family differs at random bonus-room position index 2: Japan
stores `$D2` where USA and Europe store `$B2`; the other 115 bytes in the
family match semantically. This is useful evidence for later Japanese support,
but it does not imply that their program code, presentation, audio, or graphics
are shared.

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

The object-motion codec now audits both physical layouts independently. USA
uses `$D9D3-$DBDE`; Europe uses `$D953-$DB5E`. Their 388 action selectors are
identical, but relocated pointer values and all 35 PAL Y/X vector records have
separate reviewed hashes. `make object-motion-profile-audits` proves exact
524-byte coverage and decode/encode identity for each source-built image.

Object-animation data is likewise bound to each physical layout rather than
being inferred from the USA manifest. USA uses `$D0E8-$D9D2`; Europe uses
`$D068-$D952`. Both profiles decode to 33 type pointers, 340 descriptors, 126
sequences, and 275 frame records. Their relocated pointer-bearing regions have
independent hashes, while their raw frame records have a deliberately shared
hash. `make object-animation-profile-audits` proves exact 2,283-byte
decode/encode identity for both source-built images.

Static PPU programs also have independent contracts. Their regional layout is
not a uniform relocation: USA occupies `$9488-$961A`, while Europe occupies
`$94A2-$9622`. The PAL source contains the same 18 public stream indices but
uses 25 commands and 349 encoded bytes instead of USA's 26 commands and 367
bytes because its final license message is shorter. Two other text streams
select a regional tile value. `make ppu-update-profile-audits` validates the
split pointer tables, exact coverage, hashes, and lossless encoding for both.

Packed title graphics and the attract-demo controller script move `$70` bytes
earlier in PAL without changing their encoded content. USA uses
`$CD5F-$CF34`; Europe uses `$CCEF-$CEC4`. Their separate manifests retain the
same hashes for 402 title bytes and 68 demo bytes, while
`make title-data-profile-audits` proves those values by decoding each regional
source build at its own addresses.

The complete 29-entry item-dispatch appendix and all 20 unique handler targets
move `$80` bytes earlier in PAL. The profile manifests preserve one common
selector-to-map-tile vocabulary while recording distinct physical targets and
table hashes. `make item-handler-profile-audits` validates every semantic
entry against both source-built ROMs.

Enemy AI dispatch is a verified shared island: its 28 entries and 14 unique
code targets stay at identical PRG addresses in both profiles. The adjacent
runtime record-pointer tables also retain their PRG addresses, but PAL's 17 AI
records and 21 object records begin one RAM byte higher. The paired
`enemy-ai-profile-audits` and `enemy-pointer-profile-audits` targets distinguish
these two cases explicitly.

The cooperative scheduler keeps its eight contexts and 23 known entry codes,
but PAL moves the initial stack-pointer table from `$8E01` to `$8E10` and the
context-base table from `$8E09` to `$8E18`. Entry targets relocate according
to their owning subsystems rather than one global delta. The European manifest
therefore records every static and reviewed dynamic code explicitly;
`make scheduler-profile-audits` checks both layouts and the shared source call
inventory.

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

Debugger exports use that same source-built profile rather than reusing USA
addresses. `make validate-revision-symbols PROFILE=europe` resolves all 26
reviewed execute breakpoints and 27 watch ranges against the PAL linker files,
including fourteen relocated routines and the one-byte-shifted gameplay/audio
RAM tail. `make validate-revision-symbol-profiles` applies this contract to
both required builds and leaves FCEUX `.nl` files beside each exact ROM.

The first PAL runtime matrix consumes those labels in four deterministic FCEUX
scenarios: cold boot, natural Room 1 entry, pause/resume, and overlapping audio
priority. It records distinct PAL scheduler/timer totals and relocated audio
stream starts while retaining the same controller and virtual-channel behavior.
`make trace-revision-runtime PROFILE=europe` captures and immediately validates
the European evidence; `make trace-revision-runtimes` repeats both regional
matrices from their respective source-built images.

## Editing

Source Reconstruction 2.0 accepted four profile-aware editors (levels, audio,
graphics and presentation) with headless round trips. Source Reconstruction
3.0 retired them: Retrolarium Studio edits every revision from
`solomons_key.rlj` through the kit's Solomon's Key profile, which owns the
codecs, the capacity limits and the views. See
[editing in Retrolarium](retrolarium.md). The editors and their documents
remain in the `source-reconstruction-2.0` and `-2.1` tags.

## Source 2.0 release boundary

The complete European source build closes the regional byte-reconstruction
milestone: semantic symbols align the profiles, every PRG difference is
classified and source-owned, and both images reproduce without post-link
patching. The revision-three Source 2.0 manifest consolidates the regional
room, audio, scheduler, PPU, title, object, and handler contracts. Four
purpose-built studios accept room content, audio, fixed CHR/palettes, and
title/demo presentation; all four share their serializers with headless
round-trip gates.

The scope review deliberately leaves PPU update streams, object animations,
and object motion as tested regional codecs without a claimed visual editor.
Scheduler, AI, handler, and pointer records remain engineering contracts, not
content-authoring targets. Sound preview is deterministic and profile-aware,
but exact console synthesis and subjective source-built emulator audition are
not claimed. The direct ten-scenario USA and four-scenario PAL matrices are
bounded evidence rather than exhaustive longplays.

The immutable 2.0 manifest records the `tag-ready` state that was accepted in
the published annotated `source-reconstruction-2.0` tag. Japanese
reconstruction, expanded ROMs, mapper changes, unclaimed studios, and rarer
runtime paths remain later explicitly scoped work. Source Reconstruction 3.0
later retired the four studios in favour of Retrolarium; see [Editing](#editing).

Regional work must not weaken the byte-identical USA build or mutate the
Source 1.0 manifest retroactively.
