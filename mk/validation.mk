# Static quality, format contracts, and release gates.

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

scaffold-check: lint
	$(PYTHON) -m unittest $(ROMLESS_TEST_MODULES) -v

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

scheduler-profile-audit: build-revision
	$(PYTHON) scripts/scheduler_data.py audit --image "$(REVISION_ROM)" \
		--profile "$(PROFILE)"

scheduler-profile-audits:
	$(MAKE) scheduler-profile-audit PROFILE=usa
	$(MAKE) scheduler-profile-audit PROFILE=europe

enemy-ai-report: $(ROM)
	$(PYTHON) scripts/enemy_ai_data.py report --image "$(ROM)"

enemy-ai-audit: $(ROM)
	$(PYTHON) scripts/enemy_ai_data.py audit --image "$(ROM)"

enemy-ai-profile-audit: build-revision
	$(PYTHON) scripts/enemy_ai_data.py audit --image "$(REVISION_ROM)"

enemy-ai-profile-audits:
	$(MAKE) enemy-ai-profile-audit PROFILE=usa
	$(MAKE) enemy-ai-profile-audit PROFILE=europe

item-handler-report: $(ROM)
	$(PYTHON) scripts/item_handler_data.py report --image "$(ROM)"

item-handler-audit: $(ROM)
	$(PYTHON) scripts/item_handler_data.py audit --image "$(ROM)"

item-handler-profile-audit: build-revision
	$(PYTHON) scripts/item_handler_data.py audit --image "$(REVISION_ROM)" \
		--profile "$(PROFILE)"

item-handler-profile-audits:
	$(MAKE) item-handler-profile-audit PROFILE=usa
	$(MAKE) item-handler-profile-audit PROFILE=europe

enemy-pointer-report: $(ROM)
	$(PYTHON) scripts/enemy_pointer_data.py report --image "$(ROM)"

enemy-pointer-audit: $(ROM)
	$(PYTHON) scripts/enemy_pointer_data.py audit --image "$(ROM)"

enemy-pointer-profile-audit: build-revision
	$(PYTHON) scripts/enemy_pointer_data.py audit --image "$(REVISION_ROM)" \
		--profile "$(PROFILE)"

enemy-pointer-profile-audits:
	$(MAKE) enemy-pointer-profile-audit PROFILE=usa
	$(MAKE) enemy-pointer-profile-audit PROFILE=europe

ppu-update-report: $(ROM)
	$(PYTHON) scripts/ppu_update_data.py report --image "$(ROM)"

ppu-update-audit: $(ROM)
	$(PYTHON) scripts/ppu_update_data.py audit --image "$(ROM)"

ppu-update-profile-audit: build-revision
	$(PYTHON) scripts/ppu_update_data.py audit --image "$(REVISION_ROM)" \
		--profile "$(PROFILE)"

ppu-update-profile-audits:
	$(MAKE) ppu-update-profile-audit PROFILE=usa
	$(MAKE) ppu-update-profile-audit PROFILE=europe

object-animation-report: $(ROM)
	$(PYTHON) scripts/object_animation_data.py report --image "$(ROM)"

object-animation-audit: $(ROM)
	$(PYTHON) scripts/object_animation_data.py audit --image "$(ROM)"

object-animation-profile-audit: build-revision
	$(PYTHON) scripts/object_animation_data.py audit --image "$(REVISION_ROM)" \
		--profile "$(PROFILE)"

object-animation-profile-audits:
	$(MAKE) object-animation-profile-audit PROFILE=usa
	$(MAKE) object-animation-profile-audit PROFILE=europe

object-motion-report: $(ROM)
	$(PYTHON) scripts/object_motion_data.py report --image "$(ROM)"

object-motion-audit: $(ROM)
	$(PYTHON) scripts/object_motion_data.py audit --image "$(ROM)"

object-motion-profile-audit: build-revision
	$(PYTHON) scripts/object_motion_data.py audit --image "$(REVISION_ROM)" \
		--profile "$(PROFILE)"

