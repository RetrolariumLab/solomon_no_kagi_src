PYTHON ?= python
RUN_TOOL := $(PYTHON) scripts/run.py
CA65 ?= bin/ca65.exe
LD65 ?= bin/ld65.exe
REFERENCE_ROM ?= Solomon's Key (U) [!].nes
EUROPE_REFERENCE_ROM ?= Solomon's Key (E) [!].nes
MANIFEST := assets/manifest.json
VERIFY_ROM := build.verify_rom
TOOLCHAIN_MANIFEST := config/toolchain.json
SOURCE_2_RELEASE_MANIFEST := config/source_reconstruction_2_0.json
SOURCE_2_RELEASE_TOOL := validation.source_2_release
SOURCE_2_MINOR_MANIFEST := config/source_reconstruction_2_1.json
SOURCE_2_MINOR_TOOL := validation.source_2_minor_release
REVISION_MANIFEST := config/revision_profiles.json
REVISION_TOOL := build.revision_profiles
PROFILE ?= usa
LEFT_PROFILE ?= usa
RIGHT_PROFILE ?= europe
REVISION_BUILD_DIR = build/revisions/$(PROFILE)
REVISION_OBJECT = $(REVISION_BUILD_DIR)/solomons_key.o
REVISION_ROM = $(REVISION_BUILD_DIR)/solomons_key.nes
REVISION_LABELS = $(REVISION_BUILD_DIR)/solomons_key.lbl
REVISION_MAP = $(REVISION_BUILD_DIR)/solomons_key.map
REVISION_DEBUG = $(REVISION_BUILD_DIR)/solomons_key.dbg
REVISION_SYMBOL_SUMMARY = $(REVISION_BUILD_DIR)/debug_symbols.json
REVISION_DEFINE_usa = 0
REVISION_DEFINE_europe = 1
REVISION_DEFINE = $(REVISION_DEFINE_$(PROFILE))
AUDIO_REFERENCE_usa = $(REFERENCE_ROM)
AUDIO_REFERENCE_europe = $(EUROPE_REFERENCE_ROM)
AUDIO_PROFILE_IMAGE = $(AUDIO_REFERENCE_$(PROFILE))

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
RUNTIME_LUA := scripts/runtime/capture_runtime_scenario.lua
RUNTIME_TRACE_DIR := $(BUILD_DIR)/runtime
REVISION_RUNTIME_SCENARIOS_usa = scenarios/runtime_scenarios.json
REVISION_RUNTIME_SCENARIOS_europe = scenarios/runtime_scenarios_europe.json
REVISION_RUNTIME_SCENARIOS = $(REVISION_RUNTIME_SCENARIOS_$(PROFILE))
REVISION_RUNTIME_TRACE_DIR = $(REVISION_BUILD_DIR)/runtime
DEBUG_SYMBOLS := $(RUN_TOOL) validation.debug_symbols --debug "$(DEBUG)" --map "$(MAP)" \
	--labels "$(LABELS)" --breakpoints config/debugger/breakpoints.json \
	--watches config/debugger/watches.json --output-dir "$(SYMBOL_DIR)" \
	--rom-name "$(notdir $(ROM))" --summary "$(SYMBOL_SUMMARY)"
