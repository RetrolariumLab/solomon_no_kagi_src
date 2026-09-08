# Profile-aware level, audio, graphics, and presentation authoring.

export-levels:
	$(RUN_TOOL) $(LEVEL_EDITOR) --profiles "$(REVISION_MANIFEST)" export \
		--profile "$(PROFILE)" --output "$(LEVEL_DOCUMENT)"

validate-levels:
	$(RUN_TOOL) $(LEVEL_EDITOR) --profiles "$(REVISION_MANIFEST)" validate \
		--input "$(LEVEL_DOCUMENT)"

build-levels:
	$(RUN_TOOL) $(LEVEL_EDITOR) --profiles "$(REVISION_MANIFEST)" build \
		--input "$(LEVEL_DOCUMENT)" --output "$(LEVEL_ROM)"

roundtrip-levels:
	$(RUN_TOOL) $(LEVEL_EDITOR) --profiles "$(REVISION_MANIFEST)" roundtrip \
		--profile "$(PROFILE)"

roundtrip-level-profiles:
	$(MAKE) roundtrip-levels PROFILE=usa
	$(MAKE) roundtrip-levels PROFILE=europe

level-summary:
	$(RUN_TOOL) $(LEVEL_EDITOR) --profiles "$(REVISION_MANIFEST)" summary \
		--input "$(LEVEL_DOCUMENT)"

