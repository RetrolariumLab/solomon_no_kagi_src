# Deterministic runtime capture and validation.

trace-revision-runtime: verify-runtime-toolchain validate-revision-symbols
	$(PYTHON) scripts/runtime_scenarios.py trace --fceux "$(FCEUX)" \
		--rom "$(REVISION_ROM)" --lua "$(RUNTIME_LUA)" \
		--scenarios "$(REVISION_RUNTIME_SCENARIOS)" \
		--output-dir "$(REVISION_RUNTIME_TRACE_DIR)" --profile "$(PROFILE)"
	$(MAKE) validate-revision-runtime PROFILE=$(PROFILE)

validate-revision-runtime:
	$(PYTHON) scripts/runtime_scenarios.py validate \
		--scenarios "$(REVISION_RUNTIME_SCENARIOS)" \
		--trace-dir "$(REVISION_RUNTIME_TRACE_DIR)" --profile "$(PROFILE)"

trace-revision-runtimes:
	$(MAKE) trace-revision-runtime PROFILE=usa
	$(MAKE) trace-revision-runtime PROFILE=europe

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