SOURCE_FILES := src/main.asm \
	src/system/boot_and_frame.asm src/system/thread_runtime.asm \
	src/audio/engine.asm src/audio/data.asm src/audio/europe_streams.asm \
	src/game/nmi/gameplay_interactions.asm src/game/nmi/dana_and_sprites.asm \
	src/game/objects/update_pipeline.asm src/game/objects/collision_and_motion.asm \
	src/game/enemies/runtime.asm src/game/enemies/early_ai.asm \
	src/game/enemies/mid_ai.asm src/game/enemies/pathfinding_ai.asm \
	src/game/enemies/collision_ai.asm src/game/enemies/late_ai.asm \
	src/game/rooms/lifecycle.asm src/game/rooms/decoding.asm \
	src/game/rooms/mechanics.asm src/game/items/collection.asm \
	src/game/items/progression.asm src/game/demon_mirror/runtime.asm \
	src/game/ending/sequence.asm src/game/ending/special_room_support.asm \
	src/game/flow/runtime.asm src/game/timer/runtime.asm \
	src/game/transitions/orbit.asm src/game/dana_actions.asm src/game/scoring.asm \
	src/graphics/ppu/runtime.asm src/graphics/rooms/rendering.asm \
	src/graphics/hud/runtime.asm src/graphics/title_screen.asm src/graphics/chr.asm \
	src/data/static_layout.asm src/data/enemies/tables.asm \
	src/data/objects/animations.asm src/data/objects/motion.asm \
	src/data/rooms/metadata.asm src/data/rooms/blocks.asm \
	src/data/rooms/enemies.asm src/data/rooms/items.asm \
	src/memory/hardware.inc src/memory/ram.inc
MAKE_FRAGMENTS := mk/profiles.mk mk/runtime.mk mk/validation.mk
ROMLESS_TEST_MODULES := \
	tests.build.test_atomic_io \
	tests.build.test_make_help \
	tests.build.test_project \
	tests.build.test_script_runner \
	tests.build.test_verify_rom \
	tests.build.test_revision_profiles \
	tests.runtime.test_runtime_scenarios \
	tests.validation.test_asm_style \
	tests.validation.test_debug_symbols \
	tests.validation.test_prg_layout \
	tests.validation.test_reconstruction_status \
	tests.validation.test_release_history \
	tests.validation.test_room_data \
	tests.validation.test_public_text \
	tests.validation.test_public_command_smoke \
	tests.validation.test_source_2_minor_release

.PHONY: all help build split verify verify-reference verify-built verify-header \
	verify-prg verify-chr verify-payload verify-rom verify-assets check-assets \
	verify-toolchain verify-build-toolchain verify-runtime-toolchain verify-host \
	verify-private-input \
	rom-info rom-info-reference rom-info-built symbols validate-symbols \
	trace trace-runtime validate-runtime \
	format format-check lint lint-asm validate-public-text \
	lint-source lint-project test scaffold-check quality-check check release-audit pre-tag-audit \
	release-static-check release-check source-1-audit source-1-post-tag-audit rooms \
	source-1-regression-check source-2-profile-audits \
	source-2-release-audit source-2-static-check source-2-regression-check \
	source-2-pre-tag-audit source-2-post-tag-audit source-2-check \
	public-command-smoke \
	source-2-minor-audit source-2-minor-check source-2-minor-pre-tag-check \
	source-2-minor-tag-check \
	validate-rooms room-data-audit chr-bank-report chr-bank-audit roundtrip-formats \
	reconstruction-status reconstruction-audit \
	prg-layout-report prg-layout-audit format-coverage-audit \
	scheduler-report scheduler-audit scheduler-profile-audit \
	scheduler-profile-audits enemy-ai-report enemy-ai-audit \
	enemy-ai-profile-audit enemy-ai-profile-audits \
	item-handler-report item-handler-audit item-handler-profile-audit \
	item-handler-profile-audits \
	enemy-pointer-report enemy-pointer-audit enemy-pointer-profile-audit \
	enemy-pointer-profile-audits ppu-update-report ppu-update-audit \
	ppu-update-profile-audit ppu-update-profile-audits \
	object-animation-report object-animation-audit object-animation-profile-audit \
	object-animation-profile-audits \
	object-motion-report object-motion-audit object-motion-profile-audit \
	object-motion-profile-audits \
	title-data-report title-data-audit title-data-profile-audit \
	title-data-profile-audits audio-data-report audio-data-audit \
	audio-profile-audit audio-profile-audits clean \
	list-revisions identify-revision verify-revision-reference \
	verify-revision-references split-revision-assets split-all \
	revision-room-report revision-room-audit compare-revision-rooms \
	studio-check source-3-audit source-3-check \
	build-revision verify-revision-source verify-revision-sources \
	verify-revision verify-revisions revision-symbols validate-revision-symbols \
	validate-revision-symbol-profiles trace-revision-runtime \
	validate-revision-runtime trace-revision-runtimes

