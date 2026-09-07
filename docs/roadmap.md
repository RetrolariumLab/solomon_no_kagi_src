# Roadmap

## Preservation baseline (complete)

- reproducible ca65/ld65 build with private extracted CHR;
- exact header/PRG/CHR/file identity manifest;
- strict verify and split commands;
- direct original/build comparisons with region-specific diagnostics;
- local toolchain provenance;
- initial unit-test and lint gates.

## Source reconstruction 1.0

### 0. Reproducible preservation baseline - Complete

- byte-identical ca65/ld65 build;
- private CHR extraction and manifest identity;
- layered lint, tests, room validation, and complete ROM comparison.

### 1. Measured reconstruction inventory - Complete

`config/reconstruction.json` records semantic module ranges and monotonic
cleanup thresholds. `make reconstruction-status` reports current progress;
`make reconstruction-audit` checks module ranges against the linker map and
accepted names against `docs/provenance/label_renames.json` and the ld65 label
file. The audit is part of `make release-check`.

Accepted baseline after the first split:

```text
semantic modules            49
documented PRG bytes      3647 / 32768 (11.130%)
generated address labels   675
raw control-flow targets   334
preservation lines       10060
```

These are non-regression bounds, not a completion claim. As reconstruction
advances, semantic coverage must increase while the three legacy counts only
decrease.

### 2. Mechanical modularization - Complete

- `$8000-$80FE`: NMI, CNROM bank selection, OAM DMA, and PPU scroll commit are
  isolated in `src/system/nmi.asm`;
- `$80FF-$837C`: alternating enemy overlap scans, fireball RoomMap collision,
  A/B Dana action setup, and the pending-thread request queue are isolated in
  `src/game/nmi/gameplay_interactions.asm`;
- `$83C2-$863B`: the seven-group Dana input/action dispatcher, non-Dana Y
  sorting, scanline allowance pass, and two-sprite OAM composition are isolated
  in `src/game/nmi/dana_and_sprites.asm`;
- `$837D-$83C1`: both controller ports are serially sampled and merged into
  raw and policy-filtered cached input bytes in `src/system/controller_input.asm`;
- `$863C-$87DF`: the 21-record active-object traversal, signed fixed-point
  motion, six-cell RoomMap collision sampling, and packed animation sequencer
  are isolated as four adjacent modules;
- `$87E0-$8A61`: the object-state gate, 16-entry collision-handler table, all
  mask-specific responses, and shared `$...D` Y clamp are source-owned;
- `$8C00-$8D5E`: reset, warm-boot state, PPU initialization, and scheduler
  bootstrap are isolated in `src/system/startup.asm`;
- `$8D5F-$8E46`: the eight-context cooperative scheduler and its initial
  stack/entry tables are isolated in `src/system/scheduler.asm`;
- `$8A62-$8A7E`: the shared object Y-to-surface clamp is isolated in
  `src/game/objects/clamp_y.asm`, with all three calls named;
- `$8A7F-$8AA3`: the left-surface object X clamp and motion reset are isolated
  in `src/game/objects/clamp_x_left.asm`, with all three calls named;
- `$8AA4-$8ABF`: the complementary right-surface object X clamp is isolated,
  with all three calls named and the shared motion-clear tail documented;
- `$8AC0-$8B50`: type/action-driven Y/X motion and animation descriptor
  resolution is isolated in `src/game/objects/motion_animation.asm`;
- `$8B51-$8B7E`: the NMI-side RoomMap attribute-byte read and stale-request
  timeout are isolated in `src/graphics/ppu/attribute_read.asm`;
- `$8BE2-$8BFF`: Bisqwit's 30-byte `FillerBefore8C00` range is explicitly
  classified in `src/data/pre_startup_padding.asm`;
- `$8E47-$8E8C`: context 2 selector 1's Start-button pause/debounce loop is
  isolated in `src/system/pause_thread.asm`;
