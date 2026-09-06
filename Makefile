PYTHON ?= python
CA65 ?= bin/ca65.exe
LD65 ?= bin/ld65.exe
REFERENCE_ROM ?= Solomon's Key (U) [!].nes
MANIFEST := assets/manifest.json
VERIFY_ROM := scripts/verify_rom.py
TOOLCHAIN_MANIFEST := config/toolchain.json

BUILD_DIR := build/native
GENERATED_ASSET_DIR := assets/generated
CHR_ASSET := $(GENERATED_ASSET_DIR)/chr/solomons_key.chr
OBJECT := $(BUILD_DIR)/solomons_key.o
ROM := $(BUILD_DIR)/solomons_key.nes
LABELS := $(BUILD_DIR)/solomons_key.lbl
MAP := $(BUILD_DIR)/solomons_key.map
DEBUG := $(BUILD_DIR)/solomons_key.dbg
SYMBOL_DIR := $(BUILD_DIR)
SYMBOL_SUMMARY := $(BUILD_DIR)/debug_symbols.json
FCEUX ?= ../fceux_automation/vc/x64/Release/fceux64.exe
RUNTIME_SCENARIOS := scenarios/runtime_scenarios.json
RUNTIME_LUA := scripts/capture_runtime_scenario.lua
RUNTIME_TRACE_DIR := $(BUILD_DIR)/runtime
DEBUG_SYMBOLS := $(PYTHON) scripts/debug_symbols.py --debug "$(DEBUG)" --map "$(MAP)" \
	--labels "$(LABELS)" --breakpoints config/debugger_breakpoints.json \
	--watches config/debugger_watches.json --output-dir "$(SYMBOL_DIR)" \
	--rom-name "$(notdir $(ROM))" --summary "$(SYMBOL_SUMMARY)"
SOURCE_FILES := src/main.asm src/system/nmi.asm src/game/nmi_gameplay_interactions.asm \
	src/system/controller_input.asm src/game/nmi_dana_and_sprites.asm \
	src/game/object_update.asm src/game/object_motion.asm \
	src/game/object_collision.asm src/game/object_animation.asm \
	src/game/object_collision_dispatch.asm src/data/object_collision_handlers.asm \
	src/game/object_collision_response.asm src/game/object_y_thirteen_clamp.asm \
	src/system/startup.asm \
	src/system/scheduler.asm src/system/pause_thread.asm \
	src/system/sound_effect_queue.asm \
	src/system/ppu_update_buffer.asm src/system/jump_with_params.asm \
	src/data/room_load_palette.asm src/game/room_clear_thread.asm \
	src/data/room_clear.asm src/game/room_time_bonus.asm \
	src/game/room_load_thread.asm src/data/room_load.asm \
	src/game/new_game_state_reset.asm \
	src/system/gameplay_delay_setup.asm \
	src/system/masked_ram_wait.asm \
	src/system/secondary_thread_reset.asm \
	src/game/room_door_key_update.asm src/game/room_intro.asm \
	src/data/room_intro.asm src/game/two_digit_number.asm \
	src/game/room_entry_animation.asm src/data/room_entry_animation.asm \
	src/game/transition_object_orbit.asm \
	src/game/transition_orbit_position.asm \
	src/game/transition_orbit_scale.asm src/game/quarter_sine.asm \
	src/data/quarter_sine.asm \
	src/game/room_transition_reset.asm \
	src/graphics/nametable_clear.asm src/data/nametable_clear.asm \
	src/graphics/full_nametable_clear.asm \
	src/graphics/title_screen.asm \
	src/graphics/ppu_address.asm \
	src/graphics/direct_ppu_transfer.asm \
	src/graphics/ppu_data_writers.asm src/data/repeated_ppu_patterns.asm \
	src/graphics/room_nametable_frame.asm \
	src/game/room_item_decode.asm src/data/room_item_decode.asm \
	src/game/room_block_decode.asm src/data/room_blocks.asm \
	src/data/room_items.asm \
	src/system/audio_engine.asm \
	src/data/audio.asm \
	src/game/dana_actions.asm \
	src/system/counter_wait.asm \
	src/game/map_interactions.asm src/game/coordinate_object_overlap.asm \
	src/graphics/room_map_cell_update.asm src/graphics/room_map_ppu_address.asm \
	src/data/main_thread_padding.asm \
	src/graphics/static_ppu_update_queue.asm src/data/static_ppu_update_streams.asm \
	src/game/room_enemy_load.asm src/data/room_enemies.asm \
	src/graphics/room_map_render.asm \
	src/game/object_y_clamp.asm \
	src/game/object_x_left_clamp.asm \
	src/game/object_x_right_clamp.asm \
	src/game/object_motion_animation.asm \
	src/data/object_animations.asm \
	src/data/object_motion.asm \
	src/graphics/ppu_update_stream.asm \
	src/graphics/ppu_attribute_read.asm \
	src/data/pre_startup_padding.asm \
	src/game/main_thread.asm \
	src/game/demon_mirror_activation.asm \
	src/game/demon_mirror_schedule.asm src/game/demon_mirror_spawn.asm \
	src/game/demon_mirror_initialization.asm src/game/timer.asm \
	src/data/timer_warning.asm \
	src/game/timer_item_effects.asm \
	src/game/inventory_item_effects.asm \
	src/data/item_scores.asm src/game/auxiliary_effect.asm \
	src/game/score.asm src/game/gameplay_exit_transition.asm \
	src/game/coordinate_conversion.asm \
	src/game/timer_display.asm src/game/enemy_movement.asm \
	src/game/enemy_ai_dispatch.asm \
	src/graphics/fireball_inventory_display.asm \
	src/data/fireball_inventory_display.asm \
	src/game/fireball_lifetime.asm \
	src/game/enemy_initialization.asm \
	src/game/enemy_type_configuration.asm \
	src/data/enemy_types.asm \
	src/game/enemy_ai_handlers.asm src/game/early_enemy_ai.asm \
	src/game/mid_enemy_ai.asm src/game/pathfinding_enemy_ai.asm \
	src/game/collision_enemy_ai.asm src/game/late_enemy_ai.asm \
	src/game/enemy_position.asm \
	src/game/enemy_pointers.asm \
	src/game/enemy_slot_allocation.asm \
	src/data/enemy_record_pointers.asm \
	src/game/enemy_deactivation.asm \
	src/game/current_enemy_deactivation.asm \
	src/game/special_room_scripts.asm \
	src/game/ending_sequence.asm \
	src/game/ending_and_special_room_support.asm \
	src/game/active_object_states.asm \
	src/game/object_pointer.asm \
	src/game/non_dana_object_deactivation.asm src/game/attract_demo_flow.asm \
	src/graphics/gameplay_hud.asm src/data/gameplay_hud.asm \
	src/graphics/score_display.asm \
	src/game/item_collision.asm src/data/item_handlers.asm \
	src/game/red_bottle_item.asm src/game/special_item_flags.asm \
	src/game/key_item.asm src/game/door_item.asm \
	src/game/gameplay_pool_clear.asm \
	src/game/coordinate_delta.asm \
	src/graphics/chr.asm src/memory/hardware.inc src/memory/ram.inc