all: verify

help:
	@$(PYTHON) -m scripts.build.make_help

$(BUILD_DIR):
	$(RUN_TOOL) build.project mkdir --path "$(BUILD_DIR)"

$(CHR_ASSET):
	$(RUN_TOOL) build.project require --path "$@" --hint "run 'make split' first"

$(OBJECT): $(SOURCE_FILES) $(CHR_ASSET) Makefile $(MAKE_FRAGMENTS) | $(BUILD_DIR) verify-build-toolchain
	$(CA65) --debug-info -g -o "$@" -l "$(BUILD_DIR)/solomons_key.lst" "src/main.asm"

$(ROM): $(OBJECT) config/linker/cnrom.cfg | verify-build-toolchain
	$(LD65) -C config/linker/cnrom.cfg -o "$@" "$<" -Ln "$(LABELS)" -m "$(MAP)" --dbgfile "$(DEBUG)"

build: verify-build-toolchain $(ROM)

verify-build-toolchain:
	$(RUN_TOOL) build.project toolchain --manifest "$(TOOLCHAIN_MANIFEST)" \
		--scope build --component-path "assembler=$(CA65)" \
		--component-path "linker=$(LD65)"

verify-runtime-toolchain:
	$(RUN_TOOL) build.project toolchain --manifest "$(TOOLCHAIN_MANIFEST)" \
		--scope runtime --component-path "runtime_emulator=$(FCEUX)"

verify-private-input:
	$(RUN_TOOL) build.project toolchain --manifest "$(TOOLCHAIN_MANIFEST)" \
		--scope private --component-path "usa_reference_rom=$(REFERENCE_ROM)"

verify-host:
	$(RUN_TOOL) build.project toolchain --manifest "$(TOOLCHAIN_MANIFEST)" \
		--scope host

verify-toolchain: verify-build-toolchain verify-runtime-toolchain verify-private-input verify-host

verify-reference: verify-private-input
	$(RUN_TOOL) build.project verify --image "$(REFERENCE_ROM)" --manifest "$(MANIFEST)"

verify-built: $(ROM)
	$(RUN_TOOL) build.project verify --image "$(ROM)" --manifest "$(MANIFEST)"

verify-header: $(ROM)
	$(RUN_TOOL) $(VERIFY_ROM) compare --built "$(ROM)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region header

verify-prg: $(ROM)
	$(RUN_TOOL) $(VERIFY_ROM) compare --built "$(ROM)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region prg

verify-chr: $(ROM)
	$(RUN_TOOL) $(VERIFY_ROM) compare --built "$(ROM)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region chr

verify-payload: $(ROM)
	$(RUN_TOOL) $(VERIFY_ROM) compare --built "$(ROM)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region payload

verify-rom: $(ROM)
	$(RUN_TOOL) $(VERIFY_ROM) compare --built "$(ROM)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region rom

verify-assets: $(CHR_ASSET)
	$(RUN_TOOL) $(VERIFY_ROM) asset --asset "$(CHR_ASSET)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region chr

check-assets: verify-assets

verify: verify-reference verify-built verify-header verify-prg verify-chr verify-payload verify-rom verify-assets

split: verify-private-input
	$(RUN_TOOL) build.project split --image "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --output-dir "$(GENERATED_ASSET_DIR)"

rom-info-reference:
	$(RUN_TOOL) $(VERIFY_ROM) report --image "$(REFERENCE_ROM)" --manifest "$(MANIFEST)"

rom-info-built: $(ROM)
	$(RUN_TOOL) $(VERIFY_ROM) report --image "$(ROM)" --manifest "$(MANIFEST)"

rom-info: rom-info-reference rom-info-built

include $(MAKE_FRAGMENTS)

check: release-static-check

clean:
	$(RUN_TOOL) build.project clean --path build