level-studio:
	$(RUN_TOOL) $(LEVEL_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile "$(PROFILE)" --document "$(LEVEL_DOCUMENT)" \
		--output "$(LEVEL_ROM)" --fceux "$(FCEUX)"

check-level-studio:
	$(RUN_TOOL) $(LEVEL_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile usa --check
	$(RUN_TOOL) $(LEVEL_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile europe --check

check-level-block-reference:
	$(RUN_TOOL) $(LEVEL_EDITOR) --profiles "$(REVISION_MANIFEST)" \
		check-block-reference --profile "$(PROFILE)" \
		--csv "$(LEVEL_BLOCK_REFERENCE)"

smoke-level-playtest:
	$(RUN_TOOL) $(LEVEL_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile "$(PROFILE)" --document "$(LEVEL_DOCUMENT)" \
		--output "$(LEVEL_ROM)" --fceux "$(FCEUX)" --check-playtest \
		--playtest-room "$(LEVEL_PLAYTEST_ROOM)"

smoke-level-playtests:
	$(MAKE) smoke-level-playtest PROFILE=usa LEVEL_PLAYTEST_ROOM=1
	$(MAKE) smoke-level-playtest PROFILE=europe LEVEL_PLAYTEST_ROOM=30

export-audio:
	$(RUN_TOOL) $(AUDIO_EDITOR) --profiles "$(REVISION_MANIFEST)" export \
		--profile "$(PROFILE)" --output "$(AUDIO_DOCUMENT)"

validate-audio:
	$(RUN_TOOL) $(AUDIO_EDITOR) --profiles "$(REVISION_MANIFEST)" validate \
		--input "$(AUDIO_DOCUMENT)"

build-audio:
	$(RUN_TOOL) $(AUDIO_EDITOR) --profiles "$(REVISION_MANIFEST)" build \
		--input "$(AUDIO_DOCUMENT)" --output "$(AUDIO_ROM)"

roundtrip-audio:
	$(RUN_TOOL) $(AUDIO_EDITOR) --profiles "$(REVISION_MANIFEST)" roundtrip \
		--profile "$(PROFILE)"

roundtrip-audio-profiles:
	$(MAKE) roundtrip-audio PROFILE=usa
	$(MAKE) roundtrip-audio PROFILE=europe

audio-summary:
	$(RUN_TOOL) $(AUDIO_EDITOR) --profiles "$(REVISION_MANIFEST)" summary \
		--input "$(AUDIO_DOCUMENT)"

preview-audio:
	$(RUN_TOOL) $(AUDIO_PREVIEW_TOOL) --profiles "$(REVISION_MANIFEST)" \
		--input "$(AUDIO_DOCUMENT)" --profile "$(PROFILE)" \
		--effect "$(AUDIO_EFFECT)" --seconds "$(AUDIO_PREVIEW_SECONDS)" \
		--channels "$(AUDIO_CHANNELS)" \
		--output "$(AUDIO_PREVIEW)"

sound-studio:
	$(RUN_TOOL) $(SOUND_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile "$(PROFILE)" --document "$(AUDIO_DOCUMENT)" \
		--output "$(AUDIO_ROM)"

check-sound-studio:
	$(RUN_TOOL) $(SOUND_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile usa --check
	$(RUN_TOOL) $(SOUND_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile europe --check

export-graphics:
	$(RUN_TOOL) $(GRAPHICS_EDITOR) --profiles "$(REVISION_MANIFEST)" export \
		--profile "$(PROFILE)" --output "$(GRAPHICS_DOCUMENT)"

validate-graphics:
	$(RUN_TOOL) $(GRAPHICS_EDITOR) --profiles "$(REVISION_MANIFEST)" validate \
		--input "$(GRAPHICS_DOCUMENT)"

build-graphics:
	$(RUN_TOOL) $(GRAPHICS_EDITOR) --profiles "$(REVISION_MANIFEST)" build \
		--input "$(GRAPHICS_DOCUMENT)" --output "$(GRAPHICS_ROM)"

roundtrip-graphics:
	$(RUN_TOOL) $(GRAPHICS_EDITOR) --profiles "$(REVISION_MANIFEST)" roundtrip \
		--profile "$(PROFILE)"

roundtrip-graphics-profiles:
	$(MAKE) roundtrip-graphics PROFILE=usa
	$(MAKE) roundtrip-graphics PROFILE=europe

graphics-summary:
	$(RUN_TOOL) $(GRAPHICS_EDITOR) --profiles "$(REVISION_MANIFEST)" summary \
		--input "$(GRAPHICS_DOCUMENT)"

graphics-studio:
	$(RUN_TOOL) $(GRAPHICS_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile "$(PROFILE)" --document "$(GRAPHICS_DOCUMENT)" \
		--output "$(GRAPHICS_ROM)"

check-graphics-studio:
	$(RUN_TOOL) $(GRAPHICS_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile usa --check
	$(RUN_TOOL) $(GRAPHICS_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile europe --check

export-presentation:
	$(RUN_TOOL) $(PRESENTATION_EDITOR) --profiles "$(REVISION_MANIFEST)" export \
		--profile "$(PROFILE)" --output "$(PRESENTATION_DOCUMENT)"

validate-presentation:
	$(RUN_TOOL) $(PRESENTATION_EDITOR) --profiles "$(REVISION_MANIFEST)" validate \
		--input "$(PRESENTATION_DOCUMENT)"

build-presentation:
	$(RUN_TOOL) $(PRESENTATION_EDITOR) --profiles "$(REVISION_MANIFEST)" build \
		--input "$(PRESENTATION_DOCUMENT)" --output "$(PRESENTATION_ROM)"

roundtrip-presentation:
	$(RUN_TOOL) $(PRESENTATION_EDITOR) --profiles "$(REVISION_MANIFEST)" roundtrip \
		--profile "$(PROFILE)"

roundtrip-presentation-profiles:
	$(MAKE) roundtrip-presentation PROFILE=usa
	$(MAKE) roundtrip-presentation PROFILE=europe

presentation-summary:
	$(RUN_TOOL) $(PRESENTATION_EDITOR) --profiles "$(REVISION_MANIFEST)" summary \
		--input "$(PRESENTATION_DOCUMENT)"

presentation-studio:
	$(RUN_TOOL) $(PRESENTATION_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile "$(PROFILE)" --document "$(PRESENTATION_DOCUMENT)" \
		--output "$(PRESENTATION_ROM)"

check-presentation-studio:
	$(RUN_TOOL) $(PRESENTATION_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile usa --check
	$(RUN_TOOL) $(PRESENTATION_STUDIO) --profiles "$(REVISION_MANIFEST)" \
		--profile europe --check

editor-ui-smoke-profile:
	$(RUN_TOOL) authoring.editor_workstation_smoke \
		--profiles "$(REVISION_MANIFEST)" --profile "$(PROFILE)"

editor-ui-smoke-profiles:
	$(MAKE) editor-ui-smoke-profile PROFILE=usa
	$(MAKE) editor-ui-smoke-profile PROFILE=europe