- `$8E8D-$8E9F`: the three-slot sound-effect request producer is isolated in
  `src/system/sound_effect_queue.asm`, with all 34 calls named;
- `$8EA0-$8EA8`: the shared RAM PPU update-program publisher is isolated in
  `src/system/ppu_update_buffer.asm`, with all 16 calls named;
- `$8EA9-$8EBF`: the stack-consuming inline appendix tail dispatcher is
  isolated in `src/system/jump_with_params.asm`, with all 11 calls named;
- `$8EC0-$915D`: the room palette template, context-one room-clear flow,
  decimal remaining-time bonus, common room loader, selection tables, and
  new-game state reset are split into seven source-owned modules;
- `$9165-$9189`: inverse cooperative waits yield until selected masked
  zero-page bits clear or become set, with all ten callers named;
- `$918A-$91B8`: both directions of the pixel/packed-room-index conversion are
  isolated in `src/game/objects/coordinate_conversion.asm`, with all 31 calls named;
- `$91B9-$9470`: initial door/key publication, intro UI and data, two-digit
  formatting, room-entry placement, the fifteen-object transition orbit,
  fixed-point scaling, and the quarter-sine table are source-owned;
- `$96DC-$970A`: thirteen direct PPU transfer boundaries use named begin/end
  helpers that coordinate update-stream idleness, rendering, and NMI state;
- `$970B-$97A2`: the room-init path draws the two right columns, two bottom
  rows, and attribute table surrounding the 30x24 room nametable area;
- `$97A3-$97C7`: two repeated PPU_DATA writers and their four source patterns
  are split into separate code/data modules with symbolic pointer operands;
- `$97C8-$99F1`: the runtime room item/header decoder and its constellation,
  timer-rate, and special-room lookup tables are source-owned;
- `$99F2-$9A6C`: room-map initialization computes `E02C + room*48` and expands
  both 24-byte block planes into the bordered 16x14 runtime map;
- `$9A6D-$9C51`: context 1's three Dana action entries handle head collisions,
  consume packed fireball inventory, and create or remove targeted blocks;
- `$9C60-$9DCF`: shared map/object interaction setup, block occupancy handling,
  object-header initialization, and coordinate overlap checks are source-owned;
- `$9DD0-$9F22`: one-cell PPU update construction, NMI attribute-read
  synchronization, and both packed-cell address conversions are source-owned;
- `$9F23-$9FFF`: 221 bytes before the main thread are explicitly classified as
  non-code filler rather than disassembled instructions;
- `$A000-$A04B`: scheduler context 3's main gameplay service loop and queued
  fairy path are isolated in `src/game/flow/main_thread.asm`;
- `$A04C-$A15E`: both Demon Mirror schedules, capacity gating, placeholder
  allocation, cyclic enemy-set decoding, delayed activation, and coordinate
  initialization are isolated as four runtime modules;
- `$A15F-$A225`: countdown arithmetic, decimal borrow propagation, display
  dirty state, and threshold transitions are isolated in `src/game/timer/runtime.asm`;
- `$A226-$A237`: the overlapping four-entry BCD threshold table and two timer
  warning PPU streams are isolated with their shared `$A22C` byte preserved;
- `$A238-$A273`: timer digit formatting and NMI update-program construction
  are isolated in `src/game/timer/display.asm`;
- `$A274-$A2DB`: the 17-slot active-enemy movement prepass is isolated in
  `src/game/enemies/movement.asm`;
- `$A2DC-$A30B`: the eligibility scan and per-enemy AI dispatch are isolated
  in `src/game/enemies/ai_dispatch.asm`;
- `$A30C-$A3A3`: the two-row fireball-inventory HUD producer, two-bit slot
  decoding, tile mapping, and reverse-copy command headers are source-owned;
- `$A3A4-$A3D6`: fireball lifetime comparison, expiration, and delayed object
  cleanup are isolated in `src/game/items/fireball_lifetime.asm`;
