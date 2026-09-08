# Verification contract

The preservation proof has three independent inputs:

1. `assets/manifest.json`, the immutable expected identity;
2. `Solomon's Key (U) [!].nes`, the ignored original image;
3. `build/native/solomons_key.nes`, assembled from tracked PRG source plus the
   ignored CHR extracted by `make split`.

`make verify` does not trust any one of these in isolation. It validates both
complete images against the manifest, then performs direct byte comparisons of
the iNES header, PRG, CHR, headerless payload, full image, and extracted CHR.

## Targets

| Target | Contract |
| --- | --- |
| `verify-reference` | original image matches every manifest field |
| `verify-built` | built image matches every manifest field |
| `verify-header` | built and original iNES header/trainer regions match |
| `verify-prg` | built and original 32 KiB PRG match |
| `verify-chr` | CHR inside built and original images match |
| `verify-payload` | headerless PRG+CHR payloads match |
| `verify-rom` | complete headered files match |
| `verify-assets` | ignored extracted CHR matches original CHR |
| `check-assets` | alias for `verify-assets` |
| `verify` | aggregate of every target above |
| `verify-toolchain` | verify pinned assembler, linker, FCEUX, and private input hashes |
| `rom-info` | print and validate identities for original and built images |
| `room-data-audit` | round-trip rooms, RoomMap tile patterns, and Demon Mirror data |
| `roundtrip-formats` | aggregate all implemented byte-level format codecs |
| `symbols` | export audited FCEUX labels and resolved debugger configuration |
| `validate-symbols` | bind configured breakpoints and watch ranges to current linker symbols |
| `validate-revision-symbols` | export and validate the same semantic debugger inventory for one source-built profile |
| `validate-revision-symbol-profiles` | validate profile-selected symbols for required USA and Europe builds |
| `trace-revision-runtime` | freshly capture and validate one profile's ROM- and symbol-bound runtime contract |
| `validate-revision-runtime` | revalidate generated traces against the selected regional manifest |
| `trace-revision-runtimes` | capture the frozen USA and focused European PAL runtime matrices |
| `prg-layout-audit` | classify all 32 KiB as code, data, stream, padding, or vectors |
| `format-coverage-audit` | require one codec owner for every stream-classified segment |
| `trace-runtime` | capture and validate deterministic cold-boot and Room 1 FCEUX traces |
| `trace` | stable alias for fresh runtime capture |
| `validate-runtime` | revalidate existing generated runtime traces without launching FCEUX |
| `scheduler-audit` | check stacks, static/reviewed dynamic entries, and call counts |
| `scheduler-profile-audits` | validate all scheduler tables and 23 known entry codes in USA and PAL |
| `enemy-ai-audit` | check all 28 inline enemy-AI handler pointers |
| `enemy-ai-profile-audits` | prove the complete enemy-AI handler appendix is shared by USA and PAL |
| `enemy-pointer-profile-audits` | validate identical PRG tables against one-byte-shifted PAL runtime pools |
| `item-handler-audit` | check all 29 item selectors, pointers, names, and table hash |
| `item-handler-profile-audits` | validate all semantic item selectors against native USA/PAL handler addresses |
| `ppu-update-audit` | check 18 static stream pointers, coverage, hashes, and byte round trips |
| `ppu-update-profile-audits` | independently round-trip all USA/PAL static PPU programs and localized payloads |
| `object-animation-audit` | round-trip 2,283 bytes of pointers, descriptors, selectors, and frames |
| `object-animation-profile-audits` | independently round-trip relocated USA and PAL animation layouts and prove their shared frame payload |
| `object-motion-audit` | round-trip 524 bytes of pointers, selectors, and vectors |
| `object-motion-profile-audits` | independently round-trip relocated USA and PAL pointer, selector, and motion-vector layouts |
| `title-data-audit` | round-trip packed title streams and the adjacent attract-demo tables |
| `title-data-profile-audits` | independently round-trip relocated USA/PAL title graphics and demo input |
| `audio-data-audit` | check audio pointers, reachability, hashes, and byte round trips |
| `release-audit` | cross-check the revision-3 manifest, identity, scope, evidence, toolchain, profiles, and artifacts |
| `pre-tag-audit` | check clean tree, commit policy, release title, and local/remote tag absence |
| `release-check` | clean rebuild and complete Source 1.0 pre-tag contract, including fresh runtime capture |
| `source-1-audit` | compatibility alias for `release-check` |
| `source-1-post-tag-audit` | verify the local annotated and published tag both peel to `HEAD` |
| `check` | full static development gate without emulator or tag-state checks |

Focused region targets deliberately compare only their named output region.
For example, `verify-prg` can prove that a source-only PRG reconstruction is
correct even while investigating a separate CHR problem. `verify` remains the
release gate and accepts no differences anywhere.

`make reconstruction-audit` complements byte identity by checking accepted
semantic module ranges against the linker map and provenance-ledger addresses
against the ld65 label file. Byte comparison proves output fidelity; this
separate audit proves that reported reconstruction progress matches the built
artifacts. `make scheduler-audit` separately binds packed `StartThread` codes
and their RTS-derived entry addresses to a reviewed manifest, including known
targets reached through dynamically selected codes.
`make enemy-ai-audit` applies the same reviewed-manifest contract to the
inline `JumpWithParams` handler appendix.
`make item-handler-audit` binds selectors `$00-$1C`, map tiles `$06-$22`,
semantic names, target addresses, and the exact 58-byte appendix hash to
`config/validation/item_handlers.json`.
`make ppu-update-audit` decodes the split pointer table and every command in
the adjacent static PPU stream range. It requires exact reviewed hashes,
single coverage of every payload byte, and lossless re-encoding.
`make ppu-update-profile-audits` applies that proof to the independently
addressed and hashed USA and European source builds.

## Public command smoke

`make public-command-smoke` creates a disposable clone containing only tracked
repository files, runs the real public `make lint` workflow there, and requires
the clone to remain clean. This catches stale internal paths, missing tracked
files, and accidental writes without requiring either private ROM image.

The Source Reconstruction 2.1 aggregate gate runs this smoke after the complete
published 2.0 regression gate and before the compatible-minor audit.

`make source-2-minor-audit` also checks that the 2.1 manifest explicitly repeats
the accepted 2.0 profiles, direct runtime coverage, toolchain owner, artifact
hashes, and licensing surface. Its requirement evidence is resolved by type:
Make targets must exist, files and scenario manifests must be present, and
artifact IDs must name declared byte-identical outputs.

## Editor workstation actions

`make editor-ui-smoke-profiles` opens each public studio in a disposable
workspace for both accepted profiles. It invokes the real Save and Build
handlers, renders a preview, exercises Level Studio Play through a mocked
process boundary, produces and dispatches the Sound Studio WAV preview, and
checks both reject and accept branches of dirty-close confirmation. Generated
documents, ROMs, and previews must be nonempty and are removed with the
temporary workspace.

## Failure diagnostics

The comparison script reports the first different byte. PRG failures include
both the PRG offset and mapped CPU address; CHR failures include the 8 KiB CNROM
bank and bank-relative offset. Length differences report `EOF` on the missing
side. This makes a failed proof actionable without opening a hex editor first.

## Typical workflow

```bash
make split
make verify-prg
make verify
make check
make release-check
```

`make clean` removes only `build/`; it preserves the ignored extracted CHR so a
clean rebuild does not require repeating `make split`.
