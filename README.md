# Solomon's Key NES Disassembly

A byte-identical ca65 reconstruction and reverse-engineering workspace for the
USA NES release of **Solomon's Key** (`NES-KE-USA`). The project follows the
preservation-first structure of the sibling `smb1_src` repository: a stable
baseline, explicit ROM identity, reproducible build artifacts, documented
evidence, and small tested tools for decoded game data.

The grouped [documentation index](docs/index.md) is the shortest route into
the release contract, architecture, runtime evidence, and individual
subsystems.

## Current status

- **Source Reconstruction 1.0 is tag-ready for the fixed USA profile.** Its
  stable contract and tag procedure are in
  [`docs/source_reconstruction_1_0.md`](docs/source_reconstruction_1_0.md).
- The complete 65,552-byte iNES image assembles byte-for-byte.
- `make verify` checks the header, PRG, CHR, complete payload, and complete file.
- The complete PRG is assembled from registered semantic and classified-data
  modules; CHR is a private generated asset and is not stored in Git.
- Confirmed NES registers and high-confidence RAM aliases are separated into
  `src/memory/`.
- One hundred sixty semantic PRG modules own NMI (`$8000-$80FE`), its
  gameplay interaction services (`$80FF-$837C`), controller input
  (`$837D-$83C1`), Dana control and object-to-OAM composition
  (`$83C2-$863B`), reset/startup
  (`$8C00-$8D5E`), the cooperative scheduler (`$8D5F-$8E46`), and the main
  gameplay thread (`$A000-$A04B`), plus countdown timer arithmetic and warning
  transitions (`$A15F-$A225`), its HUD update builder (`$A238-$A273`), and
  the enemy movement prepass (`$A274-$A2DB`) plus AI dispatcher
  (`$A2DC-$A30B`), and fireball lifetime service (`$A3A4-$A3D6`).
  Enemy slot position/state initialization owns `$A3D7-$A3F7`, followed by
  type-specific object/AI configuration at `$A3F8-$A44D` and its table at
  `$A44E-$A468`. The inline 28-entry enemy AI handler dispatcher owns
  `$A469-$A4A5`, followed by its shared position-copy helper at
  `$A4A6-$A4B2`. Additional enemy AI families continue through `$B289`,
  including action dispatch, linked-slot allocation, fairy motion/collection,
  and a 16-way RoomMap path selector.
  Shared object/AI record pointer helpers own `$B28A-$B2A1`,
  the free-slot allocator owns `$B42A-$B445`, their split pointer tables own
  `$B446-$B491`, and slot deactivation owns `$B492-$B4B5`.
  Current-record deactivation follows at `$B4B6-$B4C3`.
  Timer multiplication and fixed-value item handlers own `$C628-$C697`.
  Inventory and related item handlers continue through `$C70F`.
  Item score lookup tables and auxiliary-effect initialization own
  `$C710-$C73A`.
  Shared score addition owns `$C73B-$C755`.
  Secondary-context transition reset owns `$C756-$C789`.
  Life-loss, `TIME OVER`, `YOUR GDV`, best-score, and next-thread selection
  own `$C78A-$C980`, followed by their presentation data at `$C981-$C9A6`.
  Shared room-transition state reset owns `$C9A7-$C9BC`.
  Direct PPU nametable clearing and its descriptor table own `$C9BD-$CA3B`.
  Non-Dana object-pool state and teardown sweeps own `$CA3C-$CA4E` and
  `$CA5A-$CA6D`, around the pointer resolver at `$CA4F-$CA59`.
  Post-game summary, title wait, demo setup, and recorded input playback own
  `$CA6E-$CB6E`.
  Full clearing of both physical nametables owns `$CB6F-$CBA5`.
  Packed title graphics, score/best-score/GDV presentation, and fixed logo
  patterns own `$CBA6-$CD52`; both packed streams and the parallel demo
  duration/input tables continue through `$CF34`. The classified 203-byte
  filler and all 58 four-byte RoomMap tile patterns continue through `$D0E7`.
  The parallel 33-entry object-animation descriptor pointer table follows at
  `$D0E8-$D129`.
  All 340 action descriptors, four variant selectors, 126 referenced animation
  sequences, and 275 three-byte frame records continue through `$D9D2`.
  Object-type motion pointers, 20 action-selector groups, and all 35 paired Y/X
  motion vectors are source-owned at `$D9D3-$DBDE`.
  Classified filler and the complete Demon Mirror schedule/enemy-set data
  continue through `$DCEB`.
  All 53 split room-enemy pointers and 53 losslessly round-tripped spawn streams
  are source-owned at `$DCEC-$E02B`.
  All 53 paired brown/white room block bitplanes continue through `$EA1B`.
  All 53 split room-item pointers, metadata headers, and compressed placement
  streams are source-owned at `$EA1C-$EFC3`.
  Classified pre-audio padding and the NMI-driven eight-channel sequencer,
  APU publisher, and `$F0-$F9` command handlers continue through `$F367`.
  Timing and envelope tables, all 26 sound-effect descriptors, the complete
  reachable audio bytecode, and CPU vectors own `$F368-$FFFF`.
  The common PPU latch/address writer owns `$CD53-$CD5E`.
  Pixel/room-map conversion owns `$918A-$91B8` and all 31 callers use symbols.
  Direct CPU-to-PPU transfer state owns `$96DC-$970A` and all 13 boundary calls
  use symbols.
  The 30x24 room nametable frame renderer owns `$970B-$97A2`.
  Repeated PPU writers and four source patterns own `$97A3-$97C7`.
  Runtime room item/header decoding and its tables own `$97C8-$99F1`.
  Room-map initialization and fixed block-plane expansion own `$99F2-$9A6C`.
  Dana's head-collision, fireball, and block-magic actions own `$9A6D-$9C51`.
  Shared map/object interactions and overlap checks own `$9C60-$9DCF`.
  Buffered room-cell rendering, its address converters, and classified filler
  own the complete `$9DD0-$9FFF` range.
  The main context-three loop and complete Demon Mirror schedule, placeholder,
  cyclic enemy-set, and activation runtime own `$A000-$A15E`.
  Object surface clamps own `$8A62-$8ABF`; the type/action-driven motion and
  animation definition loader follows at `$8AC0-$8B50`.
  The complete 21-record object update, fixed-point motion, RoomMap collision
  sampling, and animation sequencer own `$863C-$87DF`.
  The collision dispatcher, 16-entry handler table, all mask responses, and
  shared `$...D` Y clamp continue through `$8A61`.
  The NMI RoomMap attribute reader owns `$8B51-$8B7E`, followed by the PPU
  stream interpreter at `$8B7F-$8BE1` and classified pre-Reset filler through
  `$8BFF`; the blocking producer for
  18 ROM-resident streams owns `$9471-$9487`, followed by the split pointer
  tables and complete static stream payload at `$9488-$961A`.
  Current-room enemy stream loading owns `$961B-$9660`.
  Direct rendering of all 192 RoomMap interior cells owns `$9661-$96DB`.
  Context 2's pause loop owns `$8E47-$8E8C`, the sound-effect request queue
  owns `$8E8D-$8E9F`, shared PPU-buffer publication owns `$8EA0-$8EA8`, and
  the inline appendix dispatcher is source-owned at `$8EA9-$8EBF`.
  The complete context-one room-clear, remaining-time bonus, room-load,
  palette-selection, and new-game reset pipeline follows at `$8EC0-$915D`.
  Pixel/map coordinate conversion and the complete door/key, intro HUD,
  room-entry animation, fifteen-object orbit, scaled sine lookup, and source
  table continue through `$9470`.
  Cooperative masked-RAM waits own `$9165-$9189`.