- `$A3D7-$A3F7`: parallel AI/object slot initialization and coordinate setup
  are isolated in `src/game/enemies/initialization.asm`;
- `$A3F8-$A44D`: spawn-type decoding and conditional object/AI configuration
  are isolated in `src/game/enemies/type_configuration.asm`;
- `$A44E-$A468`: the directly indexed 27-byte enemy-type flag table is
  isolated in `src/data/enemies/types.asm`;
- `$A469-$A4A5`: selector normalization, inline dispatch, and all 28 handler
  pointers are isolated in `src/game/enemies/ai_handlers.asm`;
- `$A4A6-$A4B2`: the shared current-enemy position-copy helper is isolated in
  `src/game/enemies/position.asm`;
- `$A4B3-$A68B`: the first two enemy AI families, collision reward dispatch,
  and small-to-large fireball inventory upgrade are source-owned;
- `$A68C-$A997`: four additional AI families, their inline action tables,
  Dana proximity checks, linked-pair allocation, fairy collection, and
  two-axis motion correction are source-owned;
- `$A998-$AD36`: the remaining `$08-$0B` orientation actions and the shared
  `$14-$1B` RoomMap path selector, including its 16-entry mask dispatcher and
  direction tables, are source-owned;
- `$AD37-$AF5B`: the shared `$1C-$37` and `$5C-$63` collision-driven action
  dispatchers, four-cell RoomMap probe, and linked-slot paths are source-owned;
- `$AF5C-$B289`: the final `$64-$6B`, `$0C-$0F`, and `$48-$53` handlers,
  collision-direction helpers, linked cleanup, and paired-enemy state paths
  are source-owned; the legacy preservation listing is eliminated;
- `$B28A-$B2A1`: the indexed object/AI record pointer resolvers are isolated
  in `src/game/enemies/pointers.asm`, and all 28 call sites use their symbols;
- `$B2A2-$B429`: action dispatch for the `$50-$5B` type family, shared
  `$50-$67` direction helpers, forward map probes, and one/two linked-slot
  allocation paths are source-owned;
- `$B42A-$B445`: the seventeen-entry free enemy-slot allocator and its carry
  return contract are isolated in `src/game/enemies/slot_allocation.asm`;
- `$B446-$B491`: the 17-entry AI and 21-entry object split pointer tables are
  formula-generated and machine-audited in `src/data/enemies/record_pointers.asm`;
- `$B492-$B4B5`: linked enemy slots are retired from both parallel record
  pools by `DeactivateEnemySlot` in `src/game/enemies/deactivation.asm`;
- `$B4B6-$B4C3`: eleven enemy behavior tail-calls retire the dispatcher-
  selected slot through `DeactivateCurrentEnemy`;
- `$B4C4-$B7FF`: the shared room-configured enemy lifetime transition and the
  classified 783-byte filler before context 6 are source-owned;
- `$C23C-$C2A5`: scheduler code `$34` pauses Dana/fireball/enemy updates,
  removes the collected key, runs its door flight, restores object states, and
  restarts main gameplay in the existing key-item module;
- `$C2A6-$C363`: the cooperative key-to-door flight, object template, fixed-
  point integrator, pointer constants, and deliberately overlapping offset
  tables are source-owned in the existing key-item module;
- `$C364-$C385`: five transition callers share one signed two-axis coordinate
  delta builder with an explicit Y-low/Y-high/X-low/X-high output contract;
- `$C386-$C3D3`: all four context-4 item presentation entries, their timed
  common lifecycle, and auxiliary RoomMap cleanup are source-owned in the
  existing item-collision module;
- `$C3D4-$C42D`: the serialized score/inventory/fairy HUD refresh, fairy PPU
  template, and seven-digit leading-zero score formatter are source-owned;
- `$C42E-$C627`: the Dana-centered item classifier, all 29 dispatch pointers,
  bonus and special effects, key/door progression, and exact 556-byte object
  plus enemy-AI pool clear are split into seven semantic modules;
