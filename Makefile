# Solomon's Key: build the source back into the USA and European ROMs and
# check it. `make help` lists the targets.
PYTHON ?= python
RUN_TOOL := $(PYTHON) scripts/run.py
# cc65 from Retrolarium Kit (RLTOOL, default rltool), asked once per run; the
# recipes' shell needs forward slashes.
RLTOOL ?= rltool
export RLTOOL
CA65 ?= $(eval CA65 := $$(subst \,/,$$(shell $$(RLTOOL) build-tools path nes ca65)))$(CA65)
LD65 ?= $(eval LD65 := $$(subst \,/,$$(shell $$(RLTOOL) build-tools path nes ld65)))$(LD65)
# MAME for `make test-full` and `make golden`.
MAME ?= $(RETROLARIUM_MAME)

REFERENCE_ROM ?= Solomon's Key (U) [!].nes
MANIFEST := assets/manifest.json
VERIFY_ROM := $(RUN_TOOL) build.verify_rom
TOOLCHAIN_MANIFEST := config/toolchain.json
LINKER_CONFIG := config/linker/cnrom.cfg
REVISION_MANIFEST := config/revision_profiles.json
REVISION_TOOL := $(RUN_TOOL) build.revision_profiles --manifest "$(REVISION_MANIFEST)"
PROFILE ?= usa
REVISION_DEFINE_usa = 0
REVISION_DEFINE_europe = 1
REVISION_BUILD_DIR = build/revisions/$(PROFILE)
REVISION_ROM = $(REVISION_BUILD_DIR)/solomons_key.nes