- `make reconstruction-status` reports monotonic cleanup metrics, while
  `make reconstruction-audit` binds module ranges and renamed labels to linker
  output.
- `scripts/room_data.py` decodes the block planes, enemy streams, item streams,
  and ten-byte metadata headers for all 53 room records.
- `scripts/object_animation_data.py` validates all 33 type pointers, 340
  action descriptors, four variant selectors, and 275 animation frame records.
- `scripts/object_motion_data.py` validates all 33 motion-table pointers, 20
  selector groups, 388 action selectors, and 35 paired Y/X vectors.
- `scripts/audio_data.py` validates the period/duration/envelope tables, 26
  effect descriptors, and complete reachability of the audio bytecode range.
- Architecture, RAM, room formats, provenance, naming policy, and unknowns are
  recorded under `docs/`.
- Initial Mesen watches and breakpoints live under `config/` with a trace
  workflow in `docs/debugger_workflow.md`.

The address-ordered preservation listing has been eliminated. No generated
address labels or raw numeric control-flow targets remain. Low-level constants
stay intentionally neutral where stronger historical intent is unproven, while
the permanent verification gate protects byte identity during later semantic
refinement.

## Reference image

The baseline is exactly:

```text
Solomon's Key (USA)
File size  65,552 bytes
File SHA-1 18102689fd35c7d531a5e6241b06b748accab2f6
ROM CRC32  40684e95 (headerless PRG + CHR)
Mapper     3 (CNROM), horizontal mirroring
PRG        32 KiB, loaded at $8000-$FFFF
CHR        32 KiB, four switchable 8 KiB banks
```