- `$C100-$C23B`: context-5 defeated-enemy processing, both drop tables, and
  the shared deterministic random-state mixer are source-owned;
- `$B800-$BA33`: all 53 context-6 room dispatch entries and the shared scripted
  block/enemy triggers are source-owned;
- `$BA34-$BD93`: the room-index 49 ending sequence, convergence animation,
  randomized object fall, message selection, palette fade, and input handoff
  are source-owned;
- `$BD94-$C0FF`: ending helpers and text, Solomon's Seal reveal state, special
  room position/bitplane tables, and the classified pre-`$C100` filler are
  source-owned;
- `$C628-$C697`: timer items perform four-digit decimal doubling, fivefold
  multiplication, and the fixed `10000`/`05000` assignments;
- `$C698-$C70F`: Scroll Extender, fireball bottles, Fairy Bell, Tzo, and score
  items operate on the packed inventory and confirmed lifetime/score helpers;
- `$C710-$C73A`: item score lookup tables and the shared auxiliary-effect
  initializer are classified as separate data and code modules;
- `$C73B-$C755`: score addition propagates carry across eight unpacked decimal
  digits and is gated by `GameStateFlags` bit 0;
- `$C756-$C789`: six transition paths stop all other secondary contexts and
  clear the pending-start area through one shared reset helper;
- `$C78A-$C980`: scheduler entries `$33`, `$31`, `$35`, and `$16` implement
  the cooperative `TIME OVER` and Dana-death presentations, shared pool
  cleanup, `YOUR GDV` calculation, best-score replacement, and next-thread
  selection;
- `$C981-$C9A6`: the life-loss PPU-mask cycle, `TIME OVER.` stream, and
  patchable post-game result template are source-owned;
- `$C9A7-$C9BC`: the larger `$C78A` transition scene shares one context,
  gameplay-flag, fireball, and sound reset helper across two paths;
- `$C9BD-$CA32`: two public wrappers select descriptor-driven direct PPU
  nametable clears, followed by their three records at `$CA33-$CA3B`;
- classifying `$CA33-$CA3B` as descriptor data removed three false decoded
  instructions and their four apparent control-flow targets from the legacy
  preservation inventory;
- `$CA3C-$CA6D`: two twenty-record state/teardown sweeps bracket
  `LoadObjectPointer`, all using source-owned plus-one pointer table aliases;
- `$CA6E-$CB6E`: scheduler codes `$17`, `$18`, and `$22` own the post-game
  summary/title attract loop, fixed demo-room setup, and duration-driven demo
  input playback with real Start/Select interruption;
- `$CB6F-$CBA5`: three screen-reset paths share a direct PPU helper that fills
  both physical nametables with 960 blank tiles and 64 attribute bytes each;
- `$CBA6-$CD52`: the packed title-data decoder, record/background and logo
  layers, current/best score formatting, best-GDV display, and fixed direct
  PPU patterns are source-owned;
- `$CD53-$CD5E`: all ten direct PPU writers share one latch-reset/address
  helper with an explicit `A:X` input contract;
- `$CD5F-$CEF0`: both packed title streams are classified at their `$7F`
  terminators and source-owned alongside their decoder;
- `$CEF1-$CF34`: the attract demo's two parallel 34-byte duration/controller
  tables are source-owned with count and adjacency assertions;