.PHONY: all build split verify verify-reference verify-built verify-header \
	verify-prg verify-chr verify-payload verify-rom verify-assets check-assets \
	verify-toolchain verify-build-toolchain verify-runtime-toolchain verify-host \
	verify-private-input \
	rom-info rom-info-reference rom-info-built symbols validate-symbols \
	trace trace-runtime validate-runtime \
	format format-check lint lint-asm \
	lint-source lint-project test quality-check check release-audit pre-tag-audit \
	release-static-check release-check source-1-audit source-1-post-tag-audit rooms \
	validate-rooms room-data-audit chr-bank-report chr-bank-audit roundtrip-formats \
	reconstruction-status reconstruction-audit \
	prg-layout-report prg-layout-audit format-coverage-audit \
	scheduler-report scheduler-audit enemy-ai-report enemy-ai-audit \
	item-handler-report item-handler-audit \
	enemy-pointer-report enemy-pointer-audit ppu-update-report ppu-update-audit \
	object-animation-report object-animation-audit \
	object-motion-report object-motion-audit \
	title-data-report title-data-audit audio-data-report audio-data-audit clean

all: verify

$(BUILD_DIR):
	$(PYTHON) scripts/project.py mkdir --path "$(BUILD_DIR)"

$(CHR_ASSET):
	$(PYTHON) scripts/project.py require --path "$@" --hint "run 'make split' first"

$(OBJECT): $(SOURCE_FILES) $(CHR_ASSET) | $(BUILD_DIR) verify-build-toolchain
	$(CA65) --debug-info -g -o "$@" -l "$(BUILD_DIR)/solomons_key.lst" "src/main.asm"

$(ROM): $(OBJECT) config/linker/cnrom.cfg | verify-build-toolchain
	$(LD65) -C config/linker/cnrom.cfg -o "$@" "$<" -Ln "$(LABELS)" -m "$(MAP)" --dbgfile "$(DEBUG)"

