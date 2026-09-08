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
- [Level editor boundary](#level-editor-boundary)
- [Audio authoring document](#audio-authoring-document)
- [Graphics authoring document](#graphics-authoring-document)
- [Presentation authoring document](#presentation-authoring-document)
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

## Level editor boundary

The level editor is the first authoring deliverable. Its canonical document
exposes the 16 by 12 block grid, enemy placements and profile-specific
spawn lifetime, item placements and compressed commands, player/key/door and
mirror positions, Demon Mirror schedules and enemy sets, room CHR-bank choice,
tile-pattern metadata, and all 116 bytes of table-backed special-room content.

Import must decode a selected private or source-built profile. Export must be
deterministic and lossless for an untouched document. Modified documents must
be validated for grid bounds, encodable positions, legal object types,
terminators, pointer capacity, and the fixed PRG budget before they can produce
a ROM.

Shared geometry and item data will be authored once. Timing fields may select
NTSC or PAL defaults without silently copying one region into the other. This
lets the editor preserve both official profiles while also supporting an
explicit modified-content build later in the 2.0 line.

The visual studio is a thin layer over the stable document model and
command-line round trip. Like the SMB studio, it supports room selection,
direct grid editing, structured property controls, deterministic save, build,
and focused emulator playtest. The UI is not the only route to validate or
reproduce edited content; all core operations remain callable from Make and
unit tests.

### Authoring document workflow

The command-line document model is implemented in `scripts/authoring/level_editor.py`.
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
| Special-room tables | 116 | 116 | Six fixed profile-addressed regions |
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

Level document schema 2 adds the random bonus-room positions and item types,
the eight room-bound Seal positions, Princess-room hidden cells, and both
special item bitplanes. Loading a schema-1 workspace first verifies its bound
base ROM, then imports only these previously absent tables from that profile;
existing authored room changes are retained. The upgraded document is written
as schema 2 on its next Save.

The `Special rooms` dialog authors those tables without exposing their physical
profile addresses. Its bonus-room tab keeps the 32-position and 16-item cycles
independent, matching the engine's separate indices. The fixed-cell tab edits
the eight room-bound Seal positions and twelve Princess-room cells, while the
bitplane tab toggles every logical cell in the room-20 bat-symbol and room-30
blue-opal planes. All operations share the studio's bounded undo history and
the same profile-selected encoder used by `Build ROM`.

Room 51 additionally previews the procedural bonus layer on the main canvas.
`Layout 00-31` selects the masked output consumed by the original backward,
wrapping 16-item placement loop. `Source quartet` reproduces the palette group
selected from the saved ordinary-room index, and the optional ghost overlay
marks all 32 candidate cells without changing encoded room data. The selected
16 items use their native art, hidden/embedded translucency, and hexadecimal
type markers. Cyan `S`, `B`, `O`, and `H` overlays continue to project the other
otherwise invisible scripted content onto the rooms that consume it.

### Visual Level Studio

Open the visual editor for either required profile with:

```console
make level-studio PROFILE=usa
make level-studio PROFILE=europe
```

The studio creates the ignored workspace on first launch, then presents each
room as its native 16 by 12 logical grid. The background is rendered from the
selected room's original 8 KiB CHR bank, the `$1000` background pattern table,
the source-owned four-tile RoomMap records, and the palette produced by the
room loader. Brown and white blocks, doors, keys, Demon Mirrors, exposed and
flagged items, and the six-cell constellation layouts therefore use their game
art rather than editor-only colored boxes. Enemy and item type bytes appear in
the common unframed top-left style, so the number does not cover the native
art. Grid labels stay above that image so overlapping records remain easy to
select.

Five view toggles independently show the grid, metadata, items, enemies, and
scripted special-room content. The special layer uses native RoomMap art for
all eight Solomon's Seals, the room-20 bat-symbol bitplane, and the room-30
blue-opal bitplane; only script cells without an established initial pattern
retain dashed editor overlays. Metadata, item, and special switches are applied
inside the RoomMap renderer, and the enemy switch suppresses native sprite
composition, so a hidden layer is not merely covered by an editor overlay.
`Ctrl+S` and `Ctrl+Z` save and undo, `G` toggles the grid outside text controls,
and `Page Up`, `Page Down`, `Home`, and `End` navigate the 53-room set.

Placed enemies are rendered through the engine's own type configuration,
33-entry animation pointer table, initial action descriptor, three-byte frame
record, 8x16 sprite-table convention, packed palette/flip flags, and room CHR
bank. The European animation table is independently located at `$D068`
instead of inheriting the USA `$D0E8` address; both values live in the
validated revision manifest. A type outside the decoded engine range remains
visible as an explicit editor marker rather than being assigned invented art.
The lateral ground-enemy families `$50-$7F` receive the editor's vertical
orientation correction so their initial frames stand upright; flying families
retain the direct native projection. The player start uses Dana's Type 00
standing-idle descriptor `$16/$17` and faces toward the center of the room,
rather than showing the room loader's transient walking pose or a `P`
placeholder.

Item flag `$80` draws the brown-block base at reduced opacity and overlays the
collectible more strongly, keeping both the wall and the embedded object
legible. Flag `$40` keeps the empty or constellation background and uses a
half-opacity overlay for an item revealed after creating and breaking a block.
Hidden and embedded keys follow the corresponding rule. This is a preview-only
composition: the stored item byte and both original block planes remain
unchanged.

The toolbar can place brown, white, or combined brown-and-white blocks, erase a
complete cell, move the player start, key, door, and either Demon Mirror, and
add typed enemies or items. The combined mode sets both original bitplanes;
the preview draws the resulting gray block at half opacity instead of adding a
`B+W` outline or label, distinguishing this breakable combination from an
ordinary solid gray block. Existing direct, repeated, and constellation item
records are all visible; erasing one repeated placement shrinks the command
and removes it when its last position disappears.

Block and erase tools support continuous mouse strokes. The editor fills every
logical cell on a Bresenham path between motion events, so fast diagonal or
horizontal drags cannot leave gaps merely because the window received fewer
mouse events. All cells touched during one press-drag-release gesture form one
compound edit: repeated cells are ignored, a no-op stroke creates no history,
and one `Ctrl+Z` restores both source bitplanes and every erased record from the
entire gesture. Other tools retain their single-click semantics to prevent an
accidental drag from cloning enemies, items, or room anchors.

Whole-room actions fill the practical blank-canvas gap identified while
reviewing `skchain`. `Copy` and `Paste` transfer an independent deep copy of
the room's geometry, placed records, metadata, anchors, and terminating
tileset/constellation command while retaining the destination room number.
`Clear contents` removes only block geometry, placed enemies, and placed item
records after confirmation. It deliberately keeps enemy lifetime, room
properties, anchors, and the terminating command, so the result remains a
well-formed room rather than silently discarding required loader state. Paste
and clear are single undoable changes and remain subject to the global stream
capacity checks at save/build time.

`repeat item position` authors the stream's compact repeated-item form without
exposing its raw opcode. Select an existing direct or repeated item record and
click additional cells on the room canvas. The first click after selecting a
direct item converts it to a repeat while preserving the original position and
shared type; later clicks append positions to that same command. Each change is
undoable, the new position remains selected, and the original format's maximum
of 32 positions is enforced before the document reaches the ROM builder.

The `ROM allocation` panel continuously runs the same encoders used by
`Build ROM`. It shows the selected room's enemy/item stream sizes plus global usage,
capacity, and remaining bytes for the enemy, item, and variable Demon Mirror
set pools. Stock data fills each variable pool exactly, so adding a record in
one room normally requires removing or compressing data elsewhere. An overflow
is highlighted immediately and may remain in the undoable workspace, but Save,
Build ROM, and validation continue to reject it before any image is written.

The same panel distinguishes storage capacity from runtime capacity. The room
loader allocates from the 17-entry enemy pool and does not branch around a
failed eighteenth allocation, so both the document codec and the visual
editor reject more than 17 initially placed enemies. The panel also reports
how many slots remain for Demon Mirror and linked-enemy activity. A missing
white block in column 15 is shown as a right-wall wrap risk rather than being
silently repaired: all stock rooms seal that column, but an author may choose
the original engine's wraparound behavior deliberately.

Enemy and item controls pair every stored byte with a readable name while
keeping the hexadecimal prefix editable. The enemy catalog covers the complete
`$18-$83` configuration-table range and decodes family, direction, speed,
variant, and the catalog's no-slow flag. Item labels separate the low-six-bit
visual identity from the hidden and embedded-in-block flags; constellation
opcodes are named only when they occupy the terminating command position, not
when the same byte appears as the payload of a repeat command. Names are
cross-checked against `skchain`, while gameplay-effect wording follows this
reconstruction's handler analysis in `docs/room_map_tiles.md`.

The `Browse...` controls turn those lists into searchable visual catalogs. All
108 encoder-accepted enemy values are projected through their native initial
animation frame, packed sprite flags, current room CHR bank, and NES sprite
palette. All 195 legal direct-item encodings are shown with their low-six-bit
collectible identity, so hidden and embedded variants retain readable art while
their storage flags remain explicit in the description. Searching accepts
names or `$XX` codes; choosing a row switches directly to the corresponding
placement tool. `make check-level-studio` renders every catalog entry for both
profiles and rejects a supported enemy type without a resolvable native frame.
This workflow was selected after independent UX review of `skchain`; all image
decoding and type boundaries still come from this project's reconstructed code
and profile contracts.

`RoomMap art` edits all 58 shared four-tile graphics records used by initial
room rendering and incremental cell updates. Each record exposes its semantic
identity, background subpalette, and four NES tile indices. The dialog renders
the selected record with the active room's real CHR bank and palette, and lists
every initial room preview that currently references it with per-room cell
counts; records used only by transitions remain available explicitly. Because
the original format overlays the two palette bits on the top-left tile byte,
the editor requires that tile index to be a multiple of four. Edits are global,
undoable, immediately redraw the room, and are encoded through the existing
fixed-size 232-byte round-trip codec.

`Tileset` edits the terminating item-stream command. Ordinary rooms can select
any of the four CHR banks while preserving the terminator's otherwise unused
low bits. A room may also be converted to or from a positioned zodiac command;
for that form the named `$F0-$FB` constellation opcode determines both the
zodiac and CHR bank exactly as the original loader does. The dialog states the
stored opcode and implied bank, and every conversion remains an ordinary
undoable document mutation subject to the item-stream allocation check.

The Room records table exposes every enemy and item entry, including encoded
source kind, type, coordinates, command number, and repeat-position number.
Select a row or click an occupied map cell to edit its type and position in
place; repeated clicks cycle overlapping records. Repeat positions retain one
shared item type, so the inspector labels that relationship and a type edit
updates the complete repeat command while a coordinate edit moves only the
selected position. Deleting the final repeat position removes its command.
Deleting a constellation converts it to the equivalent ordinary terminator,
preserving the room's selected CHR bank instead of leaving an invalid stream.
All inspector mutations are covered by the same undo stack as direct grid
edits.

The room-property panel exposes enemy spawn lifetime, key state, timer decrease
rate, both mirror schedule selectors, and both mirror enemy-set selectors.
These are the known profile-sensitive level fields: opening a European
workspace displays PAL values from the European ROM instead of silently
copying USA timing.

`Mirror data` edits the shared records selected by those four room properties.
All 16 schedules expose their four-byte initial and four-byte looping phases;
all 17 enemy sets expose their ordered enemy types and an explicit loop offset.
The dialog lists every room that references the selected record, keeps the
complete table within its original 42-byte encoded allocation, and rejects a
loop target outside its own set. Enemy types are limited to `$18-$83`, the
range addressable by the engine's 27-entry four-type configuration table, in
both ordinary room streams and Demon Mirror sets.

`Save` encodes and decodes the complete document before replacing its JSON.
`Build ROM` performs the same validation and writes the ignored profile image
under `build/content/PROFILE/`. `Play` first builds that exact image and then
starts the selected room in the pinned FCEUX executable. The Lua workflow
presses Start through the ordinary title path, intercepts the profile-specific
first `RoomLoadThread` entry, selects `CurrentRoomIndex` before the original
loader reads it, and then hands control to the real `MainGameplayThread`.
Neither the content ROM nor its code is patched for point playtesting. `Stop`
closes only the emulator process owned by the current studio. A bounded
in-memory undo history covers all grid and property mutations, and closing a
dirty workspace asks before discarding changes.

The USA and Europe hook addresses are part of each validated revision profile;
the PAL loader is not assumed to share the USA address. Exercise both paths
without opening the editor with:

```console
make smoke-level-playtest PROFILE=usa LEVEL_PLAYTEST_ROOM=1
make smoke-level-playtests
```

The aggregate smoke enters USA Room 1 and Europe Room 30, requires an observed
`MainGameplayThread` hit with the requested room still active, writes its
diagnostic result under ignored `build/content/`, and terminates only the
bounded smoke process.

The UI delegates every binary operation to `scripts/authoring/level_editor.py`; it has no
private serializer or ROM patch path. `scripts/authoring/level_preview.py` is likewise a
read-only projection of that authored document and the verified private CHR,
not a second level decoder. This keeps GUI edits subject to the same pointer,
capacity, coordinate, and decode-after-build checks used by Make and the unit
suite. Use the headless smoke target to render all 53 rooms for both profiles
when a display is unavailable:

```console
make check-level-studio
```

On untouched workspaces this reports 310/310 native placed-enemy sprites for
both USA and Europe in addition to rendering every room background.

### Independent level-block spreadsheet

The disassembly author's `Solomon's Key (NES) - levelBlocks.csv` is useful as
an external check on the highest-priority editor format. It identifies the
source range as `$E02C-$EA1B` and records all 53 rooms as 16 by 12 values:
zero for empty, one for the brown bitplane, two for the white bitplane, and
three when both original planes are set. The latter matters because the
spreadsheet's rendered columns show white precedence, while its packed first
column preserves all ten dual-plane cells.

The locally supplied file has SHA-256
`4380f0888fbbf23d65bb45e4de32e4dc9409789845a838d8f40c8489fb69271b`.
It remains under ignored `references/`; neither the third-party spreadsheet
nor a ROM-derived copy is committed. With that file at
`references/levelBlocks.csv`, run:

```console
make check-level-block-reference PROFILE=usa
```

The checker parses the quoted hexadecimal rows instead of trusting the lossy
display columns, reconstructs the two bitplanes independently from the
verified USA ROM through the level document codec, and compares all 10,176
cells. The current result is zero mismatches, including the ten value-3 cells.
This corroborates grid orientation, row order, room order, bit significance,
and combined-block handling through a source independent of this repository.

## Audio authoring document

Sound Studio is backed by the deterministic document codec in
`scripts/authoring/audio_editor.py`. Export either complete regional audio bank to an
ignored workspace with:

```console
make export-audio PROFILE=usa
make export-audio PROFILE=europe
```

The defaults are `content/workspace/usa/audio.json` and
`content/workspace/europe/audio.json`. Like a level document, each file binds
itself to one source profile and the complete source-ROM SHA-256. It exposes
the 12 pitch periods, 26 NTSC or 64 PAL duration values, regional timing tail,
eight volume envelopes, all 26 sound-effect descriptors, 114 stream entry
points, the complete physical command area, and regional trailing bytes up to
the vectors. PAL needs the full six-bit duration index space: stock commands
use indices through 52, so only the final two bytes before the envelope pointer
table are non-duration tail data. Schema 2 corrects the earlier 26/40 split;
schema-1 workspaces are migrated losslessly when loaded.

Audio control flow is authored symbolically. The exporter assigns stable
`stream_000` through `stream_113` identities to every entry and uses those
names in effect descriptors, jumps, and calls. The encoder first lays out the
physical command list and then resolves every pointer, so equal-sized edits
may move an entry without leaving stale absolute addresses. Overlapping
reachable streams do not duplicate commands in JSON: every physical command
has one owner, while any entry at that address is attached to the record.

The sound-effect format has its own deliberate overlap. Bit 7 on the first
channel selector starts an effect and ends the preceding descriptor. The
document presents 26 ordinary channel lists; the encoder regenerates that
boundary convention and the single final `$FF` marker. Envelopes similarly
remain structured duration/volume steps instead of unchecked byte arrays.

Validate or build an edited document with:

```console
make validate-audio PROFILE=usa
make build-audio PROFILE=usa
make audio-summary PROFILE=usa
```

Validation enforces the original fixed allocations for timing, envelopes,
effect descriptors, command bytes, and the small regional trailing area. It
rejects invalid note/duration classes, unknown stream targets, duplicate or
missing entries, illegal virtual channels, malformed effect boundaries, and
growth into adjacent code or vectors. A successful build is decoded again and
must reproduce the canonical input document before its ROM is written.

Run the untouched identity proof for both required revisions with:

```console
make roundtrip-audio-profiles
```

The USA and Europe documents differ where the PAL engine actually differs;
neither inherits offsets, duration counts, stream bounds, or trailing bytes
from the other. Both complete 65,552-byte images currently round-trip byte for
byte.

Open the visual editor with:

```console
make sound-studio PROFILE=usa
make sound-studio PROFILE=europe
```

The Streams tab selects any of the 114 physical entry spans and shows each
decoded command, symbolic entry/target, operand, and concise engine meaning.
It permits in-place conversion only among commands with the same encoded size;
this keeps an isolated edit within the fixed stream budget while the shared
codec still performs a complete validation. Note, duration, control, sequence,
loop, sweep, volume, call, jump, return, and stop records are all editable.

The initial Music player tab presents the 26 engine descriptors as an audible
library instead of requiring authors to start from physical stream numbers.
It separates persistent music loops, finite musical cues, gameplay effects,
and engine-control programs, while the All programs view keeps every descriptor
reachable. These groupings describe observed duration and reviewed
`AddSoundEffect` call contexts; deliberately neutral names remain where one
descriptor serves multiple flows.

`Play selection` writes a WAV and starts it asynchronously on Windows. `Stop`
ends that playback, while `Loop generated WAV` repeats the selected preview for
long listening sessions. Four mixer switches independently audition Pulse 1,
Pulse 2, Triangle, and Noise. The same switches dim muted lanes in the
ten-second piano roll; even-numbered primary virtual channels remain outlined
over their resumable odd-numbered partners. Selecting a descriptor channel and
using `Open starting stream` jumps directly to the editable command sequence.

The Music player also exposes every descriptor channel and keeps the
first-record boundary bit derived rather than asking the author to maintain it
manually. The Streams tab decodes and edits the selected physical program. The
Envelopes tab edits each duration/volume pair and plots the four-bit volume
contour. The Timing tab edits all period words and regional duration bytes. All
mutations share a bounded undo history; closing a dirty workspace asks before
discarding it and stops active preview playback.

`Save` first rebuilds and decodes the document before replacing the ignored
JSON. `Build ROM` writes the same profile-derived content image as
`make build-audio`; there is no GUI-only serializer. Exercise both regional
models without opening Tk with:

```console
make check-sound-studio
```

This validates all 114 non-empty entry projections after a complete codec
round trip and traces every effect through the command VM for 180 frames.

`Play selection` traces the selected descriptor through the reconstructed
eight-channel sequencer and writes an ignored WAV beside the content ROM.
Call, jump, return, counted-loop, duration, envelope, control, and primary-over-
secondary channel behavior follow `src/audio/engine.asm`. The renderer
then models both pulse channels, triangle, short/long noise LFSR modes, the NES
nonlinear pulse/TND mixer, and the two-high-pass/one-low-pass output chain.
NTSC uses 60.0988 Hz and the 1.789773 MHz CPU clock; PAL uses 50.0070 Hz, the
1.662607 MHz clock, and its own noise periods.

Render the same preview without opening Tk with:

```console
make preview-audio PROFILE=usa AUDIO_EFFECT=5 AUDIO_PREVIEW_SECONDS=12
make preview-audio PROFILE=usa AUDIO_EFFECT=1 AUDIO_CHANNELS=pulse1,pulse2
```

`AUDIO_CHANNELS` accepts any comma-separated subset of `pulse1`, `pulse2`,
`triangle`, and `noise`; its default is `all`. An empty value deliberately
renders silence and is useful as a mixer regression reference.

The synthetic preview is intended for fast authoring feedback. The current
renderer does not emulate the pulse sweep unit cycle for cycle, so final sound
decisions must still be checked in the built ROM. The library names describe
confirmed gameplay contexts rather than claiming an unpublished soundtrack
track list.

## Graphics authoring document

The graphics-authoring layer is the deterministic schema-2 codec in
`scripts/authoring/graphics_editor.py`. It exports all four 8 KiB CNROM banks as 2,048
indexed NES tiles. Every tile is represented by eight strings of eight values
from `0` through `3`; the encoder reconstructs the original pair of bitplanes
instead of retaining an opaque copy of the tile bytes. The same document owns
all eight room/sprite subpalettes, fourteen room-group selectors, and the
three-step ending fade. Schema-1 CHR-only workspaces migrate by importing these
small tables from their verified profile image while retaining tile edits.

Create and inspect an ignored, profile-bound document with:

```console
make export-graphics PROFILE=usa
make validate-graphics PROFILE=usa
make graphics-summary PROFILE=usa
```

The default path is `content/workspace/<profile>/graphics.json`. Although the
stock USA and European releases share their 32 KiB CHR payload, their documents
retain distinct source-ROM identities. A document therefore cannot silently be
applied to the other regional image. The fixed bank count, bank size, tile
indices, row dimensions, and two-bit pixel alphabet are validated before a ROM
can be produced.

Build an edited image or prove the zero-edit contract with:

```console
make build-graphics PROFILE=usa
make roundtrip-graphics-profiles
```

The build replaces only the fixed CHR allocation in a verified private base
image, then decodes it again and compares the canonical document. Both required
profiles reproduce their complete 65,552-byte reference images byte for byte.
Private ROMs, split CHR, editable workspaces, and built content images remain
ignored. Open the visual layer with `make graphics-studio PROFILE=usa` (or
`europe`). It presents one complete 512-tile atlas per bank and an enlarged
8x8 editor with drag painting, fill, reflections, rotation, copy/paste, and a
bounded shared undo history. The palette panel provides a complete 64-color
NES picker for all eight background/sprite subpalettes, the fourteen room-group
selectors, and the three ending-fade colors. `$80` is an explicit special-room
marker rather than a fake color and can be selected only for a group entry.
Selecting a subpalette recolors both the bank atlas and enlarged tile.
`make check-graphics-studio` projects all 131,072 pixels and 49 palette values
for each profile without opening Tk. Save and build still pass through the
headless encoder and canonical decode check, so the GUI introduces no second
serialization path.

## Presentation authoring document

`scripts/authoring/presentation_editor.py` combines the two packed title-screen graphics
streams and the complete attract-demo controller program in one profile-bound
schema. The `record` and `logo` streams expose cursor commands and 377 literal
tile values; the demo exposes all 34 duration/button steps with named NES
buttons rather than opaque masks.

```console
make export-presentation PROFILE=usa
make validate-presentation PROFILE=usa
make build-presentation PROFILE=usa
make roundtrip-presentation-profiles
```

Both streams retain their original fixed encoded sizes, and literal bytes must
remain in the packed format's `$80-$FF` tile range. Demo indices, durations,
and button names are validated before the two physical tables are emitted.
The USA and PAL payloads are semantically identical but relocated by `$70`, so
each document records its own address layout and complete source-ROM identity.
Build writes only the declared PRG ranges, decodes the result, and compares the
canonical document. Untouched workspaces reproduce both complete ROMs byte for
byte. Open the visual layer with `make presentation-studio PROFILE=usa` (or
`europe`). Its title tab renders the physical 32x30 nametable destinations with
the original fourth CNROM bank and background pattern table selected by
`PpuCtrlShadow = $B0`. Packed cursor commands and fixed-length literal runs can
be edited without exposing raw offsets. The attract tab presents all 34 steps
as named buttons, duration bytes, and a proportional timeline; a zero duration
is shown with its effective 256-frame meaning. Both tabs share one bounded undo
history, and every mutation passes through the headless codec before it becomes
editor state.

`make check-presentation-studio` runs without Tk and projects both regional
documents. It accounts for all 377 literal destinations, all 256 glyphs in the
selected title pattern table, all 34 input steps, and all 1,502 effective demo
frames, then proves that the unedited visual model reproduces the complete
reference image byte for byte.

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
runtime paths remain later explicitly scoped work.

Regional work must not weaken the byte-identical USA build or mutate the
Source 1.0 manifest retroactively.