- `$CF35-$CFFF`: Bisqwit's complete 203-byte `FillerBeforeD000_203bytes`
  range is explicitly classified and size-asserted beside the demo data;
  - `$D000-$D0E7`: all 58 four-byte logical tile patterns consumed by buffered
    RoomMap cell updates are source-owned, record-count asserted, and
    semantically round-trip checked;
  - `$D0E8-$D129`: all 33 object-type animation descriptor pointers are
    source-owned and count asserted;
  - the complete `$D12A-$D9D2` animation definition/frame layout is guarded by
    `make object-animation-audit`: 340 descriptors, four variant selectors,
    126 referenced sequences, 275 frame records, three reviewed hashes, and a
    2,283-byte decode/encode round trip including its pointer table;
    those definitions are now source-owned as readable macro records with
    symbolic pointer relationships;
  - `$D9D3-$DBDE` object motion data is structurally audited as 33 type
    pointers, 20 selector groups, 388 action selectors, and 35 Y/X vectors,
    with all 524 bytes reconstructed from the decoded records;
    it is now source-owned as macro records with symbolic group pointers;
  - `$DBDF-$DCEB`: the pre-table filler plus all Demon Mirror schedule and
    cyclic enemy-set pointers/payloads are classified and source-owned;
  - `$DCEC-$E02B`: all 53 room-enemy pointers and complete encoded streams are
    macro-structured source and round-trip checked;
  - `$E02C-$EA1B`: all 53 paired room block bitplanes are source-owned,
    reproducibly emitted, and round-trip checked;
  - `$EA1C-$EFC3`: all 53 room-item pointers, metadata headers, and compressed
    placement streams are macro-structured source and round-trip checked;
  - `$EFC4-$F367`: pre-audio padding and the complete NMI sound consumer,
    eight virtual-channel updates, APU publication, and ten command handlers
    are source-owned;
  - `$F368-$FFFF`: all timing/envelope tables, 26 sound-effect descriptors,
    114 reachable audio stream entries, and the three CPU vectors are
    symbolic source guarded by the audio-data audit;
- the former preservation range is fully split into reset/startup, scheduler,
  room, gameplay/object, rendering, audio, static-data, and vector modules at
  proven code/data boundaries;
- address order and `make verify` were preserved after every split.

### 3. Semantic naming and provenance - Complete for 1.0

- every accepted ROM-label rename enters the machine-readable provenance
  ledger with address, confidence, and evidence;
- replace generated labels and raw control-flow targets only when static or
  runtime evidence supports a behavioral name;
- debugger breakpoints and watch ranges are bound to current ld65 symbols;
  `make symbols` exports FCEUX ROM/RAM labels and a resolved JSON summary.
- all 1,838 source labels are semantic or accepted original names, all renamed
  labels have provenance, and no generated address label or raw numeric
  control-flow target remains.

### 4. Code/data boundary classification - Complete

- all 32 KiB of PRG are classified from ld65 source spans as code, ordinary
  data, encoded streams, padding, or CPU vectors;
- nested operand spans are resolved in favor of their containing instruction,
  while explicit data directives inside code segments remain data;
- `make prg-layout-audit` checks exact category counts and a complete-layout
  SHA-1 fingerprint as part of the release gate.

### 5. Subsystem documentation and runtime evidence - Complete for 1.0

- document contracts for reset, scheduler, room loading, objects, collision,
  rendering, audio, and progression;
- add deterministic emulator scenarios that bind runtime behavior to semantic
  source symbols;
- the first FCEUX scenarios now prove cold-boot scheduler activity and the
  natural Start-to-Room-1 path, core gameplay dispatch, and controller-driven
  Dana movement and block casting without RAM patches;
- all eight scheduler contexts have a statically proven subsystem role, and
  the manifest assigns all 23 known entry codes to their exact contexts;
- a three-write controlled inventory/lifetime setup proves B-cast fireball
  activation, NMI collision service, lifetime deactivation, cleanup, and object
  retirement at deterministic frames;
- a controlled, fully declared open-door setup proves the original
  `EnterRoomDoor` to `RoomClearThread` to next-room-load progression, while
  paired Room 1/attract traces prove scheduler-sensitive timer cadence and
  lossless catch-up of every serviced gameplay NMI tick.
- a controlled audio-mailbox scenario proves descending request-slot priority,
  even-over-odd virtual-channel ownership, and background-channel resumption;
- additional rare-mechanic traces are welcome 2.0 evidence rather than a reason
  to keep the fixed USA 1.0 preservation contract indefinitely open.

