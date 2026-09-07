# Documentation index

This page is the navigation entry point for the reconstruction. Start with the
release contract and architecture, then follow the subsystem group relevant to
the code or evidence being reviewed. File names generally mirror the owning
ASM module.

## Release, evidence, and project policy

- [Source Reconstruction 1.0](source_reconstruction_1_0.md) defines the fixed
  USA scope and tag gate.
- [Source Reconstruction 2.0](source_reconstruction_2_0.md) defines the
  additive USA/PAL source, runtime, authoring, and release-gate contract.
- [Revision profiles](revision_profiles.md) define the active 2.0 USA, Europe,
  and Japan identities, private-asset boundary, room comparisons, and planned
  regional build structure.
- [Verification](verification.md), [code quality](code_quality.md), and the
  [toolchain contract](toolchain.md) describe commands, pinned binaries, and
  release evidence. The [roadmap](roadmap.md) records milestone boundaries.
- [Runtime evidence](runtime_evidence.md) and the
  [debugger workflow](debugger_workflow.md) cover deterministic FCEUX traces,
  generated symbols, breakpoints, and watches.
- [Naming policy](naming.md), [provenance](provenance.md), the machine-readable
  [rename ledger](provenance/label_renames.json), and
  [unknowns](unknowns.md) define what semantic claims the source makes.
- [Licensing and redistribution boundaries](licensing.md) classify project
  tools, imported material, reconstructed source, and private inputs separately.

## Architecture, memory, and source ownership

- [Architecture](architecture.md) is the high-level execution and data-flow
  overview.
- [Source layout](source_layout.md) maps semantic modules to the PRG image.
- [Source organization](source_organization.md) defines subsystem directories,
  preferred file sizes, and the reviewed exceptions enforced by `make lint`.
- [RAM map](ram_map.md) records runtime storage, aliases, and record ranges.
- [Data formats](data_formats.md) summarizes encoded streams and their
  round-trip tooling.
- [Object record](object_record.md), [enemy AI record](enemy_ai_record.md), and
  [RoomMap tiles](room_map_tiles.md) define the main shared data contracts.

## Reset, NMI, input, and cooperative scheduling

- [Startup](startup.md), [NMI](nmi.md),
  [gameplay NMI interactions](nmi_gameplay_interactions.md), and
  [Dana/OAM NMI services](nmi_dana_and_sprites.md).
- [Controller input](controller_input.md), [scheduler](scheduler.md), and the
  complete [scheduler entry table](scheduler_entries.md).
- [Pause thread](pause_thread.md),
  [secondary-thread reset](secondary_thread_reset.md),
  [counter wait](counter_wait.md), [masked RAM wait](masked_ram_wait.md), and
  [inline parameter jumps](jump_with_params.md).

## Room lifecycle, maps, and progression

- [Room transition pipeline](room_transition_pipeline.md),
  [room transition reset](room_transition_reset.md), and
  [room intro/orbit](room_intro_and_orbit.md).
- [Room block decode](room_block_decode.md),
  [room item decode](room_item_decode.md), and
  [room enemy load](room_enemy_load.md).
- [RoomMap rendering](room_map_render.md),
  [cell updates](room_map_cell_update.md),
  [nametable frame](room_nametable_frame.md), and
  [CHR-bank policy](chr_bank_policy.md).
- [Demon Mirror runtime](demon_mirror_runtime.md),
  [special-room scripts](special_room_scripts.md),
  [special-room/ending support](ending_and_special_room_support.md), and the
  [ending sequence](ending_sequence.md).

## Main gameplay and Dana

- [Main gameplay thread](main_gameplay_thread.md),
  [Dana actions](dana_actions.md), and
  [Dana action states](dana_action_states.md).
- [Map interactions](map_interactions.md),
  [item interactions](item_interactions.md),
  [inventory effects](inventory_item_effects.md), and
  [item score tables](item_score_tables.md).
- [Timer](timer.md), [timer item effects](timer_item_effects.md),
  [score](score.md), and [gameplay exit](gameplay_exit_transition.md).
- [Fireball lifetime](fireball_lifetime.md),
  [fireball inventory display](fireball_inventory_display.md), and
  [auxiliary effect](auxiliary_effect.md).
- [Attract/demo flow](attract_demo_flow.md),
  [coordinate conversion](coordinate_conversion.md), and
  [coordinate deltas](coordinate_delta.md).

## Objects and collision

- [Object update pipeline](object_update_pipeline.md),
  [motion/animation loading](object_motion_animation.md), and
  [collision response](object_collision_response.md).
- [Object pointer lookup](object_pointer.md) and
  [object-pool maintenance](object_pool_maintenance.md).
- [Y clamp](object_y_clamp.md), [left X clamp](object_x_left_clamp.md), and
  [right X clamp](object_x_right_clamp.md).

## Enemies and AI

- [Enemy initialization](enemy_initialization.md),
  [type configuration](enemy_type_configuration.md),
  [movement](enemy_movement.md), [position helpers](enemy_position.md), and
  [lifetime](enemy_lifetime.md).
- [AI dispatch](enemy_ai_dispatch.md), [AI handlers](enemy_ai_handlers.md),
  [early AI](early_enemy_ai.md), [mid AI](mid_enemy_ai.md),
  [late AI](late_enemy_ai.md), [collision AI](collision_enemy_ai.md), and
  [pathfinding AI](pathfinding_enemy_ai.md).
- [Linked enemy AI](linked_enemy_ai.md),
  [slot allocation](enemy_slot_allocation.md),
  [record pointers](enemy_record_pointers.md), and the lower-level
  [pointer families](enemy_pointers.md).
- [Enemy deactivation](enemy_deactivation.md) and
  [current-enemy deactivation](current_enemy_deactivation.md).

## PPU, presentation, and audio

- [PPU address writer](ppu_address.md),
  [direct PPU transfer](direct_ppu_transfer.md),
  [PPU data writers](ppu_data_writers.md),
  [update buffer](ppu_update_buffer.md), and
  [update-stream interpreter](ppu_update_stream.md).
- [Static PPU update queue](static_ppu_update_queue.md),
  [nametable clear](nametable_clear.md), and
  [title screen](title_screen.md).
- [Gameplay HUD](gameplay_hud.md),
  [sound-effect queue](sound_effect_queue.md), and
  [audio engine](audio_engine.md).
