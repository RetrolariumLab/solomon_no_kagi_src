# Solomon's Key: build the source back into the USA and European ROMs and
# check it. `make help` lists the targets.
PYTHON ?= python
# cc65 from Retrolarium Kit (RLTOOL, default rltool), asked once per run; the
# recipes' shell needs forward slashes.
RLTOOL ?= rltool
export RLTOOL
CA65 ?= $(eval CA65 := $$(subst \,/,$$(shell $$(RLTOOL) build-tools path nes ca65)))$(CA65)
LD65 ?= $(eval LD65 := $$(subst \,/,$$(shell $$(RLTOOL) build-tools path nes ld65)))$(LD65)
# MAME for `make test-full` and `make golden`.
MAME ?= $(RETROLARIUM_MAME)

# The private assets: assets/manifest.json names the ROMs and what `make split`
# cuts out of them; `rltool assets` (Retrolarium Kit) splits, checks and
# verifies.
ASSETS = $(RLTOOL) assets $(1)
BASE_IMAGE := usa
REFERENCE_ROM ?= Solomon's Key (U) [!].nes
LINKER_CONFIG := config/linker/cnrom.cfg
# The revisions the source builds: image ids of assets/manifest.json and their
# SolomonRevision value (the Japanese image is not reconstructed yet).
REVISIONS := usa europe
REVISION ?= europe
SOLOMON_REVISION_usa := 0
SOLOMON_REVISION_europe := 1
BUILD_DIR := build/native
ROM := $(BUILD_DIR)/solomons_key.nes
REVISION_ROM = build/revisions/$(REVISION)/solomons_key.nes
# Fifty-one segments before the audio code moved (scripts/build/relocate.py).
RELOCATED_DIR := build/relocated
RELOCATED_ROM := $(RELOCATED_DIR)/solomons_key.nes
# The movies test-full plays, in this order: a TAS first, then a longplay,
# then the attract mode.
MOVIE_CHECKS := movies/attract.check.json
SOURCE_FILES := $(sort $(wildcard src/*.asm src/*/*.asm src/*/*/*.asm src/*/*.inc))

# One build of src/main.asm: $(call build_rom,<output ROM>,<SolomonRevision>)
build_rom = $(PYTHON) -c "from pathlib import Path; Path('$(dir $(1))').mkdir(parents=True, exist_ok=True)" && \
	$(CA65) -D SolomonRevision=$(2) --debug-info -g -o "$(basename $(1)).o" -l "$(basename $(1)).lst" "src/main.asm" && \
	$(LD65) -C $(LINKER_CONFIG) -o "$(1)" "$(basename $(1)).o" -Ln "$(basename $(1)).lbl" \
		-m "$(basename $(1)).map" --dbgfile "$(basename $(1)).dbg"

.PHONY: all help build verify build-revision verify-revision verify-revisions split \
	_require-assets build-relocated verify-toolchain studio-check lint format format-check \
	test test-full golden hooks clean

all: verify

split:
	$(call ASSETS,split)

_require-assets:
	$(call ASSETS,check) --image $(BASE_IMAGE)

$(ROM): $(SOURCE_FILES) Makefile | verify-toolchain _require-assets
	$(call build_rom,$@,0)

build: $(ROM)

verify: $(ROM)
	$(call ASSETS,verify) --image $(BASE_IMAGE) --built "$(ROM)"

# One revision (REVISION=usa or europe).
build-revision: verify-toolchain _require-assets
	$(call build_rom,$(REVISION_ROM),$(SOLOMON_REVISION_$(REVISION)))

verify-revision: build-revision
	$(call ASSETS,verify) --image $(REVISION) --built "$(REVISION_ROM)"

# Every revision the source builds whose ROM is here.
verify-revisions:
	@for revision in $$($(call ASSETS,images) --present); do \
		case " $(REVISIONS) " in *" $$revision "*) \
			$(MAKE) --no-print-directory verify-revision REVISION=$$revision || exit 1;; \
		esac; \
	done

build-relocated: $(SOURCE_FILES) | verify-toolchain _require-assets
	$(PYTHON) scripts/build/relocate.py --main src/main.asm --linker-config $(LINKER_CONFIG) \
		--output "$(RELOCATED_DIR)/main.asm"
	$(CA65) -g -o "$(RELOCATED_DIR)/solomons_key.o" "$(RELOCATED_DIR)/main.asm"
	$(LD65) -C $(LINKER_CONFIG) -o "$(RELOCATED_ROM)" "$(RELOCATED_DIR)/solomons_key.o"

verify-toolchain:
	$(PYTHON) scripts/build/toolchain.py --manifest config/toolchain.json

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
	$(MAKE) --no-print-directory verify verify-revisions build-relocated studio-check

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
	$(PYTHON) -c "import shutil; shutil.rmtree('build', ignore_errors=True)"

help:
	@echo "Solomon's Key source reconstruction"
	@echo "  make split                  cut the assets out of the ROMs that are here (once)"
	@echo "  make build / verify         the USA revision / and byte for byte"
	@echo "  make build-revision REVISION=usa|europe / verify-revision / verify-revisions"
	@echo "  make build-relocated        fifty-one segments moved"
	@echo "  make studio-check           open and rebuild every solomons_key.rlj revision"
	@echo "  make test                   the quick suite"
	@echo "  make test-full              test, then the attract mode in MAME (MAME=<path>)"
	@echo "  make golden                 record the attract mode's checkpoints from the original"
	@echo "  make lint / format / format-check   the house style (Retrolarium Kit)"
	@echo "  make hooks                  install the Git hooks"
	@echo "  make verify-toolchain / clean"
