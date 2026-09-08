# Revision discovery, source builds, and profile identity checks.

list-revisions:
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" list

identify-revision:
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" identify \
		--image "$(REVISION_ROM)"

verify-revision-reference:
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" verify \
		--profile "$(PROFILE)"

verify-revision-references:
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" verify

split-revision-assets:
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" split \
		--profile "$(PROFILE)" --output-dir "$(GENERATED_ASSET_DIR)"

split-all:
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" split \
		--output-dir "$(GENERATED_ASSET_DIR)"

revision-room-report:
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" room-report \
		--profile "$(PROFILE)"

revision-room-audit:
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" audit-rooms

compare-revision-rooms:
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" compare-rooms \
		--left "$(LEFT_PROFILE)" --right "$(RIGHT_PROFILE)"

build-revision: $(CHR_ASSET) verify-build-toolchain
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" \
		source-check --profile "$(PROFILE)"
	$(RUN_TOOL) build.project mkdir --path "$(REVISION_BUILD_DIR)"
	$(CA65) -D SolomonRevision=$(REVISION_DEFINE) --debug-info -g \
		-o "$(REVISION_OBJECT)" -l "$(REVISION_BUILD_DIR)/solomons_key.lst" \
		"src/main.asm"
	$(LD65) -C config/linker/cnrom.cfg -o "$(REVISION_ROM)" \
		"$(REVISION_OBJECT)" -Ln "$(REVISION_BUILD_DIR)/solomons_key.lbl" \
		-m "$(REVISION_BUILD_DIR)/solomons_key.map" \
		--dbgfile "$(REVISION_BUILD_DIR)/solomons_key.dbg"

verify-revision-source: build-revision
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" \
		verify-source --profile "$(PROFILE)" --built "$(REVISION_ROM)"

verify-revision-sources:
	$(MAKE) verify-revision-source PROFILE=usa
	$(MAKE) verify-revision-source PROFILE=europe

verify-revision: build-revision
	$(RUN_TOOL) $(REVISION_TOOL) --manifest "$(REVISION_MANIFEST)" \
		verify-built --profile "$(PROFILE)" --built "$(REVISION_ROM)"

verify-revisions:
	$(MAKE) verify-revision PROFILE=usa
	$(MAKE) verify-revision PROFILE=europe

revision-symbols: build-revision
	$(RUN_TOOL) validation.debug_symbols --debug "$(REVISION_DEBUG)" \
		--map "$(REVISION_MAP)" --labels "$(REVISION_LABELS)" \
		--breakpoints config/debugger_breakpoints.json \
		--watches config/debugger_watches.json --profile "$(PROFILE)" \
		--output-dir "$(REVISION_BUILD_DIR)" \
		--rom-name "$(notdir $(REVISION_ROM))" \
		--summary "$(REVISION_SYMBOL_SUMMARY)"

validate-revision-symbols: revision-symbols
	$(RUN_TOOL) validation.debug_symbols --debug "$(REVISION_DEBUG)" \
		--map "$(REVISION_MAP)" --labels "$(REVISION_LABELS)" \
		--breakpoints config/debugger_breakpoints.json \
		--watches config/debugger_watches.json --profile "$(PROFILE)" \
		--output-dir "$(REVISION_BUILD_DIR)" \
		--rom-name "$(notdir $(REVISION_ROM))" \
		--summary "$(REVISION_SYMBOL_SUMMARY)" --check

validate-revision-symbol-profiles:
	$(MAKE) validate-revision-symbols PROFILE=usa
	$(MAKE) validate-revision-symbols PROFILE=europe