### 6. Data-format round trips - Complete

- `make room-data-audit` decodes and re-encodes all 53 block-plane
  records, enemy streams, item metadata/command streams, all 16 Demon Mirror
  schedules, all 17 mirror enemy sets, and all four split pointer families,
  plus 58 RoomMap tile patterns, comparing 5,292 encoded bytes with the built
  PRG;
- `make roundtrip-formats` aggregates that contract with byte-level codecs for
  all 18 static PPU update streams, object animation, object motion, and every
  reachable audio command stream;
- both packed title streams are decoded into 25 semantic cursor commands and
  17 literal runs, then all 402 bytes are re-encoded and compared;
- all 34 attract-demo duration/controller pairs are decoded to named button
  sets and re-encoded, including the terminal duration alias at their boundary;
- `make format-coverage-audit` proves that all seven stream-classified linker
  segments have exactly one codec owner and that their 8,113 bytes match the
  complete PRG stream classification;
- additional semantic codecs for fixed-size data tables remain useful future
  refinements, but no stream-classified PRG byte is outside the aggregate gate.

### 7. Source Reconstruction 1.0 release - Tag-ready

Release only when the fixed PRG is entirely owned by reviewed semantic modules,
all code/data boundaries are classified, required runtime scenarios and format
round trips pass, unknowns are explicitly registered, and one aggregate audit
proves the full contract.

Those criteria are now encoded in `config/source_reconstruction_1_0.json` and
documented in `docs/source_reconstruction_1_0.md`. `make source-1-audit` runs
the complete static release gate and then freshly captures all ten committed
runtime scenarios. The annotated release tag is created only after that command
passes on the reviewed `main` commit.

## Semantic reconstruction 2.0

- `config/revision_profiles.json` now records independently verified USA,
  Europe, and Japan identities; `make verify-revision-references` covers the
  required USA/Europe scope and profile-aware split output remains private;
- all seven decoded room families round-trip in both required profiles. Shared
  geometry, items, tile patterns, mirror enemy sets, and the 116 bytes of
  table-backed special-room content are fingerprinted;
  European mirror schedules and enemy spawn lifetimes are explicitly distinct;
- the European ca65 profile now selects the PAL bootstrap, RAM layout,
  gameplay flow, level timing, object motion, relocated calls, and regional
  filler data. Its full 32 KiB PRG and 65,552-byte iNES image reproduce the
  European reference byte for byte;
- the complete relocated PAL audio bank is source-owned: shifted channel-state
  RAM fields, duration and extension tables, shared envelopes, one regional
  descriptor selector set, 114 streams, padding, and vectors add another
  4,224 verified European bytes without checked-in ROM fragments;
- `make verify-revision` checks one complete source-built profile and
  `make verify-revisions` proves both required USA and Europe images without
  importing assumptions between profiles;
- profile-aware debugger export validates the same 26 execute breakpoints and
  27 watch ranges against each build, with explicit PAL relocation overrides;
- four ROM- and symbol-bound PAL traces cover boot, Room 1 entry, pause/resume,
  scheduler/timer cadence, and relocated audio-stream priority behavior;
- independent object-motion manifests round-trip the relocated pointers,
  shared selectors, and all 35 profile-selected USA/PAL velocity pairs;