The full identity contract is in `assets/manifest.json`. ROM files and locally
extracted assets are ignored by Git.

## Building

On Windows, the repository includes matched ca65/ld65 2.19 executables:

```bash
make build
make verify
```

The build produces the ROM, listing, labels, linker map, and debug records in
`build/native/`. `make verify` validates the original and built images
independently against the manifest, then compares the header, PRG, CHR,
headerless payload, complete file, and extracted CHR asset byte-for-byte.
Mismatch diagnostics include the first differing file/region offset and a CPU
address for PRG differences.

Before the first build, place a legally obtained matching image outside Git and
extract its CHR payload with:

```bash
make split
```

The default filename is `Solomon's Key (U) [!].nes`. Override it when needed:

```bash
make split REFERENCE_ROM="path/to/Solomon's Key (USA).nes"
```

This validates the complete image plus its header, PRG, and CHR identities,
then writes only the ignored `assets/generated/chr/solomons_key.chr`. Builds
fail with a focused instruction if this private asset is absent.

Source Reconstruction 2.0 adds independently hashed revision profiles without
changing the tagged USA 1.0 build. The locally verified USA and European ROMs
share byte-identical CHR but have distinct PRGs; the Japanese image has its own
PRG and CHR. Profile-aware commands identify inputs by hash, keep extracted
assets ignored, and compare decoded room formats across regional layouts:

```bash
make list-revisions
make verify-revision-references
make split-revision-assets PROFILE=europe
make revision-room-audit
make compare-revision-rooms LEFT_PROFILE=usa RIGHT_PROFILE=europe
```

Europe is a complete source-built profile: its PRG and full iNES image reproduce
the private PAL reference byte for byte. See `docs/revision_profiles.md` for
identities, exact room-family differences, the binary/source boundary, and the
remaining runtime and authoring work.

## Useful targets