BUILD_DIR := build/native
GENERATED_ASSET_DIR := assets/generated
CHR_ASSET := $(GENERATED_ASSET_DIR)/chr/solomons_key.chr
OBJECT := $(BUILD_DIR)/solomons_key.o
ROM := $(BUILD_DIR)/solomons_key.nes
LABELS := $(BUILD_DIR)/solomons_key.lbl
MAP := $(BUILD_DIR)/solomons_key.map
DEBUG := $(BUILD_DIR)/solomons_key.dbg
# Fifty-one segments before the audio code moved (scripts/build/relocate.py).
RELOCATED_DIR := build/relocated
RELOCATED_ROM := $(RELOCATED_DIR)/solomons_key.nes
# The movies test-full plays, in this order: a TAS first, then a longplay,
# then the attract mode.
MOVIE_CHECKS := movies/attract.check.json
SOURCE_FILES := $(sort $(wildcard src/*.asm src/*/*.asm src/*/*/*.asm src/*/*.inc))

.PHONY: all help build split verify verify-reference verify-built verify-header verify-prg \
	verify-chr verify-payload verify-rom verify-assets rom-info rom-info-reference \
	rom-info-built list-revisions identify-revision verify-revision-reference \
	verify-revision-references split-revision-assets split-all build-revision \
	verify-revision-source verify-revision-sources verify-revision verify-revisions \
	build-relocated verify-toolchain studio-check lint format format-check test test-full \
	golden hooks clean

all: verify

$(BUILD_DIR) $(RELOCATED_DIR):
	$(RUN_TOOL) build.project mkdir --path "$@"

$(CHR_ASSET):
	$(RUN_TOOL) build.project require --path "$@" --hint "run 'make split' first"

$(OBJECT): $(SOURCE_FILES) $(CHR_ASSET) Makefile | $(BUILD_DIR) verify-toolchain
	$(CA65) --debug-info -g -o "$@" -l "$(BUILD_DIR)/solomons_key.lst" "src/main.asm"

$(ROM): $(OBJECT) $(LINKER_CONFIG)
	$(LD65) -C $(LINKER_CONFIG) -o "$@" "$<" -Ln "$(LABELS)" -m "$(MAP)" --dbgfile "$(DEBUG)"

build: $(ROM)

split:
	$(RUN_TOOL) build.project split --image "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --output-dir "$(GENERATED_ASSET_DIR)"

verify-reference:
	$(RUN_TOOL) build.project verify --image "$(REFERENCE_ROM)" --manifest "$(MANIFEST)"

verify-built: $(ROM)
	$(RUN_TOOL) build.project verify --image "$(ROM)" --manifest "$(MANIFEST)"

verify-header verify-prg verify-chr verify-payload verify-rom: $(ROM)
	$(VERIFY_ROM) compare --built "$(ROM)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region $(subst verify-,,$@)

verify-assets: $(CHR_ASSET)
	$(VERIFY_ROM) asset --asset "$(CHR_ASSET)" --reference "$(REFERENCE_ROM)" --manifest "$(MANIFEST)" --region chr

verify: verify-reference verify-built verify-header verify-prg verify-chr verify-payload \
	verify-rom verify-assets

rom-info-reference:
	$(VERIFY_ROM) report --image "$(REFERENCE_ROM)" --manifest "$(MANIFEST)"

rom-info-built: $(ROM)
	$(VERIFY_ROM) report --image "$(ROM)" --manifest "$(MANIFEST)"

rom-info: rom-info-reference rom-info-built

# The regional revisions (config/revision_profiles.json), PROFILE=usa or europe.
list-revisions:
	$(REVISION_TOOL) list

identify-revision:
	$(REVISION_TOOL) identify --image "$(REVISION_ROM)"

verify-revision-reference:
	$(REVISION_TOOL) verify --profile "$(PROFILE)"

verify-revision-references:
	$(REVISION_TOOL) verify

split-revision-assets:
	$(REVISION_TOOL) split --profile "$(PROFILE)" --output-dir "$(GENERATED_ASSET_DIR)"

split-all:
	$(REVISION_TOOL) split --output-dir "$(GENERATED_ASSET_DIR)"

build-revision: $(CHR_ASSET) verify-toolchain
	$(REVISION_TOOL) source-check --profile "$(PROFILE)"
	$(RUN_TOOL) build.project mkdir --path "$(REVISION_BUILD_DIR)"
	$(CA65) -D SolomonRevision=$(REVISION_DEFINE_$(PROFILE)) --debug-info -g \
		-o "$(REVISION_BUILD_DIR)/solomons_key.o" "src/main.asm"
	$(LD65) -C $(LINKER_CONFIG) -o "$(REVISION_ROM)" "$(REVISION_BUILD_DIR)/solomons_key.o" \
		-Ln "$(REVISION_BUILD_DIR)/solomons_key.lbl" -m "$(REVISION_BUILD_DIR)/solomons_key.map" \
		--dbgfile "$(REVISION_BUILD_DIR)/solomons_key.dbg"

verify-revision-source: build-revision
	$(REVISION_TOOL) verify-source --profile "$(PROFILE)" --built "$(REVISION_ROM)"

verify-revision-sources:
	$(MAKE) --no-print-directory verify-revision-source PROFILE=usa
	$(MAKE) --no-print-directory verify-revision-source PROFILE=europe

verify-revision: build-revision
	$(REVISION_TOOL) verify-built --profile "$(PROFILE)" --built "$(REVISION_ROM)"

verify-revisions:
	$(MAKE) --no-print-directory verify-revision PROFILE=usa
	$(MAKE) --no-print-directory verify-revision PROFILE=europe

build-relocated: $(SOURCE_FILES) $(CHR_ASSET) | $(RELOCATED_DIR) verify-toolchain
	$(PYTHON) scripts/build/relocate.py --main src/main.asm --linker-config $(LINKER_CONFIG) \
		--output "$(RELOCATED_DIR)/main.asm"
	$(CA65) -g -o "$(RELOCATED_DIR)/solomons_key.o" "$(RELOCATED_DIR)/main.asm"
	$(LD65) -C $(LINKER_CONFIG) -o "$(RELOCATED_ROM)" "$(RELOCATED_DIR)/solomons_key.o"

verify-toolchain:
	$(RUN_TOOL) build.project toolchain --manifest "$(TOOLCHAIN_MANIFEST)" \
		--scope build --component-path "assembler=$(CA65)" --component-path "linker=$(LD65)"

# Open every revision of solomons_key.rlj in a throwaway copy of the
# repository the way Retrolarium Studio does, and rebuild each without edits.
studio-check:
	$(RLTOOL) studio check solomons_key.rlj

lint:
	$(RLTOOL) lint

format:
	$(RLTOOL) lint --fix

format-check:
	$(RLTOOL) lint --only assembly

# The quick suite: the unit tests, both revisions byte for byte, the relocated
# build and the studio check.
test:
	$(PYTHON) -m unittest discover -s tests -t .
	$(MAKE) --no-print-directory verify verify-revisions verify-revision-sources \
		build-relocated studio-check

# The full suite: the quick one, then the movies in MAME on the relocated
# build in turn (the first that differs stops it); the attract mode plays with
# no input: the title, the demo and its game over. Compared with what the
# original ROM gives (movies/*.check.json, written by `make golden`).
test-full: test
	$(RLTOOL) movie check $(MOVIE_CHECKS) --rom "$(RELOCATED_ROM)" --mame "$(MAME)"

golden:
	$(RLTOOL) movie golden $(MOVIE_CHECKS) --rom "$(REFERENCE_ROM)" --mame "$(MAME)"

# `make hooks`, once per clone, makes Git check every commit and push for stop
# words and run `make lint` and `make format-check` first (Retrolarium Kit's
# rltool hooks; the stop-word list lives outside the repositories).
hooks:
	$(RLTOOL) hooks install --project .

clean:
	$(RUN_TOOL) build.project clean --path build

help:
	@echo "Solomon's Key source reconstruction"
	@echo "  make split                  unpack the assets from your USA ROM (once)"
	@echo "  make build / verify         the USA revision / and byte for byte"
	@echo "  make verify-revisions       USA and Europe (PROFILE=usa|europe for one)"
	@echo "  make build-relocated        fifty-one segments moved"
	@echo "  make studio-check           open and rebuild every solomons_key.rlj revision"
	@echo "  make test                   the quick suite"
	@echo "  make test-full              test, then the attract mode in MAME (MAME=<path>)"
	@echo "  make golden                 record the attract mode's checkpoints from the original"
	@echo "  make lint / format / format-check   the house style (Retrolarium Kit)"
	@echo "  make hooks                  install the Git hooks"
	@echo "  make rom-info / list-revisions / identify-revision / split-all / clean"