- the level authoring document and editor described in
  `docs/revision_profiles.md` are the first content-tooling deliverable. The
  document importer, validator, ROM builder, capacity checks, and byte-exact
  untouched round trips are complete for USA and Europe. The visual studio now
  edits the complete logical room grid and profile-sensitive properties, draws
  native backgrounds from each room's original CHR bank, palette, RoomMap
  records, constellation pattern, and two-sprite enemy animation records, and
  keeps save/build/play actions backed
  by the same validated codec. Its record inspector edits or deletes existing
  enemies, direct items, repeat positions, and constellation commands without
  flattening their source representation. Direct item records can be promoted
  to the compact repeated-item stream form and extended visually from the room
  canvas, with shared-type, 32-position, undo, and round-trip guarantees. Its
  live allocation panel uses the build encoders to expose per-room stream sizes
  and global enemy, item, and Demon Mirror pool pressure before Save or Build.
  The shared-data dialog edits all 16 Demon Mirror schedules and all 17 cyclic
  enemy sets with room-reference, loop-boundary, enemy-type, and original
  allocation checks. Complete semantic enemy and item catalogs expose the raw
  byte together with family, direction, speed, visibility, and block-state
  meaning. Its RoomMap-art dialog edits all 58 shared palette/four-tile records,
  previews them with the active room's native CHR and palette, and reports
  initial-room references without hiding transition-only patterns. The
  room-terminator editor also exposes all four CHR banks and safe conversion
  between normal and positioned zodiac endings without pretending their shared
  opcode fields are independent. Runtime diagnostics enforce the source-proven
  17-slot placed-enemy ceiling and expose free dynamic slots plus intentional
  right-wall wrap risks without rewriting authored geometry.
  Level document schema 2 also round-trips the random bonus-room pool, Seal
  positions, Princess hidden cells, and special room 20/30 item bitplanes;
  Level Studio exposes all six tables through undoable editors and projects
  their scripted cells onto the applicable room canvases;
  legacy workspaces import only these absent tables from their verified ROM;
  Profile-specific FCEUX hooks enter the selected USA or PAL room through the
  original loader, with a two-profile runtime smoke gate;
- the disassembly author's independently produced level-block spreadsheet
  agrees with all 10,176 USA room cells, including the ten positions where
  both original block bitplanes are set. The optional checker consumes the
  ignored external CSV and guards orientation and bit significance without
  making third-party research input part of the build;
- the first audio-authoring layer exports one editable USA or Europe document
  for timing tables, envelopes, overlapping effect descriptors, and every
  physical stream command. Stable symbolic stream entries allow the encoder to
  reflow absolute jump/call/effect pointers, while exact allocation and
  decode-after-build checks protect adjacent code and vectors. Untouched audio
  documents rebuild both complete regional ROMs byte for byte. Sound Studio
  edits the complete physical stream graph, effect routing, envelope steps,
  pitch periods, and regional durations over this single codec, with bounded
  undo and headless checks for both profiles. Its command-VM preview traces all
  26 effects and renders NTSC/PAL pulse, triangle, and noise through an
  APU-like nonlinear mixer and console output filters. This executable model
  also exposed the PAL bank's full 64-byte duration index space. A four-voice
  piano roll and a complete call-site-derived effect catalog make routing and
  primary/secondary channel use visible without inventing soundtrack titles;
- the revision-three `config/source_reconstruction_2_0.json` manifest binds
  the accepted USA/PAL source, artifact, runtime, structured-data, and editor
  evidence. `make source-2-static-check` passes the additive matrix, while
  `make source-2-regression-check` begins with the complete published 1.0
  technical gate;
- profile-aware Graphics Studio owns all fixed CHR and palette data, while
  Presentation Studio owns both packed title layers and the complete attract
  controller program; all four accepted studios have exact regional round trips
  and headless model checks;
- the final scope review keeps PPU updates, object animations, and object
  motion as tested regional codecs without claiming visual editors. Scheduler,
  AI, handler, and pointer tables remain engineering contracts rather than
  authored content;
- Source Reconstruction 2.0 is tag-ready. Its bounded runtime matrix contains
  ten direct USA and four direct PAL scenarios plus two profile-specific Level
  Studio room-entry smokes; future scenarios are added only for new claims;
- Japanese reconstruction, expanded layouts, extra content studios, exact APU
  synthesis, rare-mechanic coverage, and deeper historical-intent research are
  explicitly later work.

Castle Excellent / Castlequest research is related but intentionally outside
this repository's byte-identity contract. It should receive its own project so
that engines, platforms, and evidence do not become conflated.