object-motion-profile-audits:
	$(MAKE) object-motion-profile-audit PROFILE=usa
	$(MAKE) object-motion-profile-audit PROFILE=europe

title-data-report: $(ROM)
	$(PYTHON) scripts/title_data.py report --image "$(ROM)"

title-data-audit: $(ROM)
	$(PYTHON) scripts/title_data.py audit --image "$(ROM)"

title-data-profile-audit: build-revision
	$(PYTHON) scripts/title_data.py audit --image "$(REVISION_ROM)" \
		--profile "$(PROFILE)"

title-data-profile-audits:
	$(MAKE) title-data-profile-audit PROFILE=usa
	$(MAKE) title-data-profile-audit PROFILE=europe

audio-data-report: $(ROM)
	$(PYTHON) scripts/audio_data.py report --image "$(ROM)"

audio-data-audit: $(ROM)
	$(PYTHON) scripts/audio_data.py audit --image "$(ROM)"

audio-profile-audit:
	$(MAKE) verify-revision-reference PROFILE=$(PROFILE)
	$(PYTHON) scripts/audio_data.py audit --profile "$(PROFILE)" \
		--image "$(AUDIO_PROFILE_IMAGE)"

audio-profile-audits:
	$(MAKE) audio-profile-audit PROFILE=usa
	$(MAKE) audio-profile-audit PROFILE=europe

source-2-profile-audits:
	$(MAKE) revision-room-audit
	$(MAKE) scheduler-profile-audits enemy-ai-profile-audits \
		enemy-pointer-profile-audits item-handler-profile-audits
	$(MAKE) ppu-update-profile-audits object-animation-profile-audits \
		object-motion-profile-audits title-data-profile-audits \
		audio-profile-audits

source-2-release-audit:
	$(PYTHON) "$(SOURCE_2_RELEASE_TOOL)" audit \
		--release "$(SOURCE_2_RELEASE_MANIFEST)"

source-2-pre-tag-audit:
	$(PYTHON) "$(SOURCE_2_RELEASE_TOOL)" pre-tag-audit \
		--release "$(SOURCE_2_RELEASE_MANIFEST)"

source-2-post-tag-audit:
	$(PYTHON) "$(SOURCE_2_RELEASE_TOOL)" post-tag-audit \
		--release "$(SOURCE_2_RELEASE_MANIFEST)"

quality-check: lint test

release-static-check: quality-check verify validate-rooms roundtrip-formats \
	reconstruction-audit prg-layout-audit validate-symbols scheduler-audit \
	enemy-ai-audit enemy-pointer-audit chr-bank-audit \
	item-handler-audit release-audit

source-1-regression-check:
	$(MAKE) clean
	$(MAKE) verify-toolchain verify-reference
	$(MAKE) lint
	$(MAKE) test roundtrip-formats
	$(MAKE) verify validate-rooms reconstruction-audit prg-layout-audit \
		scheduler-audit enemy-ai-audit enemy-pointer-audit chr-bank-audit \
		item-handler-audit
	$(MAKE) validate-symbols trace-runtime
	$(MAKE) release-audit

release-check:
	$(MAKE) source-1-regression-check
	$(MAKE) pre-tag-audit

source-1-audit: release-check

source-2-static-check:
	$(MAKE) verify-revision-references verify-revision-sources verify-revisions
	$(MAKE) source-2-profile-audits roundtrip-level-profiles \
		roundtrip-audio-profiles roundtrip-graphics-profiles \
		roundtrip-presentation-profiles
	$(MAKE) check-level-studio check-sound-studio check-graphics-studio \
		check-presentation-studio \
		validate-revision-symbol-profiles
	$(MAKE) source-2-release-audit

source-2-regression-check:
	$(MAKE) source-1-regression-check
	$(MAKE) source-2-static-check
	$(MAKE) trace-revision-runtimes smoke-level-playtests
	$(MAKE) source-2-release-audit

source-2-check:
	$(MAKE) source-2-regression-check
	$(MAKE) source-2-pre-tag-audit
