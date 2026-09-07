# Static PPU update queue

`QueueStaticPpuUpdateStream` at USA `$9471-$9487` / Europe `$948B-$94A1` is
the producer for 18 ROM-resident PPU update programs. The caller supplies a
zero-based stream index in `A`.

If `PpuUpdateStreamPointer + 1` is nonzero, the producer preserves the index on
the current cooperative context's stack and yields through `SwitchThreads`.
Once the NMI consumer clears that high byte, the producer indexes parallel
low- and high-byte tables at USA `$9488`/`$949A` or Europe
`$94A2`/`$94B4` and publishes the selected address through
`PpuUpdateStreamPointer`.

The routine therefore serializes static updates with RAM-buffer producers; it
does not overwrite a stream still being consumed. Eleven call sites select
indices spanning the complete `$00-$11` table. The pointer tables and their
18 target programs occupy USA `$9488-$961A` or Europe `$94A2-$9622`. They are
source-owned by `src/data/static_ppu_update_streams.asm`: pointer order follows
the public indices, while stream labels remain in physical ROM order.

`make ppu-update-report` emits the decoded pointers, commands, PPU addresses,
increments, modes, counts, and payloads. `make ppu-update-audit` binds the
tables and complete payload range to `config/ppu_update_streams.json`, checks
that the 18 programs cover every byte exactly once, and re-encodes each stream
byte-for-byte. The audit is part of `make release-check`.

Source Reconstruction 2.0 adds an independent PAL manifest at
`config/ppu_update_streams_europe.json`. PAL decodes 25 commands in 349
encoded bytes, versus 26 commands in 367 bytes for USA: two text streams
select a regional tile value, and stream 17 uses the shorter European license
message. Run
`make ppu-update-profile-audits` to bind both physical pointer layouts and
localized payloads to their own hashes and round-trip every stream.

The source representation uses `PpuUpdateCommand` headers rather than opaque
control bytes. Each header names its PPU address, repeat/literal mode, and
write count; payload bytes remain exact tile or palette values. The split
pointer tables use `<` and `>` references to the 18 stream labels, so linker
movement cannot silently detach an index from its program.
