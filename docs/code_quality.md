# Code quality

The quality targets follow the same split used by the sibling Pac-Man and
Super Mario Bros. preservation projects.

- `make format` normalizes every ca65 `.asm` and `.inc` source, then runs all
  linters
- `make format-check` checks assembly formatting without changing files
- `make lint-asm` checks the shared assembly style contract
- `make lint-source` checks the repository structure, every Python and JSON
  source, local documentation links, source contracts, ASM module sizes and
  directory organization, and tracked private/generated output policy
- `make lint-project` is a compatibility alias for `make lint-source`
- `make lint` runs every linter
- `make test` runs the Python unit-test suite
- `make quality-check` runs lint and tests without requiring a reference ROM
- `make symbols` validates ld65 source mappings and exports FCEUX ROM/RAM
  labels plus a machine-readable debugger summary
- `make validate-symbols` proves that the debugger configs and generated
  summary still match the current linker symbols
- `make prg-layout-audit` classifies every PRG byte from source mappings and
  checks the reviewed code/data/stream/padding/vector fingerprint
- `make trace-runtime` captures deterministic FCEUX boot and Room 1 traces;
  `make validate-runtime` rechecks their event timing and final RAM state
- `make check` adds byte-identical ROM verification, room-data validation and
  round trips, semantic reconstruction audit, debugger symbols, and every
  subsystem contract without launching the emulator
- `make release-check` starts from an empty build directory, verifies the
  pinned toolchain and private input, runs the static gate, freshly captures all
  ten runtime scenarios, validates the preservation release manifest, then checks
  commit history, worktree cleanliness, and tag absence
- `make source-1-audit` is a compatibility alias for `make release-check`
- `make source-1-post-tag-audit` validates annotated local and published tag
  integrity after release

The former address-ordered preservation listing has been eliminated. New
semantic refinements should continue to follow understood subsystem boundaries
and remain registered in the reconstruction manifest. Formatting remains safe
because the release check rebuilds the ROM and compares every byte with the
reference.

Assembly modules normally contain 300–700 lines. `make lint` requires every
shorter or longer file to have a concrete architectural justification in
`config/reconstruction/source_organization.json`, limits each directory to six ASM files, and
rejects repeated underscore-delimited filename prefixes within one directory.
This keeps compact fixed tables and generated-asset boundaries possible without
allowing subsystem code to drift back into a flat collection of tiny files.

Comments that contain only an address, optionally followed by encoded bytes,
such as `; $B173` or `; $82AD D0 01`, are rejected as
`machine-code-comment`. They duplicate the assembler listing without
explaining behavior. `make format` removes these pure address/byte dumps
automatically; a comment that also explains the code is kept.

Important generated and authored outputs use the shared
`scripts/build/atomic_io.py` writer: a uniquely named sibling temporary file is
flushed before `os.replace` publishes it. ROMs, JSON documents, debugger label
reports, formatted assembly, and WAV previews therefore never expose a partial
destination. The FCEUX Lua capture scripts follow the same temporary-then-rename
contract, and project lint rejects new direct Python `write_text`/`write_bytes`
calls outside the shared owner.