build: verify-build-toolchain $(ROM)

verify-build-toolchain:
	$(PYTHON) scripts/project.py toolchain --manifest "$(TOOLCHAIN_MANIFEST)" \
		--scope build --component-path "assembler=$(CA65)" \
		--component-path "linker=$(LD65)"

verify-runtime-toolchain:
	$(PYTHON) scripts/project.py toolchain --manifest "$(TOOLCHAIN_MANIFEST)" \
		--scope runtime --component-path "runtime_emulator=$(FCEUX)"

verify-private-input:
	$(PYTHON) scripts/project.py toolchain --manifest "$(TOOLCHAIN_MANIFEST)" \
		--scope private --component-path "usa_reference_rom=$(REFERENCE_ROM)"

verify-host:
	$(PYTHON) scripts/project.py toolchain --manifest "$(TOOLCHAIN_MANIFEST)" \
		--scope host

verify-toolchain: verify-build-toolchain verify-runtime-toolchain verify-private-input verify-host

verify-reference: verify-private-input
	$(PYTHON) scripts/project.py verify --image "$(REFERENCE_ROM)" --manifest "$(MANIFEST)"

verify-built: $(ROM)
	$(PYTHON) scripts/project.py verify --image "$(ROM)" --manifest "$(MANIFEST)"

verify-header: $(ROM)
	$(PYTHON) "$(VERIFY_ROM)" compare --built "$(ROM)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region header

verify-prg: $(ROM)
	$(PYTHON) "$(VERIFY_ROM)" compare --built "$(ROM)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region prg

verify-chr: $(ROM)
	$(PYTHON) "$(VERIFY_ROM)" compare --built "$(ROM)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region chr

verify-payload: $(ROM)
	$(PYTHON) "$(VERIFY_ROM)" compare --built "$(ROM)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region payload

verify-rom: $(ROM)
	$(PYTHON) "$(VERIFY_ROM)" compare --built "$(ROM)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region rom

verify-assets: $(CHR_ASSET)
	$(PYTHON) "$(VERIFY_ROM)" asset --asset "$(CHR_ASSET)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region chr

check-assets: verify-assets

verify: verify-reference verify-built verify-header verify-prg verify-chr verify-payload verify-rom verify-assets

split: verify-private-input
	$(PYTHON) scripts/project.py split --image "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --output-dir "$(GENERATED_ASSET_DIR)"

rom-info-reference:
	$(PYTHON) "$(VERIFY_ROM)" report --image "$(REFERENCE_ROM)" --manifest "$(MANIFEST)"

rom-info-built: $(ROM)
	$(PYTHON) "$(VERIFY_ROM)" report --image "$(ROM)" --manifest "$(MANIFEST)"

rom-info: rom-info-reference rom-info-built

symbols: $(ROM)
	$(DEBUG_SYMBOLS)

validate-symbols: symbols
	$(DEBUG_SYMBOLS) --check

trace-runtime: verify-runtime-toolchain symbols
	$(PYTHON) scripts/runtime_scenarios.py trace --fceux "$(FCEUX)" --rom "$(ROM)" \
		--lua "$(RUNTIME_LUA)" --scenarios "$(RUNTIME_SCENARIOS)" \
		--output-dir "$(RUNTIME_TRACE_DIR)"
	$(MAKE) validate-runtime

trace: trace-runtime

validate-runtime:
	$(PYTHON) scripts/runtime_scenarios.py validate --scenarios "$(RUNTIME_SCENARIOS)" \
		--trace-dir "$(RUNTIME_TRACE_DIR)"

format:
	$(PYTHON) scripts/asm_style.py --fix src
	$(MAKE) lint

format-check: lint-asm

lint-asm:
	$(PYTHON) scripts/asm_style.py src

lint-source:
	$(PYTHON) scripts/project.py lint

lint-project: lint-source

lint: lint-asm lint-source

test:
	$(PYTHON) -m unittest discover -s tests -v

rooms: $(ROM)
	$(PYTHON) scripts/room_data.py --image "$(ROM)" --pretty

validate-rooms: $(ROM)
	$(PYTHON) scripts/room_data.py --image "$(ROM)" --validate

room-data-audit: $(ROM)
	$(PYTHON) scripts/room_data.py --image "$(ROM)" --roundtrip

chr-bank-report: $(ROM)
	$(PYTHON) scripts/room_data.py --image "$(ROM)" --chr-bank-report --pretty

chr-bank-audit: $(ROM)
	$(PYTHON) scripts/room_data.py --image "$(ROM)" --chr-bank-audit