```bash
make build       # assemble and link the complete iNES image
make split-all   # extract assets for required USA and Europe profiles
make list-revisions # list known regional ROM identities and source status
make verify-revision-reference PROFILE=europe # verify one regional ROM
make verify-revision-references # verify required Source 2.0 references
make revision-room-audit # round-trip and fingerprint USA/Europe rooms
make revision-room-report PROFILE=europe # print regional room fingerprints
make compare-revision-rooms LEFT_PROFILE=usa RIGHT_PROFILE=europe # semantic diff
make export-levels PROFILE=usa # create an ignored editable 53-room JSON document
make validate-levels PROFILE=usa # validate and decode a rebuilt editor image
make build-levels PROFILE=usa # build a ROM with the workspace's edited levels
make roundtrip-level-profiles # prove untouched USA and Europe editor identity
make level-summary PROFILE=usa # summarize blocks, enemies, and item commands
make level-studio PROFILE=usa # edit rooms, tilesets, RoomMap art, and shared tables
make check-level-studio # render all native room previews and check both codecs
make check-level-block-reference # compare all 10,176 cells with the external CSV
make smoke-level-playtests # enter selected USA/PAL rooms through real FCEUX hooks
make audio-profile-audits # decode and byte-round-trip USA and PAL audio data
make export-audio PROFILE=usa # create an ignored editable audio JSON document
make validate-audio PROFILE=usa # validate and decode a rebuilt audio image
make build-audio PROFILE=usa # build a ROM with the workspace's edited audio
make roundtrip-audio-profiles # prove untouched USA and Europe audio identity
make audio-summary PROFILE=usa # summarize effects, envelopes, and stream commands
make preview-audio PROFILE=usa AUDIO_EFFECT=5 # render an APU-like WAV preview
make sound-studio PROFILE=usa # edit streams, effects, envelopes, and timing
make check-sound-studio # headlessly validate both regional studio projections
make build-revision PROFILE=europe # assemble the complete PAL source profile
make verify-revision-source PROFILE=europe # verify the complete source-owned PAL PRG
make verify-revision-sources # verify source-owned PRG bytes for USA and Europe
make verify-revision PROFILE=europe # verify one complete regional ROM image
make verify-revisions # verify complete USA and Europe source-built ROMs
make enemy-ai-profile-audits # prove shared USA/PAL AI handler dispatch
make enemy-pointer-profile-audits # verify native USA/PAL runtime pool pointers
make item-handler-profile-audits # verify native USA/PAL item dispatch tables
make ppu-update-profile-audits # round-trip localized USA/PAL PPU streams
make object-animation-profile-audits # round-trip all USA/PAL animation tables
make object-motion-profile-audits # round-trip all USA/PAL motion tables
make title-data-profile-audits # round-trip relocated USA/PAL title/demo data
make validate-revision-symbols PROFILE=europe # export and verify PAL debugger labels
make validate-revision-symbol-profiles # verify USA and Europe debugger contracts
make trace-revision-runtime PROFILE=europe # freshly capture and validate PAL traces
make trace-revision-runtimes # capture the complete USA and focused PAL matrices
make verify      # complete original-vs-build byte-identity contract
make verify-prg  # compare only the 32 KiB PRG region
make verify-chr  # compare only the 32 KiB CHR region in built/original ROMs
make verify-assets # compare extracted CHR directly with the original
make verify-toolchain # verify pinned ca65, ld65, FCEUX, and private ROM hashes
make rom-info    # print sizes, SHA-1, SHA-256, CRC32, mapper, and mirroring
make format      # normalize ca65 source and run every linter
make format-check # check ca65 formatting without changing files
make lint        # validate assembly style, repository, and source contracts
make lint-source # validate manifests, includes, and tracked-binary policy
make test        # run Python unit tests
make quality-check # lint and test without requiring a reference ROM
make symbols     # export audited FCEUX labels and debugger symbol summary
make validate-symbols # verify debugger configs against current linker symbols
make trace-runtime # capture and validate deterministic FCEUX runtime evidence
make trace       # stable alias for fresh runtime capture
make validate-runtime # revalidate already captured runtime traces
make reconstruction-status # report semantic coverage and remaining raw source
make reconstruction-audit # validate module ranges, provenance, and thresholds
make release-audit # cross-check the machine-readable Source 1.0 contract
make prg-layout-report # report byte-exact code/data/stream/padding coverage
make prg-layout-audit # verify the complete PRG classification fingerprint
make scheduler-report # decode scheduler stack and entry tables as JSON
make object-animation-report # decode object animation definitions as JSON
make object-motion-report # decode object motion definitions as JSON
make object-animation-audit # round-trip animation pointers, descriptors, and frames
make object-motion-audit # round-trip motion pointers, selectors, and vectors
make title-data-report # decode packed title and attract-demo records as JSON
make title-data-audit # round-trip title streams and parallel demo-input tables
make audio-data-report # decode audio tables, descriptors, and streams as JSON
make scheduler-audit # check static/reviewed dynamic entries and call inventory
make enemy-ai-report # decode the 28-entry AI handler appendix
make enemy-ai-audit # compare every handler pointer with its reviewed manifest
make item-handler-report # decode item selectors, tiles, names, and targets
make item-handler-audit # verify all 29 item pointers and the table hash
make enemy-pointer-report # decode the split object/AI record pointer tables
make enemy-pointer-audit # verify pointer bases, strides, and counts
make ppu-update-report # decode all 18 static PPU update streams as JSON
make ppu-update-audit # verify pointers, coverage, hashes, and byte round trips
make audio-data-audit # verify audio pointers, hashes, reachability, and round trips
make room-data-audit # round-trip rooms, tile patterns, and Demon Mirror data
make chr-bank-report # list the gameplay rooms assigned to each CHR bank
make chr-bank-audit # verify the complete 53-room CHR-bank profile
make roundtrip-formats # aggregate every byte-level format round trip
make format-coverage-audit # prove every classified stream byte has one codec owner
python scripts/room_data.py --image "Solomon's Key (U) [!].nes" --source-enemies # regenerate room enemy ASM
python scripts/room_data.py --image "Solomon's Key (U) [!].nes" --source-blocks # regenerate room block ASM
python scripts/room_data.py --image "Solomon's Key (U) [!].nes" --source-items # regenerate room item ASM
python scripts/audio_data.py source --image "Solomon's Key (U) [!].nes" # regenerate audio ASM
make check       # complete static development gate without emulator capture
make release-check # clean Source 1.0 pre-tag gate, including fresh runtime
make source-1-audit # compatibility alias for release-check
make source-1-post-tag-audit # verify local annotated and published tag identity
make rooms       # decode all 53 rooms as JSON
make validate-rooms # structurally decode every room without JSON output
make clean       # remove build artifacts only
```

Focused identity targets also include `verify-reference`, `verify-built`,
`verify-header`, `verify-payload`, and `verify-rom`. See
`docs/verification.md` for their exact contracts.

To inspect one room without emitting all room records:

```bash
python scripts/room_data.py --image build/native/solomons_key.nes --room 1 --pretty
```

## Repository structure

```text
assets/manifest.json       exact reference identity
config/revision_profiles.json regional ROM, asset, and room-data identities
bin/                       local ca65/ld65 toolchain and license
config/toolchain.json      pinned build/runtime/private input identities
config/source_reconstruction_1_0.json revision-3 release contract
config/linker/cnrom.cfg    complete iNES/PRG/CHR linker layout
config/reconstruction.json machine-checked module inventory and progress floors
config/scheduler_entries.json reviewed scheduler-entry inventory
config/enemy_ai_handlers.json reviewed enemy AI handler pointer inventory
config/enemy_record_pointers.json reviewed record-pool pointer layouts
config/ppu_update_streams.json reviewed static PPU stream inventory
config/ppu_update_streams_europe.json reviewed PAL static PPU stream inventory
docs/                      architecture and reverse-engineering notes
docs/special_room_scripts.md context-six room dispatch and trigger evidence
docs/ending_sequence.md      room-index 49 ending choreography
docs/ending_and_special_room_support.md ending text, Seal logic, and room data
docs/enemy_lifetime.md       room enemy lifetime transition and carry contract
docs/enemy_ai_record.md      complete eight-byte AI record layout and aliases
docs/object_record.md        complete 20-byte object and collision-mask layout
docs/linked_enemy_ai.md      linked-slot allocation and action dispatch
docs/gameplay_exit_transition.md cooperative death, TIME OVER, and GDV flow
docs/attract_demo_flow.md    post-game, title, and recorded demo control
docs/chr_bank_policy.md      complete CNROM request and screen/room bank policy
docs/room_map_tiles.md       RoomMap byte classes, collision, and rendering
docs/dana_action_states.md   Dana action pairs, facing, Y motion, and cast state
docs/title_screen.md         packed title renderer and record presentation
scripts/project.py         split, verify, lint, and safe build helpers
scripts/asm_style.py       shared ca65 formatter and style checker
scripts/verify_rom.py      original/build/asset comparison and ROM reports
scripts/room_data.py       room-format decoder
scripts/revision_profiles.py regional verification, split, and room comparison
scripts/level_editor.py    deterministic level document import/build pipeline
scripts/level_studio.py    visual room editor with build and FCEUX play actions
scripts/audio_editor.py    deterministic audio document import/build pipeline
scripts/audio_preview.py   sequencer trace and APU-like WAV preview renderer
scripts/sound_studio.py    visual audio-bank editor over the shared codec
scripts/reconstruction_status.py semantic coverage and provenance audit
scripts/scheduler_data.py scheduler-table decoder and source-call audit
scripts/enemy_ai_data.py enemy AI handler-table decoder and audit
scripts/enemy_pointer_data.py split record-pointer decoder and audit
scripts/ppu_update_data.py static PPU stream decoder and round-trip audit
src/data/static_ppu_update_streams.asm reviewed static stream tables and payload
src/data/pre_startup_padding.asm classified filler immediately before Reset
src/main.asm               assembly entrypoint and iNES header
src/system/nmi.asm         semantic `$8000-$80FE` vertical-blank module
src/system/controller_input.asm serial sampling and cached controller input
src/system/startup.asm     reset, warm-boot state, PPU and thread bootstrap
src/system/scheduler.asm   eight-context cooperative stack scheduler
src/system/pause_thread.asm context-two Start-button pause loop
src/game/special_room_scripts.asm 53-entry room script dispatcher and triggers
src/game/ending_sequence.asm room-index 49 ending sequence
src/game/ending_and_special_room_support.asm ending and special-room support
src/system/sound_effect_queue.asm three-slot sound command producer
src/system/audio_engine.asm NMI audio sequencer, command VM, and APU publisher
src/system/ppu_update_buffer.asm publish shared RAM program to NMI
src/graphics/ppu_attribute_read.asm NMI RoomMap attribute-byte reader
src/system/jump_with_params.asm inline appendix tail-dispatch ABI
src/game/room_clear_thread.asm context-one room completion and handoff
src/game/room_time_bonus.asm decimal remaining-time score conversion
src/game/room_load_thread.asm common new-game and room loading pipeline
src/game/new_game_state_reset.asm initial counters, flags, and score reset
src/data/room_load_palette.asm mutable room palette update template
src/data/room_clear.asm overlapping transition AI/object templates
src/data/room_load.asm Dana preload and room palette selection tables
src/game/room_door_key_update.asm initial visible room cells
src/game/room_intro.asm room/lives HUD and special-room names
src/game/room_entry_animation.asm Dana placement and entry presentation
src/game/transition_object_orbit.asm timed fifteen-object orbit controller
src/game/transition_orbit_position.asm sine-scaled orbit positioning
src/data/quarter_sine.asm 32-entry transition magnitude table
src/system/masked_ram_wait.asm cooperative masked zero-page waits
src/system/secondary_thread_reset.asm stop other contexts during transitions
src/game/gameplay_exit_transition.asm life-loss, TIME OVER, and GDV flow
src/game/room_transition_reset.asm exit-screen data and transition state reset
src/game/object_y_clamp.asm align object Y to a 16-pixel surface
src/game/object_x_left_clamp.asm clamp object X against its left surface
src/game/object_x_right_clamp.asm clamp object X against its right surface
src/game/object_motion_animation.asm load type/action motion and animation data
src/game/object_update.asm  traverse and update all 21 object records
src/game/object_motion.asm  integrate signed fixed-point object motion
src/game/object_collision.asm sample RoomMap cells into collision masks
src/game/object_animation.asm advance packed animation frames
src/game/object_collision_dispatch.asm dispatch collision-mask responses
src/data/object_collision_handlers.asm 16-entry response pointer table
src/game/object_collision_response.asm coordinate/motion/action responses
src/game/object_y_thirteen_clamp.asm clamp object Y to the `$...D` inset
src/game/coordinate_conversion.asm pixel and packed room-index conversion
src/game/main_thread.asm   context-three gameplay service loop
src/game/demon_mirror_schedule.asm two eight-byte spawn schedules
src/game/demon_mirror_spawn.asm allocate scheduled mirror placeholders
src/game/demon_mirror_activation.asm cyclic enemy-set activation
src/game/demon_mirror_initialization.asm mirror coordinate/object setup
src/game/timer.asm         countdown arithmetic and warning-state transitions
src/game/timer_item_effects.asm multiply or replace time from collected items
src/game/inventory_item_effects.asm packed inventory and related item handlers
src/data/item_scores.asm  collectible score digit and amount lookup tables
src/game/auxiliary_effect.asm shared auxiliary-object effect initialization
src/game/score.asm         game-state-gated decimal score addition
src/game/timer_display.asm NMI update-program builder for timer digits
src/game/enemy_movement.asm active-enemy movement prepass
src/game/enemy_ai_dispatch.asm 17-slot per-enemy AI selector
src/game/fireball_lifetime.asm fireball expiration and delayed cleanup
src/game/enemy_initialization.asm enemy slot position/state initialization
src/game/enemy_type_configuration.asm spawn-type object/AI configuration
src/data/enemy_types.asm  packed enemy-type configuration table
src/game/enemy_ai_handlers.asm handler tables and linked-slot behavior support
src/game/enemy_position.asm shared current-enemy position-copy helper
src/game/enemy_pointers.asm shared object/AI record pointer resolvers
src/game/enemy_slot_allocation.asm free enemy-record allocator
src/data/enemy_record_pointers.asm generated record-pool pointer tables
src/game/enemy_deactivation.asm parallel-record slot retirement
src/game/current_enemy_deactivation.asm retirement, lifetime, and adjacent filler
src/game/active_object_states.asm update active non-Dana record states
src/game/object_pointer.asm non-Dana object-record pointer resolver
src/game/non_dana_object_deactivation.asm clear the non-Dana object pool
src/graphics/chr.asm       `.incbin` wrapper for ignored generated CHR
src/memory/                hardware and RAM symbol registries
tests/                     tooling and codec tests
```

## Evidence boundary

Names in source and documentation are classified as confirmed,
high-confidence, tentative, or unknown. A readable name is not treated as
proof by itself. Static control flow, pointer tables, read/write traces, and
repeatable runtime scenarios are the intended evidence layers. See
`docs/naming.md` and `docs/unknowns.md`.

## Upstream material and rights

The preservation listing was imported from
[rbmichael/solomons_key_disassembly](https://github.com/rbmichael/solomons_key_disassembly),
which attributes the original disassembly to `ninespaces`. That repository did
not contain an explicit license when imported. This project therefore does not
assert a blanket license over the imported listing or game data. Original
tooling and documentation should be treated separately from third-party and
copyrighted material. See `docs/provenance.md` for the complete source ledger
and `docs/licensing.md` for component-by-component redistribution boundaries.

This is an unofficial preservation and research project. Solomon's Key and its
game data remain property of their respective rights holders.