roundtrip-formats: room-data-audit ppu-update-audit object-animation-audit \
	object-motion-audit title-data-audit audio-data-audit format-coverage-audit

reconstruction-status:
	$(PYTHON) scripts/reconstruction_status.py report

reconstruction-audit: $(ROM)
	$(PYTHON) scripts/reconstruction_status.py audit --map "$(MAP)" --labels "$(LABELS)"

release-audit: $(ROM)
	$(PYTHON) scripts/reconstruction_status.py release-audit \
		--map "$(MAP)" --labels "$(LABELS)" \
		--release config/source_reconstruction_1_0.json

pre-tag-audit: $(ROM)
	$(PYTHON) scripts/reconstruction_status.py pre-tag-audit \
		--map "$(MAP)" --labels "$(LABELS)" \
		--release config/source_reconstruction_1_0.json

source-1-post-tag-audit: $(ROM)
	$(PYTHON) scripts/reconstruction_status.py post-tag-audit \
		--map "$(MAP)" --labels "$(LABELS)" \
		--release config/source_reconstruction_1_0.json

prg-layout-report: $(ROM)
	$(PYTHON) scripts/prg_layout.py report --debug "$(DEBUG)" --config config/prg_layout.json

prg-layout-audit: $(ROM)
	$(PYTHON) scripts/prg_layout.py audit --debug "$(DEBUG)" --config config/prg_layout.json

format-coverage-audit: $(ROM)
	$(PYTHON) scripts/prg_layout.py format-audit --debug "$(DEBUG)" --config config/prg_layout.json

scheduler-report: $(ROM)
	$(PYTHON) scripts/scheduler_data.py report --image "$(ROM)"

scheduler-audit: $(ROM)
	$(PYTHON) scripts/scheduler_data.py audit --image "$(ROM)"

enemy-ai-report: $(ROM)
	$(PYTHON) scripts/enemy_ai_data.py report --image "$(ROM)"

enemy-ai-audit: $(ROM)
	$(PYTHON) scripts/enemy_ai_data.py audit --image "$(ROM)"

item-handler-report: $(ROM)
	$(PYTHON) scripts/item_handler_data.py report --image "$(ROM)"

item-handler-audit: $(ROM)
	$(PYTHON) scripts/item_handler_data.py audit --image "$(ROM)"

enemy-pointer-report: $(ROM)
	$(PYTHON) scripts/enemy_pointer_data.py report --image "$(ROM)"

enemy-pointer-audit: $(ROM)
	$(PYTHON) scripts/enemy_pointer_data.py audit --image "$(ROM)"

ppu-update-report: $(ROM)
	$(PYTHON) scripts/ppu_update_data.py report --image "$(ROM)"

ppu-update-audit: $(ROM)
	$(PYTHON) scripts/ppu_update_data.py audit --image "$(ROM)"

object-animation-report: $(ROM)
	$(PYTHON) scripts/object_animation_data.py report --image "$(ROM)"

object-animation-audit: $(ROM)
	$(PYTHON) scripts/object_animation_data.py audit --image "$(ROM)"

object-motion-report: $(ROM)
	$(PYTHON) scripts/object_motion_data.py report --image "$(ROM)"

object-motion-audit: $(ROM)
	$(PYTHON) scripts/object_motion_data.py audit --image "$(ROM)"

title-data-report: $(ROM)
	$(PYTHON) scripts/title_data.py report --image "$(ROM)"

title-data-audit: $(ROM)
	$(PYTHON) scripts/title_data.py audit --image "$(ROM)"

audio-data-report: $(ROM)
	$(PYTHON) scripts/audio_data.py report --image "$(ROM)"

audio-data-audit: $(ROM)
	$(PYTHON) scripts/audio_data.py audit --image "$(ROM)"

quality-check: lint test

release-static-check: quality-check verify validate-rooms roundtrip-formats \
	reconstruction-audit prg-layout-audit validate-symbols scheduler-audit \
	enemy-ai-audit enemy-pointer-audit chr-bank-audit \
	item-handler-audit release-audit

release-check:
	$(MAKE) clean
	$(MAKE) verify-toolchain verify-reference
	$(MAKE) lint
	$(MAKE) test roundtrip-formats
	$(MAKE) verify validate-rooms reconstruction-audit prg-layout-audit \
		scheduler-audit enemy-ai-audit enemy-pointer-audit chr-bank-audit \
		item-handler-audit
	$(MAKE) validate-symbols trace-runtime
	$(MAKE) release-audit
	$(MAKE) pre-tag-audit

source-1-audit: release-check

check: release-static-check

clean:
	$(PYTHON) scripts/project.py clean --path build
